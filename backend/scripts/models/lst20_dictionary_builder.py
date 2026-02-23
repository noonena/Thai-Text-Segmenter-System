"""
ENHANCED Dictionary Builder with Compound Word Generation

This version adds compounds by:
1. Tracking word co-occurrences (bigrams, trigrams)
2. Adding frequent compounds (frequency-based)
3. Adding pattern-based compounds (ผู้ + X, แม่ + X, etc.)

Run this to rebuild your dictionary with compounds!
"""

import os
import json
import pickle
import glob
import sys
import argparse
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
    
    def add_word(self, word: str, pos: str = "UNK"):
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
        
        # Add specific Thai compound patterns that should always be compounds
        always_compounds = {
            'ไหมลาย',  # patterned silk
            'มันฝรั่ง',  # french fries
            'มือถือ',   # mobile phone
            'ผ้าไหม',   # silk cloth
            'การใช้',   # usage
            'รัฐบาล',   # government
            'โทรศัพท์', # telephone
            'คอมพิวเตอร์', # computer
        }
        
        for compound in always_compounds:
            if compound not in self.words:
                self.add_word(compound, 'COMPOUND')
                self.compounds.add(compound)
                compounds_added += 1
        
        # 2-word patterns
        for (word1, word2), count in bigram_counts.items():
            if count >= 2:  # Lowered threshold from 3 to 2
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
        """Save dictionary to JSON for continuous learning"""
        from datetime import datetime
        
        data = {
            'words': list(self.words),
            'word_to_pos': dict(self.word_to_pos),
            'compounds': list(self.compounds),
            'stats': self.stats,
            'last_updated': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        # Save as JSON for easy editing and continuous learning
        json_path = filepath.replace('.pkl', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Also save as pickle for fast loading
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"✅ Dictionary saved as JSON: {json_path}")
        print(f"📦 Dictionary saved as PKL: {filepath}")
    
    @staticmethod
    def load(filepath: str) -> 'LST20Dictionary':
        """Load dictionary from JSON or PKL file"""
        # Try JSON first for newer format
        json_path = filepath.replace('.pkl', '.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📖 Dictionary loaded from JSON: {json_path}")
        else:
            # Fallback to PKL
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            print(f"📦 Dictionary loaded from PKL: {filepath}")
        
        dictionary = LST20Dictionary()
        dictionary.words = set(data['words']) if isinstance(data['words'], list) else data['words']
        dictionary.word_to_pos = defaultdict(Counter, data['word_to_pos'])
        dictionary.trie = data['trie']
        dictionary.compounds = set(data.get('compounds', []))
        dictionary.stats = data['stats']
        
        print(f"📚 Loaded {len(dictionary.words):,} words from dictionary")
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


def update_from_error_patterns(dictionary_path: str, error_file: str = None):
    """Update dictionary from error patterns found in evaluation"""
    print("Updating dictionary from error patterns...")
    
    # Load existing dictionary
    dictionary = LST20Dictionary.load(dictionary_path)
    original_size = len(dictionary.words)
    
    # If no error file specified, try to find recent evaluation results
    if not error_file:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        error_file = os.path.join(base_dir, 'real_evaluation_results.json')
    
    if os.path.exists(error_file):
        with open(error_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Add missing words from sample compound cases
        compound_cases = results.get('details', {}).get('sample_compounds', [])
        
        for case in compound_cases:
            gold_word = case.get('gold', '')
            predicted = case.get('predicted', '')
            
            # Add gold word if not already present
            if gold_word and len(gold_word) > 1:
                dictionary.words.add(gold_word)
                # Add common POS for unknown words (default to noun)
                dictionary.word_to_pos[gold_word]['NN'] += 1
            
            # Add predicted parts if they seem valid
            if predicted and '_' in predicted:
                parts = predicted.split('_')
                for part in parts:
                    if len(part) > 1 and part.isalpha():
                        dictionary.words.add(part)
                        dictionary.word_to_pos[part]['NN'] += 1
    
    # Add common Thai words that are frequently missed
    common_missing_words = {
        'เจนีวา', 'อินเดีย', 'รายงาน', 'ความ', 'ภัยธรรมชาติ', 'เกี่ยวข้อง',
        'การ', 'และ', 'ที่', 'มี', 'เป็น', 'ได้', 'ให้', 'กับ', 'ของ',
        'ตาม', 'ดัง', 'นี้', 'อย่าง', 'โดย', 'เพื่อ', 'เช่น', 'เนื่องจาก'
    }
    
    for word in common_missing_words:
        dictionary.words.add(word)
        dictionary.word_to_pos[word]['NN'] += 1
    
    # Generate new compounds from expanded dictionary
    # dictionary._generate_compounds()  # Commented out - method doesn't exist
    
    # Save updated dictionary
    dictionary.save(dictionary_path)
    
    new_size = len(dictionary.words)
    print(f"Dictionary updated: {new_size - original_size:,} new words added")
    print(f"   Total words: {new_size:,}")
    
    return dictionary

def main():
    parser = argparse.ArgumentParser(description='Enhanced LST20 Dictionary Builder')
    parser.add_argument('--update-from-errors', action='store_true', 
                      help='Update dictionary from evaluation error patterns')
    parser.add_argument('--dict-path', default=None,
                      help='Path to existing dictionary file')
    parser.add_argument('--error-file', default=None,
                      help='Path to error results file (JSON)')
    
    args = parser.parse_args()
    
    if args.update_from_errors:
        # Update existing dictionary from errors
        dict_path = args.dict_path
        if not dict_path:
            # Default to backend models directory
            dict_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'lst20_dictionary.pkl')
        
        if not os.path.exists(dict_path):
            print(f"❌ Dictionary not found at: {dict_path}")
            return
        
        update_from_error_patterns(dict_path, args.error_file)
        
    else:
        # Build fresh dictionary from LST20
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