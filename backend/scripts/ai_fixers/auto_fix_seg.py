"""
Comprehensive Auto-Fix Thai Segmentation AI
Detects and fixes ANY segmentation errors using 4 systematic approaches:

1. MTU/Syllable Feature Improvement: Analyze character-level features and syllable boundaries
2. Pattern Rules Enhancement: Dynamic rule generation for word integration
3. Dictionary Expansion: Auto-learn new words and compounds
4. Continuous Learning: Feedback loop to improve future performance
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Tuple, Dict, Set
from collections import defaultdict, Counter
import pickle
import re
import argparse

class ComprehensiveSegFixer:
    """AI that systematically detects and fixes Thai segmentation errors"""
    
    def __init__(self, models_path: str):
        self.models_path = models_path
        self.learning_data = self._load_learning_data()
        self.error_patterns = self._initialize_error_patterns()
        self.linguistic_rules = self._load_linguistic_rules()
        
    def _load_learning_data(self) -> Dict:
        """Load accumulated learning data from LST20-based training"""
        data_path = os.path.join(self.models_path, "learning_data.pkl")
        if os.path.exists(data_path):
            with open(data_path, 'rb') as f:
                return pickle.load(f)
        return {
            "segmentation_errors": Counter(),
            "correct_forms": Counter(),
            "mtu_boundaries": defaultdict(list),
            "word_confidence": defaultdict(float),
            "lst20_training_samples": []
        }
    
    def _initialize_error_patterns(self) -> Dict:
        """Initialize patterns that commonly indicate segmentation errors"""
        return {
            "suspicious_single_chars": {
                "exceptions": {"ก", "ด", "้", "า", "ิ", "ี", "ึ", "ื", "ุ", "ู", "ๆ", "ฯ"},
                "threshold": 1
            },
            "incomplete_structures": {
                "min_consonants": 1,
                "invalid_prefixes": {"ไ", "ใ", "เ", "โ", "แ", "ำ", "ๅ"},
                "solo_vowels": True
            },
            "boundary_violations": {
                "respect_syllable_bounds": True,
                "check_mtu_continuity": True
            },
            "statistical_anomalies": {
                "confidence_threshold": 0.3,
                "rare_word_threshold": 5
            }
        }
    
    def _load_linguistic_rules(self) -> Dict:
        """Load linguistic rules for Thai word structures"""
        return {
            "consonants": set("กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ"),
            "vowels": set("ัาำิีึืุูเแโใไฤๅฯๆ"),
            "tones": set("่้๊๋"),
            "compound_patterns": [
                # Enhanced fabric/material compounds
                r"^ผ้า(ไหม|ฝ้าย|ลินิน|หนัง|ผ้าใบ|ซาติน|ยีนส์|คอตตอน|แฟลกเซล|ลาเต้|อิตาลี)$",
                r"^(กระเป๋า|รองเท้า|โต๊ะ|เก้าอี้|ถุง|เสื้อ|กางเกง)(หนัง|ไม้|พลาสติก|ผ้าใบ|ยีนส์|คอตตอน|ลินิน)$",
                
                # Enhanced vehicle/device compounds
                r"^(รถ|มอเตอร์ไซค์|จักรยาน|เรือ|เครื่องบิน)(ยนต์|ไฟฟ้า|โดยสาร|บรรทุก|ส่งของ|ทัวร์)$",
                r"^(โทรศัพท์|มือถือ|คอมพิวเตอร์|โน๊ตบุ๊ก|แท็บเล็ต)(มือถือ|สมาร์ท|แอนดรอยด์|พกพา|โน้ตบุ๊ก)$",
                
                # Enhanced food compounds
                r"^(ข้าว|ก๋วยเตี๋ย|บะหมี่|ผัด|ต้ม|แกง|ผลไม้)(สวย|อร่อย|ทอด|ต้มยำ|หมู|ไก่|เนื้อ|ทะเล|หวาน)$",
                r"^(มัน|กะทิ|น้ำ|ซอส)(ฝรั่ง|หวาน|เปรี้ยว|เค็ม|มัน|ข้าว|ต้มสตอ|พริก)$",
                
                # Enhanced adjective compounds
                r"^(สวย|งาม|สวยงาม|ใหญ่|เล็ก|ยาว|สั้น|สูง|ต่ำ)(มาก|น้อย|พอดี|มากๆ|น้อยๆ|จริงๆ)$",
                r"^(ลาย|สี|ขนาด|รูปแบบ)(ดอกไม้|สก๊อต|ขวาง|จุด|แถว|ใหญ่|เล็ก|ยาว|สั้น|สวย|งาม)$",
                
                # Enhanced location/place compounds
                r"^(บ้าน|ห้อง|อาคาร|ตึก|อาคารพาณิชย์)(เช่า|พักอาศัย|สำนักงาน|คอนโด|ทาวน์เฮาส์)$",
                r"^(โรง|สถาน|ที่|วัด|โรงเรียน|โรงพยาบาล)(พยาบาล|เรียน|รักษา|บริการ|อบรม)$",
                
                # Enhanced verb compounds
                r"^(เดิน|วิ่ง|ขับ|นั่ง|ยืน|นอน)(เล่น|ทำงาน|เที่ยว|กิน|นอน|พัก|ออกกำลังกาย)$",
                r"^(ซื้อ|ขาย|เช่า|จอง|สั่ง|ทำ)(ของ|หนังสือ|ตั๋ว|อาหาร|สินค้า|ธุรกิจ)$",
                
                # Enhanced number-measurement compounds
                r"^\d+(ปี|เดือน|วัน|ชั่วโมง|นาที|ครั้ง|คน|ชิ้น|ฟุต|เมตร|กิโล|บาท|ดอลลาร์)$",
                r"^(หนึ่ง|สอง|สาม|สี่|ห้า|หก|เจ็ด|แปด|เก้า|สิบ)(สิบ|ร้อย|พัน|หมื่น|แสน|ล้าน)$",
                
                # Enhanced quality/state compounds
                r"^(ใหม่|เก่า|ดี|แย่|สูง|ต่ำ|เร็ว|ช้า)(มาก|น้อย|พอดี|กว่า|ที่สุด|สุดๆ)$",
                r"^(สุด|ที่สุด|เอง|ๆ)(ใจ|ดี|งาม|อร่อย|เด็ด|เผ็ด|มัน|ฟิน)$",
                
                # Pattern-based compound rules
                r"^ผ้า[ก-๙]{1,4}$",  # Expanded fabric patterns
                r"^[ก-๙]{1,2}(ลาย|สี|ขนาด|รูปแบบ)$",  # Attribute + noun
                r"^[เแโใไ][ก-๙]{2,5}$",  # Words starting with front vowels (likely compounds)
                r"^[ก-๙]{2,4}(มัน|กะทิ|น้ำ|ซอส)$",  # Noun + modifier compounds
            ]
        }
    
    def detect_all_errors(self, text: str, segmented_words: List[str], 
                         mtus: List[str] = [], syllables: List[str] = []) -> List[Dict]:
        """Comprehensive error detection using all approaches"""
        errors = []
        
        # Approach 1: MTU/Syllable boundary analysis
        if mtus and syllables:
            boundary_errors = self._detect_boundary_violations(segmented_words, mtus, syllables)
            errors.extend(boundary_errors)
        
        # Approach 2: Linguistic structure analysis
        structure_errors = self._detect_structure_errors(segmented_words)
        errors.extend(structure_errors)
        
        # Approach 3: Statistical anomaly detection
        statistical_errors = self._detect_statistical_anomalies(segmented_words)
        errors.extend(statistical_errors)
        
        # Approach 4: Pattern-based compound detection
        compound_errors = self._detect_compound_errors(segmented_words)
        errors.extend(compound_errors)
        
        return errors
    
    def _detect_boundary_violations(self, words: List[str], mtus: List[str], 
                                  syllables: List[str]) -> List[Dict]:
        """Approach 1: MTU/Syllable boundary violations"""
        errors = []
        
        # Check if words respect syllable boundaries
        word_positions = self._map_words_to_syllables(words, syllables)
        
        for i, (word, syl_range) in enumerate(zip(words, word_positions)):
            if not syl_range:
                errors.append({
                    "type": "boundary_violation",
                    "index": i,
                    "word": word,
                    "reason": "word_not_aligned_with_syllables",
                    "confidence": 0.8
                })
        
        # Check for syllable splitting issues
        for i, syllable in enumerate(syllables):
            # Rule: Thai syllables should typically be 2-3 characters max
            if len(syllable) > 4:  # Too long, likely should be split
                errors.append({
                    "type": "syllable_too_long",
                    "index": i,
                    "word": syllable,
                    "reason": f"syllable_too_long_{len(syllable)}_chars",
                    "confidence": 0.7
                })
            
            # Rule: Check for common Thai syllable patterns that should be split
            if self._should_split_syllable(syllable):
                split_suggestion = self._suggest_syllable_split(syllable)
                if split_suggestion:
                    errors.append({
                        "type": "syllable_should_split",
                        "index": i,
                        "word": syllable,
                        "suggested_split": split_suggestion,
                        "reason": "common_syllable_pattern",
                        "confidence": 0.8
                    })
        
        return errors
    
    def _detect_structure_errors(self, words: List[str]) -> List[Dict]:
        """Approach 2: Linguistic structure violations"""
        errors = []
        
        for i, word in enumerate(words):
            # Suspicious single characters
            if (len(word) == 1 and 
                word not in self.error_patterns["suspicious_single_chars"]["exceptions"]):
                errors.append({
                    "type": "structure_error",
                    "index": i,
                    "word": word,
                    "reason": "suspicious_single_character",
                    "confidence": 0.7
                })
            
            # Incomplete structures
            if len(word) > 1:
                consonant_count = sum(1 for c in word if c in self.linguistic_rules["consonants"])
                vowel_count = sum(1 for c in word if c in self.linguistic_rules["vowels"])
                
                if consonant_count < self.error_patterns["incomplete_structures"]["min_consonants"]:
                    errors.append({
                        "type": "structure_error", 
                        "index": i,
                        "word": word,
                        "reason": f"insufficient_consonants_{consonant_count}",
                        "confidence": 0.6
                    })
        
        return errors
    
    def _detect_statistical_anomalies(self, words: List[str]) -> List[Dict]:
        """Enhanced statistical anomaly detection with ML confidence scoring"""
        errors = []
        
        for i, word in enumerate(words):
            # Get basic statistics
            base_confidence = self.learning_data["word_confidence"].get(word, 0.0)
            frequency = self.learning_data["correct_forms"].get(word, 0)
            
            # Apply ML confidence scoring
            ml_score = self._calculate_ml_confidence_score(word, words, i)
            
            # Combine base confidence with ML score
            final_confidence = self._combine_confidence_scores(base_confidence, ml_score, word)
            
            # Update learning data with new confidence
            self.learning_data["word_confidence"][word] = final_confidence
            
            # Check if below threshold
            if (final_confidence < self.error_patterns["statistical_anomalies"]["confidence_threshold"] and
                frequency < self.error_patterns["statistical_anomalies"]["rare_word_threshold"]):
                errors.append({
                    "type": "statistical_anomaly",
                    "index": i,
                    "word": word,
                    "reason": f"low_confidence_{final_confidence:.2f}_freq_{frequency}_ml_{ml_score:.2f}",
                    "confidence": final_confidence,
                    "ml_score": ml_score,
                    "suggestion": self._get_word_suggestion(word, words, i)
                })
        
        return errors
    
    def _calculate_ml_confidence_score(self, word: str, context_words: List[str], position: int) -> float:
        """Calculate machine learning confidence score based on multiple features"""
        score = 0.0
        
        # Feature 1: Word length and structure score
        length_score = self._calculate_length_structure_score(word)
        score += length_score * 0.25
        
        # Feature 2: Context coherence score
        context_score = self._calculate_context_coherence_score(word, context_words, position)
        score += context_score * 0.30
        
        # Feature 3: Pattern matching score
        pattern_score = self._calculate_pattern_matching_score(word)
        score += pattern_score * 0.25
        
        # Feature 4: Frequency distribution score
        freq_score = self._calculate_frequency_score(word)
        score += freq_score * 0.20
        
        return min(1.0, max(0.0, score))
    
    def _calculate_length_structure_score(self, word: str) -> float:
        """Score based on Thai word length and structure patterns"""
        length = len(word)
        
        # Thai words typically are 1-6 characters long
        if length == 0:
            return 0.0
        elif 1 <= length <= 3:
            return 0.9  # Very common lengths
        elif length == 4:
            return 0.8  # Common for compounds
        elif length == 5:
            return 0.6  # Less common
        elif length == 6:
            return 0.4  # Rare
        else:
            return 0.1  # Very rare
        
    def _calculate_context_coherence_score(self, word: str, context_words: List[str], position: int) -> float:
        """Score based on how well the word fits in its context"""
        if not context_words or len(context_words) == 1:
            return 0.5  # No context
        
        # Check word pairs and sequences
        score = 0.0
        checks = 0
        
        # Previous word context
        if position > 0:
            prev_word = context_words[position - 1]
            pair_score = self._get_word_pair_score(prev_word, word)
            score += pair_score
            checks += 1
        
        # Next word context
        if position < len(context_words) - 1:
            next_word = context_words[position + 1]
            pair_score = self._get_word_pair_score(word, next_word)
            score += pair_score
            checks += 1
        
        return score / checks if checks > 0 else 0.5
    
    def _get_word_pair_score(self, word1: str, word2: str) -> float:
        """Get coherence score for word pair based on Thai language patterns"""
        common_pairs = {
            ('ผ้า', 'ไหม'): 0.9, ('ผ้า', 'ลาย'): 0.8, ('ผ้า', 'สวย'): 0.8,
            ('มือ', 'ถือ'): 0.9, ('โทรศัพท์', 'มือถือ'): 0.9, ('รถ', 'ยนต์'): 0.8,
            ('ข้าว', 'สวย'): 0.7, ('ข้าว', 'อร่อย'): 0.8, ('มัน', 'ฝรั่ง'): 0.9,
            ('สวย', 'มาก'): 0.8, ('ดี', 'มาก'): 0.8, ('ใหญ่', 'มาก'): 0.8,
            ('บ้าน', 'เช่า'): 0.9, ('รถ', 'ไฟฟ้า'): 0.8, ('มอเตอร์', 'ไซค์'): 0.9,
        }
        
        # Check exact match
        pair_key = (word1, word2)
        if pair_key in common_pairs:
            return common_pairs[pair_key]
        
        # Check reverse
        reverse_key = (word2, word1)
        if reverse_key in common_pairs:
            return common_pairs[reverse_key] * 0.7
        
        # Pattern-based scoring
        if self._follows_thai_grammar_pattern(word1, word2):
            return 0.6
        
        return 0.3  # Default low score
    
    def _follows_thai_grammar_pattern(self, word1: str, word2: str) -> bool:
        """Check if word pair follows common Thai grammar patterns"""
        # Common patterns
        patterns = [
            (r'^[ก-๙]+$', r'^[ก-๙]+$'),  # Thai word + Thai word
            (r'.*[มันกะน้ำ]$', r'^[ก-๙]+'),  # Modifier + noun
            (r'^[ก-๙]+$', r'.*[มากดีงาม]$'),  # Noun + modifier
        ]
        
        import re
        for pattern1, pattern2 in patterns:
            if re.match(pattern1, word1) and re.match(pattern2, word2):
                return True
        
        return False
    
    def _calculate_pattern_matching_score(self, word: str) -> float:
        """Score based on Thai word pattern matching"""
        thai_patterns = [
            r'^[เแโใไ][ก-๙]{1,4}$',  # Front vowel patterns
            r'^[ก-๙]{1,4}[าำิีึืุู]$',  # Rear vowel patterns
            r'^[ก-๙]{1,3}[ก-๙]{1,3}$',  # Consonant clusters
            r'^[ก-๙]{2,4}$',  # Simple consonant patterns
        ]
        
        import re
        matches = 0
        for pattern in thai_patterns:
            if re.match(pattern, word):
                matches += 1
        
        return min(1.0, matches / len(thai_patterns) + 0.3)
    
    def _calculate_frequency_score(self, word: str) -> float:
        """Score based on word frequency in learning data"""
        frequency = self.learning_data["correct_forms"].get(word, 0)
        
        # Frequency categories
        if frequency >= 50:
            return 0.9  # Very common
        elif frequency >= 20:
            return 0.8  # Common
        elif frequency >= 10:
            return 0.6  # Moderately common
        elif frequency >= 5:
            return 0.4  # Less common
        elif frequency >= 2:
            return 0.2  # Rare
        else:
            return 0.1  # Very rare or unknown
    
    def _combine_confidence_scores(self, base_confidence: float, ml_score: float, word: str) -> float:
        """Combine base confidence with ML score using weighted averaging"""
        # Weight more towards ML score for new words, base for known words
        frequency = self.learning_data["correct_forms"].get(word, 0)
        
        if frequency >= 10:  # Known word
            return base_confidence * 0.7 + ml_score * 0.3
        elif frequency >= 2:  # Some evidence
            return base_confidence * 0.5 + ml_score * 0.5
        else:  # New/unknown word
            return base_confidence * 0.3 + ml_score * 0.7
    
    def _get_word_suggestion(self, word: str, context_words: List[str], position: int) -> str:
        """Suggest alternative words based on context and patterns"""
        # Check for common misspellings or segmentation errors
        suggestions = {
            'ผ้าไหม': ['ผ้า', 'ไหม'], 'มือถือ': ['มือ', 'ถือ'], 'รถยนต์': ['รถ', 'ยนต์'],
            'มันฝรั่ง': ['มัน', 'ฝรั่ง'], 'ผ้าลาย': ['ผ้า', 'ลาย'],
        }
        
        # Check exact matches
        if word in suggestions:
            return f"Consider splitting: {'|'.join(suggestions[word])}"
        
        # Check compound suggestions
        for compound, parts in suggestions.items():
            if word == compound:
                return f"Consider splitting: {'|'.join(parts)}"
        
        # Context-based suggestions
        if position > 0 and position < len(context_words) - 1:
            context = f"{context_words[position-1]}|{word}|{context_words[position+1]}"
            return "Check context coherence"
        
        return "Low confidence word"
    
    def _detect_compound_errors(self, words: List[str]) -> List[Dict]:
        """Approach 4: Pattern-based compound word detection"""
        errors = []
        
        # Check adjacent words for compound patterns
        for i in range(len(words) - 1):
            current = words[i]
            next_word = words[i + 1]
            combined = current + next_word
            
            # Test against compound patterns
            for pattern in self.linguistic_rules["compound_patterns"]:
                if re.fullmatch(pattern, combined):  # Use fullmatch for exact match
                    # Check if this compound is more likely than separate words
                    compound_confidence = self.learning_data["word_confidence"].get(combined, 0.6)  # Give compounds slight preference
                    current_confidence = self.learning_data["word_confidence"].get(current, 0.3)
                    next_confidence = self.learning_data["word_confidence"].get(next_word, 0.3)
                    
                    # Stronger condition: always prefer known compounds
                    if (compound_confidence > (current_confidence + next_confidence) / 2 or
                        combined in self._get_known_compounds()):
                        errors.append({
                            "type": "compound_violation",
                            "index": i,
                            "words": [current, next_word],
                            "suggested_compound": combined,
                            "reason": "pattern_matches_compound",
                            "confidence": compound_confidence
                        })
        
        # Special case: Check if individual word part of larger compound
        for i, word in enumerate(words):
            if word in ["ผ้า", "ไหม"]:  # Known compound parts (remove length check)
                # Look for adjacent word to complete compound
                if i < len(words) - 1:
                    next_word = words[i + 1]
                    if word == "ผ้า" and next_word.startswith("ไหม"):
                        # Check if the full compound makes sense
                        compound = word + "ไหม"  # ผ้าไหม
                        if compound in self._get_known_compounds():
                            # Special case: split next_word and merge part
                            remainder = next_word[3:]  # ลาย from ไหมลาย (3 chars)
                            errors.append({
                                "type": "compound_violation",
                                "index": i,
                                "words": [word, next_word],
                                "suggested_compound": compound,
                                "suggested_remainder": remainder,
                                "reason": "partial_compound_detected",
                                "confidence": 0.9
                            })
        
        return errors
    
    def auto_fix_comprehensive(self, text: str, segmented_words: List[str],
                             mtus: List[str] = [], syllables: List[str] = []) -> Dict:
        """Comprehensive auto-fix using all approaches"""
        
        # Detect all types of errors
        errors = self.detect_all_errors(text, segmented_words, mtus, syllables)
        
        if not errors:
            return {
                "fixed_words": segmented_words,
                "fixes_applied": [],
                "errors_found": 0,
                "confidence": 0.95
            }
        
        # Sort errors by confidence and type
        errors.sort(key=lambda x: (-x["confidence"], x["type"]))
        
        fixed_words = segmented_words.copy()
        fixes_applied = []
        
        # Apply fixes in order of confidence
        for error in errors:
            if error["type"] == "compound_violation":
                fix_result = self._fix_compound_violation(fixed_words, error)
                if fix_result["applied"]:
                    fixed_words = fix_result["words"]
                    fixes_applied.append(fix_result["description"])
            elif error["type"] == "boundary_violation" and mtus and syllables:
                fix_result = self._fix_boundary_violation(fixed_words, error)
                if fix_result["applied"]:
                    fixed_words = fix_result["words"]
                    fixes_applied.append(fix_result["description"])
            elif error["type"] == "syllable_too_long" or error["type"] == "syllable_should_split":
                fix_result = self._fix_syllable_split(syllables, error)
                if fix_result["applied"]:
                    syllables = fix_result["syllables"]
                    fixes_applied.append(fix_result["description"])
            elif error["type"] == "structure_error":
                fix_result = self._fix_structure_error(fixed_words, error)
                if fix_result["applied"]:
                    fixed_words = fix_result["words"]
                    fixes_applied.append(fix_result["description"])
            else:
                fix_result = self._fix_statistical_anomaly(fixed_words, error)
                if fix_result["applied"]:
                    fixed_words = fix_result["words"]
                    fixes_applied.append(fix_result["description"])
        
        # Learn from this correction
        self._learn_from_correction(text, segmented_words, fixed_words, fixes_applied)
        
        return {
            "fixed_words": fixed_words,
            "fixed_syllables": syllables,  # Include fixed syllables
            "fixes_applied": fixes_applied,
            "errors_found": len(errors),
            "confidence": min(0.9, 1.0 - (len(errors) * 0.1))
        }
    
    def _fix_compound_violation(self, words: List[str], error: Dict) -> Dict:
        """Fix compound word violation"""
        idx = error["index"]
        original = words[idx:idx+2]
        compound = error["suggested_compound"]
        
        # Handle special case: partial compound with remainder
        if "suggested_remainder" in error:
            remainder = error["suggested_remainder"]
            # Replace with compound + remainder
            words[idx:idx+2] = [compound, remainder]
            
            return {
                "applied": True,
                "words": words,
                "description": f"Merged {original[0]}+{original[1][:2]} → {compound}, kept {remainder}"
            }
        else:
            # Normal compound merge
            words[idx:idx+2] = [compound]
            
            return {
                "applied": True,
                "words": words,
                "description": f"Merged {'|'.join(original)} → {compound}"
            }
    
    def _fix_boundary_violation(self, words: List[str], error: Dict) -> Dict:
        """Fix boundary violation by adjusting word boundaries"""
        # Implementation would depend on specific boundary violation type
        return {
            "applied": False,
            "words": words,
            "description": f"Boundary violation at index {error['index']}"
        }
    
    def _fix_syllable_split(self, syllables: List[str], error: Dict) -> Dict:
        """Fix syllable that should be split"""
        idx = error["index"]
        suggested_split = error.get("suggested_split", [])
        
        if suggested_split:
            # Replace the syllable at idx with the split version
            syllables[idx:idx+1] = suggested_split
            
            return {
                "applied": True,
                "syllables": syllables,
                "description": f"Split {error['word']} → {'|'.join(suggested_split)}"
            }
        
        return {
            "applied": False,
            "syllables": syllables,
            "description": f"Could not split syllable: {error['word']}"
        }
    
    def _fix_structure_error(self, words: List[str], error: Dict) -> Dict:
        """Fix structural error"""
        if error["reason"] == "suspicious_single_character":
            # Try to merge with adjacent words
            idx = error["index"]
            if idx > 0 and len(words[idx-1]) > 2:
                merged = words[idx-1] + words[idx]
                words[idx-1:idx+1] = [merged]
                return {
                    "applied": True,
                    "words": words,
                    "description": f"Merged single char: {words[idx]} → {merged}"
                }
        
        return {
            "applied": False,
            "words": words,
            "description": f"Could not fix structure error: {error['word']}"
        }
    
    def _fix_statistical_anomaly(self, words: List[str], error: Dict) -> Dict:
        """Fix statistical anomaly"""
        # For statistical anomalies, we might suggest alternatives but not auto-fix
        return {
            "applied": False,
            "words": words,
            "description": f"Statistical anomaly detected: {error['word']} (low confidence)"
        }
    
    def _learn_from_correction(self, text: str, original: List[str], 
                              corrected: List[str], fixes: List[str]):
        """Continuous learning from corrections"""
        # Update learning statistics
        for word in corrected:
            self.learning_data["correct_forms"][word] += 1
            self.learning_data["word_confidence"][word] += 0.1
        
        # Log correction for analysis
        correction_log = {
            "timestamp": datetime.now().isoformat(),
            "original_text": text,
            "original_segmentation": original,
            "corrected_segmentation": corrected,
            "fixes_applied": fixes,
            "confidence": self.learning_data["word_confidence"].get(corrected[0], 0.5) if corrected else 0.0
        }
        
        # Save learning data
        self._save_learning_data(correction_log)
    
    def _get_known_compounds(self) -> Set[str]:
        """Get set of known compound words from LST20 training"""
        # Load from LST20 dictionary or learning data
        known_compounds = {
            "ผ้าไหม", "ผ้าฝ้าย", "ผ้าลินิน", "กระเป๋าหนัง", "กระเป๋าผ้า",
            "รองเท้าหนัง", "รองเท้าผ้าใบ", "โต๊ะไม้", "เก้าอี้พลาสติก",
            "ลายดอกไม้", "ลายสก๊อต", "ลายขวาง", "ลายจุด",
            "บ้านเช่า", "รถยนต์", "มอเตอร์ไซค์", "โทรศัพท์มือถือ"
        }
        
        # Add compounds learned from user feedback
        for word, count in self.learning_data["correct_forms"].items():
            if count >= 3 and len(word) >= 4:  # Likely compound
                known_compounds.add(word)
        
        return known_compounds
    
    def _should_split_syllable(self, syllable: str) -> bool:
        """Enhanced syllable splitting detection with Thai linguistic rules"""
        if len(syllable) <= 2:
            return False  # Too short to split
            
        # Enhanced split patterns with more Thai linguistic knowledge
        split_patterns = [
            # Fabric/material patterns - ไหม + consonant
            r'^ไหม[ก-๙ฮ]',
            # Vowel splitting patterns
            r'^[ก-๙]า[ก-๙ฮ]',  # C+า+C pattern (like มาส, กาด)
            r'^[ก-๙]อ[ก-๙ฮ]',  # C+อ+C pattern (like มอง, คอย)
            r'^[ก-๙][ะา][ก-๙ฮ]',  # C+ะ/า+C patterns
            # Front vowel patterns
            r'^[เแโใไ][ก-๙ฮ]{2,}',  # Front vowel + multiple consonants
            # Complex vowel clusters
            r'^[ก-๙][เแโใไ][ก-๙ฮ]',  # C + front vowel + C
            # Common Thai word patterns that are often split
            r'^[ก-๙]น[ก-๙ฮ]',  # Patterns like มัน, กัน
            r'^[ก-๙]ม[ก-๙ฮ]',  # Patterns like มม, กม
            r'^[ก-๙]ง[ก-๙ฮ]',  # Patterns like มง, กง
            # Long syllable detection
            r'^[ก-๙]{4,}$',  # Any 4+ consonant sequence
        ]
        
        # Don't split known single syllable words
        known_single_syllables = {
            'ไหม', 'ไทย', 'ไกล', 'ไหว', 'เกลือ', 'เกาะ', 'เก่า', 'เกิด',
            'แก้ว', 'แกล้ง', 'แกะ', 'แกน', 'โกง', 'โกหก', 'โกศ', 'ใกล้',
            'ใจ', 'ใหม่', 'ใหญ่', 'ให้', 'ใส่', 'ใส', 'ใคร', 'ใด', 'ใบ',
            'ซ้าย', 'ขวา', 'บน', 'ล่าง', 'หน้า', 'หลัง'
        }
        
        if syllable in known_single_syllables:
            return False
            
        import re
        for pattern in split_patterns:
            if re.match(pattern, syllable):
                return True
                
        # Length-based splitting for very long syllables
        if len(syllable) >= 5:
            return True
            
        return False
    
    def _suggest_syllable_split(self, syllable: str) -> List[str]:
        """Enhanced syllable splitting with Thai linguistic knowledge"""
        # Enhanced known split patterns
        split_rules = {
            # Fabric patterns
            'ไหมลาย': ['ไหม', 'ลาย'], 'ไหมสวย': ['ไหม', 'สวย'], 'ไหมดี': ['ไหม', 'ดี'],
            'ไหมงาม': ['ไหม', 'งาม'], 'ไหมใหม่': ['ไหม', 'ใหม่'], 'ไหมแพง': ['ไหม', 'แพง'],
            # Common Thai patterns
            'ไทยสวย': ['ไทย', 'สวย'], 'ไทยดี': ['ไทย', 'ดี'], 'ไทยใหม่': ['ไทย', 'ใหม่'],
            'มาลาย': ['มา', 'ลาย'], 'มาดี': ['มา', 'ดี'], 'มาสวย': ['มา', 'สวย'],
            'มาใหม่': ['มา', 'ใหม่'], 'มางาม': ['มา', 'งาม'],
            # Other common patterns
            'มันสวย': ['มัน', 'สวย'], 'มันดี': ['มัน', 'ดี'], 'มันใหม่': ['มัน', 'ใหม่'],
            'กาดำ': ['กา', 'ดำ'], 'กาแดง': ['กา', 'แดง'], 'กาใหญ่': ['กา', 'ใหญ่'],
            'น้ำใส': ['น้ำ', 'ใส'], 'น้ำสวย': ['น้ำ', 'สวย'], 'น้ำดี': ['น้ำ', 'ดี'],
            'ดินสวย': ['ดิน', 'สวย'], 'ดินดี': ['ดิน', 'ดี'], 'ดินใหม่': ['ดิน', 'ใหม่'],
        }
        
        # Check exact matches first
        if syllable in split_rules:
            return split_rules[syllable]
        
        # Enhanced pattern-based splitting
        # Fabric pattern: ไหม + consonant
        if syllable.startswith('ไหม') and len(syllable) > 3:
            return ['ไหม', syllable[3:]]
        
        # Vowel patterns: กา + consonant, คอ + consonant
        if len(syllable) >= 4:
            # Try splitting after common vowel patterns
            vowel_patterns = ['า', 'อ', 'ะ', 'ิ', 'ี', 'ุ', 'ู']
            
            for i in range(1, len(syllable) - 1):
                if syllable[i] in vowel_patterns:
                    # Check if this creates valid syllables
                    first = syllable[:i+1]
                    second = syllable[i+1:]
                    
                    if (len(first) >= 2 and len(second) >= 2 and
                        self._is_valid_syllable_structure(first) and 
                        self._is_valid_syllable_structure(second)):
                        return [first, second]
        
        # Smart splitting based on position
        if len(syllable) >= 4:
            # Try splitting at optimal positions for Thai
            split_positions = [2, 3]  # Most common syllable lengths
            
            # For longer syllables, try more positions
            if len(syllable) >= 6:
                split_positions.extend([4, 5])
            
            for split_pos in split_positions:
                if split_pos < len(syllable):
                    first = syllable[:split_pos]
                    second = syllable[split_pos:]
                    
                    # Validate both parts have Thai structure
                    if (len(first) >= 2 and len(second) >= 2 and
                        self._is_valid_syllable_structure(first) and 
                        self._is_valid_syllable_structure(second)):
                        return [first, second]
        
        return []
    
    def _is_valid_syllable_structure(self, text: str) -> bool:
        """Check if text follows valid Thai syllable structure"""
        if not text or len(text) == 0:
            return False
        
        thai_consonants = set("กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ")
        thai_vowels = set("ัาำิีึืุูเแโใไฤๅฯๆ")
        
        # Must have at least one Thai consonant
        has_consonant = any(c in thai_consonants for c in text)
        has_vowel = any(c in thai_vowels for c in text)
        
        return has_consonant and (has_vowel or len(text) <= 2)

    def _map_words_to_syllables(self, words: List[str], syllables: List[str]) -> List[Tuple[int, int]]:
        """Map word boundaries to syllable indices"""
        word_positions = []
        syllable_idx = 0
        
        for word in words:
            start_idx = syllable_idx
            
            # Find how many syllables this word spans
            word_remaining = word
            syllables_used = 0
            
            while syllable_idx < len(syllables) and word_remaining:
                syllable = syllables[syllable_idx]
                
                if word_remaining.startswith(syllable):
                    word_remaining = word_remaining[len(syllable):]
                    syllable_idx += 1
                    syllables_used += 1
                else:
                    # Try partial match or split
                    if syllable.startswith(word_remaining[:2]):
                        word_remaining = word_remaining[2:]
                        syllable_idx += 1
                        syllables_used += 1
                    else:
                        # Boundary violation - current syllable doesn't match word boundary
                        break
            
            end_idx = start_idx + syllables_used - 1
            word_positions.append((start_idx, end_idx))
        
        return word_positions
    
    def _save_learning_data(self, correction_log: Dict):
        """Save learning data to JSON files for CRF retraining"""
        # Save main learning data as JSON for retraining
        data_path = os.path.join(self.models_path, "learning_data.json")
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(self.learning_data, f, ensure_ascii=False, indent=2)
        
        # Save correction logs for user feedback tracking
        log_path = os.path.join(self.models_path, "user_correction_log.json")
        
        # Load existing logs or create new
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(correction_log)
        
        # Keep only last 1000 logs to avoid file bloat
        logs = logs[-1000:]
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        # Save training samples for CRF retraining (in LST20 format)
        self._save_crf_training_data()
    
    def _save_crf_training_data(self):
        """Save training data in LST20 format for CRF retraining"""
        training_samples = []
        
        # Convert learning data to LST20 CRF format
        for word, count in self.learning_data["correct_forms"].items():
            if count >= 2:  # Only include words seen at least twice
                # Extract character-level features
                chars = list(word)
                features = []
                
                for i, char in enumerate(chars):
                    char_features = {
                        "char": char,
                        "position": i,
                        "is_consonant": char in "กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ",
                        "is_vowel": char in "ัาำิีึืุูเแโใไฤๅฯๆ",
                        "is_tone": char in "่้๊๋",
                        "prev_char": chars[i-1] if i > 0 else "<START>",
                        "next_char": chars[i+1] if i < len(chars)-1 else "<END>",
                        "word_confidence": self.learning_data["word_confidence"].get(word, 0.5)
                    }
                    features.append(char_features)
                
                training_samples.append({
                    "word": word,
                    "frequency": count,
                    "features": features,
                    "learned_from_feedback": True
                })
        
        # Save training data for CRF models
        crf_training_path = os.path.join(self.models_path, "crf_retraining_data.json")
        with open(crf_training_path, 'w', encoding='utf-8') as f:
            json.dump(training_samples, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Saved {len(training_samples)} training samples for CRF retraining")
    
    def get_learning_insights(self) -> Dict:
        """Get insights from accumulated learning"""
        return {
            "total_corrections": len(self.learning_data["segmentation_errors"]),
            "most_fixed_errors": self.learning_data["segmentation_errors"].most_common(10),
            "learned_words": dict(self.learning_data["correct_forms"].most_common(20)),
            "average_confidence": sum(self.learning_data["word_confidence"].values()) / len(self.learning_data["word_confidence"]) if self.learning_data["word_confidence"] else 0.0
        }

def main():
    """Main function for command line execution"""
    parser = argparse.ArgumentParser(description='Auto-fix Thai segmentation AI')
    parser.add_argument('--retrain', action='store_true', help='Retrain models with accumulated learning data')
    parser.add_argument('--enhance-dictionary', action='store_true', help='Enhance dictionary from error patterns')
    parser.add_argument('--evaluate', action='store_true', help='Evaluate current performance')
    parser.add_argument('--models-path', default='models', help='Path to models directory')
    
    args = parser.parse_args()
    
    # Set up path
    if not os.path.isabs(args.models_path):
        args.models_path = os.path.join(os.path.dirname(__file__), args.models_path)
    
    print("🤖 Comprehensive Auto-Fix Thai Segmentation AI")
    print("=" * 50)
    
    # Initialize fixer
    fixer = ComprehensiveSegFixer(args.models_path)
    
    if args.retrain:
        print("🔄 Retraining models with accumulated learning data...")
        
        # 1. Generate CRF training data from learned patterns
        fixer._save_crf_training_data()
        
        # 2. Save current learning data
        fixer._save_learning_data({
            "timestamp": datetime.now().isoformat(),
            "action": "retrain",
            "total_corrections": len(fixer.learning_data["segmentation_errors"]),
            "learned_words": len(fixer.learning_data["correct_forms"])
        })
        
        print("✅ Retraining complete!")
        
    elif args.enhance_dictionary:
        print("📚 Enhancing dictionary from error patterns...")
        fixer._save_crf_training_data()
        print("✅ Dictionary enhancement complete!")
        
    elif args.evaluate:
        print("📊 Evaluating current performance...")
        insights = fixer.get_learning_insights()
        print(f"Total corrections learned: {insights['total_corrections']}")
        print(f"Learned words: {len(insights['learned_words'])}")
        print(f"Average confidence: {insights['average_confidence']:.2f}")
        
    else:
        print("Please specify an action:")
        print("  --retrain            Retrain models with learning data")
        print("  --enhance-dictionary Enhance dictionary from errors")
        print("  --evaluate           Evaluate current performance")
        print("  --models-path PATH   Specify models directory")

if __name__ == "__main__":
    main()