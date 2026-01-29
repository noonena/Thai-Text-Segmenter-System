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
import glob
import pickle
from pathlib import Path
from typing import List, Tuple, Dict
import sklearn_crfsuite
from sklearn_crfsuite import metrics

# Character type classification (Table 3.1 from dissertation)
CONSONANTS = set("ก ข ฃ ค ฅ ฆ ง จ ฉ ช ซ ฌ ญ ฎ ฏ ฐ ฑ ฒ ณ ด ต ถ ท ธ น บ ป ผ ฝ พ ฟ ภ ม ย ร ล ว ศ ษ ส ห ฬ อ ฮ".split())
NON_SUFFIX_CONSONANTS = set("ฃ ฅ ฆ ฉ ช ซ ฌ ญ ฑ ฒ ณ ต ผ ฝ ฟ ภ".split())
FRONT_VOWELS = set("เ แ โ ไ ใ".split())
UPPER_VOWELS = set("ิ ี ึ ื".split())
SPECIAL_VOWELS = set("ั ็".split())
REAR_VOWELS = set("า ๅ ว ะ ำ".split())
LOWER_VOWELS = set("ุ ู".split())
TONES = set("่ ้ ๊ ๋".split())
KARAN = "์"
SPECIAL_SYMBOLS = set("ๆ ฯ ํ".split())
# DIGITS = set("0123456789๐๑๒๓๔๕๖๗๘๙")
DIGITS = set("0123456789๐๑๒๓๔๕๖๗๘๙")


def get_char_type(ch: str) -> str:
    """Get character type based on Table 3.1"""
    if ch in CONSONANTS: return "C"
    if ch in NON_SUFFIX_CONSONANTS: return "N"
    if ch in FRONT_VOWELS: return "F"
    if ch in UPPER_VOWELS: return "U"
    if ch in SPECIAL_VOWELS: return "S"
    if ch in REAR_VOWELS: return "B"
    if ch in LOWER_VOWELS: return "L"
    if ch in TONES: return "T"
    if ch == KARAN: return "K"
    if ch in SPECIAL_SYMBOLS: return "O"
    if ch in DIGITS: return "D"
    if ch in (" ", "\t"): return "G"
    return "Q"  # Other symbols

