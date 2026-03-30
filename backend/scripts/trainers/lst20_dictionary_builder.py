"""
LST20 Dictionary Builder

Builds a word dictionary from the LST20 corpus including:
1. Individual words with POS frequency counts
2. Frequent bigram compounds (only when both parts don't already exist individually)
"""

import os
import json
import pickle
import glob
import argparse
from collections import defaultdict, Counter

# Words that should always be kept as a single unit.
# These are common compounds not annotated as single tokens in LST20
# but which feel like natural units in practice.
FORCED_COMPOUNDS = {
    # Common compound words
    'ตากลม':    'ADJ',
    'ซักผ้า':   'VACT',
    'หญิงสาว':  'NCMN',
    # Country names (ประเทศ + country)
    'ประเทศไทย':        'NPRP',
    'ประเทศญี่ปุ่น':    'NPRP',
    'ประเทศจีน':        'NPRP',
    'ประเทศเกาหลี':     'NPRP',
    'ประเทศอเมริกา':    'NPRP',
    'ประเทศอังกฤษ':     'NPRP',
    'ประเทศฝรั่งเศส':   'NPRP',
    'ประเทศเยอรมัน':    'NPRP',
    'ประเทศสิงคโปร์':   'NPRP',
    'ประเทศมาเลเซีย':   'NPRP',
    'ประเทศอินเดีย':    'NPRP',
    'ประเทศออสเตรเลีย': 'NPRP',
    'ประเทศรัสเซีย':    'NPRP',
    'ประเทศอิตาลี':     'NPRP',
    'ประเทศสเปน':       'NPRP',
    'ประเทศเวียดนาม':   'NPRP',
    'ประเทศพม่า':       'NPRP',
    'ประเทศอินโดนีเซีย':'NPRP',
    'ประเทศฟิลิปปินส์': 'NPRP',
    'ประเทศกัมพูชา':    'NPRP',
    'ประเทศลาว':        'NPRP',
    'ประเทศบราซิล':     'NPRP',
    'ประเทศแคนาดา':     'NPRP',
    'ประเทศแอฟริกาใต้': 'NPRP',
    'ประเทศตุรกี':      'NPRP',
    'ประเทศซาอุดีอาระเบีย': 'NPRP',
    'ประเทศอิหร่าน':    'NPRP',
    'ประเทศอิสราเอล':   'NPRP',
    'ประเทศนิวซีแลนด์': 'NPRP',
    # Royal names
    'พระจุลจอมเกล้าเจ้าอยู่หัว': 'NPRP',
}

