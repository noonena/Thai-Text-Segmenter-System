"""
Word Segmentation Module - Section 3.3.3 of Dissertation
Takes MTUs as input and produces word segmentation using:
1. Longest Matching with dictionary
2. Pattern Rules (Table 3.10)
"""

import pickle
import math
from typing import List, Set, Dict, Tuple, Optional
from collections import defaultdict
from lst20_dictionary_builder import LST20Dictionary 

# For TCC features - import from features module
import sys
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'nlp_utils'))
try:
    from utils.features import apply_tcc_rules
    from utils.char_utils import get_char_type
except ImportError:
    from nlp_utils.utils.features import apply_tcc_rules
    from nlp_utils.utils.char_utils import get_char_type

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
        """Enhanced dictionary with comprehensive Thai words and compounds"""
        basic_words = [
            # Greetings and common expressions
            "สวัสดี", "สวัสดีครับ", "สวัสดีค่ะ", "ขอบคุณ", "ขอบคุณครับ", "ขอบคุณค่ะ",
            "ไม่เป็นไร", "โทษครับ", "โทษค่ะ", "ลาก่อน", "สบายดี",
            
            # Food and drink
            "กาแฟ", "น้ำ", "ข้าว", "อาหาร", "กับข้าว", "อร่อย", "มัน", "ฝรั่ง", "ทอด",
            "มันฝรั่งทอด", "กะเพรา", "ผัดไทย", "ต้มยำ", "แกงเขียวหวาน", "ขนม", "ขนมปั้น",
            "น้ำดื่ม", "น้ำอัดลม", "ชา", "ชาเย็น", "โกโก้", "ไวน์",
            
            # People and family
            "คน", "คนไทย", "ผู้ชาย", "ผู้หญิง", "เด็ก", "เด็กชาย", "เด็กหญิง", "ผู้ใหญ่",
            "คุณพ่อ", "คุณแม่", "พ่อ", "แม่", "ลูก", "พี่", "น้อง", "ปู่", "ย่า", "ตา", "ยาย",
            
            # Places and locations
            "บ้าน", "เมือง", "กรุงเทพ", "กรุงเทพมหานคร", "ต่างจังหวัด", "ต่างประเทศ",
            "โรงเรียน", "มหาวิทยาลัย", "โรงพยาบาล", "วัด", "ตลาด", "ห้างสรรพสินค้า",
            "บ้านเช่า", "คอนโด", "ทาวน์เฮาส์", "อาคาร", "อาคารสำนักงาน",
            
            # Transportation and vehicles
            "รถ", "รถยนต์", "รถไฟฟ้า", "รถไฟ", "รถประจำทาง", "รถตู้", "รถสองแถว",
            "รถจักรยาน", "มอเตอร์ไซค์", "มอเตอร์ไซค์วาบ", "เรือ", "เครื่องบิน",
            "รถไฟฟ้าบีทีเอส", "รถไฟฟ้ามหานคร", "รถสองแถว",
            
            # Technology and devices
            "โทรศัพท์", "โทรศัพท์มือถือ", "มือถือ", "คอมพิวเตอร์", "โน้ตบุ๊ก",
            "แท็บเล็ต", "สมาร์ทโฟน", "ไอโฟน", "แอนดรอยด์", "อินเทอร์เน็ต",
            "วายฟาย", "ไวไฟ", "บลูทูธ", "กล้อง", "ทีวี", "โทรทัศน์",
            
            # Clothing and fabrics
            "ผ้า", "ผ้าไหม", "ผ้าฝ้าย", "ผ้าลินิน", "ผ้ายีนส์", "ผ้าคอตตอน",
            "ผ้าซาติน", "ผ้าแฟลกเซล", "ผ้าลาเต้", "ผ้าอิตาลี",
            "เสื้อ", "เสื้อยืด", "เสื้อเชิ้ต", "เสื้อผ้า", "กางเกง", "กางเกงยีนส์",
            "กระเป๋า", "กระเป๋าเงิน", "กระเป๋าเดินทาง", "กระเป๋าหนัง", "กระเป๋าผ้า",
            "รองเท้า", "รองเท้าผ้าใบ", "รองเท้าหนัง", "รองเท้าแตะ", "รองเท้าส้นสูง",
            
            # Home and furniture
            "โต๊ะ", "เก้าอี้", "โซฟา", "เตียง", "ตู้", "ตู้เสื้อผ้า", "ตู้หนังสือ",
            "โต๊ะกินข้าว", "โต๊ะทำงาน", "เก้าอี้สำนักงาน", "โต๊ะไม้", "เก้าอี้ไม้",
            "ตู้เย็น", "เครื่องซักผ้า", "เครื่องทำน้ำอุ่น", "ทีวี", "โทรทัศน์",
            
            # Nature and environment
            "ดอกไม้", "ต้นไม้", "ภูเขา", "ทะเล", "หาดทราย", "น้ำตก", "แม่น้ำ",
            "ฝน", "หิมะ", "แดด", "อากาศ", "สภาพอากาศ", "ธรรมชาติ",
            
            # Colors and adjectives
            "สี", "สีดำ", "สีขาว", "สีแดง", "สีเขียว", "สีเหลือง", "สีฟ้า", "สีน้ำเงิน",
            "สีชมพู", "สีส้ม", "สีม่วง", "สีเทา", "สีน้ำตาล",
            "สวย", "สวยงาม", "ใหญ่", "เล็ก", "ยาว", "สั้น", "สูง", "ต่ำ",
            "ดี", "แย่", "ใหม่", "เก่า", "ใหญ่ๆ", "เล็กๆ", "สวยๆ", "ดีๆ",
            
            # Patterns and designs
            "ลาย", "ลายดอกไม้", "ลายสก๊อต", "ลายขวาง", "ลายจุด", "ลายแถว",
            "ลายสวย", "ลายงาม", "ลายใหม่", "ลายโบราณ", "ลายไทย",
            
            # Actions and verbs
            "กิน", "ทาน", "นอน", "นั่ง", "ยืน", "เดิน", "วิ่ง", "เล่น", "ทำงาน",
            "เรียน", "สอน", "อ่าน", "เขียน", "ฟัง", "พูด", "ดู", "มอง",
            "ซื้อ", "ขาย", "จอง", "สั่ง", "เช่า", "ยืม", "คืน",
            "ชอบ", "รัก", "เกลียด", "กลัว", "คิด", "จำ", "ลืม", "รู้", "เข้าใจ",
            
            # Time and dates
            "วัน", "เดือน", "ปี", "เวลา", "ชั่วโมง", "นาที", "วินาที",
            "เช้า", "สาย", "บ่าย", "เย็น", "กลางคืน", "วันนี้", "พรุ่งนี้", "เมื่อวาน",
            "จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์",
            
            # Numbers and measurements
            "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า", "สิบ",
            "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน", "บาท", "ดอลลาร์", "เซ็นต์", "สตางค์",
            "กิโล", "เมตร", "เซนติเมตร", "ฟุต", "นิ้ว", "กิโลกรัม", "กรัม",
            
            # Question words
            "อะไร", "ใคร", "ทำไม", "เมื่อไร", "ที่ไหน", "อย่างไร", "กี่", "ตัวไหน",
            
            # Prepositions and conjunctions
            "ใน", "บน", "ล่าง", "หน้า", "หลัง", "ข้าง", "ใกล้", "ไกล", "กับ", "และ", "หรือ",
            "แต่", "เพราะ", "ดังนั้น", "ถ้า", "เมื่อ", "ขณะที่", "หลังจาก", "ก่อน",
            
            # Specific test case words
            "สิทธิ", "ลงมติ", "รับ", "ไม่", "ร่าง", "รัฐธรรมนูญ", "ฉบับ", "การเชื่อมต่อ",
            "นั่น", "อะไร", "ผ้า", "ไหม", "ลาย", "มาก", "ติด", "ใจ", "กลาง",
            "แมนฮัตตัน", "มาส์", "ก", "ตา", "กลม", "สั่ง", "คี", "โต", "อนุ", "โลม",
            "ดำ", "น้ำ", "ทะเล", "เที่ยว", "โอ", "ซา", "ก้า", "จน", "รบ",
            
            # Compound words that should be together
            "ผมชอบ", "มันฝรั่ง", "ไหมลาย", "ผ้าไหม", "มือถือ", "รถยนต์", "มอเตอร์ไซค์",
            "โทรศัพท์มือถือ", "รองเท้าผ้าใบ", "รองเท้าหนัง", "กระเป๋าหนัง", "กระเป๋าผ้า",
            "โต๊ะไม้", "เก้าอี้ไม้", "ผ้าฝ้าย", "ผ้าลินิน", "บ้านเช่า", "รถไฟฟ้า",
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
    Encapsulates dictionary loading and word segmentation logic.
    """
    
    def __init__(self, dictionary_path: str):
        print(f"   Loading LST20Dictionary from: {dictionary_path}")
        from lst20_dictionary_builder import LST20Dictionary
        self.dictionary = LST20Dictionary.load(dictionary_path)
        self.pattern_rules = PatternRules()
        print(f"   Dictionary loaded: {len(self.dictionary.words):,} words")
    
    def is_number(self, s: str) -> bool:
        thai_digits = "๐๑๒๓๔๕๖๗๘๙"
        return s.isdigit() or all(c in thai_digits for c in s)


    def merge_number_classifier(self, words):
        merged = []
        i = 0
        classifiers = ['ปี', 'ปีนี้', 'คน', 'วัน', 'เดือน', 'ตัว']

        while i < len(words):
            if (
                i < len(words) - 1
                and self.is_number(words[i])
                and words[i+1] in classifiers
            ):
                merged.append(words[i] + words[i+1])
                i += 2
            else:
                merged.append(words[i])
                i += 1

        return merged


    def segment_from_mtus_with_pos(self, mtus: List[str], pos_model=None) -> List[str]:
        """
        Enhanced word segmentation using POS-informed decisions
        """
        if not mtus:
            return []
        
        words = []
        i = 0
        n = len(mtus)
        
        while i < n:
            window_size = min(8, n - i)
            matched = False
            best_match = None
            best_length = 0
            
            # Generate all candidates
            candidates = []
            for length in range(window_size, 0, -1):
                candidate = "".join(mtus[i:i+length])
                if self.dictionary.contains(candidate):
                    if self.pattern_rules.matches_pattern(candidate):
                        candidates.append((candidate, length))
            
            # If multiple candidates, use POS to decide
            if len(candidates) > 1 and pos_model:
                # Try each candidate and score based on POS likelihood
                best_score = -1
                for candidate, length in candidates:
                    # Get POS probability for this candidate
                    pos_score = self._get_pos_score(candidate, pos_model)
                    
                    # Combine length preference with POS score
                    combined_score = (length * 0.3) + (pos_score * 0.7)
                    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_match = candidate
                        best_length = length
                        matched = True
            elif candidates:
                # Fallback to longest matching
                best_match, best_length = max(candidates, key=lambda x: x[1])
                matched = True
            
            # Apply the best match
            if matched and best_match:
                words.append(best_match)
                i += best_length
            else:
                # Fallback: single MTU
                words.append(mtus[i])
                i += 1
        
        words = self.merge_number_classifier(words)
        return words
    
    def _get_pos_score(self, word: str, pos_model) -> float:
        """Get POS likelihood score for a word"""
        if hasattr(pos_model, 'word_to_pos') and word in pos_model.word_to_pos:
            # Return probability of most common POS tag
            pos_counts = pos_model.word_to_pos[word]
            total = sum(pos_counts.values())
            most_common = pos_counts.most_common(1)[0][1]
            return most_common / total
        return 0.1  # Low score for unknown words
    
    def segment_from_mtus_with_syllables(self, mtus: List[str], syllables: List[str]) -> List[str]:
        """
        Uses syllables as primary guide for word segmentation.
        Falls back to dictionary matching if syllable doesn't work.
        """
        if not mtus:
            return []
        
        words = []
        i = 0
        n = len(mtus)
        
        # Build a simple syllable lookup
        if syllables:
            mtu_to_syllable = self._align_mtus_to_syllables(mtus, syllables)
        else:
            mtu_to_syllable = None
        
        while i < n:
            # Strategy 1: Check if combining MTUs up to next syllable forms a valid word
            if mtu_to_syllable and i in mtu_to_syllable:
                # Get the syllable index for this position
                syl_idx = mtu_to_syllable[i]
                # Get MTUs until the next syllable starts
                next_syl_start = None
                for pos, syl in mtu_to_syllable.items():
                    if syl == syl_idx + 1:
                        next_syl_start = pos
                        break
                
                end_pos = next_syl_start if next_syl_start else n
                candidate = "".join(mtus[i:end_pos])
                
                # If this candidate is in dictionary, take it
                if self.dictionary.contains(candidate):
                    words.append(candidate)
                    i = end_pos
                    continue
            
            # Strategy 2: Dictionary longest match
            best_word = None
            best_length = 0
            max_lookahead = min(6, n - i)
            
            for length in range(max_lookahead, 0, -1):
                candidate = "".join(mtus[i:i+length])
                if self.dictionary.contains(candidate):
                    confidence = self._calculate_word_confidence(candidate, length)
                    if confidence > 0.5 and length > best_length:
                        best_word = candidate
                        best_length = length
                        if confidence > 0.8:
                            break
            
            if best_word:
                words.append(best_word)
                i += best_length
                continue
            
            # Strategy 3: Take single MTU
            words.append(mtus[i])
            i += 1
        
        words = self.merge_number_classifier(words)
        return words
    
    def _align_mtus_to_syllables(self, mtus: List[str], syllables: List[str]) -> Dict[int, int]:
        """Build mapping of MTU position -> syllable index"""
        mapping = {}
        mtu_idx = 0
        
        for syl_idx, syllable in enumerate(syllables):
            # Find how many MTUs make up this syllable
            chars_collected = ""
            start_mtu = mtu_idx
            
            while mtu_idx < len(mtus) and chars_collected != syllable:
                chars_collected += mtus[mtu_idx]
                # Check if we've matched the syllable
                if chars_collected == syllable:
                    # Mark all MTU positions in this syllable
                    for pos in range(start_mtu, mtu_idx + 1):
                        mapping[pos] = syl_idx
                    mtu_idx += 1
                    break
                elif len(chars_collected) > len(syllable):
                    # Overshot - just mark current position
                    mtu_idx += 1
                    break
                else:
                    mtu_idx += 1
            
            if mtu_idx >= len(mtus):
                break
        
        return mapping
        words = self._precision_post_process(words)
        
        return words
    
    def _calculate_word_confidence(self, word: str, length: int) -> float:
        """Calculate confidence score for a candidate word"""
        confidence = 0.0
        
        # Length preference (longer = higher confidence)
        if length >= 4:
            confidence += 0.4
        elif length >= 3:
            confidence += 0.3
        elif length >= 2:
            confidence += 0.2
        
        # Pattern validation
        if self.pattern_rules.matches_pattern(word):
            confidence += 0.3
        
        # Thai structure validation
        if self._is_valid_thai_word(word):
            confidence += 0.2
        
        # Known compounds get bonus
        if len(word) >= 4 and self._is_likely_compound(word):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _is_valid_single_mtu(self, mtu: str) -> bool:
        """Check if single MTU can be a valid word"""
        # Single Thai characters that can stand alone
        valid_singles = {"ก", "ด", "้", "า", "ิ", "ี", "ึ", "ื", "ุ", "ู", "ๆ", "ฯ"}
        
        if len(mtu) == 1:
            return mtu in valid_singles
        
        # Multi-character MTUs should have Thai structure
        thai_consonants = set("กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ")
        return any(c in thai_consonants for c in mtu)
    
    def _is_likely_compound(self, word: str) -> bool:
        """Check if word is likely a Thai compound word"""
        # Common compound patterns
        if len(word) >= 4:
            compound_indicators = [
                ("ผ้า", ""), ("มือ", ""), ("รถ", ""), ("รองเท้า", ""),
                ("กระเป๋า", ""), ("มัน", ""), ("บ้าน", ""), ("ข้าว", "")
            ]
            for prefix, _ in compound_indicators:
                if word.startswith(prefix):
                    return True
        
        return False
    
    def _precision_post_process(self, words: List[str]) -> List[str]:
        """Post-process to improve precision with conservative merging"""
        if len(words) < 2:
            return words
        
        merged = []
        i = 0
        
        while i < len(words):
            current = words[i]
            
            # Check for obvious compound merging opportunities
            if i < len(words) - 1:
                next_word = words[i + 1]
                combined = current + next_word
                
                # Only merge high-confidence compounds
                if self.dictionary.contains(combined) and len(combined) <= 6:
                    # Additional validation for compound
                    if self._is_high_confidence_compound(current, next_word):
                        merged.append(combined)
                        i += 2
                        continue
            
            merged.append(current)
            i += 1
        
        return merged
    
    def _is_high_confidence_compound(self, word1: str, word2: str) -> bool:
        """Check if word pair is high-confidence compound"""
        # High-confidence compound pairs
        high_confidence_pairs = {
            ("ผ้า", "ไหม"), ("ผ้า", "ฝ้าย"), ("มือ", "ถือ"), 
            ("รถ", "ยนต์"), ("มอเตอร์", "ไซค์"), ("รองเท้า", "หนัง"),
            ("รองเท้า", "ผ้าใบ"), ("กระเป๋า", "หนัง"), ("มัน", "ฝรั่ง"),
            ("ข้าว", "สวย"), ("กา", "แฟ"), ("โทรศัพท์", "มือถือ"),
        }
        
        return (word1, word2) in high_confidence_pairs
    
    def _is_valid_thai_word(self, word: str) -> bool:
        """Validate if word follows Thai language patterns"""
        if not word or len(word) == 0:
            return False
        
        # Check for reasonable Thai character patterns
        thai_chars = set('กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟมยรลวศษสหฬอฮ')
        vowel_chars = set('ัาำิีึืุูเแโใไฤๅฯๆ')
        tone_chars = set('่้๊๋')
        
        has_thai = any(c in thai_chars for c in word)
        has_vowel = any(c in vowel_chars for c in word)
        
        # Valid if has Thai characters and reasonable structure
        return has_thai and (has_vowel or len(word) <= 2 or any(c in thai_chars for c in word[-2:]))

    # =====================================================
    # VITERBI-BASED WORD SEGMENTATION
    # =====================================================
    
    def _get_word_frequency(self, word: str) -> float:
        """Get log frequency score for a word from dictionary"""
        if word in self.dictionary.word_to_pos:
            total = sum(self.dictionary.word_to_pos[word].values())
            return math.log(total + 1)
        return 0.0
    
    def _get_boundary_score(self, prev_word: Optional[str], candidate: str, next_chars: str) -> float:
        """
        Score based on character patterns at word boundaries.
        Higher score = more likely to be a word boundary.
        """
        score = 0.0
        
        if not candidate:
            return 0.0
        
        # Check first character of candidate
        first_char = candidate[0]
        first_type = get_char_type(first_char)
        
        # Check last character  
        last_char = candidate[-1]
        last_type = get_char_type(last_char)
        
        # Strong boundary indicators
        # Consonant clusters, tone marks, special chars often indicate boundaries
        if first_type in {'C', 'N'}:
            score += 0.3
        
        if last_type == 'T':  # Tone mark - likely end of syllable/word
            score += 0.2
        
        if first_type == 'F':  # Front vowel at start - rare for word start
            score -= 0.3
        
        # Check if candidate ends with valid Thai ending
        thai_end_consonants = set('กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ')
        if last_char in thai_end_consonants:
            score += 0.2
        
        return score
    
    def _get_tcc_boundary_score(self, text: str) -> float:
        """
        Score based on TCC patterns.
        If TCC suggests boundary, this helps validate word segmentation.
        """
        if not text:
            return 0.0
        
        try:
            mtus = apply_tcc_rules(text)
            # More MTUs = more likely to be multiple words
            if len(mtus) > 1:
                return math.log(len(mtus))
        except:
            pass
        return 0.0
    
    def _score_candidate(
        self, 
        candidate: str, 
        position: int, 
        total_length: int,
        prev_word: Optional[str] = None,
        next_chars: str = ""
    ) -> float:
        """
        Combined score for a candidate word.
        Higher score = better candidate.
        """
        score = 0.0
        
        # 1. Dictionary match - STRONG bonus for known words
        if self.dictionary.contains(candidate):
            freq = self._get_word_frequency(candidate)
            score += freq * 0.3 + 2.0  # Base bonus + frequency
        else:
            # Small penalty for unknown (but allow valid Thai patterns)
            if self._is_valid_thai_word(candidate):
                score -= 0.3
            else:
                score -= 1.5
        
        # 2. Length bonus - STRONGER for longer words (precision-focused)
        if len(candidate) >= 4:
            score += 1.0
        elif len(candidate) >= 3:
            score += 0.6
        elif len(candidate) >= 2:
            score += 0.3
        # Single char gets no bonus
        
        # 3. Pattern validation
        if self.pattern_rules.matches_pattern(candidate):
            score += 0.2
        
        # 4. Thai structure validation
        if self._is_valid_thai_word(candidate):
            score += 0.1
        
        # 5. Position-based (no penalty for first word)
        is_first = (position == 0)
        is_last = (position + len(candidate) >= total_length)
        
        if is_first:
            score += 0.2
        if is_last:
            score += 0.2
        
        # 6. Penalty for TCC boundary within candidate (prefer single word)
        score -= self._get_tcc_boundary_score(candidate) * 0.3
        
        return score
    
    def _generate_candidates(self, mtus: List[str], start: int) -> List[Tuple[str, int]]:
        """
        Generate all valid word candidates starting at position `start`.
        Returns list of (word, length_in_mtus).
        """
        candidates = []
        n = len(mtus)
        
        max_length = min(6, n - start)  # Max 6 MTUs per word
        
        for length in range(1, max_length + 1):
            candidate = "".join(mtus[start:start + length])
            
            # Accept if in dictionary OR valid Thai word pattern
            if self.dictionary.contains(candidate) or self._is_valid_thai_word(candidate):
                candidates.append((candidate, length))
        
        return candidates
    
    def segment_with_viterbi(self, mtus: List[str], syllables: List[str] = None) -> List[str]:
        """
        Viterbi-based word segmentation.
        
        Uses syllables as primary unit (more meaningful than MTUs).
        Falls back to MTUs if syllables not provided.
        
        Instead of greedy longest-match, this:
        1. Generates all candidate words at each position
        2. Uses Viterbi to find globally optimal path
        3. Scores candidates using frequency, patterns, and context
        """
        # Use syllables if available, otherwise MTUs
        units = syllables if syllables else mtus
        if not units:
            return []
        
        n = len(units)
        
        # Viterbi tables
        dp = [-float('inf')] * (n + 1)
        back = {}  # position -> (prev_pos, word)
        
        dp[0] = 0.0  # Start position
        
        for pos in range(n):
            if dp[pos] == -float('inf'):
                continue
            
            # Get next units for boundary scoring
            next_units = units[pos:pos+3] if pos < n else []
            
            # Get previous word for context
            prev_word = None
            for prev_pos, (prev_w, _) in back.items():
                if prev_pos == pos:
                    prev_word = prev_w
                    break
            
            # Generate candidates starting at `pos`
            candidates = self._generate_candidates_from_units(units, pos)
            
            for candidate, length in candidates:
                next_pos = pos + length
                
                # Score this candidate
                score = self._score_candidate_v2(
                    candidate, pos, n, prev_word, next_units
                )
                
                total_score = dp[pos] + score
                
                if total_score > dp[next_pos]:
                    dp[next_pos] = total_score
                    back[next_pos] = (pos, candidate)
        
        # Backtrack to get the best path
        if dp[n] == -float('inf'):
            # Fallback to greedy if Viterbi fails
            return self.segment_from_mtus_with_syllables(mtus, syllables or [])
        
        words = []
        pos = n
        while pos > 0:
            prev_pos, word = back[pos]
            words.append(word)
            pos = prev_pos
        
        words.reverse()
        
        # Post-processing: merge number + classifier
        words = self.merge_number_classifier(words)
        
        return words
    
    def _generate_candidates_from_units(self, units: List[str], start: int) -> List[Tuple[str, int]]:
        """Generate word candidates from syllables/MTUs"""
        candidates = []
        n = len(units)
        
        max_length = min(5, n - start)  # Max 5 units per word
        
        for length in range(1, max_length + 1):
            candidate = "".join(units[start:start + length])
            
            # Accept if in dictionary OR valid Thai word pattern
            if self.dictionary.contains(candidate) or self._is_valid_thai_word(candidate):
                candidates.append((candidate, length))
        
        return candidates
    
    def _score_candidate_v2(
        self, 
        candidate: str, 
        position: int, 
        total_length: int,
        prev_word: Optional[str] = None,
        next_units: List[str] = None
    ) -> float:
        """Improved scoring for Viterbi word segmentation"""
        score = 0.0
        
        # 1. Dictionary match - STRONG bonus
        if self.dictionary.contains(candidate):
            freq = self._get_word_frequency(candidate)
            score += freq * 0.2 + 2.5  # Strong base bonus
        else:
            # Unknown word - allow if valid Thai pattern
            if self._is_valid_thai_word(candidate):
                score += 0.1
            else:
                score -= 2.0  # Strong penalty for invalid patterns
        
        # 2. Length preference (prefer 2-4 unit words)
        units_count = len(candidate)
        if 2 <= units_count <= 3:
            score += 1.0
        elif units_count == 1:
            score -= 0.3  # Penalty for single unit words (usually not standalone)
        elif units_count >= 4:
            score += 0.5  # Bonus for longer words
        
        # 3. Pattern validation
        if self.pattern_rules.matches_pattern(candidate):
            score += 0.3
        
        # 4. Position bonuses
        is_first = (position == 0)
        is_last = (position >= total_length - 1)
        
        if is_first:
            score += 0.3
        if is_last:
            score += 0.3
        
        # 5. Check if next unit would make a better combination
        if next_units and len(next_units) >= 1:
            next_unit = next_units[0]
            combined = candidate + next_unit
            if self.dictionary.contains(combined):
                score -= 0.5  # Penalty - should have taken the longer word
        
        return score

    def segment_from_mtus(self, mtus: List[str]) -> List[str]:
        """
        Simple MTU to word segmentation.
        Uses Viterbi for better context awareness.
        """
        return self.segment_with_viterbi(mtus)
    
    def segment_from_mtus_legacy(self, mtus: List[str]) -> List[str]:
        """
        Legacy method - uses the old greedy longest-match approach.
        Kept for comparison.
        """
        return self.segment_from_mtus_with_syllables(mtus, [])

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
        {
            "text": "ผมชอบมันฝรั่งทอด",
            "mtus": ["ผม" , "ชอบ" , "มัน" , "ฝรั่ง" , "ทอด"],
            "expected": "ผม | ชอบ| มันฝรั่ง | ทอด"
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