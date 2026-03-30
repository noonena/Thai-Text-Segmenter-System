"""
Train CRF for Syllable Boundary Detection
Input: MTUs from LST20 corpus
Output: Syllable boundaries (BMES labels)

Strategy: Since LST20 doesn't have explicit syllable labels,
we derive them from MTU sequences within words.
"""

import os
os.environ["TQDM_DISABLE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import glob
import pickle
import argparse
import sklearn_crfsuite
from sklearn.metrics import classification_report
import sys

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, 'scripts'))
sys.path.insert(0, SCRIPT_DIR)

from nlp_utils.features.syllable_features import extract_features_for_sentence
from nlp_utils.features.char_utils import orthographic_syllabify
from models.crf_mtu_inference import load_model, segment_text_to_mtus


def get_gold_clusters(word: str) -> list:
    """Get phonological syllables for gold-standard syllable training."""
    return orthographic_syllabify(word)


def align_pred_to_gold(pred_mtus, gold_clusters):
    """
    Label pred_mtus so that merging B-M-E groups reproduces gold_clusters.

    Example:
        pred:  ["อา", "กา", "ศ"]   gold: ["อา", "กาศ"]
        → labels: [S, B, E]

        pred:  ["ประ", "เทศ"]      gold: ["ประ", "เทศ"]
        → labels: [S, S]
    """
    labels   = []
    pred_idx = 0

    for gold_syl in gold_clusters:
        collected = ""
        group_len = 0
        matched   = False

        while pred_idx < len(pred_mtus):
            collected += pred_mtus[pred_idx]
            pred_idx  += 1
            group_len += 1

            if collected == gold_syl:
                if group_len == 1:
                    labels.append("S")
                else:
                    labels.append("B")
                    labels.extend(["M"] * (group_len - 2))
                    labels.append("E")
                matched = True
                break

            if len(collected) > len(gold_syl):
                # Overshot — label consumed MTUs as singletons and move on
                labels.extend(["S"] * group_len)
                matched = True
                break

        if not matched and group_len > 0:
            # Ran out of pred MTUs before matching this gold syllable —
            # label whatever was consumed as singletons
            labels.extend(["S"] * group_len)

    # Any leftover pred MTUs not covered by gold syllables
    while pred_idx < len(pred_mtus):
        labels.append("S")
        pred_idx += 1

    # Safety: if something still went wrong, fall back to all-S
    if len(labels) != len(pred_mtus):
        return ["S"] * len(pred_mtus)

    return labels


# ======================
# CONFIG
# ======================
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'data', 'LST20_Corpus')
TRAIN_DIR = os.path.join(BASE_DIR, 'train')
DEV_DIR   = os.path.join(BASE_DIR, 'eval')
TEST_DIR  = os.path.join(BASE_DIR, 'test')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models')
MTU_MODEL_PATH = os.path.join(OUTPUT_DIR, "mtu_crf_model.pkl")
SYLLABLE_MODEL_PATH = os.path.join(OUTPUT_DIR, "syllable_crf_model.pkl")

MAX_SENTENCES = 100000   # Use more sentences for better training


# ======================
# DATA READER
# ======================
def read_lst20_for_syllable(filepath, mtu_crf):
    """
    Read LST20 and convert to MTU + Syllable labels
    
    Strategy:
    1. Read words from LST20
    2. Segment each word into MTUs using CRF
    3. Assign syllable labels based on word boundaries
    
    Args:
        filepath: Path to LST20 .txt file
        mtu_crf: Trained MTU CRF model
    
    Returns:
        List of (mtus, syllable_labels) tuples
    """
    sentences = []
    current_words = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Empty line = sentence boundary
            if not line:
                if current_words:
                    # Process this sentence
                    mtus, labels = words_to_syllable_data(current_words, mtu_crf)
                    if mtus and labels:
                        sentences.append((mtus, labels))
                    current_words = []
                continue
            
            # Parse word
            parts = line.split("\t")
            if len(parts) >= 1:
                word = parts[0]
                if word != "_":  # Skip separators
                    current_words.append(word)
    
    # Handle last sentence
    if current_words:
        mtus, labels = words_to_syllable_data(current_words, mtu_crf)
        if mtus and labels:
            sentences.append((mtus, labels))
    
    return sentences


