"""
Pipeline Evaluation — measures error at each stage separately.

Stages:
  1. MTU      — CRF output vs rule-generated labels (silver reference)
  2. Syllable — syllable boundaries vs word boundaries
  3. Word     — predicted words vs LST20 gold words  (main metric)
  4. POS      — predicted tags vs LST20 gold tags (on gold words)
"""

import os
import sys
import glob
import pickle
from collections import defaultdict
from typing import List, Tuple, Dict

# =====================================================
# Path setup (mirrors complete_pipeline.py)
# =====================================================
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPTS_DIR, ".."))
MODELS_DIR    = os.path.join(SCRIPTS_DIR, "models")
TRAINERS_DIR  = os.path.join(SCRIPTS_DIR, "trainers")
UTILS_DIR     = os.path.join(SCRIPT_DIR, "utils")

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, SCRIPTS_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, MODELS_DIR)
sys.path.insert(0, TRAINERS_DIR)
sys.path.insert(0, UTILS_DIR)

# =====================================================
# Config
# =====================================================
BASE            = os.path.join(BACKEND_DIR, "models")
MTU_MODEL_PATH  = os.path.join(BASE, "mtu_crf_model.pkl")
SYL_MODEL_PATH  = os.path.join(BASE, "syllable_crf_model.pkl")
DICT_PATH       = os.path.join(BASE, "lst20_dictionary.pkl")
POS_MODEL_PATH  = os.path.join(BASE, "pos_crf_model.pkl")

TEST_DIR        = r"D:\project\word_wrapping\script\data\AIFORTHAI-LST20Corpus\LST20_Corpus\test"
MAX_SENTENCES   = 500


# =====================================================
# LST20 reader — returns list of (words, pos_tags)
# Uses "_" token as sentence boundary (same as trainer)
# =====================================================
def read_lst20_sentences(test_dir: str, max_sentences: int) -> List[Tuple[List[str], List[str]]]:
    sentences = []
    files = sorted(glob.glob(os.path.join(test_dir, "*.txt")))

    current_words, current_pos = [], []

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) < 2:
                    continue
                word = parts[0]
                pos  = parts[1]

                # "_" = sentence boundary in LST20
                if word == "_":
                    if current_words:
                        sentences.append((current_words[:], current_pos[:]))
                        current_words, current_pos = [], []
                        if len(sentences) >= max_sentences:
                            return sentences
                else:
                    current_words.append(word)
                    current_pos.append(pos)

        if current_words:
            sentences.append((current_words[:], current_pos[:]))
            current_words, current_pos = [], []

        if len(sentences) >= max_sentences:
            break

    return sentences


# =====================================================
# Helpers
# =====================================================
def prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return p, r, f


def word_boundaries(words: List[str]) -> set:
    """Return set of character positions where a word ends."""
    bounds = set()
    pos = 0
    for w in words:
        pos += len(w)
        bounds.add(pos)
    return bounds


def syllables_from_mtus(mtus: List[str], labels: List[str]) -> List[str]:
    syllables, current = [], []
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
# Stage 1 — MTU
# =====================================================
def evaluate_mtu(mtu_crf, sentences: list) -> dict:
    from features import char2features, segment_text_to_mtus
    from crf_mtu_trainer import word_to_mtu_labels

    label_correct = label_total = 0
    tp = fp = fn = 0

    for words, _ in sentences:
        for word in words:
            if not word:
                continue
            chars = list(word)
            ref   = word_to_mtu_labels(word)
            feats = [char2features(chars, i) for i in range(len(chars))]
            pred  = mtu_crf.predict([feats])[0]

            if len(ref) != len(pred):
                continue

            for r, p in zip(ref, pred):
                label_total += 1
                if r == p:
                    label_correct += 1

            ref_bounds  = {i for i, l in enumerate(ref)  if l in ("E", "S")}
            pred_bounds = {i for i, l in enumerate(pred) if l in ("E", "S")}
            tp += len(ref_bounds & pred_bounds)
            fp += len(pred_bounds - ref_bounds)
            fn += len(ref_bounds - pred_bounds)

    p, r, f = prf(tp, fp, fn)
    return {
        "label_accuracy": label_correct / label_total if label_total else 0,
        "precision": p, "recall": r, "f1": f,
        "total_chars": label_total,
    }


