"""
SAFE CRF POS Tagger Trainer (Windows / Python 3.13)

Fixes:
- WinError 1450 (stdout / tqdm crash)
- CRF memory explosion
- all_possible_transitions blow-up
- Over-scaling during feature debugging
"""

# 🔥 MUST be first (before sklearn_crfsuite import)
import os
os.environ["TQDM_DISABLE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import glob
import pickle
import sklearn_crfsuite
from sklearn.metrics import classification_report
from utils.pos_features import extract_features, extract_labels


# ======================
# CONFIG
# ======================
TRAIN_DIR = r"D:\project\word_wrapping\script\data\AIFORTHAI-LST20Corpus\LST20_Corpus\train"
OUTPUT_DIR = r"D:\project\ThaitextSegmentersystem\backend\models"
MODEL_PATH = os.path.join(OUTPUT_DIR, "pos_crf_model.pkl")

MAX_SENTENCES = 2000   # 🔥 SAFE START (increase later)
TRAIN_RATIO = 0.8


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
    files = glob.glob(os.path.join(train_dir, "*.txt"))
    print(f"Found {len(files)} LST20 files")

    for filepath in files:
        for words, pos_tags in read_lst20_for_pos(filepath):
            X.append(extract_features(words))
            y.append(extract_labels(pos_tags))

            if len(X) >= MAX_SENTENCES:
                print(f"⚠️ Stopped at MAX_SENTENCES = {MAX_SENTENCES}")
                return X, y

    return X, y


# ======================
# TRAINING
# ======================
def train_pos_tagger(X_train, y_train):
    print("Training CRF POS tagger (SAFE MODE)...")

    crf = sklearn_crfsuite.CRF(
        algorithm="lbfgs",
        c1=0.1,
        c2=0.1,
        max_iterations=50,
        all_possible_transitions=False,  # 🔥 critical
        verbose=False                    # 🔥 critical
    )

    crf.fit(X_train, y_train)
    print("Training finished")
    return crf


# ======================
# EVALUATION
# ======================
def evaluate_model(crf, X_test, y_test):
    y_pred = crf.predict(X_test)

    y_test_flat = [t for sent in y_test for t in sent]
    y_pred_flat = [t for sent in y_pred for t in sent]

    print("\n" + "=" * 80)
    print("POS Tagger Evaluation")
    print("=" * 80)

    print(classification_report(y_test_flat, y_pred_flat, digits=3))


# ======================
# MAIN
# ======================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 80)
    print("CRF POS TAGGER — SAFE TRAINING PIPELINE")
    print("=" * 80)

    X, y = prepare_training_data(TRAIN_DIR)

    split = int(len(X) * TRAIN_RATIO)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    print(f"Train sentences: {len(X_train)}")
    print(f"Test sentences : {len(X_test)}")

    crf = train_pos_tagger(X_train, y_train)
    evaluate_model(crf, X_test, y_test)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(crf, f)

    print(f"\n✅ Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
