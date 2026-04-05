"""
Viterbi Segmenter
Generic Viterbi DP segmenter used across the pipeline.
Takes syllables as input and produces word segmentation
over the LST20 dictionary.
"""

import os
import sys
import math
from typing import List, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRAINERS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'trainers'))

sys.path.insert(0, TRAINERS_DIR)
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'features'))

from lst20_dictionary_builder import LST20Dictionary
from features.char_utils import is_number, is_valid_thai_word


class ViterbiSegmenter:
    """
    Viterbi DP segmenter over syllable units and the LST20 dictionary.
    """

    def __init__(self, dictionary_input, pos_crf=None):
        if isinstance(dictionary_input, str):
            print(f"   Loading LST20Dictionary from: {dictionary_input}")
            self.dictionary = LST20Dictionary.load(dictionary_input)
        else:
            self.dictionary = dictionary_input
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

    def _syllable_to_words(self, syllables: List[str], start: int) -> List[Tuple[str, int]]:
        """Try joining 1–8 syllables from start. Return those that are valid words."""
        candidates = []
        n = len(syllables)
        max_length = min(8, n - start)

        for syllable_count in range(1, max_length + 1):
            candidate = "".join(syllables[start : (start + syllable_count)])
            if self.dictionary.contains(candidate) or is_valid_thai_word(candidate):
                candidates.append((candidate, syllable_count))

        return candidates

    def _score_word(
        self,
        candidate: str,
        syllable_count: int,
        position: int,
        total_length: int,
    ) -> float:
        BOUNDARY_COST = -0.6

        if self.dictionary.contains(candidate):
            if candidate in self.dictionary.forced:
                return 1000.0
            freq = self._get_word_frequency(candidate)
            bonus_per_syl = 15.0
            compound_bonus = min(syllable_count - 1, 2) * bonus_per_syl
            return BOUNDARY_COST + math.log(freq + 1) + 2.5 + compound_bonus
        elif is_valid_thai_word(candidate):
            if syllable_count == 2:
                return BOUNDARY_COST + 1.0 + 7.1
            return BOUNDARY_COST - 1.0
        else:
            return BOUNDARY_COST + (-2.0)

    def _repair_syllables(self, syllables: List[str]) -> List[str]:
        """Fix stolen-consonant errors in syllables before Viterbi."""
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
            for candidate, length in self._syllable_to_words(syllables, pos):
                next_pos = pos + length
                total_score = dp[pos] + self._score_word(candidate, length, pos, n)
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
        """Returns the top-k segmentations as (score, words) pairs, best first."""
        if not syllables:
            return [(0.0, [])]

        syllables = self._repair_syllables(syllables)

        n = len(syllables)
        beams: List[List] = [[] for _ in range(n + 1)]
        beams[0] = [(0.0, [])]

        for pos in range(n):
            beams[pos] = sorted(beams[pos], key=lambda x: -x[0])[:k]
            if not beams[pos]:
                continue
            for base_score, words_so_far in beams[pos]:
                for candidate, length in self._syllable_to_words(syllables, pos):
                    word_score = self._score_word(candidate, length, pos, n)
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
        """Rerank k-best word paths using POS confidence."""
        # try:
        from features.pos_features import extract_features as _pos_features
        # except ImportError:
        #     from pos_features import extract_features as _pos_features

        kbest_word_paths = self.segment_with_viterbi_kbest(syllables, k=k)
        if kbest_word_paths:
            best_words: List[str] = kbest_word_paths[0][1]
        else:
            best_words: List[str] = syllables[:]
        best_final_score = -float('inf')

        if len(kbest_word_paths) >= 2:
            top_score_gap = kbest_word_paths[0][0] - kbest_word_paths[1][0]
            if top_score_gap > 5.0:
                return self.merge_number_classifier(best_words)

        for word_path_score, words in kbest_word_paths:
            if not words:
                continue
            features = _pos_features(words)
            marginals = pos_crf.predict_marginals([features])[0]
            pos_rerank_score = sum(
                math.log(max(m.values(), default=1e-10) + 1e-10)
                for m in marginals
            )
            final_score = word_path_score + lam * pos_rerank_score
            if final_score > best_final_score:
                best_final_score = final_score
                best_words = words

        return self.merge_number_classifier(best_words)
