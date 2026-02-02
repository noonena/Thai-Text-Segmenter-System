"""
Train CRF Model for POS Tagging
Reads LST20 corpus and trains POS tagger
"""

import os
import glob
import pickle
import sklearn_crfsuite
from sklearn_crfsuite import metrics
from utils.pos_features import extract_features, extract_labels


def read_lst20_for_pos(filepath):
    """
    Read LST20 file and extract (word, POS) pairs
    
    Format:
    Word    POS    NER    Cluster
    จูจีฮุน  NN     B_PER  B_CLS
    """
    sentences = []
    current_sentence_words = []
    current_sentence_pos = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Empty line = sentence boundary
            if not line:
                if current_sentence_words:
                    sentences.append((current_sentence_words, current_sentence_pos))
                    current_sentence_words = []
                    current_sentence_pos = []
                continue
            
            # Parse line: Word \t POS \t NER \t Cluster
            parts = line.split('\t')
            if len(parts) >= 2:
                word = parts[0]
                pos = parts[1]
                
                # Skip underscore (sentence separator)
                if word == '_':
                    continue
                
                current_sentence_words.append(word)
                current_sentence_pos.append(pos)
    
    # Handle last sentence
    if current_sentence_words:
        sentences.append((current_sentence_words, current_sentence_pos))
    
    return sentences


def prepare_training_data(train_dir):
    """Prepare training data from LST20 corpus"""
    txt_files = glob.glob(os.path.join(train_dir, "*.txt"))
    print(f"Found {len(txt_files)} training files")
    
    X_train = []  # Features
    y_train = []  # POS tags
    
    for i, filepath in enumerate(txt_files, 1):
        if i % 1000 == 0:
            print(f"  Processed {i}/{len(txt_files)} files...")
        
        sentences = read_lst20_for_pos(filepath)
        
        for words, pos_tags in sentences:
            # Extract features for this sentence
            features = extract_features(words)
            labels = extract_labels(pos_tags)
            
            X_train.append(features)
            y_train.append(labels)
    
    print(f"Prepared {len(X_train)} sentences for training")
    return X_train, y_train


def train_pos_tagger(X_train, y_train):
    """Train CRF model for POS tagging"""
    print("Training POS Tagger CRF...")
    
    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',
        c1=0.1,  # L1 regularization
        c2=0.1,  # L2 regularization
        max_iterations=100,
        all_possible_transitions=True,
        verbose=True
    )
    
    crf.fit(X_train, y_train)
    print("Training complete!")
    
    return crf


# def evaluate_model(crf, X_test, y_test):
#     """Evaluate POS tagger"""
#     y_pred = crf.predict(X_test)
    
#     # Flatten lists for evaluation
#     # labels = list(crf.classes_)
    
#     print("\n" + "="*80)
#     print("POS Tagger Evaluation")
#     print("="*80)
    
#     # print(metrics.flat_classification_report(
#     #     y_test, y_pred, labels=labels, digits=3
#     # ))
#     print(metrics.flat_classification_report(
#     y_test,
#     y_pred,
#     digits=3
#     ))
from sklearn.metrics import classification_report

def evaluate_model(crf, X_test, y_test):
    y_pred = crf.predict(X_test)

    # manual flatten
    y_test_flat = [tag for sent in y_test for tag in sent]
    y_pred_flat = [tag for sent in y_pred for tag in sent]

    print("\n" + "=" * 80)
    print("POS Tagger Evaluation")
    print("=" * 80)

    print(classification_report(
        y_test_flat,
        y_pred_flat,
        digits=3
    ))

def main():
    # Configuration
    TRAIN_DIR = r"D:\project\word_wrapping\script\data\AIFORTHAI-LST20Corpus\LST20_Corpus\train"
    OUTPUT_DIR = r"D:\project\ThaitextSegmentersystem\backend\models"
    MODEL_PATH = os.path.join(OUTPUT_DIR, "pos_crf_model.pkl")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Prepare data
    print("="*80)
    print("POS Tagger Training")
    print("="*80)
    
    X_train, y_train = prepare_training_data(TRAIN_DIR)
    
    # Split for validation (80/20)
    split_idx = int(len(X_train) * 0.8)
    X_test = X_train[split_idx:]
    y_test = y_train[split_idx:]
    X_train = X_train[:split_idx]
    y_train = y_train[:split_idx]
    
    print(f"\nTraining set: {len(X_train)} sentences")
    print(f"Test set: {len(X_test)} sentences")
    
    # Train model
    crf = train_pos_tagger(X_train, y_train)
    
    # Evaluate
    evaluate_model(crf, X_test, y_test)
    
    # Save model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(crf, f)
    print(f"\n✅ Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()