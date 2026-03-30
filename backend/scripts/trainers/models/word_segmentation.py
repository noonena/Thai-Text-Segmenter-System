"""
Word Segmentation Module
Takes syllables as input and produces word segmentation using Viterbi DP
over the LST20 dictionary.
"""

import sys
import os
import math
from typing import List, Tuple, Set

# Path setup must come before any local imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..'))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', '..', 'nlp_utils'))

from lst20_dictionary_builder import LST20Dictionary
from nlp_utils.features.char_utils import is_number, is_valid_thai_word

# Words that must always be treated as a single unit, regardless of frequency.
# Add entries here when the Viterbi incorrectly splits a known compound.

class WordSegmenter:
    """
    Word segmentation using Viterbi DP over syllable units and the LST20 dictionary.
    """

    def __init__(self, dictionary_path: str, pos_crf=None):
        print(f"   Loading LST20Dictionary from: {dictionary_path}")
        self.dictionary = LST20Dictionary.load(dictionary_path)
        self.pos_crf = pos_crf
        print(f"   Dictionary loaded: {len(self.dictionary.words):,} words")

    def segment(self, syllables: List[str]) -> List[str]:
        """Segment syllables into words using Viterbi DP."""
        return self.segment_with_viterbi(syllables)

    def merge_number_classifier(self, words: List[str]) -> List[str]:
        """Merge a number token followed by a classifier into one token."""
        merged = []
        i = 0
        classifiers = ['ปี', 'คน', 'วัน', 'เดือน', 'ตัว']

        while i < len(words):
            if (
                i < len(words) - 1
                and is_number(words[i])
                and words[i + 1] in classifiers
            ):
                merged.append(words[i] + words[i + 1])
                i += 2
            else:
                merged.append(words[i])
                i += 1

        return merged

    def _get_word_frequency(self, word: str) -> float:
        """Get log frequency score for a word from the dictionary."""
        if word in self.dictionary.word_to_pos:
            total = sum(self.dictionary.word_to_pos[word].values())
            return math.log(total + 1)
        return 0.0

    def _generate_candidates_from_units(self, units: List[str], start: int) -> List[Tuple[str, int]]:
        """Generate word candidates by joining 1–8 consecutive syllables from position start."""
        candidates = []
        n = len(units)
        max_length = min(8, n - start)

        for length in range(1, max_length + 1):
            candidate = "".join(units[start:start + length])
            if self.dictionary.contains(candidate) or is_valid_thai_word(candidate):
                candidates.append((candidate, length))

        return candidates

    def _score_candidate_v2(
        self,
        candidate: str,
        unit_length: int,
        position: int,
        total_length: int,
    ) -> float:
        """
        Score a candidate word. Every word pays BOUNDARY_COST once,
        which discourages over-segmentation. Dictionary words get a
        higher base bonus than unknown words. Multi-syllable words
        get an additional compound_bonus to favour joining syllables.
        """
        BOUNDARY_COST = -0.6

        if self.dictionary.contains(candidate):
            if candidate in self.dictionary.forced:
                return 1000.0  # always wins — never split
            freq = self._get_word_frequency(candidate)
            # Use log(freq) so high-frequency single words don't dominate over
            # longer dictionary matches (e.g. น่า freq=2051 would beat น่ารัก).
            # Larger bonus_per_syl ensures longer dict words win (longest match preference).
            bonus_per_syl = 15.0
            compound_bonus = min(unit_length - 1, 2) * bonus_per_syl
            return BOUNDARY_COST + math.log(freq + 1) + 2.5 + compound_bonus
        elif is_valid_thai_word(candidate):
            if unit_length == 2:
                # Unknown 2-syllable compound — score just above low-frequency part
                # pairs (e.g. ตา+กลม=7.21) but below medium-frequency pairs
                # (e.g. ฉัน+รัก=7.63) to avoid over-merging common separate words.
                return BOUNDARY_COST + 1.0 + 7.1   # = 7.5
            return BOUNDARY_COST - 1.0  # single or 3+ syllable unknown: keep penalty
        else:
            return BOUNDARY_COST + (-2.0)

    def _repair_syllables(self, syllables: List[str]) -> List[str]:
        """
        Pre-processing: fix stolen-consonant errors in syllables BEFORE Viterbi.

        When the syllable CRF merges the coda consonant of one word with the
        onset of the next (e.g. 'วิต'+'กว่า' instead of 'วิตก'+'ว่า'), the
        syllable that loses its coda is left as a fragment not in the dictionary.

        Rule: if syllable[i] is NOT in the dictionary but syllable[i] + syllable[i+1][0]
        IS a real dictionary word AND syllable[i+1][1:] is also a real dictionary word,
        move the first character of syllable[i+1] onto syllable[i].

        Example: ['วิต', 'กว่า']
          'วิต' not in dict, 'วิตก' in dict (real), 'ว่า' in dict (real)
          → ['วิตก', 'ว่า']
        """
        if len(syllables) < 2:
            return syllables

        result = list(syllables)
        i = 0
        while i < len(result) - 1:
            curr = result[i]
            nxt  = result[i + 1]
            if not self.dictionary.contains(curr) and len(nxt) >= 2:
                repaired_curr = curr + nxt[0]
                repaired_nxt  = nxt[1:]
                if self.dictionary.contains(repaired_curr) and self.dictionary.contains(repaired_nxt):
                    result[i]     = repaired_curr
                    result[i + 1] = repaired_nxt
                    i += 2
                    continue
            i += 1

        return result

    def segment_with_viterbi(self, syllables: List[str]) -> List[str]:
        """
        Viterbi word segmentation over syllable units.
        Syllables are the atomic unit — never MTUs.
        Falls back to returning each syllable as its own word if no path is found.
        """
        if not syllables:
            return []

        syllables = self._repair_syllables(syllables)
        n = len(syllables)
        dp = [-float('inf')] * (n + 1)
        back = {}
        dp[0] = 0.0

        for pos in range(n):
            if dp[pos] == -float('inf'):
                continue
            for candidate, length in self._generate_candidates_from_units(syllables, pos):
                next_pos = pos + length
                total_score = dp[pos] + self._score_candidate_v2(candidate, length, pos, n)
                if total_score > dp[next_pos]:
                    dp[next_pos] = total_score
                    back[next_pos] = (pos, candidate)

        if dp[n] == -float('inf'):
            return syllables[:]

        words = []
        pos = n
        while pos > 0:
            prev_pos, word = back[pos]
            words.append(word)
            pos = prev_pos

        words.reverse()
        return self.merge_number_classifier(words)

    def segment_with_viterbi_kbest(
        self, syllables: List[str], k: int = 5
    ) -> List[Tuple[float, List[str]]]:
        """
        Returns the top-k segmentations as (score, words) pairs, best first.
        Used by the comparison/benchmarking script only.
        """
        if not syllables:
            return [(0.0, [])]

        n = len(syllables)
        beams: List[List] = [[] for _ in range(n + 1)]
        beams[0] = [(0.0, [])]

        for pos in range(n):
            beams[pos] = sorted(beams[pos], key=lambda x: -x[0])[:k]
            if not beams[pos]:
                continue
            for base_score, words_so_far in beams[pos]:
                for candidate, length in self._generate_candidates_from_units(syllables, pos):
                    word_score = self._score_candidate_v2(candidate, length, pos, n)
                    next_pos = pos + length
                    beams[next_pos].append(
                        (base_score + word_score, words_so_far + [candidate])
                    )

        beams[n] = sorted(beams[n], key=lambda x: -x[0])[:k]
        if not beams[n]:
            return [(0.0, syllables[:])]
        return beams[n]

    def segment_with_pos_reranking(
        self,
        syllables: List[str],
        pos_crf,
        lam: float = 0.3,
        k: int = 5,
    ) -> List[str]:
        """
        1. Generate top-k candidates via k-best Viterbi.
        2. Score each with the POS CRF (sum of log max-marginal per token).
        3. Return candidate with highest viterbi_score + λ × pos_score.
        Used by the comparison/benchmarking script only.
        """
        try:
            from features.pos_features import extract_features as _pos_features
        except ImportError:
            from pos_features import extract_features as _pos_features

        candidates = self.segment_with_viterbi_kbest(syllables, k=k)
        if candidates:
            best_words: List[str] = candidates[0][1]
        else:
            best_words: List[str] = syllables[:]
        best_combined = -float('inf')

        # If top candidate wins by a large margin, Viterbi is confident —
        # skip POS reranking to avoid overriding correct decisions (e.g. รายงาน).
        if len(candidates) >= 2:
            gap = candidates[0][0] - candidates[1][0]
            if gap > 5.0:
                return self.merge_number_classifier(best_words)

        for viterbi_score, words in candidates:
            if not words:
                continue
            features = _pos_features(words)
            marginals = pos_crf.predict_marginals([features])[0]
            pos_score = sum(
                math.log(max(m.values(), default=1e-10) + 1e-10)
                for m in marginals
            )
            combined = viterbi_score + lam * pos_score
            if combined > best_combined:
                best_combined = combined
                best_words = words

        return self.merge_number_classifier(best_words)
