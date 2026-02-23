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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.nlp_utils.utils.features import format_mtus, segment_text_to_mtus, load_model, char2features
from scripts.nlp_utils.utils.char_utils import get_char_type

def word_to_mtu_labels(word: str) -> List[str]:
    """
    Improved MTU label generator that reduces over-segmentation
    Creates fewer, larger MTUs to improve recall
    """
    chars = list(word)
    n = len(chars)
    
    if n == 0:
        return []
    
    if n == 1:
        return ["S"]
    
    # Track MTU boundaries - True means "start of new MTU"
    boundaries = [True] + [False] * (n - 1)
    
    # Common compound words that should stay together
    compounds = {
        'ธรรมชาติ', 'เจนีวา', 'จำนวน', 'เฉลี่ย', 'สิ่งแวดล้อม',
        'ประชาชน', 'ความปลอดภัย', 'สำคัญ', 'พัฒนา', 'สังคม',
        'เศรษฐกิจ', 'การศึกษา', 'สาธารณสุข', 'ความรู้', 'เทคโนโลยี',
        'สื่อสาร', 'ความสำเร็จ', 'สิทธิมนุษยชน', 'สิ่งแวดล้อม', 'พลังงาน',
        'เศรษฐกิจ', 'การเมือง', 'สังคม', 'วัฒนธรรม', 'การศึกษา'
    }
    
    # If entire word is a known compound, keep it as one MTU
    word_str = ''.join(chars)
    if word_str in compounds and n <= 8:  # Don't make extremely long MTUs
        return ["B"] + ["M"] * (n - 2) + ["E"] if n > 1 else ["S"]
    
    i = 0
    while i < n:
        ch = chars[i]
        ct = get_char_type(ch)

        # NEW: Rule for consecutive digits - keep them together
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
        
        # Rule 16: Common function words stay together
        if i + 1 < n:
            pair = ch + chars[i + 1]
            if pair in {"ก็", "บ่", "มี", "ไป", "มา", "ให้", "ได้", "เป็น", "กับ", "และ", "ที่", "จะ", "อย่า", "อยู่"}:
                if i + 2 < n:
                    boundaries[i + 2] = True
                i += 2
                continue
        
        # NEW: Look ahead for common patterns to keep together
        if ct in {"C", "N"} and i + 2 < n:
            # Check for common 3-character patterns
            three_char = chars[i:i+3]
            three_str = ''.join(three_char)
            common_patterns = {
                'การ', 'มาก', 'น้อย', 'ใหญ่', 'เล็ก', 'สูง', 'ต่ำ', 'ใหม่', 'เก่า',
                'ดี', 'ชั่ว', 'แรง', 'อ่อน', 'ร้อน', 'เย็น', 'เร็ว', 'ช้า', 'มาก'
            }
            if three_str in common_patterns:
                if i + 3 < n:
                    boundaries[i + 3] = True
                i += 3
                continue
        
        # Rule 1: Front vowel grabs following consonant(s) - MODIFIED
        if ct == "F":
            if i + 1 < n and get_char_type(chars[i + 1]) in {"C", "N"}:
                # Be more aggressive in keeping longer sequences
                j = i + 2
                while j < n:
                    jt = get_char_type(chars[j])
                    
                    # Special vowel needs consonant after (Rule 3)
                    if jt == "S":
                        if j + 1 < n and get_char_type(chars[j + 1]) == "T":
                            j += 1
                        if j + 1 < n and get_char_type(chars[j + 1]) in {"C", "N"}:
                            j += 1
                        j += 1
                        break
                    
                    # Upper/lower vowels, tones, rear vowels can attach
                    elif jt in {"U", "L", "T", "B"}:
                        j += 1
                        if jt in {"U", "L"} and j < n and get_char_type(chars[j]) == "T":
                            j += 1
                    else:
                        # NEW: Try to attach to next consonant if it forms a valid cluster
                        if j < n and get_char_type(chars[j]) in {"C", "N"}:
                            # Check if this forms a common syllable pattern
                            j += 1
                        else:
                            break
                
                if j < n:
                    boundaries[j] = True
                i = j
                continue
        
        # Rules 2-6: Consonant with dependent characters - MODIFIED
        if ct in {"C", "N"}:
            j = i + 1

            # Special handling for รร patterns
            if (
                i + 2 < n
                and chars[i + 1] == "ร"
                and chars[i + 2] == "ร"
            ):
                j = i + 3
                if j < n:
                    boundaries[j] = True
                i = j
                continue
            
            # Attach dependent characters more aggressively
            max_attach = 3  # Allow longer attachments
            attached = 0
            
            while j < n and attached < max_attach:
                jt = get_char_type(chars[j])
                
                # Rule 2: Upper/lower vowels attach
                if jt in {"U", "L"}:
                    j += 1
                    attached += 1
                    # Check for tone after vowel
                    if j < n and get_char_type(chars[j]) == "T":
                        j += 1
                    # Special: ื, ึ can take final consonant
                    if j > i + 1 and chars[j - 1] in {"ื", "ึ"}:
                        if j < n and get_char_type(chars[j]) in {"C", "N"}:
                            j += 1
                    break

                # Rule 3: Special vowels need consonant after
                elif jt == "S":
                    j += 1
                    attached += 1
                    if j < n and get_char_type(chars[j]) == "T":
                        j += 1
                    if j < n and get_char_type(chars[j]) in {"C", "N"}:
                        j += 1
                    break
                
                # Rule 4: Rear vowels attach
                elif jt == "B":
                    j += 1
                    attached += 1
                    if j > i + 1 and chars[j - 1] == "า" and j < n and chars[j] == "ะ":
                        j += 1
                    break
                
                # Rule 6: Tones attach
                elif jt == "T":
                    j += 1
                    attached += 1
                    if j < n and get_char_type(chars[j]) == "B":
                        j += 1
                    break
                
                # Rule 13: Karan attaches
                elif jt == "K":
                    j += 1
                    attached += 1
                    break
                
                # NEW: Allow attachment of following consonant in common patterns
                elif jt in {"C", "N"} and attached == 0:
                    # Check if this C-C pattern is common
                    cc_pair = chars[i] + chars[j]
                    if cc_pair in ['กร', 'กร', 'ปร', 'สร', 'ทร', 'มร', 'วร', 'นร']:
                        j += 1
                        attached += 1
                        # Continue to see what follows
                        continue
                    else:
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
    Improved CRF model training for better MTU segmentation
    """
    print("Training CRF model with improved parameters...")
    
    # Improved CRF parameters for better recall
    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',
        c1=0.05,      # Reduced L1 regularization for more flexibility
        c2=0.05,      # Reduced L2 regularization for more flexibility  
        max_iterations=200,  # More iterations for better convergence
        all_possible_transitions=True,
        verbose=True
    )
    
    crf.fit(X_train, y_train)
    print("Training complete!")
    
    # Display training statistics
    if hasattr(crf, 'classes_') and crf.classes_:
        print(f"Number of states: {len(crf.classes_)}")
    if hasattr(crf, 'state_features_') and crf.state_features_:
        print(f"Number of features: {len(crf.state_features_)}")
    
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