# =====================================================
# Stage 2 — Syllable
# =====================================================
def evaluate_syllable(mtu_crf, syl_crf, sentences: list) -> dict:
    from features import segment_text_to_mtus
    from syllable_features import extract_features_for_sentence

    tp = fp = fn = 0

    for words, _ in sentences:
        sentence = "".join(words)
        if not sentence:
            continue

        mtus_nested, _, _ = segment_text_to_mtus(sentence, mtu_crf)
        mtus = ["".join(m) for m in mtus_nested]
        if not mtus:
            continue

        feats  = extract_features_for_sentence(mtus)
        labels = syl_crf.predict([feats])[0]

        # Gold: word boundaries mapped to MTU indices
        gold_bounds = set()
        char_pos = 0
        for word in words:
            char_pos += len(word)
            cumlen = 0
            for j, mtu in enumerate(mtus):
                cumlen += len(mtu)
                if cumlen == char_pos:
                    gold_bounds.add(j)
                    break

        pred_bounds = {i for i, l in enumerate(labels) if l in ("E", "S")}

        tp += len(gold_bounds & pred_bounds)
        fp += len(pred_bounds - gold_bounds)
        fn += len(gold_bounds - pred_bounds)

    p, r, f = prf(tp, fp, fn)
    return {"precision": p, "recall": r, "f1": f}


# =====================================================
# Stage 3 — Word segmentation
# =====================================================
def evaluate_word(mtu_crf, syl_crf, word_segmenter, sentences: list) -> dict:
    from features import segment_text_to_mtus
    from syllable_features import extract_features_for_sentence

    tp = fp = fn = 0
    errors = []

    for words, _ in sentences:
        gold_words = [w for w in words if w]
        sentence   = "".join(gold_words)
        if not sentence:
            continue

        # Run pipeline
        mtus_nested, _, _ = segment_text_to_mtus(sentence, mtu_crf)
        mtus = ["".join(m) for m in mtus_nested]

        syl_feats  = extract_features_for_sentence(mtus)
        syl_labels = syl_crf.predict([syl_feats])[0]
        syllables  = syllables_from_mtus(mtus, syl_labels)

        pred_words = word_segmenter.segment_with_viterbi(mtus, syllables)

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
# Stage 4 — POS (on gold words to isolate POS errors)
# =====================================================
def evaluate_pos(pos_crf, sentences: list) -> dict:
    from pos_features import extract_features

    correct = total = 0
    tag_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    for words, pos_tags in sentences:
        gold_words = [w for w in words if w]
        gold_tags  = [t for t in pos_tags if t]
        if not gold_words:
            continue

        feats     = extract_features(gold_words)
        pred_tags = pos_crf.predict([feats])[0]

        for gold, pred in zip(gold_tags, pred_tags):
            total += 1
            if gold == pred:
                correct += 1
                tag_stats[gold]["tp"] += 1
            else:
                tag_stats[gold]["fn"] += 1
                tag_stats[pred]["fp"] += 1

    per_tag = {}
    for tag, s in tag_stats.items():
        pp, rr, ff = prf(s["tp"], s["fp"], s["fn"])
        per_tag[tag] = {"p": pp, "r": rr, "f1": ff, "n": s["tp"] + s["fn"]}

    return {
        "accuracy": correct / total if total else 0,
        "total": total,
        "per_tag": per_tag,
    }