def word_to_mtu_labels(word: str) -> List[str]:
    """
    Convert a word to character-level MTU labels (B/M/E/S)
    Based kaon the 17 rules from Kannir Paripremkul's dissertation
    
    This generates training labels by applying linguistic rules.
    The CRF will then learn patterns from these rule-based labels.
    """
    chars = list(word)
    n = len(chars)
    
    if n == 0:
        return []
    
    if n == 1:
        return ["S"]
    
    # Track MTU boundaries - True means "start of new MTU"
    boundaries = [True] + [False] * (n - 1)
    
    i = 0
    while i < n:
        ch = chars[i]
        ct = get_char_type(ch)

        # NEW: Rule for consecutive digits - keep them together
        # I just added this in, remove incase sometinhg wrong
        if ct == "D":
            # Find end of digit sequence
            j = i + 1
            while j < n and get_char_type(chars[j]) == "D":
                j += 1
            
            # Mark boundary after last digit
            if j < n:
                boundaries[j] = True
            i = j
            continue
        
        # Rule 11: "ๆ" is always singleton
        if ch == "ๆ":
            if i + 1 < n:
                boundaries[i + 1] = True
            i += 1
            continue
        
        # Rule 12: "ฯ" patterns
        if ch == "ฯ":
            # Check for ฯลฯ
            if i + 2 < n and chars[i:i+3] == ["ฯ", "ล", "ฯ"]:
                if i + 3 < n:
                    boundaries[i + 3] = True
                i += 3
                continue
            # Check for ฯพณพฯ
            elif i + 4 < n and chars[i:i+5] == ["ฯ", "พ", "ณ", "พ", "ฯ"]:
                if i + 5 < n:
                    boundaries[i + 5] = True
                i += 5
                continue
            else:
                if i + 1 < n:
                    boundaries[i + 1] = True
                i += 1
                continue
        
        # Rule 10: "ฤ" and "ฦ"
        if ch in {"ฤ", "ฦ"}:
            if i + 1 < n and chars[i + 1] == "ๅ":
                if i + 2 < n:
                    boundaries[i + 2] = True
                i += 2
            else:
                if i + 1 < n:
                    boundaries[i + 1] = True
                i += 1
            continue
        
        # Rule 16: "ก็" and "บ่" stay together
        if i + 1 < n:
            pair = ch + chars[i + 1]
            if pair in {"ก็", "บ่"}:
                if i + 2 < n:
                    boundaries[i + 2] = True
                i += 2
                continue
        
        # Rule 1: Front vowel grabs following consonant(s)
        if ct == "F":
            if i + 1 < n and get_char_type(chars[i + 1]) in {"C", "N"}:
                # Don't break between front vowel and consonant
                j = i + 2
                # Continue with dependent characters
                while j < n:
                    jt = get_char_type(chars[j])
                    
                    # Special vowel needs consonant after (Rule 3)
                    if jt == "S":
                        if j + 1 < n and get_char_type(chars[j + 1]) == "T":
                            j += 1  # Include tone
                        if j + 1 < n and get_char_type(chars[j + 1]) in {"C", "N"}:
                            j += 1  # Include final consonant
                        j += 1
                        break
                    
                    # Upper/lower vowels, tones, rear vowels can attach
                    elif jt in {"U", "L", "T", "B"}:
                        j += 1
                        if jt in {"U", "L"} and j < n and get_char_type(chars[j]) == "T":
                            j += 1  # Include tone after vowel
                        break
                    else:
                        break
                
                if j < n:
                    boundaries[j] = True
                i = j
                continue
        
        # Rules 2-6: Consonant with dependent characters
        if ct in {"C", "N"}:
            j = i + 1

            # HARD RULE: รร cannot end an MTU
            # HARD RULE: C + รร cannot end an MTU
            if (
                i + 2 < n
                and get_char_type(chars[i]) in {"C", "N"}
                and chars[i + 1] == "ร"
                and chars[i + 2] == "ร"
            ):
                j = i + 3  # consume Cรร ONLY

                if j < n:
                    boundaries[j] = True  # boundary BEFORE the tail consonant

                i = j
                continue



            
            while j < n:
                jt = get_char_type(chars[j])
                
                # Rule 2: Upper/lower vowels attach to consonant
                if jt in {"U", "L"}:
                    j += 1
                    # Check for tone after vowel
                    if j < n and get_char_type(chars[j]) == "T":
                        j += 1
                    # Special: ื, ึ can take final consonant (รือ pattern)
                    if j > i + 1 and chars[j - 1] in {"ื", "ึ"}:
                        if j < n and get_char_type(chars[j]) in {"C", "N"}:
                            j += 1
                    break

                # Rule 3: Special vowels need consonant before AND after
                elif jt == "S":
                    j += 1
                    # Check for tone before final consonant
                    if j < n and get_char_type(chars[j]) == "T":
                        j += 1
                    # Must have consonant after
                    if j < n and get_char_type(chars[j]) in {"C", "N"}:
                        j += 1
                    break
                
                # Rule 4: Rear vowels attach to consonant
                elif jt == "B":
                    j += 1
                    # Check for าะ pattern (Rule 5)
                    if j > i + 1 and chars[j - 1] == "า" and j < n and chars[j] == "ะ":
                        j += 1
                    break
                
                # Rule 6: Tones attach to consonant/vowel
                elif jt == "T":
                    j += 1
                    # After tone, can have rear vowel
                    if j < n and get_char_type(chars[j]) == "B":
                        j += 1
                    break
                
                # Rule 13: Karan (์) attaches
                elif jt == "K":
                    j += 1
                    break
                
                else:
                    break
            
            if j < n:
                boundaries[j] = True
            i = j
            continue
        
        # Default: move to next character
        if i + 1 < n:
            boundaries[i + 1] = True
        i += 1
    
    # Convert boundaries to B/M/E/S labels
    labels = []
    i = 0
    while i < n:
        # Find the end of current MTU
        j = i + 1
        while j < n and not boundaries[j]:
            j += 1
        
        # Assign labels for this MTU
        mtu_len = j - i
        if mtu_len == 1:
            labels.append("S")
        else:
            labels.append("B")
            for k in range(1, mtu_len - 1):
                labels.append("M")
            labels.append("E")
        
        i = j
    
    return labels