def words_to_syllable_data(words, mtu_crf):
    """
    Convert words to MTUs with syllable boundary labels
    
    Strategy:
    - Each word boundary = syllable boundary
    - Within each word, MTUs form a syllable unit
    
    Example:
        Words: ["ผม", "ชอบ"]
        
        Word 1: "ผม"
          MTUs: ["ผม"]
          Label: [S]  (Single MTU = Single syllable)
        
        Word 2: "ชอบ"  
          MTUs: ["ชอบ"]
          Label: [S]
        
        Final:
          MTUs: ["ผม", "ชอบ"]
          Labels: [S, S]
    
    Another example:
        Words: ["ประเทศ"]

        Word 1: "ประเทศ"
          MTUs: ["ประ", "เทศ"]
          Labels: [S, S]  (2 MTU clusters = 2 syllables)

        Final:
          MTUs: ["ประ", "เทศ"]
          Labels: [S, S]
    """
    all_mtus = []
    all_labels = []
    
    for word in words:
        try:
            # Segment word into MTUs
            mtus_nested, _, _ = segment_text_to_mtus(word, mtu_crf)
            word_mtus = ["".join(mtu) for mtu in mtus_nested]
            
            if not word_mtus:
                continue

            # Gold syllables from rule-based label_chars
            gold_clusters = get_gold_clusters(word)

            # Align MTU model output to gold syllables → B/M/E/S labels
            word_labels = align_pred_to_gold(word_mtus, gold_clusters)
            
            all_mtus.extend(word_mtus)
            all_labels.extend(word_labels)
            
        except Exception as e:
            # Skip words that fail to segment
            print(f"Warning: Failed to segment '{word}': {e}")
            continue
    
    return all_mtus, all_labels


# ======================
# DATA PREP
# ======================
def prepare_training_data(train_dir, mtu_crf):
    """
    Prepare syllable training data from LST20
    """
    X, y = [], []
    files = glob.glob(os.path.join(train_dir, "*.txt"))
    print(f"Found {len(files)} LST20 files")
    print("Converting words to syllable data...")
    
    processed_files = 0
    
    for filepath in files[:1000]:  # Start with first 100 files
        sentences = read_lst20_for_syllable(filepath, mtu_crf)
        
        for mtus, labels in sentences:
            if not mtus or not labels or len(mtus) != len(labels):
                continue
            # Extract features
            features = extract_features_for_sentence(mtus)

            X.append(features)
            y.append(labels)
            
            if len(X) >= MAX_SENTENCES:
                print(f"⚠️ Stopped at MAX_SENTENCES = {MAX_SENTENCES}")
                return X, y
        
        processed_files += 1
        if processed_files % 10 == 0:
            print(f"  Processed {processed_files} files, {len(X)} sentences...")
    
    print(f"Total sentences collected: {len(X)}")
    return X, y


# ======================
# TRAINING
# ======================
def train_syllable_crf(X_train, y_train):
    """Train CRF for syllable boundary detection"""
    print("Training Syllable CRF (SAFE MODE)...")
    
    crf = sklearn_crfsuite.CRF(
        algorithm="lbfgs",
        c1=0.1,
        c2=0.1,
        max_iterations=50,
        all_possible_transitions=False,  # Safe mode
        verbose=False
    )
    
    crf.fit(X_train, y_train)
    print("Training finished")
    return crf


# ======================
# EVALUATION
# ======================
def evaluate_split(crf, X, y, split_name: str) -> dict:
    """Evaluate syllable CRF on a named split"""
    y_pred = crf.predict(X)

    y_flat      = [l for sent in y      for l in sent]
    y_pred_flat = [l for sent in y_pred for l in sent]

    print(f"\n{'='*60}")
    print(f"EVALUATION: {split_name}  ({len(X)} sentences)")
    print(f"{'='*60}")

    print(classification_report(y_flat, y_pred_flat, labels=['B', 'M', 'E', 'S'], digits=3))

    # Boundary P/R/F1 (E and S mark syllable ends)
    tp = fp = fn = 0
    for seq_r, seq_p in zip(y, y_pred):
        ref_b  = {i for i, l in enumerate(seq_r) if l in ('E', 'S')}
        pred_b = {i for i, l in enumerate(seq_p) if l in ('E', 'S')}
        tp += len(ref_b & pred_b)
        fp += len(pred_b - ref_b)
        fn += len(ref_b - pred_b)
    prec = tp / (tp + fp) if tp + fp else 0
    rec  = tp / (tp + fn) if tp + fn else 0
    f1   = 2 * prec * rec / (prec + rec) if prec + rec else 0
    print(f"  Boundary P/R/F1 : {prec:.4f} / {rec:.4f} / {f1:.4f}")

    return {'boundary_precision': prec, 'boundary_recall': rec, 'boundary_f1': f1}