class LST20Dictionary:

    def __init__(self):
        self.words = set()
        self.word_to_pos = defaultdict(Counter)
        self.compounds = set()
        self.forced = set()  # words that must always be kept as one unit
        self.stats = {
            'total_words': 0,
            'unique_words': 0,
            'total_sentences': 0,
            'compounds_generated': 0
        }

    def add_word(self, word: str, pos: str = "UNK", count: int = 1):
        if word == "_":
            return
        self.words.add(word)
        if pos:
            self.word_to_pos[word][pos] += count

    def contains(self, word: str) -> bool:
        return word in self.words

    def get_most_likely_pos(self, word: str) -> str:
        if word not in self.word_to_pos:
            return "UNK"
        return self.word_to_pos[word].most_common(1)[0][0]

    def load_from_lst20(self, train_dir: str):
        print("=" * 80)
        print("Building Dictionary from LST20 Corpus")
        print("=" * 80)

        txt_files = glob.glob(os.path.join(train_dir, "*.txt"))
        print(f"\nFound {len(txt_files)} training files")

        bigram_counts = defaultdict(int)
        sentence_count = 0
        word_count = 0

        print("\nPhase 1: Loading words and tracking co-occurrences...")

        for i, filepath in enumerate(txt_files, 1):
            if i % 1000 == 0:
                print(f"   Processed {i}/{len(txt_files)} files...")

            with open(filepath, 'r', encoding='utf-8') as f:
                sentence_words = []

                for line in f:
                    line = line.strip()

                    if not line:
                        if sentence_words:
                            for j in range(len(sentence_words) - 1):
                                bigram_counts[(sentence_words[j], sentence_words[j + 1])] += 1
                            sentence_count += 1
                            sentence_words = []
                        continue

                    parts = line.split('\t')
                    if len(parts) >= 2:
                        word = parts[0]
                        pos = parts[1]
                        self.add_word(word, pos)
                        word_count += 1
                        sentence_words.append(word)

                if sentence_words:
                    sentence_count += 1

        print(f"\nLoaded {len(self.words):,} unique words")
        print(f"   Found {len(bigram_counts):,} unique bigrams")

        print("\nPhase 2: Generating compound words...")
        compounds_added = 0

        # Frequent bigrams (appear 10+ times)
        for (word1, word2), count in bigram_counts.items():
            if count >= 10:
                compound = word1 + word2
                # Skip if both parts already exist — it's a frequent phrase, not a lexical unit
                if word1 in self.words and word2 in self.words:
                    continue
                if len(compound) <= 15:
                    self.add_word(compound, 'COMPOUND', count=count)
                    if compound not in self.compounds:
                        self.compounds.add(compound)
                        compounds_added += 1

        print(f"   Added {compounds_added} frequent 2-word compounds")

        print("\nPhase 3: Injecting forced compounds...")
        for compound, pos in FORCED_COMPOUNDS.items():
            self.add_word(compound, pos, count=500)
            self.forced.add(compound)
        print(f"   Injected {len(FORCED_COMPOUNDS)} forced compounds")

        self.stats['total_words'] = word_count
        self.stats['unique_words'] = len(self.words)
        self.stats['total_sentences'] = sentence_count
        self.stats['compounds_generated'] = compounds_added

        print(f"\nDictionary built successfully!")
        print(f"   Total unique words: {len(self.words):,}")
        print(f"   Compounds generated: {compounds_added:,}")

    def save(self, filepath: str):
        from datetime import datetime

        data = {
            'words': list(self.words),
            'word_to_pos': dict(self.word_to_pos),
            'compounds': list(self.compounds),
            'forced': list(self.forced),
            'stats': self.stats,
            'last_updated': datetime.now().isoformat(),
            'version': '1.0'
        }

        json_path = filepath.replace('.pkl', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

        print(f"Dictionary saved: {json_path}")
        print(f"Dictionary saved: {filepath}")

    @staticmethod
    def load(filepath: str) -> 'LST20Dictionary':
        json_path = filepath.replace('.pkl', '.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)

        dictionary = LST20Dictionary()
        if isinstance(data['words'], list):
            dictionary.words = set(data['words'])
        else:
            dictionary.words = data['words']
        dictionary.word_to_pos = defaultdict(Counter, data['word_to_pos'])
        dictionary.compounds = set(data.get('compounds', []))
        dictionary.forced = set(data.get('forced', []))
        dictionary.stats = data['stats']

        print(f"Loaded {len(dictionary.words):,} words from dictionary")
        return dictionary

    def print_stats(self):
        print("\n" + "=" * 80)
        print("Dictionary Statistics")
        print("=" * 80)
        print(f"Unique words:      {self.stats['unique_words']:,}")
        print(f"  - Individual:    {self.stats['unique_words'] - self.stats['compounds_generated']:,}")
        print(f"  - Compounds:     {self.stats['compounds_generated']:,}")
        print(f"Total occurrences: {self.stats['total_words']:,}")
        print(f"Sentences:         {self.stats['total_sentences']:,}")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='LST20 Dictionary Builder')
    parser.add_argument('--dict-path', default=None, help='Output dictionary path')
    args = parser.parse_args()

    TRAIN_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'LST20_Corpus', 'train')
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
    DICT_PATH = args.dict_path or os.path.join(OUTPUT_DIR, "lst20_dictionary.pkl")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    dictionary = LST20Dictionary()
    dictionary.load_from_lst20(TRAIN_DIR)
    dictionary.print_stats()
    dictionary.save(DICT_PATH)


if __name__ == "__main__":
    main()
