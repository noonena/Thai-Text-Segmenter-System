"""
CRF-based MTU Segmentation Inference
Use the trained CRF model to segment Thai text into MTUs
"""

import pickle
from typing import List, Dict

# Same character classification as training
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
DIGITS = set("0123456789๐๑๒๓๔๕๖๗๘๙")


def get_char_type(ch: str) -> str:
    """Get character type"""
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
    return "Q"


def char2features(chars: List[str], i: int) -> Dict[str, any]:
    """Extract features for character at position i"""
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
    
    # Bigram features
    if i > 0:
        features['char[-1,0]'] = chars[i-1] + char
        features['type[-1,0]'] = get_char_type(chars[i-1]) + get_char_type(char)
    
    if i < len(chars) - 1:
        features['char[0,+1]'] = char + chars[i+1]
        features['type[0,+1]'] = get_char_type(char) + get_char_type(chars[i+1])
    
    return features


def load_model(model_path: str):
    """Load trained CRF model"""
    with open(model_path, 'rb') as f:
        crf = pickle.load(f)
    return crf

def segment_text_to_mtus(text: str, crf):
    chars = list(text)
    features = [char2features(chars, i) for i in range(len(chars))]
    labels = crf.predict([features])[0]

    mtus = []
    current_mtu = []
    current_labels = []
    mtu_labels = []  # store BMES per MTU

    for char, label in zip(chars, labels):
        if label == 'S':
            mtus.append([char])
            mtu_labels.append(['S'])
        elif label == 'B':
            current_mtu = [char]
            current_labels = ['B']
        elif label in ['M', 'E']:
            current_mtu.append(char)
            current_labels.append(label)
            if label == 'E':
                mtus.append(current_mtu)
                mtu_labels.append(current_labels)
                current_mtu = []
                current_labels = []

    if current_mtu:
        mtus.append(current_mtu)
        mtu_labels.append(current_labels)

    return mtus, labels, mtu_labels

def format_mtus(mtus: List[List[str]]) -> str:
    """Format MTUs for display"""
    return ' | '.join([''.join(mtu) for mtu in mtus])


# Example usage
if __name__ == "__main__":
    MODEL_PATH = r"D:\project\word_wrapping\script\data\text_dataset\train_silver\mtu_crf_model.pkl"
    
    # Load model
    print("Loading CRF model...")
    crf = load_model(MODEL_PATH)
    print("Model loaded successfully!")
    
if __name__ == "__main__":
    test_cases = [
        ("สวัสดี",
          "ส | วัส | ดี"),
        ("สิทธิลงมติรับหรือไม่รับร่างรัฐธรรมนูญฉบับปี", 
         "สิ | ท | ธิ | ล | ง | ม | ติ | รับ | ห | รือ | ไม่ | รับ | ร่า | ง | รัฐ | ธ | ร | ร | ม | นู | ญ | ฉ | บับ | ปี"),
        ("กาแฟ", "กา | แฟ"),
        ("การเชื่อมต่อ", "กา | ร | เชื่ | อ | ม | ต่ | อ"),
        ("สวัสดี", "ส | วัส | ดี"),
        ("ผ้าไหมลายสวยมาก", "ผ้า | ไห | ม | ลา | ย | ส | ว | ย | มา | ก"),
        ("นั่นมือถืออะไร", "นั่น | มือ | ถือ | อะ | ไร"),
        ("รถติดใจกลางแมนฮัตตัน", "ร | ถ | ติ | ด | ใจ | ก | ลา | ง | แม | น | ฮัต | ตัน"),
        ("มาส์ก", "มา | ส์ | ก"),
        ("ตากลม", "ตา | ก | ล | ม"),
        ("สั่งกาแฟ", "สั่ง | กา | แฟ"),
        ("กินคีโตอนุโลม", "กิ | น | คี | โต | อ | นุ | โล | ม"),
        ("ดำน้ำทะเล", "ดำ | น้ำ | ทะ | เล"),
        ("เที่ยวโอซาก้า", "เที่ | ย | ว | โอ | ซา | ก้า"),
        ("คนจนรบ", "ค | น | จ | น | ร | บ"),
    ]
    
    print("=" * 80)
    correct = 0
    total = len(test_cases)

    for text, expected in test_cases:
        mtus, labels, mtu_labels = segment_text_to_mtus(text, crf)
        result = format_mtus(mtus)

        print(f"\nInput: {text}")
        # print("Chars + BMES:")
        # print(" ".join(f"{c}/{l}" for c, l in zip(text, labels)))

        print("\nMTUs + BMES:")
        for mtu, labs in zip(mtus, mtu_labels):
            print(f"{''.join(mtu):6} → {' '.join(labs)}")

        match = "✓" if result == expected else "✗"
        if match == "✓":
            correct += 1

        print(f"\n{match} Output:   {result}")
        print(f"  Expected: {expected}")