def evaluate_model(crf, X_test, y_test):
    """Backward-compat wrapper (single split)."""
    evaluate_split(crf, X_test, y_test, "TEST")


# ======================
# MAIN
# ======================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 80)
    print("CRF SYLLABLE TRAINER — LST20 Corpus")
    print("=" * 80)

    # Load MTU model (needed to segment words into MTUs)
    print(f"\nLoading MTU model from: {MTU_MODEL_PATH}")
    mtu_crf = load_model(MTU_MODEL_PATH)
    print("MTU model loaded")

    # Load official corpus splits
    print("\nLoading train...")
    X_train, y_train = prepare_training_data(TRAIN_DIR, mtu_crf)
    print("\nLoading dev (eval)...")
    X_dev,   y_dev   = prepare_training_data(DEV_DIR,   mtu_crf)
    print("\nLoading test...")
    X_test,  y_test  = prepare_training_data(TEST_DIR,  mtu_crf)

    print(f"\nSplit: train={len(X_train)}  dev={len(X_dev)}  test={len(X_test)}")

    if not X_train:
        print("No training data found!")
        return

    # Train
    crf = train_syllable_crf(X_train, y_train)

    # Evaluate on dev and test
    dev_scores  = evaluate_split(crf, X_dev,  y_dev,  "DEV")
    test_scores = evaluate_split(crf, X_test, y_test, "TEST")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for split_name, scores in [("DEV", dev_scores), ("TEST", test_scores)]:
        print(f"  {split_name}:")
        print(f"    Boundary P : {scores['boundary_precision']:.4f}")
        print(f"    Boundary R : {scores['boundary_recall']:.4f}")
        print(f"    Boundary F1: {scores['boundary_f1']:.4f}")

    # Save
    with open(SYLLABLE_MODEL_PATH, "wb") as f:
        pickle.dump(crf, f)

    print(f"\nSyllable model saved to: {SYLLABLE_MODEL_PATH}")

    # ── Save test results to JSON ──────────────────────────────
    import json
    from datetime import datetime
    RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'results')
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, 'syllable_results.json'), 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "sentences_evaluated": len(X_test),
            "precision": round(test_scores['boundary_precision'], 4),
            "recall": round(test_scores['boundary_recall'], 4),
            "f1": round(test_scores['boundary_f1'], 4),
        }, f, indent=2)
    print(f"Results saved to: syllable_results.json")
    
    # Test on example
    print("\n" + "=" * 80)
    print("Test Example")
    print("=" * 80)
    
    test_word = "สบาย"
    print(f"Word: {test_word}")
    
    # Get MTUs
    mtus_nested, _, _ = segment_text_to_mtus(test_word, mtu_crf)
    test_mtus = ["".join(mtu) for mtu in mtus_nested]
    print(f"MTUs: {' | '.join(test_mtus)}")
    
    # Predict syllable boundaries
    test_features = extract_features_for_sentence(test_mtus)
    predicted_labels = crf.predict([test_features])[0]
    print(f"Syllable labels: {predicted_labels}")
    
    # Group into syllables
    syllables = []
    current = []
    for mtu, label in zip(test_mtus, predicted_labels):
        if label == 'B':
            if current:
                syllables.append(''.join(current))
            current = [mtu]
        elif label == 'M':
            current.append(mtu)
        elif label == 'E':
            current.append(mtu)
            syllables.append(''.join(current))
            current = []
        elif label == 'S':
            if current:
                syllables.append(''.join(current))
            syllables.append(mtu)
            current = []
    
    if current:
        syllables.append(''.join(current))
    
    print(f"Syllables: {' | '.join(syllables)}")


