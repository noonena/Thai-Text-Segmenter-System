"""
Modified Corpus Builder

Re-segments the LST20 corpus using our own pipeline (MTU → Syllable → Repair → Viterbi)
then re-aligns the original POS tags to the new word boundaries using character spans.

Output: data/LST20_Resegmented/{train,eval,test}/ in same tab-separated format as LST20.

Usage:
    python resegment_corpus.py
"""

import os
import sys
import glob
import pickle
from collections import Counter

# ─── Path setup ────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
MODELS_DIR  = os.path.join(BACKEND_DIR, 'models')
NLP_DIR     = os.path.join(BACKEND_DIR, 'scripts', 'nlp_utils')

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, NLP_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'models'))

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ─── Corpus paths ──────────────────────────────────────────────
DATA_DIR    = os.path.abspath(os.path.join(BACKEND_DIR, '..', 'data'))
LST20_DIR   = os.path.join(DATA_DIR, 'LST20_Corpus')
OUTPUT_DIR  = os.path.join(DATA_DIR, 'LST20_Resegmented')

SPLITS = ['train', 'eval', 'test']


# ══════════════════════════════════════════════════════════════
# 1. LOAD PIPELINE
# ══════════════════════════════════════════════════════════════

def load_pipeline():
    """Load MTU CRF, syllable CRF, and word segmenter."""
    from word_segmentation import WordSegmenter
    from models.crf_mtu_inference import segment_text_to_mtus
    from nlp_utils.features.syllable_utils import extract_features_for_sentence

    print("Loading models...")

    with open(os.path.join(MODELS_DIR, 'mtu_crf_model.pkl'), 'rb') as f:
        mtu_crf = pickle.load(f)
    print("  MTU model loaded")

    with open(os.path.join(MODELS_DIR, 'syllable_crf_model.pkl'), 'rb') as f:
        syllable_crf = pickle.load(f)
    print("  Syllable model loaded")

    word_segmenter = WordSegmenter(os.path.join(MODELS_DIR, 'lst20_dictionary.pkl'))
    print("  Word segmenter loaded")

    return mtu_crf, syllable_crf, word_segmenter, segment_text_to_mtus, extract_features_for_sentence


# ══════════════════════════════════════════════════════════════
# 2. CORPUS READER
# ══════════════════════════════════════════════════════════════

def read_lst20_file(filepath):
    """Read one LST20 file. Returns list of (words, tags) sentences."""
    sentences = []
    words, tags = [], []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                if words:
                    sentences.append((words, tags))
                    words, tags = [], []
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                word, pos = parts[0], parts[1]
                if word == '_':
                    continue
                words.append(word)
                tags.append(pos)

    if words:
        sentences.append((words, tags))

    return sentences


# ══════════════════════════════════════════════════════════════
# 3. RE-SEGMENTATION
# ══════════════════════════════════════════════════════════════

def resegment_sentence(text, mtu_crf, syllable_crf, word_segmenter,
                       segment_text_to_mtus, extract_features_for_sentence):
    """Run full pipeline on text. Returns list of words."""
    try:
        mtus_nested, _, _ = segment_text_to_mtus(text, mtu_crf)
        mtus = ["".join(m) for m in mtus_nested]

        features  = extract_features_for_sentence(mtus)
        bmes      = list(syllable_crf.predict([features])[0])

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

        return word_segmenter.segment(syllables)

    except Exception as e:
        # Fall back to original words if pipeline fails
        return None


# ══════════════════════════════════════════════════════════════
# 4. POS RE-ALIGNMENT
# ══════════════════════════════════════════════════════════════

def realign_pos(original_words, original_tags, new_words):
    """
    Map original POS tags onto new word boundaries using character spans.

    For each new word, find which original characters it covers,
    collect the POS tags of those characters, pick the most common.

    Example:
      original: ["ราย","งาน"] tags: ["NN","NN"]  new: ["รายงาน"]
        char tags: ร=NN า=NN ย=NN ง=NN า=NN น=NN
        "รายงาน" spans all → most common = NN

      original: ["ตากลม"] tags: ["NN"]  new: ["ตาก","ลม"]
        char tags: ต=NN า=NN ก=NN ล=NN ม=NN
        "ตาก" → NN,  "ลม" → NN
    """
    # Build character-level tag array
    char_tags = []
    for word, tag in zip(original_words, original_tags):
        for _ in word:
            char_tags.append(tag)

    # Check total length matches
    total_orig = sum(len(w) for w in original_words)
    total_new  = sum(len(w) for w in new_words)

    if total_orig != total_new:
        # Text mismatch — fall back to repeating first tag
        return [original_tags[0] if original_tags else 'NN'] * len(new_words)

    # Assign tag to each new word by majority vote over its character span
    new_tags = []
    pos = 0
    for word in new_words:
        span = char_tags[pos: pos + len(word)]
        if span:
            new_tags.append(Counter(span).most_common(1)[0][0])
        else:
            new_tags.append('NN')
        pos += len(word)

    return new_tags


# ══════════════════════════════════════════════════════════════
# 5. PROCESS ONE SPLIT
# ══════════════════════════════════════════════════════════════

def process_split(split, mtu_crf, syllable_crf, word_segmenter,
                  segment_text_to_mtus, extract_features_for_sentence):
    input_dir  = os.path.join(LST20_DIR, split)
    output_dir = os.path.join(OUTPUT_DIR, split)
    os.makedirs(output_dir, exist_ok=True)

    files = sorted(glob.glob(os.path.join(input_dir, '*.txt')))
    print(f"\n[{split}] {len(files)} files")

    total_sent = 0
    changed    = 0
    failed     = 0

    for i, filepath in enumerate(files):
        filename = os.path.basename(filepath)
        out_path = os.path.join(output_dir, filename)

        sentences = read_lst20_file(filepath)
        lines_out = []

        for orig_words, orig_tags in sentences:
            text     = ''.join(orig_words)
            new_words = resegment_sentence(
                text, mtu_crf, syllable_crf, word_segmenter,
                segment_text_to_mtus, extract_features_for_sentence
            )

            if new_words is None:
                # Pipeline failed — keep original
                new_words = orig_words
                new_tags  = orig_tags
                failed   += 1
            else:
                new_tags = realign_pos(orig_words, orig_tags, new_words)
                if new_words != orig_words:
                    changed += 1

            for word, tag in zip(new_words, new_tags):
                lines_out.append(f"{word}\t{tag}")
            lines_out.append('')  # blank line between sentences

            total_sent += 1

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines_out))

        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(files)} files processed...")

    pct = (100 * changed / total_sent) if total_sent > 0 else 0
    print(f"  Total sentences : {total_sent:,}")
    print(f"  Segmentation changed: {changed:,} ({pct:.1f}%)")
    print(f"  Pipeline failed (kept original): {failed:,}")


# ══════════════════════════════════════════════════════════════
# 6. MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("Modified Corpus Builder")
    print(f"  Input:  {LST20_DIR}")
    print(f"  Output: {OUTPUT_DIR}")
    print("=" * 60)

    mtu_crf, syllable_crf, word_segmenter, segment_text_to_mtus, extract_features_for_sentence = load_pipeline()

    for split in SPLITS:
        process_split(split, mtu_crf, syllable_crf, word_segmenter,
                      segment_text_to_mtus, extract_features_for_sentence)

    print("\nDone. Re-segmented corpus saved to:", OUTPUT_DIR)
    print("Now retrain POS with: python pos_tagger_trainer.py --modified-corpus")


if __name__ == '__main__':
    main()
