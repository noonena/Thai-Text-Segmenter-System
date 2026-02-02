"""
ENHANCED Dictionary Builder with Compound Word Generation

This version adds compounds by:
1. Tracking word co-occurrences (bigrams, trigrams)
2. Adding frequent compounds (frequency-based)
3. Adding pattern-based compounds (ผู้ + X, แม่ + X, etc.)

Run this to rebuild your dictionary with compounds!
"""

import os
import glob
from collections import defaultdict, Counter
from typing import Dict, Set, List, Tuple
import pickle


class LST20Dictionary:
    """
    Enhanced dictionary with compound word generation
    """
    
    def __init__(self):
        self.words = set()
        self.word_to_pos = defaultdict(Counter)
        self.trie = {}
        self.compounds = set()  # Track generated compounds
        self.stats = {
            'total_words': 0,
            'unique_words': 0,
            'total_sentences': 0,
            'compounds_generated': 0
        }
    
    def add_word(self, word: str, pos: str = None):
        """Add word to dictionary"""
        if word == "_":
            return
        
        self.words.add(word)
        
        if pos:
            self.word_to_pos[word][pos] += 1
        
        # Build trie
        node = self.trie
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        node['$'] = True
    
    def contains(self, word: str) -> bool:
        return word in self.words
    
    def get_most_likely_pos(self, word: str) -> str:
        if word not in self.word_to_pos:
            return "UNK"
        pos_counts = self.word_to_pos[word]
        return pos_counts.most_common(1)[0][0]
    
    def should_compound_by_pattern(self, word1, word2, pos1, pos2):
        """
        Pattern-based compound detection
        
        Rules:
        - ผู้ + anything → compound
        - แม่ + NOUN → compound
        - นัก + NOUN → compound
        - การ + VERB → compound
        - VERB + งาน → compound
        """
        # Specific prefix rules
        if word1 in ['ผู้', 'แม่', 'นัก', 'พ่อ', 'ลูก', 'ช่าง']:
            return True
        
        # การ + VERB
        if word1 == 'การ' and pos2 == 'VERB':
            return True
        
        # VERB + งาน
        if pos1 == 'VERB' and word2 == 'งาน':
            return True
        
        # NOUN + NOUN (common compound pattern)
        if pos1 == 'NOUN' and pos2 == 'NOUN':
            return True
        
        return False
    
    def should_compound_3_by_pattern(self, word1, word2, word3, pos1, pos2, pos3):
        """
        3-word compound patterns
        
        Pattern: ผู้ + VERB + NOUN (e.g., ผู้ใช้งาน)
        """
        if word1 == 'ผู้' and pos2 == 'VERB' and pos3 == 'NOUN':
            return True
        
        if word1 == 'ผู้' and pos2 in ['VERB', 'NOUN'] and pos3 == 'งาน':
            return True
        
        # NOUN + NOUN + NOUN
        if pos1 == 'NOUN' and pos2 == 'NOUN' and pos3 == 'NOUN':
            return True
        
        return False
    
    def load_from_lst20(self, train_dir: str):
        """
        Load dictionary from LST20 with compound generation
        """
        print("=" * 80)
        print("Building Enhanced Dictionary with Compound Words")
        print("=" * 80)
        
        txt_files = glob.glob(os.path.join(train_dir, "*.txt"))
        print(f"\n📚 Found {len(txt_files)} training files")
        
        # Statistics tracking
        bigram_counts = defaultdict(int)
        trigram_counts = defaultdict(int)
        bigram_pos = {}  # (word1, word2) → (pos1, pos2)
        trigram_pos = {}
        
        sentence_count = 0
        word_count = 0
        
        print("\n📖 Phase 1: Loading words and tracking co-occurrences...")
        
        for i, filepath in enumerate(txt_files, 1):
            if i % 1000 == 0:
                print(f"   Processed {i}/{len(txt_files)} files...")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                sentence_words = []
                sentence_pos = []
                
                for line in f:
                    line = line.strip()
                    
                    if not line:
                        if sentence_words:
                            # Count bigrams
                            for j in range(len(sentence_words) - 1):
                                bigram = (sentence_words[j], sentence_words[j+1])
                                bigram_counts[bigram] += 1
                                bigram_pos[bigram] = (sentence_pos[j], sentence_pos[j+1])
                            
                            # Count trigrams
                            for j in range(len(sentence_words) - 2):
                                trigram = (sentence_words[j], sentence_words[j+1], sentence_words[j+2])
                                trigram_counts[trigram] += 1
                                trigram_pos[trigram] = (sentence_pos[j], sentence_pos[j+1], sentence_pos[j+2])
                            
                            sentence_count += 1
                            sentence_words = []
                            sentence_pos = []
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        word = parts[0]
                        pos = parts[1]
                        
                        # Add individual word
                        self.add_word(word, pos)
                        word_count += 1
                        
                        sentence_words.append(word)
                        sentence_pos.append(pos)
                
                # Handle last sentence
                if sentence_words:
                    sentence_count += 1
        
        print(f"\n✅ Loaded {len(self.words):,} unique words")
        print(f"   Found {len(bigram_counts):,} unique bigrams")
        print(f"   Found {len(trigram_counts):,} unique trigrams")
        
        print("\n🔧 Phase 2: Generating compound words...")
        
        compounds_added = 0
        
        # Strategy 1: High-frequency bigrams (appear 10+ times)
        print("   Adding frequent 2-word compounds...")
        freq_threshold_2 = 10
        for (word1, word2), count in bigram_counts.items():
            if count >= freq_threshold_2:
                compound = word1 + word2
                if compound not in self.words and len(compound) <= 15:
                    self.add_word(compound, 'COMPOUND')
                    self.compounds.add(compound)
                    compounds_added += 1
        
        print(f"      Added {compounds_added} high-frequency 2-word compounds")
        
        # Strategy 2: High-frequency trigrams (appear 5+ times)
        print("   Adding frequent 3-word compounds...")
        start_trigram = compounds_added
        freq_threshold_3 = 5
        for (word1, word2, word3), count in trigram_counts.items():
            if count >= freq_threshold_3:
                compound = word1 + word2 + word3
                if compound not in self.words and len(compound) <= 20:
                    self.add_word(compound, 'COMPOUND')
                    self.compounds.add(compound)
                    compounds_added += 1
        
        print(f"      Added {compounds_added - start_trigram} high-frequency 3-word compounds")
        
        # Strategy 3: Pattern-based compounds (even if low frequency)
        print("   Adding pattern-based compounds...")
        start_pattern = compounds_added
        
        # 2-word patterns
        for (word1, word2), count in bigram_counts.items():
            if count >= 3:  # At least 3 occurrences
                pos1, pos2 = bigram_pos[(word1, word2)]
                
                if self.should_compound_by_pattern(word1, word2, pos1, pos2):
                    compound = word1 + word2
                    if compound not in self.words and len(compound) <= 15:
                        self.add_word(compound, 'COMPOUND')
                        self.compounds.add(compound)
                        compounds_added += 1
        
        # 3-word patterns
        for (word1, word2, word3), count in trigram_counts.items():
            if count >= 2:  # At least 2 occurrences
                pos1, pos2, pos3 = trigram_pos[(word1, word2, word3)]
                
                if self.should_compound_3_by_pattern(word1, word2, word3, pos1, pos2, pos3):
                    compound = word1 + word2 + word3
                    if compound not in self.words and len(compound) <= 20:
                        self.add_word(compound, 'COMPOUND')
                        self.compounds.add(compound)
                        compounds_added += 1
        
        print(f"      Added {compounds_added - start_pattern} pattern-based compounds")
        
        # Update stats
        self.stats['total_words'] = word_count
        self.stats['unique_words'] = len(self.words)
        self.stats['total_sentences'] = sentence_count
        self.stats['compounds_generated'] = compounds_added
        
        print(f"\n✨ Dictionary built successfully!")
        print(f"   Total unique words: {len(self.words):,}")
        print(f"   Compounds generated: {compounds_added:,}")
        print(f"   Individual words: {len(self.words) - compounds_added:,}")
    
    def save(self, filepath: str):
        """Save dictionary to file"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'words': self.words,
                'word_to_pos': dict(self.word_to_pos),
                'trie': self.trie,
                'compounds': self.compounds,
                'stats': self.stats
            }, f)
        print(f"\n💾 Dictionary saved to: {filepath}")
    
    @staticmethod
    def load(filepath: str) -> 'LST20Dictionary':
        """Load dictionary from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        dictionary = LST20Dictionary()
        dictionary.words = data['words']
        dictionary.word_to_pos = defaultdict(Counter, data['word_to_pos'])
        dictionary.trie = data['trie']
        dictionary.compounds = data.get('compounds', set())
        dictionary.stats = data['stats']
        
        return dictionary
    
    def print_stats(self):
        """Print statistics"""
        print("\n" + "=" * 80)
        print("Dictionary Statistics")
        print("=" * 80)
        print(f"Unique words:      {self.stats['unique_words']:,}")
        print(f"  - Individual:    {self.stats['unique_words'] - self.stats['compounds_generated']:,}")
        print(f"  - Compounds:     {self.stats['compounds_generated']:,}")
        print(f"Total occurrences: {self.stats['total_words']:,}")
        print(f"Sentences:         {self.stats['total_sentences']:,}")
        
        # Show sample compounds
        print("\n📝 Sample generated compounds:")
        sample_compounds = list(self.compounds)[:15]
        for compound in sample_compounds:
            pos = self.get_most_likely_pos(compound)
            print(f"   {compound:20} → {pos}")
        
        print("=" * 80)
    
    def test_compounds(self):
        """Test if common compounds are in dictionary"""
        print("\n" + "=" * 80)
        print("Testing Common Compounds")
        print("=" * 80)
        
        test_words = [
            "ผู้ใช้งาน",      # user
            "แม่น้ำ",         # river
            "การใช้งาน",      # usage
            "นักเรียน",       # student
            "คอมพิวเตอร์",    # computer
            "โทรศัพท์",       # telephone
            "รัฐบาล",         # government
        ]
        
        for word in test_words:
            exists = word in self.words
            symbol = "✓" if exists else "✗"
            print(f"   {symbol} '{word}' in dictionary: {exists}")
        
        print("=" * 80)


def main():
    """Build enhanced dictionary"""
    
    # CONFIGURE THESE PATHS
    TRAIN_DIR = r"D:\project\word_wrapping\script\data\AIFORTHAI-LST20Corpus\LST20_Corpus\train"
    OUTPUT_DIR = r"D:\project\word_wrapping\script\data\text_dataset\train_silver"
    DICT_PATH = os.path.join(OUTPUT_DIR, "lst20_dictionary.pkl")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Build dictionary
    dictionary = LST20Dictionary()
    dictionary.load_from_lst20(TRAIN_DIR)
    
    # Print stats
    dictionary.print_stats()
    
    # Test common compounds
    dictionary.test_compounds()
    
    # Save
    dictionary.save(DICT_PATH)
    
    print("\n✅ Enhanced dictionary ready!")
    print(f"   Use: lst20_dictionary.pkl")
    print(f"   This includes {dictionary.stats['compounds_generated']:,} compound words")


if __name__ == "__main__":
    main()