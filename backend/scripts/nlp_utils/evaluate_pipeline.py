"""
Word Segmentation Pipeline Evaluation

Runs the full pipeline (MTU → Syllable → Word) on the LST20 test set
and saves word_seg_results.json. MTU, Syllable, and POS metrics are
saved by their respective trainers.
"""

import os
import sys
import json
import pickle
from datetime import datetime
from typing import List, Tuple

# =====================================================
# Path setup
# =====================================================
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPTS_DIR, ".."))
MODELS_DIR    = os.path.join(SCRIPTS_DIR, "trainers", "models")
TRAINERS_DIR  = os.path.join(SCRIPTS_DIR, "trainers")
UTILS_DIR     = os.path.join(SCRIPT_DIR, "features")

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, SCRIPTS_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, MODELS_DIR)
sys.path.insert(0, TRAINERS_DIR)
sys.path.insert(0, UTILS_DIR)

from shared.lst20_reader import read_lst20_dir
from shared.syllable_decoder import bmes_to_syllables

# =====================================================
# Config
# =====================================================
BASE           = os.path.join(BACKEND_DIR, "models")
MTU_MODEL_PATH = os.path.join(BASE, "mtu_crf_model.pkl")
SYL_MODEL_PATH = os.path.join(BASE, "syllable_crf_model.pkl")
DICT_PATH      = os.path.join(BASE, "lst20_dictionary.pkl")
TEST_DIR       = os.path.join(BACKEND_DIR, "..", "data", "LST20_Corpus", "test")
RESULTS_DIR    = os.path.join(BACKEND_DIR, "results")
MAX_SENTENCES  = 50000


def prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return p, r, f


def word_boundaries(words: List[str]) -> set:
    bounds = set()
    pos = 0
    for w in words:
        pos += len(w)
        bounds.add(pos)
    return bounds


# =====================================================
# Word Segmentation Evaluation
# =====================================================
def evaluate_word(mtu_crf, syl_crf, word_segmenter, sentences: list) -> dict:
    from mtu_features import segment_text_to_mtus
    from syllable_utils import extract_features_for_sentence

    tp = fp = fn = 0
    errors = []

    for sent_idx, (words, _) in enumerate(sentences):
        if sent_idx % 100 == 0:
            print(f"  Word: {sent_idx}/{len(sentences)} sentences...", flush=True)
        gold_words = [w for w in words if w]
        sentence   = "".join(gold_words)
        if not sentence:
            continue

        mtus_nested, _, _ = segment_text_to_mtus(sentence, mtu_crf)
        mtus = ["".join(m) for m in mtus_nested]

        syl_feats  = extract_features_for_sentence(mtus)
        syl_labels = syl_crf.predict([syl_feats])[0]
        syllables  = bmes_to_syllables(mtus, syl_labels)

        pred_words = word_segmenter.segment_with_viterbi(syllables)

        gold_bounds = word_boundaries(gold_words)
        pred_bounds = word_boundaries(pred_words)

        correct = len(gold_bounds & pred_bounds)
        tp += correct
        fp += len(pred_bounds - gold_bounds)
        fn += len(gold_bounds - pred_bounds)

        if correct < len(gold_bounds) and len(errors) < 10:
            errors.append({
                "sentence": sentence[:60],
                "gold": gold_words[:10],
                "pred": pred_words[:10],
            })

    p, r, f = prf(tp, fp, fn)
    return {"precision": p, "recall": r, "f1": f, "errors": errors}


# =====================================================
# Main
# =====================================================
def main():
    print("=" * 70)
    print("WORD SEGMENTATION EVALUATION")
    print("=" * 70)

    print("\nLoading MTU model...")
    with open(MTU_MODEL_PATH, "rb") as f: mtu_crf = pickle.load(f)
    print("Loading syllable model...")
    with open(SYL_MODEL_PATH, "rb") as f: syl_crf = pickle.load(f)

    from viterbi_segmenter import ViterbiSegmenter
    print("Loading word segmenter...")
    word_segmenter = ViterbiSegmenter(DICT_PATH)
    print("Models loaded.")

    print(f"\nReading LST20 test data (max {MAX_SENTENCES} sentences)...")
    sentences = read_lst20_dir(TEST_DIR, max_sentences=MAX_SENTENCES)
    print(f"Loaded {len(sentences)} sentences.\n")

    print("Running word segmentation evaluation...")
    w = evaluate_word(mtu_crf, syl_crf, word_segmenter, sentences)
    print(f"  P/R/F1 : {w['precision']:.3f} / {w['recall']:.3f} / {w['f1']:.3f}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, "word_seg_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "sentences_evaluated": len(sentences),
            "precision": round(w["precision"], 4),
            "recall": round(w["recall"], 4),
            "f1": round(w["f1"], 4),
            "errors": w["errors"][:5],
        }, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
