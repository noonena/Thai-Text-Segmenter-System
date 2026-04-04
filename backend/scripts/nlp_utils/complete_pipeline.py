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
TRAINERS_DIR = os.path.join(SCRIPTS_DIR, "trainers")           # scripts/trainers/
MODELS_DIR  = os.path.join(SCRIPTS_DIR, "trainers", "models")  # scripts/trainers/models/
UTILS_DIR   = os.path.join(SCRIPT_DIR, "features")         # scripts/nlp_utils/features/

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, SCRIPTS_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, TRAINERS_DIR)
sys.path.insert(0, MODELS_DIR)
sys.path.insert(0, UTILS_DIR)

from shared.syllable_decoder import bmes_to_syllables

# =====================================================
# Imports (no "models." prefix since MODELS_DIR is in path)
# =====================================================
from lst20_dictionary_builder import LST20Dictionary  # type: ignore # required for pickle to deserialize lst20_dictionary.pkl
from viterbi_segmenter import ViterbiSegmenter
from features.mtu_features import segment_text_to_mtus
from features.syllable_utils import orthographic_syllabify


class ThaiTextSegmenter:
    """MTU → Syllable → Word → POS"""

    def __init__(
        self,
        mtu_model_path: str,
        syllable_model_path: str,
        word_segmentation_path: str,
        pos_model_path: str,
    ):
        print("Initializing Thai NLP Pipeline...")

        print(f"Loading MTU model: {mtu_model_path}")
        with open(mtu_model_path, "rb") as f:
            self.mtu_crf = pickle.load(f)

        print(f"Loading syllable model: {syllable_model_path}")
        with open(syllable_model_path, "rb") as f:
            self.syllable_crf = pickle.load(f)

        print(f"Loading POS model: {pos_model_path}")
        with open(pos_model_path, "rb") as f:
            self.pos_crf = pickle.load(f)

        print(f"Loading Word Segmenter: {word_segmentation_path}")
        with open(word_segmentation_path, "rb") as f:
            dictionary = pickle.load(f)
        self.word_segmenter = ViterbiSegmenter(dictionary, pos_crf=self.pos_crf)
        self.dictionary = self.word_segmenter.dictionary

        print("Pipeline ready\n")

    # =====================================================
    # MTU (CRF model)
    # =====================================================
    def _segment_to_mtus(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        try:
            from features.mtu_features import segment_text_to_mtus
            mtus_nested, _, _ = segment_text_to_mtus(text, self.mtu_crf)
            return ["".join(mtu) for mtu in mtus_nested]
        except Exception as e:
            print(f"[WARN] MTU segmentation failed for '{text}': {e}")
            return []

    # =====================================================
    # SYLLABLE
    # =====================================================
    def _segment_to_syllables(self, mtus: List[str]) -> List[str]:
        if not mtus:
            return []
        from features.syllable_utils import extract_features_for_sentence

        # Features include NFA (orthographic_syllabify) boundary as a signal
        features = extract_features_for_sentence(mtus)
        labels   = self.syllable_crf.predict([features])[0]
        return bmes_to_syllables(mtus, labels)

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
    # WORD - Using Viterbi for better compound word detection
    # =====================================================
    def segment_words(self, text: str) -> List[str]:
        import re
        if not text or not text.strip():
            return []

        results = []
        for chunk in re.finditer(r'[\u0E00-\u0E7F]+|[^\u0E00-\u0E7F]+', text):
            token = chunk.group()
            if re.fullmatch(r'[\u0E00-\u0E7F]+', token):
                try:
                    mtus = self._segment_to_mtus(token)
                    syllables = self._segment_to_syllables(mtus)
                    results.extend(self.word_segmenter.segment(syllables))
                except Exception as e:
                    print(f"[WARN] Word segmentation failed for '{token}': {e}")
                    results.append(token)
            else:
                results.append(token)
        return results

    # =====================================================
    # WORD + POS + SYLLABLE
    # =====================================================
    def segment_with_pos_and_syllables(self, text: str, show_debug=False) -> List[Tuple[str, str, List[str]]]:
        from features.pos_features import extract_features

        # MTU
        mtus = self._segment_to_mtus(text)

        # Syllable
        syllables = self._segment_to_syllables(mtus)

        # Word (k-best Viterbi reranked by POS CRF)
        fixed_words = self.word_segmenter.segment_with_pos_reranking(syllables, self.pos_crf)

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
    POS_MODEL      = os.path.join(BASE, "pos_crf_model_modified.pkl")

    segmenter = ThaiTextSegmenter(MTU_MODEL, SYLLABLE_MODEL, DICT_MODEL, POS_MODEL)

    tests = [
        "ผมชอบมันฝรั่งทอด",
        "นั่นมือถืออะไร",
        "ผ้าไหมลายสวยมาก",
        "เที่ยวโอซาก้า",
        "ภัยธรรมชาติทำให้แห้งแล้งเป็นอย่างมากล้ำค่าสุดล้ำ",
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
