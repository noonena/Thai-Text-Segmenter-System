"""
CRF POS Tagger Trainer — LST20 Corpus (official train/eval/test splits)
"""

# MUST be first (before sklearn_crfsuite import)
import os
os.environ["TQDM_DISABLE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import glob
import pickle
import sys
import sklearn_crfsuite
from sklearn.metrics import classification_report
from collections import defaultdict

# Add backend to path for imports
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, 'scripts'))

from nlp_utils.features.pos_features import extract_features, extract_labels


# ======================
# CONFIG
# ======================
import argparse

_args_parser = argparse.ArgumentParser(add_help=False)
_args_parser.add_argument('--modified-corpus', action='store_true',
    help='Train on LST20_Resegmented instead of original LST20_Corpus')
_known, _ = _args_parser.parse_known_args()

_corpus_name = 'LST20_Resegmented' if _known.modified_corpus else 'LST20_Corpus'
_model_name  = 'pos_crf_model_modified.pkl' if _known.modified_corpus else 'pos_crf_model.pkl'

BASE_DIR   = os.path.join(SCRIPT_DIR, '..', '..', '..', 'data', _corpus_name)
TRAIN_DIR  = os.path.join(BASE_DIR, 'train')
DEV_DIR    = os.path.join(BASE_DIR, 'eval')
TEST_DIR   = os.path.join(BASE_DIR, 'test')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '..', '..', 'models')
MODEL_PATH = os.path.join(OUTPUT_DIR, _model_name)

MAX_SENTENCES = 100000   # increase if memory allows


# ======================
# DATA READER
# ======================
def read_lst20_for_pos(filepath):
    sentences = []
    words, tags = [], []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                if words:
                    sentences.append((words, tags))
                    words, tags = [], []
                continue

            parts = line.split("\t")
            if len(parts) >= 2:
                word, pos = parts[0], parts[1]
                if word == "_":
                    continue
                words.append(word)
                tags.append(pos)

    if words:
        sentences.append((words, tags))

    return sentences


# ======================
# DATA PREP
# ======================
def prepare_training_data(train_dir):
    X, y = [], []
    files = sorted(glob.glob(os.path.join(train_dir, "*.txt")))
    print(f"Found {len(files)} LST20 files in {os.path.basename(train_dir)}")

    for filepath in files:
        for words, pos_tags in read_lst20_for_pos(filepath):
            X.append(extract_features(words))
            y.append(extract_labels(pos_tags))

            if len(X) >= MAX_SENTENCES:
                print(f"Stopped at MAX_SENTENCES = {MAX_SENTENCES}")
                return X, y

    print(f"Total sentences: {len(X)}")
    return X, y


# ======================
# TRAINING
# ======================
def train_pos_tagger(X_train, y_train):
    print("Training CRF POS tagger...")

    crf = sklearn_crfsuite.CRF(
        algorithm="lbfgs",
        c1=0.1,
        c2=0.1,
        max_iterations=100,
        all_possible_transitions=False,
        verbose=False
    )

    crf.fit(X_train, y_train)
    print("Training finished")
    return crf


# ======================
# EVALUATION
# ======================
def evaluate_split(crf, X, y, split_name: str) -> dict:
    """Evaluate POS tagger on a named split using gold words → gold tags."""
    y_pred = crf.predict(X)

    y_flat      = [t for sent in y      for t in sent]
    y_pred_flat = [t for sent in y_pred for t in sent]

    print(f"\n{'='*60}")
    print(f"EVALUATION: {split_name}  ({len(X)} sentences, {len(y_flat)} tokens)")
    print(f"{'='*60}")
    print(classification_report(y_flat, y_pred_flat, digits=3))

    correct  = sum(r == p for r, p in zip(y_flat, y_pred_flat))
    accuracy = correct / len(y_flat) if y_flat else 0
    print(f"  Overall accuracy: {accuracy:.4f}  ({correct}/{len(y_flat)})")

    # Top confusions — which (gold, pred) pairs occur most
    confusion: dict = defaultdict(int)
    for gold, pred in zip(y_flat, y_pred_flat):
        if gold != pred:
            confusion[(gold, pred)] += 1

    print(f"\n  Top-10 confusions (gold -> pred):")
    for (gold, pred), count in sorted(confusion.items(), key=lambda x: -x[1])[:10]:
        print(f"    {gold:8} -> {pred:8}  {count:5}")

    tag_stats: dict = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    for gold, pred in zip(y_flat, y_pred_flat):
        if gold == pred:
            tag_stats[gold]["tp"] += 1
        else:
            tag_stats[gold]["fn"] += 1
            tag_stats[pred]["fp"] += 1
    per_tag = {}
    for tag, s in tag_stats.items():
        tp, fp, fn = s["tp"], s["fp"], s["fn"]
        p = tp / (tp + fp) if (tp + fp) > 0 else 0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        f = 2 * p * r / (p + r) if (p + r) > 0 else 0
        per_tag[tag] = {"p": round(p, 4), "r": round(r, 4), "f1": round(f, 4), "n": tp + fn}

    return {'tag_accuracy': accuracy, 'total_tags': len(y_flat), 'per_tag': per_tag}


# ======================
# MAIN
# ======================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 80)
    print(f"CRF POS TAGGER — {_corpus_name}")
    print(f"Model output: {_model_name}")
    print("=" * 80)

    print("\nLoading train...")
    X_train, y_train = prepare_training_data(TRAIN_DIR)
    print("\nLoading dev (eval)...")
    X_dev,   y_dev   = prepare_training_data(DEV_DIR)
    print("\nLoading test...")
    X_test,  y_test  = prepare_training_data(TEST_DIR)

    print(f"\nSplit: train={len(X_train)}  dev={len(X_dev)}  test={len(X_test)}")

    if not X_train:
        print("No training data found!")
        return

    crf = train_pos_tagger(X_train, y_train)

    dev_scores  = evaluate_split(crf, X_dev,  y_dev,  "DEV")
    test_scores = evaluate_split(crf, X_test, y_test, "TEST")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  {'Split':<6}  {'Accuracy':>10}")
    print(f"  {'-'*6}  {'-'*10}")
    for split_name, scores in [("DEV", dev_scores), ("TEST", test_scores)]:
        print(f"  {split_name:<6}  {scores['tag_accuracy']:>10.4f}")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(crf, f)

    print(f"\nModel saved to: {MODEL_PATH}")

    # ── Save test results to JSON ──────────────────────────────
    import json
    from datetime import datetime
    RESULTS_DIR = os.path.join(SCRIPT_DIR, '..', '..', 'results')
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, 'pos_results.json'), 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "sentences_evaluated": len(X_test),
            "accuracy": round(test_scores['tag_accuracy'], 4),
            "total_tags": test_scores['total_tags'],
            "per_tag": test_scores['per_tag'],
        }, f, indent=2)
    print(f"Results saved to: pos_results.json")


if __name__ == "__main__":
    main()
