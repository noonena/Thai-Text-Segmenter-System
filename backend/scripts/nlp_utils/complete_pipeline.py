"""
Complete Thai NLP Pipeline

Pipeline:
Text
 → MTU Segmentation (CRF)
 → Syllable Segmentation (CRF)
 → Word Segmentation (Viterbi with dictionary + context)
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
from crf_mtu_inference import segment_text_to_mtus


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

        # MTU stage uses TCC rules (no model needed)
        if mtu_model_path and os.path.exists(mtu_model_path):
            print(f"Loading MTU model: {mtu_model_path}")
            with open(mtu_model_path, "rb") as f:
                self.mtu_crf = pickle.load(f)
        else:
            print("MTU stage: using TCC rules (no model)")
            self.mtu_crf = None

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
    # MTU (using TCC rules)
    # =====================================================
    def _segment_to_mtus(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        try:
            # Use TCC rules (apply_tcc_rules) instead of CRF
            from features import apply_tcc_rules
            mtus = apply_tcc_rules(text)
            return mtus
        except Exception as e:
            print(f"[WARN] MTU segmentation failed for '{text}': {e}")
            return []

    # =====================================================
    # SYLLABLE
    # =====================================================
    def _segment_to_syllables(self, mtus: List[str]) -> List[str]:
        if not mtus:
            return []
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
    # WORD - Legacy method with syllable guidance
    # =====================================================
    def segment_words(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        
        try:
            mtus = self._segment_to_mtus(text)
            syllables = self._segment_to_syllables(mtus)
            return self.word_segmenter.segment_from_mtus_with_syllables(mtus, syllables)
        except Exception as e:
            print(f"[WARN] Word segmentation failed for '{text}': {e}")
            return [text]  # Return original text as single word

    # =====================================================
    # WORD + POS + SYLLABLE
    # =====================================================
    def segment_with_pos_and_syllables(self, text: str, show_debug=False) -> List[Tuple[str, str, List[str]]]:
        from pos_features import extract_features

        # MTU
        mtus = self._segment_to_mtus(text)

        # Syllable
        syllables = self._segment_to_syllables(mtus)

        # Word (using syllable-guided segmentation)
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