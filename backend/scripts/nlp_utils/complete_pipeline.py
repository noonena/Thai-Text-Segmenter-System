"""
Complete Thai NLP Pipeline

Pipeline:
Text
 → MTU Segmentation (CRF)
 → Syllable Segmentation (CRF)
 → Word Segmentation (Dictionary longest match)
 → POS Tagging (CRF)
"""

import os
import sys
import pickle
from typing import List, Tuple

# =====================================================
# Fix Windows encoding
# =====================================================
if sys.platform == "win32":
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)
    except (AttributeError, TypeError):
        import locale
        locale.setlocale(locale.LC_ALL, 'Thai_Thailand.65001')

# =====================================================
# Path setup
# =====================================================
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))   # scripts/nlp_utils/
SCRIPTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))  # scripts/
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPTS_DIR, "..")) # backend/
MODELS_DIR  = os.path.join(SCRIPTS_DIR, "models")          # scripts/models/
UTILS_DIR   = os.path.join(SCRIPT_DIR, "utils")            # scripts/nlp_utils/utils/

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, SCRIPTS_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, MODELS_DIR)
sys.path.insert(0, UTILS_DIR)

# =====================================================
# Imports (no "models." prefix since MODELS_DIR is in path)
# =====================================================
from lst20_dictionary_builder import LST20Dictionary
from word_segmentation import WordSegmenter
from features import segment_text_to_mtus_rules


class ThaiTextSegmenter:
    """MTU → Syllable → Word → POS"""

    def __init__(
        self,
        mtu_model_path: str,        # kept for API compatibility, no longer used
        syllable_model_path: str,
        word_segmentation_path: str,
        pos_model_path: str,
    ):
        print("Initializing Thai NLP Pipeline...")
        print("MTU stage: using TCC rules directly (no model needed)")

        print(f"Loading syllable model: {syllable_model_path}")
        with open(syllable_model_path, "rb") as f:
            self.syllable_crf = pickle.load(f)

        print(f"Loading Word Segmenter: {word_segmentation_path}")
        self.word_segmenter = WordSegmenter(word_segmentation_path)
        self.dictionary = self.word_segmenter.dictionary

        print(f"Loading POS model: {pos_model_path}")
        with open(pos_model_path, "rb") as f:
            self.pos_crf = pickle.load(f)

        print("Pipeline ready\n")

    # =====================================================
    # MTU
    # =====================================================
    def _segment_to_mtus(self, text: str) -> List[str]:
        mtus_nested, _, _ = segment_text_to_mtus_rules(text)
        return ["".join(mtu) for mtu in mtus_nested]

    # =====================================================
    # SYLLABLE
    # =====================================================
    def _segment_to_syllables(self, mtus: List[str]) -> List[str]:
        from syllable_features import extract_features_for_sentence

        features = extract_features_for_sentence(mtus)
        labels = self.syllable_crf.predict([features])[0]

        syllables = []
        current = []

        for mtu, label in zip(mtus, labels):
            if label == "S":
                if current:
                    syllables.append("".join(current))
                    current = []
                syllables.append(mtu)
            elif label == "B":
                current = [mtu]
            elif label == "M":
                current.append(mtu)
            elif label == "E":
                current.append(mtu)
                syllables.append("".join(current))
                current = []

        if current:
            syllables.append("".join(current))

        return syllables

    # =====================================================
    # SYLLABLE → WORD ALIGNMENT
    # =====================================================
    def _map_syllables_to_words(self, words: List[str], syllables: List[str]) -> List[List[str]]:
        result = []
        s_idx = 0

        for word in words:
            word_syllables = []
            reconstructed = ""

            while s_idx < len(syllables) and reconstructed != word:
                syl = syllables[s_idx]
                reconstructed += syl
                word_syllables.append(syl)
                s_idx += 1

                if len(word_syllables) > 10:
                    break

            result.append(word_syllables)

        return result

    # =====================================================
    # WORD
    # =====================================================
    def segment_words(self, text: str) -> List[str]:
        mtus = self._segment_to_mtus(text)
        syllables = self._segment_to_syllables(mtus)
        return self.word_segmenter.segment_from_mtus_with_syllables(mtus, syllables)

    # =====================================================
    # WORD + POS + SYLLABLE
    # =====================================================
    def segment_with_pos_and_syllables(self, text: str, show_debug=False) -> List[Tuple[str, str, List[str]]]:
        from pos_features import extract_features

        # MTU
        mtus = self._segment_to_mtus(text)

        # Syllable
        syllables = self._segment_to_syllables(mtus)

        # Word
        fixed_words = self.word_segmenter.segment_from_mtus_with_syllables(mtus, syllables)

        # POS tagging
        features = extract_features(fixed_words)
        pos_tags = self.pos_crf.predict([features])[0]

        # Syllable alignment
        word_syllables = self._map_syllables_to_words(fixed_words, syllables)

        if show_debug:
            print("MTUs      :", " | ".join(mtus))
            print("Syllables :", " | ".join(syllables))
            print("Words     :", " | ".join(fixed_words))
            print("POS Tags  :", " | ".join(pos_tags))

        return list(zip(fixed_words, pos_tags, word_syllables))


# =====================================================
# MAIN
# =====================================================
def main():
    # .pkl models are in backend/models/
    BASE = os.path.join(BACKEND_DIR, "models")

    MTU_MODEL      = os.path.join(BASE, "mtu_crf_model.pkl")
    SYLLABLE_MODEL = os.path.join(BASE, "syllable_crf_model.pkl")
    DICT_MODEL     = os.path.join(BASE, "lst20_dictionary.pkl")
    POS_MODEL      = os.path.join(BASE, "pos_crf_model.pkl")

    segmenter = ThaiTextSegmenter(MTU_MODEL, SYLLABLE_MODEL, DICT_MODEL, POS_MODEL)

    tests = [
        "ผมชอบมันฝรั่งทอด",
        "นั่นมือถืออะไร",
        "ผ้าไหมลายสวยมาก",
        "เที่ยวโอซาก้า",
    ]

    for t in tests:
        print("=" * 80)
        print("Input:", t)
        result = segmenter.segment_with_pos_and_syllables(t, show_debug=True)
        for w, p, s in result:
            print(f"{w:15} → {p:6} | syllables: {'-'.join(s)}")

    print("\n✅ Pipeline complete")


if __name__ == "__main__":
    main()