def char2features(chars: List[str], i: int) -> Dict[str, any]:
    """
    Extract features for character at position i
    Based on Table 3.4: Feature Template for Minimum Text Unit Extraction
    Uses unigram features C[-3:3] and bigram C[-1,1]
    """
    char = chars[i]
    features = {
        'bias': 1.0,
        'char': char,
        'char_type': get_char_type(char),
    }
    
    # Unigram features C[-3:3]
    for offset in [-3, -2, -1, 0, 1, 2, 3]:
        pos = i + offset
        if 0 <= pos < len(chars):
            features[f'char[{offset:+d}]'] = chars[pos]
            features[f'type[{offset:+d}]'] = get_char_type(chars[pos])
        else:
            features[f'char[{offset:+d}]'] = 'BOS' if pos < 0 else 'EOS'
            features[f'type[{offset:+d}]'] = 'BOUNDARY'
    
    # Bigram feature C[-1,1]
    if i > 0:
        features['char[-1,0]'] = chars[i-1] + char
        features['type[-1,0]'] = get_char_type(chars[i-1]) + get_char_type(char)
    
    if i < len(chars) - 1:
        features['char[0,+1]'] = char + chars[i+1]
        features['type[0,+1]'] = get_char_type(char) + get_char_type(chars[i+1])
    
    return features


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

def prepare_training_data(train_dir: str) -> Tuple[List[List[Dict]], List[List[str]]]:
    X_train = []
    y_train = []

    txt_files = glob.glob(os.path.join(train_dir, "*.txt"))
    print(f"Found {len(txt_files)} training files")

    for filepath in txt_files:
        print(f"Processing: {os.path.basename(filepath)}")
        lst20_data = read_lst20_file(filepath)

        sentence_chars = []
        sentence_labels = []

        for word, pos, ne, cluster in lst20_data:
            if word == "_" or word.strip() == "":
                if sentence_chars:
                    X_train.append(
                        [char2features(sentence_chars, i) for i in range(len(sentence_chars))]
                    )
                    y_train.append(sentence_labels)

                    sentence_chars = []
                    sentence_labels = []
                continue

            chars = list(word)
            labels = word_to_mtu_labels(word)

            sentence_chars.extend(chars)
            sentence_labels.extend(labels)

        # flush last sentence in file
        if sentence_chars:
            X_train.append(
                [char2features(sentence_chars, i) for i in range(len(sentence_chars))]
            )
            y_train.append(sentence_labels)

    print(f"Prepared {len(X_train)} training sentences")
    return X_train, y_train

def train_crf_model(X_train: List[List[Dict]], y_train: List[List[str]]) -> sklearn_crfsuite.CRF:
    """
    Train CRF model for MTU segmentation
    """
    print("Training CRF model...")
    
    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',
        c1=0.1,      # L1 regularization
        c2=0.1,      # L2 regularization
        max_iterations=100,
        all_possible_transitions=True,
        verbose=True
    )
    
    crf.fit(X_train, y_train)
    print("Training complete!")
    
    return crf


def save_model(crf: sklearn_crfsuite.CRF, output_path: str):
    """Save trained CRF model"""
    with open(output_path, 'wb') as f:
        pickle.dump(crf, f)
    print(f"Model saved to: {output_path}")


