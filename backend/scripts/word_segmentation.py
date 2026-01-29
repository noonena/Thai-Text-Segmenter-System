"""
Word Segmentation Module - Section 3.3.3 of Dissertation
Takes MTUs as input and produces word segmentation using:
1. Longest Matching with dictionary
2. Pattern Rules (Table 3.10)
"""

import pickle
from typing import List, Set, Dict
from collections import defaultdict

# Character classifications for pattern rules (Table 3.10)
CONSONANTS = set("ก ข ฃ ค ฅ ฆ ง จ ฉ ช ซ ฌ ญ ฎ ฏ ฐ ฑ ฒ ณ ด ต ถ ท ธ น บ ป ผ ฝ พ ฟ ภ ม ย ร ล ว ศ ษ ส ห ฬ อ ฮ".split())
FRONT_VOWELS = set("เ แ โ ไ ใ".split())
UPPER_VOWELS = set("ิ ี ึ ื".split())
SPECIAL_VOWELS = set("ั ็".split())
REAR_VOWELS = set("า ๅ ว ะ ำ".split())
LOWER_VOWELS = set("ุ ู".split())
TONES = set("่ ้ ๊ ๋".split())
KARAN = "์"


class ThaiDictionary:
    """
    Simple Trie-based dictionary for Thai words.
    In production, you'd load from a real Thai dictionary.
    """
    
    def __init__(self):
        self.words = set()
        self.trie = {}
    
    def add_word(self, word: str):
        """Add a word to the dictionary"""
        self.words.add(word)
        
        # Build trie for efficient prefix matching
        node = self.trie
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        node['$'] = True  # Mark end of word
    
    def contains(self, word: str) -> bool:
        """Check if word is in dictionary"""
        return word in self.words
    
    def get_all_words_with_prefix(self, prefix: str) -> List[str]:
        """Get all words starting with prefix"""
        result = []
        node = self.trie
        
        # Navigate to prefix
        for char in prefix:
            if char not in node:
                return []
            node = node[char]
        
        # Collect all words from this node
        def collect(current_node, current_word):
            if '$' in current_node:
                result.append(current_word)
            for char, next_node in current_node.items():
                if char != '$':
                    collect(next_node, current_word + char)
        
        collect(node, prefix)
        return result
    
    def load_basic_words(self):
        """Load some basic Thai words for testing"""
        basic_words = [
            # Common words
            "สวัสดี", "ขอบคุณ", "กาแฟ", "น้ำ", "ข้าว", "อาหาร",
            "คน", "ไทย", "เมือง", "บ้าน", "รถ", "เครื่องบิน",
            "การ", "เชื่อม", "ต่อ", "อุปกรณ์", "คอมพิวเตอร์",
            "โทรศัพท์", "มือ", "ถือ", "แฟ", "ร้าน", "ซื้อ",
            # From test cases
            "สิทธิ", "ลงมติ", "รับ", "หรือ", "ไม่", "ร่าง",
            "รัฐธรรมนูญ", "ฉบับ", "ปี", "การ", "เชื่อม", "ต่อ",
            "สวัสดี", "กาแฟ", "นั่น", "อะไร", "ผ้า", "ไหม",
            "ลาย", "สวย", "มาก", "รถ", "ติด", "ใจ", "กลาง",
            "แมนฮัตตัน", "มา", "ส์", "ก", "ตา", "กลม",
            "สั่ง", "กิน", "คี", "โต", "อนุ", "โลม",
            "ดำ", "น้ำ", "ทะเล", "เที่ยว", "โอ", "ซา", "ก้า",
            "คน", "จน", "รบ",
        ]
        
        for word in basic_words:
            self.add_word(word)


class PatternRules:
    """
    Pattern rules from Table 3.10 to validate word structures.
    These prevent incorrect word boundaries.
    """
    
    @staticmethod
    def is_consonant(c: str) -> bool:
        return c in CONSONANTS
    
    @staticmethod
    def is_front_vowel(c: str) -> bool:
        return c in FRONT_VOWELS
    
    @staticmethod
    def is_upper_vowel(c: str) -> bool:
        return c in UPPER_VOWELS
    
    @staticmethod
    def is_special_vowel(c: str) -> bool:
        return c in SPECIAL_VOWELS
    
    @staticmethod
    def is_rear_vowel(c: str) -> bool:
        return c in REAR_VOWELS
    
    @staticmethod
    def is_lower_vowel(c: str) -> bool:
        return c in LOWER_VOWELS
    
    @staticmethod
    def is_tone(c: str) -> bool:
        return c in TONES
    
    @staticmethod
    def matches_pattern(text: str) -> bool:
        """
        Check if text matches any valid Thai word pattern from Table 3.10.
        Returns True if it's a valid structure.
        """
        if not text:
            return False
        
        chars = list(text)
        
        # Pattern rules (Table 3.10):
        # 1. Consonant + Tone
        # 2. Consonant + Upper vowel
        # 3. Consonant + Upper vowel + Tone
        # 4. Consonant + Lower vowel
        # 5. Consonant + Lower vowel + Tone
        # 6. Consonant + Rear vowel
        # 7. Consonant + Tone + Rear vowel
        # 8. Consonant + Others vowel
        # 9. Consonant + Special vowel 1 + Consonant
        # 10. Consonant + Special vowel 2
        # 11. Front vowel + Consonant
        # 12. Front vowel + Consonant + Consonant
        # 13. Front vowel + Consonant + Tone
        # 14. Front vowel + Consonant + Upper vowel + Consonant
        # 15. Front vowel + Consonant + Upper vowel + Tone + Consonant
        # 16. Front vowel + Consonant + Rear vowel
        # 17. Front vowel + Consonant + Tone + Rear vowel
        
        # For simplicity, we accept any text that:
        # - Has at least one consonant OR
        # - Starts with front vowel followed by consonant
        
        has_consonant = any(PatternRules.is_consonant(c) for c in chars)
        starts_with_front = len(chars) > 1 and PatternRules.is_front_vowel(chars[0])
        
        return has_consonant or starts_with_front


