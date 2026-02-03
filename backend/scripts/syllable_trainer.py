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
import sklearn_crfsuite
from sklearn.metrics import classification_report
import sys

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

from utils.syllable_features import extract_features_for_sentence
from crf_mtu_inference import load_model, segment_text_to_mtus


# ======================
# CONFIG
# ======================
TRAIN_DIR = r"D:\project\word_wrapping\script\data\AIFORTHAI-LST20Corpus\LST20_Corpus\train"
OUTPUT_DIR = r"D:\project\ThaitextSegmentersystem\backend\models"
MTU_MODEL_PATH = os.path.join(OUTPUT_DIR, "mtu_crf_model.pkl")
SYLLABLE_MODEL_PATH = os.path.join(OUTPUT_DIR, "syllable_crf_model.pkl")

MAX_SENTENCES = 2000   # Start with 2000 sentences
TRAIN_RATIO = 0.8


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
        Words: ["สบาย"]
        
        Word 1: "สบาย"
          MTUs: ["ส", "บา", "ย"]
          Labels: [B, M, E]  (Multiple MTUs = One syllable)
        
        Final:
          MTUs: ["ส", "บา", "ย"]
          Labels: [B, M, E]
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
            
            # Assign syllable labels
            # Strategy: Treat each word as one syllable unit
            num_mtus = len(word_mtus)
            
            if num_mtus == 1:
                # Single MTU word = Single syllable
                word_labels = ['S']
            else:
                # Multiple MTUs = One syllable with B-M-E structure
                word_labels = ['B'] + ['M'] * (num_mtus - 2) + ['E']
            
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
    
    for filepath in files[:100]:  # Start with first 100 files
        sentences = read_lst20_for_syllable(filepath, mtu_crf)
        
        for mtus, labels in sentences:
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
def evaluate_model(crf, X_test, y_test):
    """Evaluate syllable CRF"""
    y_pred = crf.predict(X_test)
    
    # Flatten for evaluation
    y_test_flat = [label for sent in y_test for label in sent]
    y_pred_flat = [label for sent in y_pred for label in sent]
    
    print("\n" + "=" * 80)
    print("Syllable CRF Evaluation")
    print("=" * 80)
    
    print(classification_report(
        y_test_flat, 
        y_pred_flat, 
        labels=['B', 'M', 'E', 'S'],
        digits=3
    ))


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
    print("✅ MTU model loaded")
    
    # Prepare training data
    print("\nPreparing syllable training data...")
    X, y = prepare_training_data(TRAIN_DIR, mtu_crf)
    
    # Split train/test
    split = int(len(X) * TRAIN_RATIO)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    print(f"\nTrain sentences: {len(X_train)}")
    print(f"Test sentences : {len(X_test)}")
    
    # Show sample
    if X_train:
        print("\nSample training data:")
        print(f"  MTUs: {len(X_train[0])} MTUs in first sentence")
        print(f"  Labels: {y_train[0][:10]}...")  # Show first 10 labels
    
    # Train
    crf = train_syllable_crf(X_train, y_train)
    
    # Evaluate
    evaluate_model(crf, X_test, y_test)
    
    # Save
    with open(SYLLABLE_MODEL_PATH, "wb") as f:
        pickle.dump(crf, f)
    
    print(f"\n✅ Syllable model saved to: {SYLLABLE_MODEL_PATH}")
    
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


if __name__ == "__main__":
    main()