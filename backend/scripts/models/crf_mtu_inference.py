"""
CRF-based MTU Segmentation Inference
Use the trained CRF model to segment Thai text into MTUs
"""

import pickle
from typing import List, Dict
import os
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from scripts.nlp_utils.utils.features import format_mtus, segment_text_to_mtus, load_model
from scripts.nlp_utils.utils.char_utils import get_char_type
# Example usage
if __name__ == "__main__":
    # MODEL_PATH = r"D:\project\word_wrapping\script\data\text_dataset\train_silver\mtu_crf_model.pkl"
   
    # Get the directory where this script is located
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Build path relative to script location
    # Go up one level from scripts/models to backend/, then into models/
    MODEL_PATH = os.path.join(SCRIPT_DIR, "..", "..", "models", "mtu_crf_model.pkl")

    # Or normalize the path
    MODEL_PATH = os.path.normpath(MODEL_PATH)

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
