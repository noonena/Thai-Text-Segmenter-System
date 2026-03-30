"""
CRF-based MTU Segmentation Training Pipeline
Based on Kannikar Paripremkul's dissertation (2020)

This script:
1. Reads LST20 corpus .txt files
2. Converts word-level data to character-level with MTU labels
3. Extracts features based on Table 3.3-3.5 from the dissertation
4. Trains a CRF model for MTU boundary detection
5. Outputs trained model for inference
"""

import os
import sys
import glob
import pickle
from pathlib import Path
from typing import List, Tuple, Dict
import sklearn_crfsuite
from sklearn_crfsuite import metrics

# Add backend to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, 'scripts'))

from nlp_utils.features.mtu_features import format_mtus, segment_text_to_mtus, load_model, char2features,label_chars
from nlp_utils.features.char_utils import get_char_type, AKSON_NAM_CLUSTERS

def extract_features_and_labels(text: str) -> Tuple[List[Dict], List[str]]:
    """Extract CRF features and labels from text"""
    chars = list(text)
    
    # Get MTU labels (simplified - ideally from gold annotations)
    labels = []
    for char in chars:
        # This is a placeholder - you should derive labels from LST20 cluster tags
        labels.append("S")  # Simplified for now
    
    # Extract features for each character
    features = [char2features(chars, i) for i in range(len(chars))]
    
    return features, labels


def read_lst20_file(filepath: str) -> List[Tuple[str, str, str, str]]:
    """
    Read LST20 format file
    Returns: [(word, pos, ne, cluster), ...]
    """
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 4:
                word, pos, ne, cluster = parts[:4]
                data.append((word, pos, ne, cluster))
    return data

def prepare_training_data(train_dir: str):
    """
    Returns X, y, word_bounds:
      X           — CRF feature sequences
      y           — silver BMES label sequences (from label_chars)
      word_bounds — per sentence: list of char positions where each word ends
                    (used as partial truth signal: every word end = MTU boundary)
    """
    X, y, word_bounds = [], [], []

    txt_files = sorted(glob.glob(os.path.join(train_dir, "*.txt")))
    print(f"Found {len(txt_files)} training files")

    for file_idx, filepath in enumerate(txt_files):
        if file_idx % 200 == 0:
            print(f"  {file_idx}/{len(txt_files)} files, {len(X)} sentences so far...", flush=True)
        lst20_data = read_lst20_file(filepath)

        sentence_chars, sentence_labels, sentence_word_bounds = [], [], []

        for word, pos, ne, cluster in lst20_data:
            if word == "_" or word.strip() == "":
                if sentence_chars:
                    X.append([char2features(sentence_chars, i) for i in range(len(sentence_chars))])
                    y.append(sentence_labels)
                    word_bounds.append(sentence_word_bounds[:])
                    sentence_chars, sentence_labels, sentence_word_bounds = [], [], []
                continue

            offset = len(sentence_chars)
            chars  = list(word)
            labels = label_chars(word)
            sentence_chars.extend(chars)
            sentence_labels.extend(labels)
            sentence_word_bounds.append(offset + len(chars) - 1)  # last char index of this word

        if sentence_chars:
            X.append([char2features(sentence_chars, i) for i in range(len(sentence_chars))])
            y.append(sentence_labels)
            word_bounds.append(sentence_word_bounds[:])

    print(f"Prepared {len(X)} sentences total")
    return X, y, word_bounds


def labels_to_spans(labels: List[str]) -> set:
    """Convert BMES label sequence to set of (start, end) char-index spans."""
    spans = set()
    start = 0
    for i, label in enumerate(labels):
        if label in ('S', 'E'):
            spans.add((start, i))
            start = i + 1
        elif label == 'B':
            start = i
    return spans