def main():
    # Configuration
    TRAIN_DIR = r"D:\project\word_wrapping\script\data\AIFORTHAI-LST20Corpus\LST20_Corpus\train"
    OUTPUT_DIR = r"D:\project\word_wrapping\script\data\text_dataset\train_silver"
    MODEL_PATH = os.path.join(OUTPUT_DIR, "mtu_crf_model.pkl")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 80)
    print("MTU Segmentation - CRF Training Pipeline")
    print("=" * 80)
    
    # Test the rule-based label generator first
    print("\n📋 Testing rule-based MTU label generator:")
    print("-" * 80)
    test_words = [
        "สวัสดี",      # ส | วัส | ดี
        "กาแฟ",        # กา | แฟ
        "ไม่",         # ไม่
        "เชื่อ",       # เชื่|อ
        "นั่น",        # นั่น
        "รือ",         # รือ
        "บับ",         # บับ
        "การเชื่อมต่ออุปกรณ์", #กา | ร | เชื่ | อ | ม | ต่ | อ | อุ | ป | ก | ร | ณ์
        "เที่ยวโอซาก้า", #เที่ | ย | ว | โอ | ซา | ก้า
        "รัฐธรรมนูญ" #รัฐ | ธรร | ม | นูญ
    ]
    
    for word in test_words:
        labels = word_to_mtu_labels(word)
        chars = list(word)
        
        # Group by labels to show MTUs
        mtus = []
        current_mtu = []
        for char, label in zip(chars, labels):
            if label == "S":
                mtus.append([char])
            elif label == "B":
                current_mtu = [char]
            elif label in ["M", "E"]:
                current_mtu.append(char)
                if label == "E":
                    mtus.append(current_mtu)
                    current_mtu = []
        
        if current_mtu:
            mtus.append(current_mtu)
        
        mtu_str = " | ".join(["".join(mtu) for mtu in mtus])
        label_str = " ".join(labels)
        
        print(f"Word: {word:15} → MTU: {mtu_str:30} Labels: {label_str}")
    
    print("-" * 80)
    
    # Ask user if they want to proceed with training
    print("\n⚠️  The label generator uses rule-based logic.")
    print("This will create training labels automatically from your LST20 data.")
    proceed = input("\nProceed with training? (y/n): ").strip().lower()
    
    if proceed != 'y':
        print("Training cancelled.")
        return
    
    # Prepare training data
    print("\n📚 Preparing training data from LST20 corpus...")
    X_train, y_train = prepare_training_data(TRAIN_DIR)
    
    if len(X_train) == 0:
        print("❌ No training data found!")
        return
    
    # Train model
    crf = train_crf_model(X_train, y_train)
    
    # Save model
    save_model(crf, MODEL_PATH)
    
    # Print model info
    # In crf_mtu_trainer.py, at the end of main():

    print("\n" + "=" * 80)
    print("🧪 Testing Trained Model on Known Words")
    print("=" * 80)

    test_words = [
        "รัฐธรรมนูญ",  # Should be: รัฐ|ธรร|ม|นูญ
        "แม่น้ำ",      # Should be: แม่|น้ำ
        "กรุงเทพมหานคร"  # Should be: กรุง|เทพ|มหา|นคร
    ]

    for word in test_words:
        chars = list(word)
        expected_labels = word_to_mtu_labels(word)
        features = [char2features(chars, i) for i in range(len(chars))]
        predicted_labels = crf.predict([features])[0]
        
        # Reconstruct MTUs from labels
        mtus_expected = []
        mtus_predicted = []
        
        current_mtu = []
        for i, (char, label) in enumerate(zip(chars, expected_labels)):
            current_mtu.append(char)
            if label in ['S', 'E']:
                mtus_expected.append(''.join(current_mtu))
                current_mtu = []
        
        current_mtu = []
        for i, (char, label) in enumerate(zip(chars, predicted_labels)):
            current_mtu.append(char)
            if label in ['S', 'E']:
                mtus_predicted.append(''.join(current_mtu))
                current_mtu = []
        
        print(f"\nWord: {word}")
        print(f"  Expected MTUs:  {' | '.join(mtus_expected)}")
        print(f"  Predicted MTUs: {' | '.join(mtus_predicted)}")
        print(f"  Match: {'✅' if mtus_expected == mtus_predicted else '❌'}")


if __name__ == "__main__":
    main()