# =====================================================
# Main
# =====================================================
def main():
    print("=" * 70)
    print("PIPELINE EVALUATION")
    print("=" * 70)

    # Load models
    print("\nLoading models...")
    with open(MTU_MODEL_PATH,  "rb") as f: mtu_crf  = pickle.load(f)
    with open(SYL_MODEL_PATH,  "rb") as f: syl_crf  = pickle.load(f)
    with open(POS_MODEL_PATH,  "rb") as f: pos_crf  = pickle.load(f)

    from word_segmentation import WordSegmenter
    word_segmenter = WordSegmenter(DICT_PATH)
    print("Done.")

    # Load test data
    print(f"\nReading LST20 test data (max {MAX_SENTENCES} sentences)...")
    sentences = read_lst20_sentences(TEST_DIR, MAX_SENTENCES)
    print(f"Loaded {len(sentences)} sentences.\n")

    # ── Stage 1 ──────────────────────────────────────
    print("=" * 70)
    print("STAGE 1: MTU")
    print("=" * 70)
    m = evaluate_mtu(mtu_crf, sentences)
    print(f"  Label accuracy  : {m['label_accuracy']:.3f}")
    print(f"  Boundary P/R/F1 : {m['precision']:.3f} / {m['recall']:.3f} / {m['f1']:.3f}")
    print(f"  Total chars     : {m['total_chars']}")

    # ── Stage 2 ──────────────────────────────────────
    print("\n" + "=" * 70)
    print("STAGE 2: SYLLABLE  (vs word boundaries)")
    print("=" * 70)
    s = evaluate_syllable(mtu_crf, syl_crf, sentences)
    print(f"  P/R/F1 : {s['precision']:.3f} / {s['recall']:.3f} / {s['f1']:.3f}")
    print("  Note: current model treats each word as one syllable")

    # ── Stage 3 ──────────────────────────────────────
    print("\n" + "=" * 70)
    print("STAGE 3: WORD SEGMENTATION  ← main metric")
    print("=" * 70)
    w = evaluate_word(mtu_crf, syl_crf, word_segmenter, sentences)
    print(f"  P/R/F1 : {w['precision']:.3f} / {w['recall']:.3f} / {w['f1']:.3f}")
    print(f"\n  Error examples:")
    for ex in w["errors"][:5]:
        print(f"    Input : {ex['sentence']}")
        print(f"    Gold  : {' | '.join(ex['gold'])}")
        print(f"    Pred  : {' | '.join(ex['pred'])}")
        print()

    # ── Stage 4 ──────────────────────────────────────
    print("=" * 70)
    print("STAGE 4: POS  (evaluated on gold words)")
    print("=" * 70)
    p = evaluate_pos(pos_crf, sentences)
    print(f"  Accuracy : {p['accuracy']:.3f}  (over {p['total']} tags)")
    print(f"\n  Per-tag F1 (top 15 by frequency):")
    sorted_tags = sorted(p["per_tag"].items(), key=lambda x: -x[1]["n"])
    for tag, v in sorted_tags[:15]:
        print(f"    {tag:6}  P={v['p']:.3f}  R={v['r']:.3f}  F1={v['f1']:.3f}  (n={v['n']})")

    # ── Summary ──────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Stage 1 MTU       F1 : {m['f1']:.3f}")
    print(f"  Stage 2 Syllable  F1 : {s['f1']:.3f}")
    print(f"  Stage 3 Word seg  F1 : {w['f1']:.3f}  ← focus here")
    print(f"  Stage 4 POS  acc     : {p['accuracy']:.3f}")

    stages = [("MTU", m["f1"]), ("Syllable", s["f1"]),
              ("Word seg", w["f1"]), ("POS", p["accuracy"])]
    weakest = min(stages, key=lambda x: x[1])
    print(f"\n  Weakest stage → {weakest[0]}  ({weakest[1]:.3f})")

    # ── Save results to JSON ──────────────────────────
    import json
    from datetime import datetime

    results = {
        "timestamp": datetime.now().isoformat(),
        "sentences_evaluated": len(sentences),
        "mtu": {
            "label_accuracy": round(m["label_accuracy"], 4),
            "precision": round(m["precision"], 4),
            "recall": round(m["recall"], 4),
            "f1": round(m["f1"], 4),
        },
        "syllable": {
            "precision": round(s["precision"], 4),
            "recall": round(s["recall"], 4),
            "f1": round(s["f1"], 4),
        },
        "word_seg": {
            "precision": round(w["precision"], 4),
            "recall": round(w["recall"], 4),
            "f1": round(w["f1"], 4),
            "errors": w["errors"][:5],
        },
        "pos": {
            "accuracy": round(p["accuracy"], 4),
            "total_tags": p["total"],
            "per_tag": {
                tag: {"p": round(v["p"], 4), "r": round(v["r"], 4),
                      "f1": round(v["f1"], 4), "n": v["n"]}
                for tag, v in p["per_tag"].items()
            },
        },
        "weakest_stage": weakest[0],
    }

    out_path = os.path.join(BACKEND_DIR, "results", "evaluation_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  Results saved to: {out_path}")


if __name__ == "__main__":
    main()