def evaluate_split(crf, X, y, word_bounds, split_name: str) -> dict:
    print(f"\n{'='*60}")
    print(f"EVALUATION: {split_name}  ({len(X)} sentences)")
    print(f"{'='*60}")

    y_pred = crf.predict(X)

    # ── 1. BMES accuracy (silver) ─────────────────────────────
    correct = total = 0
    for seq_r, seq_p in zip(y, y_pred):
        for r, p in zip(seq_r, seq_p):
            total += 1
            if r == p:
                correct += 1
    bmes_acc = correct / total if total else 0
    print(f"  BMES accuracy        : {bmes_acc:.4f}  ({correct}/{total} chars)")

    # ── 2. Boundary P/R/F1 (silver) ──────────────────────────
    tp = fp = fn = 0
    for seq_r, seq_p in zip(y, y_pred):
        ref_b  = {i for i, l in enumerate(seq_r) if l in ('E', 'S')}
        pred_b = {i for i, l in enumerate(seq_p) if l in ('E', 'S')}
        tp += len(ref_b & pred_b)
        fp += len(pred_b - ref_b)
        fn += len(ref_b - pred_b)
    bp = tp / (tp + fp) if tp + fp > 0 else 0
    br = tp / (tp + fn) if tp + fn > 0 else 0
    bf1 = 2 * bp * br / (bp + br) if bp + br > 0 else 0
    print(f"  Boundary  P/R/F1     : {bp:.4f} / {br:.4f} / {bf1:.4f}")

    # ── 3. Exact MTU match F1 (silver) ───────────────────────
    mtu_tp = mtu_fp = mtu_fn = 0
    for seq_r, seq_p in zip(y, y_pred):
        ref_spans  = labels_to_spans(seq_r)
        pred_spans = labels_to_spans(seq_p)
        mtu_tp += len(ref_spans & pred_spans)
        mtu_fp += len(pred_spans - ref_spans)
        mtu_fn += len(ref_spans - pred_spans)
    mp  = mtu_tp / (mtu_tp + mtu_fp) if mtu_tp + mtu_fp > 0 else 0
    mr  = mtu_tp / (mtu_tp + mtu_fn) if mtu_tp + mtu_fn > 0 else 0
    mf1 = 2 * mp * mr / (mp + mr) if mp + mr > 0 else 0
    print(f"  Exact MTU match F1   : {mp:.4f} / {mr:.4f} / {mf1:.4f}")

    # ── 4. Word-boundary recall (partial truth) ───────────────
    # Every word-final char MUST be an MTU boundary (E or S).
    # Measures how often CRF agrees with this hard linguistic constraint.
    wb_correct = wb_total = 0
    for seq_p, bounds in zip(y_pred, word_bounds):
        for pos in bounds:
            wb_total += 1
            if pos < len(seq_p) and seq_p[pos] in ('E', 'S'):
                wb_correct += 1
    wb_recall = wb_correct / wb_total if wb_total else 0
    print(f"  Word-boundary recall : {wb_recall:.4f}  ({wb_correct}/{wb_total})  ← partial truth")

    return {
        'bmes_acc': bmes_acc,
        'boundary_precision': bp,
        'boundary_recall': br,
        'boundary_f1': bf1,
        'mtu_match_f1': mf1,
        'word_boundary_recall': wb_recall,
    }


def train_crf_model(X_train: List[List[Dict]], y_train: List[List[str]]) -> sklearn_crfsuite.CRF:
    print("Training CRF model...")
    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',
        c1=0.05,
        c2=0.05,
        max_iterations=200,
        all_possible_transitions=True,
        verbose=True
    )
    crf.fit(X_train, y_train)
    print("Training complete!")
    return crf


def save_model(crf: sklearn_crfsuite.CRF, output_path: str):
    with open(output_path, 'wb') as f:
        pickle.dump(crf, f)
    print(f"Model saved to: {output_path}")


def main():
    BASE       = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '..', '..', '..', 'data', 'LST20_Corpus')
    TRAIN_DIR  = os.path.join(BASE, 'train')
    DEV_DIR    = os.path.join(BASE, 'eval')
    TEST_DIR   = os.path.join(BASE, 'test')
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '..', '..', 'models')
    MODEL_PATH = os.path.join(OUTPUT_DIR, "mtu_crf_model.pkl")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("="*60)
    print("MTU CRF TRAINER — LST20 Corpus")
    print("="*60)

    # ── Prepare data from official splits ────────────────────
    print("\nLoading train...")
    X_train, y_train, wb_train = prepare_training_data(TRAIN_DIR)
    print("\nLoading dev (eval)...")
    X_dev, y_dev, wb_dev       = prepare_training_data(DEV_DIR)
    print("\nLoading test...")
    X_test, y_test, wb_test    = prepare_training_data(TEST_DIR)

    if not X_train:
        print("No training data found!")
        return

    print(f"\nSplit: train={len(X_train)}  dev={len(X_dev)}  test={len(X_test)}")

    # ── Train ─────────────────────────────────────────────────
    crf = train_crf_model(X_train, y_train)

    # ── Evaluate ──────────────────────────────────────────────
    dev_scores  = evaluate_split(crf, X_dev,  y_dev,  wb_dev,  "DEV")
    test_scores = evaluate_split(crf, X_test, y_test, wb_test, "TEST")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for split, scores in [("DEV", dev_scores), ("TEST", test_scores)]:
        print(f"  {split}:")
        print(f"    BMES accuracy        : {scores['bmes_acc']:.4f}")
        print(f"    Boundary F1          : {scores['boundary_f1']:.4f}")
        print(f"    Exact MTU match F1   : {scores['mtu_match_f1']:.4f}")
        print(f"    Word-boundary recall : {scores['word_boundary_recall']:.4f}")

    # ── Save model ────────────────────────────────────────────
    save_model(crf, MODEL_PATH)

    # ── Save test results to JSON ──────────────────────────────
    import json
    from datetime import datetime
    RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'results')
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, 'mtu_results.json'), 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "sentences_evaluated": len(X_test),
            "label_accuracy": round(test_scores['bmes_acc'], 4),
            "precision": round(test_scores['boundary_precision'], 4),
            "recall": round(test_scores['boundary_recall'], 4),
            "f1": round(test_scores['boundary_f1'], 4),
        }, f, indent=2)
    print(f"Results saved to: mtu_results.json")


if __name__ == "__main__":
    main()