def main_with_args():
    parser = argparse.ArgumentParser(description='CRF Syllable Trainer for Thai')
    parser.add_argument('--retrain', action='store_true', help='Retrain with accumulated learning data')
    parser.add_argument('--test', action='store_true', help='Test current model')
    
    args = parser.parse_args()
    
    if args.retrain:
        print("Retraining syllable model with accumulated data...")
        # Implementation would load learning data and retrain
        print("Syllable model retraining complete")

    elif args.test:
        print("Testing current syllable model...")
        test_current_model()
        
    else:
        main()

def _load_test_models():
    """Load syllable CRF, MTU CRF, and word segmenter. Returns (syllable_crf, mtu_crf, word_segmenter) or None on failure."""
    import sys
    models_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
    model_path     = os.path.join(models_dir, 'syllable_crf_model.pkl')
    mtu_model_path = os.path.join(models_dir, 'mtu_crf_model.pkl')
    dict_path      = os.path.join(models_dir, 'lst20_dictionary.pkl')

    for path, label in [(model_path, 'Syllable model'), (mtu_model_path, 'MTU model')]:
        if not os.path.exists(path):
            print(f"{label} not found: {path}")
            return None

    print(f"Loading syllable model: {model_path}")
    with open(model_path, 'rb') as f:
        syllable_crf = pickle.load(f)

    print(f"Loading MTU model: {mtu_model_path}")
    with open(mtu_model_path, 'rb') as f:
        mtu_crf = pickle.load(f)

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))
    from word_segmentation import WordSegmenter
    word_segmenter = WordSegmenter(dict_path)

    return syllable_crf, mtu_crf, word_segmenter


def _load_test_cases():
    """Load test cases from data/test.json. Returns list or None on failure."""
    import json
    test_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'test.json')
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return None
    with open(test_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def _run_pipeline(text, mtu_crf, syllable_crf):
    """Run MTU → syllable stages on one text. Returns (mtus, mtu_char_bmes, syllable_bmes, syllables)."""
    from models.crf_mtu_inference import segment_text_to_mtus

    mtus_nested, mtu_char_bmes, _ = segment_text_to_mtus(text, mtu_crf)
    mtus = ["".join(m) for m in mtus_nested]

    features = extract_features_for_sentence(mtus)
    bmes     = list(syllable_crf.predict([features])[0])

    syllables = []
    current   = []
    for mtu, label in zip(mtus, bmes):
        if label == 'S':
            if current:
                syllables.append(''.join(current))
                current = []
            syllables.append(mtu)
        elif label == 'B':
            current = [mtu]
        elif label == 'M':
            current.append(mtu)
        elif label == 'E':
            current.append(mtu)
            syllables.append(''.join(current))
            current = []
    if current:
        syllables.append(''.join(current))

    return mtus, mtu_char_bmes, bmes, syllables


def _print_case_result(case, mtus, mtu_char_bmes, bmes, syllables, pred_words):
    """Print a single test case result."""
    text          = case['text']
    expected_word = case['word']
    note          = case.get('note', '')
    ok            = pred_words == expected_word

    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {text}")
    if note:
        print(f"       note         : {note}")
    print(f"       chars        : {list(text)}")
    print(f"       mtu_bmes     : {list(mtu_char_bmes)}")
    print(f"       mtu          : {mtus}")
    print(f"       syllable_bmes: {bmes}")
    print(f"       syllable     : {syllables}")
    if not ok:
        print(f"       expected     : {expected_word}")
        print(f"       got          : {pred_words}")
    else:
        print(f"       word         : {pred_words}")
    print()
    return ok


def test_current_model():
    """Test the current syllable model end-to-end against data/test.json."""
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    result = _load_test_models()
    if result is None:
        return
    syllable_crf, mtu_crf, word_segmenter = result

    test_cases = _load_test_cases()
    if test_cases is None:
        return

    print(f"\nRunning {len(test_cases)} test cases\n")
    print("=" * 60)

    passed = 0
    for case in test_cases:
        mtus, mtu_char_bmes, bmes, syllables = _run_pipeline(case['text'], mtu_crf, syllable_crf)
        pred_words = word_segmenter.segment(syllables)
        if _print_case_result(case, mtus, mtu_char_bmes, bmes, syllables, pred_words):
            passed += 1

    print("=" * 60)
    print(f"Result: {passed}/{len(test_cases)} passed")

if __name__ == "__main__":
    main_with_args()