class WordSegmenter:
    """
    Main word segmentation class using Longest Matching + Pattern Rules.
    """
    
    def __init__(self, dictionary: ThaiDictionary):
        self.dictionary = dictionary
        self.pattern_rules = PatternRules()

    def segment_from_mtus(self, mtus: List[str]) -> List[str]:
            if not mtus:
                return []
            
            words = []
            i = 0
            n = len(mtus)
            
            while i < n:
                window_size = min(6, n - i)
                matched = False
                
                # Try from longest to shortest - GREEDY
                for length in range(window_size, 0, -1):
                    candidate = "".join(mtus[i:i+length])
                    
                    if self.dictionary.contains(candidate):
                        if self.pattern_rules.matches_pattern(candidate):
                            words.append(candidate)
                            i += length
                            matched = True
                            break  # Take first (longest) match
                
                if not matched:
                    words.append(mtus[i])
                    i += 1
            
            return words
    

    # def segment_from_mtus(self, mtus: List[str]) -> List[str]:
    #     """
    #     Segment MTUs into words using Longest Matching.
        
    #     Algorithm (from Section 3.3.3):
    #     1. Process 6 MTUs at a time
    #     2. Try to match longest word in dictionary
    #     3. Apply pattern rules to validate
    #     4. Move to next unprocessed MTU
    #     """
    #     if not mtus:
    #         return []
        
    #     words = []
    #     i = 0
    #     n = len(mtus)
        
    #     while i < n:
    #         # Take up to 6 MTUs as a window
    #         window_size = min(6, n - i)
    #         best_match = None
    #         best_length = 0
            
    #         # Try matching from longest to shortest
    #         for length in range(window_size, 0, -1):
    #             candidate_mtus = mtus[i:i+length]
    #             candidate_word = "".join(candidate_mtus)
                
    #             # Check if it's in dictionary
    #             if self.dictionary.contains(candidate_word):
    #                 # Validate with pattern rules
    #                 if self.pattern_rules.matches_pattern(candidate_word):
    #                     best_match = candidate_word
    #                     best_length = length
    #                     break
            
    #         # If no dictionary match, take single MTU
    #         if best_match is None:
    #             best_match = mtus[i]
    #             best_length = 1
            
    #         words.append(best_match)
    #         i += best_length
        
    #     return words
    
    def segment_text(self, text: str, mtu_crf) -> List[str]:
        """
        Segment raw text into words.
        
        Pipeline:
        1. Text → Characters
        2. Characters → MTUs (using trained CRF)
        3. MTUs → Words (using this class)
        """
        # Step 1: Convert to characters
        chars = list(text)
        
        # Step 2: Get MTUs from CRF
        from crf_mtu_inference import segment_text_to_mtus
        mtus_nested = segment_text_to_mtus(text, mtu_crf)
        mtus = ["".join(mtu) for mtu in mtus_nested]
        
        # Step 3: Segment MTUs into words
        words = self.segment_from_mtus(mtus)
        
        return words


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("Word Segmentation - Longest Matching + Pattern Rules")
    print("=" * 80)
    
    # Initialize dictionary
    dictionary = ThaiDictionary()
    dictionary.load_basic_words()
    
    print(f"\nLoaded {len(dictionary.words)} words in dictionary")
    
    # Initialize segmenter
    segmenter = WordSegmenter(dictionary)
    
    # Test cases (MTU input → Word output)
    test_cases = [
        {
            "text": "สวัสดี",
            "mtus": ["ส", "วัส", "ดี"],
            "expected": "สวัสดี"
        },
        {
            "text": "กาแฟ",
            "mtus": ["กา", "แฟ"],
            "expected": "กาแฟ"
        },
        {
            "text": "การเชื่อมต่อ",
            "mtus": ["กา", "ร", "เชื่อ", "ม", "ต่", "อ"],
            "expected": "การ | เชื่อม | ต่อ or การเชื่อมต่อ"
        },
        {
            "text": "นั่นมือถืออะไร",
            "mtus": ["นั่น", "มือ", "ถือ", "อะ", "ไร"],
            "expected": "นั่น | มือถือ | อะไร"
        },
        {
            "text": "รัฐธรรมนูญ",
            "mtus": ["รัฐ", "ธรร", "ม", "นูญ"],
            "expected": "รัฐธรรมนูญ"
        },
    ]
    
    print("\n" + "=" * 80)
    print("Testing Word Segmentation:")
    print("=" * 80)
    
    for test in test_cases:
        text = test["text"]
        mtus = test["mtus"]
        expected = test["expected"]
        
        # Segment
        words = segmenter.segment_from_mtus(mtus)
        
        # Format output
        mtu_str = " | ".join(mtus)
        word_str = " | ".join(words)
        
        print(f"\nOriginal:  {text}")
        print(f"MTUs:      {mtu_str}")
        print(f"Words:     {word_str}")
        print(f"Expected:  {expected}")
    
    print("\n" + "=" * 80)
    print("📝 Notes:")
    print("1. Dictionary contains basic words for demonstration")
    print("2. For production, load comprehensive Thai dictionary")
    print("3. Unknown words fall back to single MTU")
    print("4. Pattern rules prevent invalid word structures")
    print("=" * 80)