"""
MTU CRF Test
Shows step-by-step how text is broken into MTUs:
  - char types
  - rule-based labels (label_chars)
  - CRF model labels
  - final MTUs
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin  = io.TextIOWrapper(sys.stdin.buffer,  encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend/scripts/nlp_utils/features'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend/scripts/nlp_utils'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend/scripts/trainers'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend/scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from mtu_features import label_chars, segment_text_to_mtus, load_model, word_to_mtu_debug
from char_utils import get_char_type

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../backend/models/mtu_crf_model.pkl')


def test_word(word: str, model):
    print(f"\n{'='*50}")
    print(f"Input: {word}")
    print(f"{'='*50}")

    chars = list(word)

    # Char types
    types = [get_char_type(c) for c in chars]
    print(f"\nChar types:")
    for c, t in zip(chars, types):
        print(f"  {c}  →  {t}")

    # Rule-based labels
    rule_labels = label_chars(word)
    print(f"\nRule-based labels (label_chars):")
    for c, l in zip(chars, rule_labels):
        print(f"  {c}  →  {l}")

    # CRF labels
    mtus_nested, crf_labels, _ = segment_text_to_mtus(word, model)
    print(f"\nCRF labels:")
    for c, l in zip(chars, crf_labels):
        print(f"  {c}  →  {l}")

    # Final MTUs
    mtus = [''.join(m) for m in mtus_nested]
    print(f"\nFinal MTUs: {mtus}")

    # Rule-by-rule debug
    print(f"\nRule debug:")
    word_to_mtu_debug(word)


def main():
    print("Loading MTU CRF model...")
    model = load_model(MODEL_PATH)
    print("Model loaded.\n")

    # Default test words
    default_words = ['ต้าว', 'ตัว', 'ขาว', 'ขวา']
    print("Testing default words:")
    for w in default_words:
        test_word(w, model)

    # Interactive input
    print(f"\n{'='*50}")
    print("Enter Thai text to test (or 'q' to quit):")
    while True:
        text = input("> ").strip()
        if text.lower() == 'q':
            break
        if text:
            for word in text.split():
                test_word(word, model)


if __name__ == "__main__":
    main()
