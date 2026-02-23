"""
CRF-based POS Tagger for Thai Words
Implements LST20 specification with 16 POS tags and IOB tagging scheme

Features:
- Unigram word features: n=-2,-1,0,1,2
- Bigram context features: C1, C2  
- Character-based features for unknown words
- Pattern-based features for prefixes/suffixes

Architecture:
- Trains on LST20 corpus (train split)
- Evaluates on LST20 corpus (test split)
- Saves model with performance metrics
"""

import os
import sys
import pickle
import random
from collections import defaultdict, Counter
from typing import List, Dict, Tuple
import argparse

# Add proper encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)

# LST20 POS Tags (16 tags as specified)
LST20_TAGS = [
    'NN',    # Noun
    'VV',    # Verb
    'VV',    # Verb  
    'NU',    # Numeral
    'PX',    # Preceding Modifier
    'JJ',    # Adjective
    'XX',    # Unknown
    'PS',    # Possessive
    'AV',    # Adverb
    'AY',    # Adverb
    'NG',    # Negator
    'RZ',    # Royal Name
    'FX',    # Function Word
    'O',     # Other
    'PU',    # Punctuation
    'NNP',   # Proper Noun
    'I_CLS', # Inside Clause
    'B_ORG', # Begin Organization
    'E_ORG', # End Organization
    'B_LOC',  # Begin Location  
    'E_LOC',  # End Location
]

# IOB Tag Scheme for phrase boundaries
IOB_TAGS = ['B-', 'I-', 'E-', 'S-', 'O']


class CRFPOSTagger:
    """
    CRF-based POS Tagger with feature extraction and training capabilities
    """
    
    def __init__(self):
        self.model = None
        self.word_to_pos = defaultdict(Counter)
        self.char_features = {}
        self.tag_stats = defaultdict(int)
        
    def extract_word_features(self, words: List[str], i: int) -> Dict:
        """
        Extract features for word at position i following LST20 specification
        
        Template: n=-2,-1,0,1,2 + C1 + C2 + word features
        """
        word = words[i]
        features = {
            # Word identity features
            'word': word,
            'word.lower()': word.lower(),
            'word.isupper()': word.isupper(),
            'word.islower()': word.islower(),
            'word[-3:]': word[-3:] if len(word) >= 3 else '',
            'word[-2:]': word[-2:] if len(word) >= 2 else '',
            'word[:2]': word[:2] if len(word) >= 2 else '',
            'word[:3]': word[:3] if len(word) >= 3 else '',
            'word.length': len(word),
            'word.is_digit': word.isdigit(),
            'word.has_digit': any(c.isdigit() for c in word),
            'word.is_punctuation': self._is_punctuation(word),
            'word.is_thai': self._is_thai_word(word),
            
            # Unigram context features (n=-2,-1,0,1,2)
        }
        
        # Previous context (n=-2,-1)
        for offset in [-2, -1]:
            pos = i + offset
            if pos >= 0:
                context_word = words[pos]
                features[f'word[{offset:+d}]'] = context_word
                features[f'word[{offset:+d}].lower()'] = context_word.lower()
                features[f'word[{offset:+d}].length()'] = len(context_word)
            else:
                features[f'word[{offset:+d}]'] = '<BOS>'
                features[f'word[{offset:+d}].length()'] = 0
        
        # Current position (n=0)
        features['word[0]'] = word
        features['word[0].lower()'] = word.lower()
        features['word[0].length()'] = len(word)
        features['word[0].isfirst()'] = True
        features['word[0].islast()'] = (i == len(words) - 1)
        
        # Next context (n=1,2)
        for offset in [1, 2]:
            pos = i + offset
            if pos < len(words):
                context_word = words[pos]
                features[f'word[{offset:+d}]'] = context_word
                features[f'word[{offset:+d}].lower()'] = context_word.lower()
                features[f'word[{offset:+d}].length()'] = len(context_word)
            else:
                features[f'word[{offset:+d}]'] = '<EOS>'
                features[f'word[{offset:+d}].length()'] = 0
        
        # Bigram context features (C1, C2)
        if i > 0:
            features['C1.word'] = words[i-1]
            features['C1.word.lower()'] = words[i-1].lower()
            
        if i < len(words) - 1:
            features['C2.word'] = words[i+1]  
            features['C2.word.lower()'] = words[i+1].lower()
        
        # Character-based features for fallback
        if not self._is_thai_word(word):
            features.update(self._extract_char_features(word))
        
        # Thai-specific features
        features.update(self._extract_thai_features(word, words, i))
        
        return features
    
    def _extract_char_features(self, word: str) -> Dict:
        """Extract character-level features for unknown words"""
        if not word:
            return {}
            
        features = {}
        for i, char in enumerate(word):
            features[f'char[{i}]'] = char
            features[f'char[{i}].is_digit'] = char.isdigit()
            features[f'char[{i}].is_upper'] = char.isupper()
            features[f'char[{i}].is_lower()'] = char.islower()
            features[f'char[{i}].is_thai'] = self._is_thai_char(char)
            
        features['first_char'] = word[0] if word else ''
        features['last_char'] = word[-1] if word else ''
        features['has_punctuation'] = any(self._is_punctuation(c) for c in word)
        
        return features
    
    def _extract_thai_features(self, word: str, words: List[str], i: int) -> Dict:
        """Extract Thai-specific features"""
        features = {}
        
        # Thai consonants and vowels
        thai_consonants = set('กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ'.split())
        thai_vowels = set('เแโใไ'
        'ะาำๅฤๆเือิีึื็ั่้๊๋'.split())
        
        # Character classification
        for c in word:
            features[f'{c}.is_consonant'] = c in thai_consonants
            features[f'{c}.is_vowel'] = c in thai_vowels
            features[f'{c}.is_tone'] = c in '่้๊๋'
            features[f'{c}.is_karan'] = c == '์'
        
        # Thai-specific patterns
        features['has_thai_tone'] = any(c in '่้๊๋' for c in word)
        features['has_karan'] = '์' in word
        features['starts_with_thai_vowel'] = any(word.startswith(v) for v in thai_vowels)
        
        # Thai prefixes and suffixes
        prefixes = ['การ', 'ความ', 'ผู้', 'แม่', 'นัก', 'ที่']
        suffixes = ['กัน', 'ครั้ง', 'มาก', 'อย่าง', 'มา']
        
        for prefix in prefixes:
            features[f'prefix.{prefix}'] = word.startswith(prefix)
        
        for suffix in suffixes:
            features[f'suffix.{suffix}'] = word.endswith(suffix)
        
        return features
    
    def _is_thai_word(self, word: str) -> bool:
        """Check if word contains Thai characters"""
        return any('\u0e00' <= c <= '\u0e7f' for c in word)
    
    def _is_thai_char(self, char: str) -> bool:
        """Check if character is Thai"""
        return '\u0e00' <= char <= '\u0e7f'
    
    def _is_punctuation(self, text: str) -> bool:
        """Check if text is primarily punctuation"""
        punctuation_chars = set('.,!?;:()[]{}"\'')
        return all(c in punctuation_chars for c in text)
    
    def extract_features(self, words: List[str]) -> List[Dict]:
        """Extract features for all words in sentence"""
        return [self.extract_word_features(words, i) for i in range(len(words))]
    
    def train(self, train_file: str, test_file: str = None):
        """
        Train CRF POS Tagger on LST20 corpus
        
        Args:
            train_file: Path to training data
            test_file: Path to test data (optional)
        """
        print("Training CRF POS Tagger...")
        print(f"Training data: {train_file}")
        
        # Load training data
        X_train = []
        y_train = []
        
        with open(train_file, 'r', encoding='utf-8') as f:
            sentence_words = []
            sentence_pos = []
            
            for line in f:
                line = line.strip()
                
                if not line:  # Empty line = end of sentence
                    if sentence_words:
                        X_train.append(self.extract_features(sentence_words))
                        y_train.append(sentence_pos)
                        sentence_words = []
                        sentence_pos = []
                else:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        word = parts[0]
                        pos = parts[1] if len(parts) > 1 else 'NN'
                        
                        # Build word-to-POS mapping
                        self.word_to_pos[word][pos] += 1
                        
                        sentence_words.append(word)
                        sentence_pos.append(pos)
            
            # Handle last sentence
            if sentence_words:
                X_train.append(self.extract_features(sentence_words))
                y_train.append(sentence_pos)
        
        print(f"Loaded {len(X_train)} sentences, {sum(len(sent) for sent in X_train)} words")
        print(f"Unique POS tags: {sorted(set(pos for sent in y_train for pos in sent))}")
        
        # Train CRF model
        try:
            import pycrfsuite
            from sklearn.model_selection import train_test_split
            
            # Create validation split
            X_train_split, X_val, y_train_split, y_val = train_test_split(
                X_train, y_train, test_size=0.1, random_state=42
            )
            
            # Train CRF
            self.model = pycrfsuite.train(
                X_train_split, y_train_split,
                algorithm='lbfgs',
                c1=0.1, c2=0.1,
                max_iterations=100,
                all_possible_transitions=True
            )
            
            # Evaluate on validation set
            y_val_pred = self.model.predict(X_val)
            
            from sklearn.metrics import classification_report, accuracy_score
            print(f"Validation Accuracy: {accuracy_score(y_val, y_val_pred):.4f}")
            print("Classification Report:")
            print(classification_report(
                [item for sublist in y_val for item in sublist],
                [item for sublist in y_val_pred for item in sublist],
                target_names=LST20_TAGS
            ))
            
        except ImportError:
            print("Warning: pycrfsuite not found. Using basic CRF training.")
            import sklearn_crfsuite
            self.model = sklearn_crfsuite.train(
                X_train_split, y_train_split,
                algorithm='lbfgs',
                c1=0.1, c2=0.1,
                max_iterations=100
            )
    
    def evaluate(self, test_file: str):
        """Evaluate trained model on test data"""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        print(f"Evaluating on: {test_file}")
        
        X_test = []
        y_test = []
        
        with open(test_file, 'r', encoding='utf-8') as f:
            sentence_words = []
            sentence_pos = []
            
            for line in f:
                line = line.strip()
                
                if not line:  # End of sentence
                    if sentence_words:
                        X_test.append(self.extract_features(sentence_words))
                        y_test.append(sentence_pos)
                        sentence_words = []
                        sentence_pos = []
                else:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        word = parts[0]
                        pos = parts[1] if len(parts) > 1 else 'NN'
                        sentence_words.append(word)
                        sentence_pos.append(pos)
            
            if sentence_words:
                X_test.append(self.extract_features(sentence_words))
                y_test.append(sentence_pos)
        
        # Predict
        y_pred = self.model.predict(X_test)
        
        # Calculate metrics
        from sklearn.metrics import classification_report, accuracy_score, f1_score
        
        # Flatten for evaluation
        y_true_flat = [item for sublist in y_test for item in sublist]
        y_pred_flat = [item for sublist in y_pred for item in sublist]
        
        print(f"Test Accuracy: {accuracy_score(y_true_flat, y_pred_flat):.4f}")
        print(f"Macro F1: {f1_score(y_true_flat, y_pred_flat, average='macro'):.4f}")
        print(f"Micro F1: {f1_score(y_true_flat, y_pred_flat, average='micro'):.4f}")
        
        print("\nDetailed Classification Report:")
        print(classification_report(y_true_flat, y_pred_flat, target_names=LST20_TAGS))
    
    def predict(self, words: List[str]) -> List[str]:
        """Predict POS tags for words"""
        if self.model is None:
            # Fallback to rule-based prediction
            return self._fallback_predict(words)
        
        features = self.extract_features(words)
        pos_tags = self.model.predict(features)
        
        # Convert to simple tags (remove IOB if present)
        simple_tags = []
        for tag in pos_tags:
            if any(tag.startswith(prefix) for prefix in ['B-', 'I-', 'E-']):
                simple_tags.append(tag[2:])  # Remove IOB prefix
            else:
                simple_tags.append(tag)
        
        return simple_tags
    
    def _fallback_predict(self, words: List[str]) -> List[str]:
        """
        Rule-based fallback POS prediction for unknown words
        
        Based on Thai linguistic patterns:
        - Words ending with กัน → VERB
        - Words starting with การ → NOUN (gerund)
        - Numeric words → NUMERAL
        - Thai punctuation → PUNCT
        - Common patterns → assigned based on frequency and context
        """
        pos_tags = []
        
        for word in words:
            if not word.strip():
                pos_tags.append('PU')
                continue
            
            # Rule-based prediction
            if word.isdigit():
                pos_tags.append('NU')
            elif word.endswith(('กัน', 'ครั้ง', 'มาก', 'อย่าง')):
                pos_tags.append('VV')
            elif word.startswith(('การ', 'ความ', 'ผู้', 'แม่', 'นัก')):
                pos_tags.append('NN')
            elif word in self.word_to_pos:
                # Use frequency-based prediction
                pos_counts = self.word_to_pos[word]
                pos_tags.append(pos_counts.most_common(1)[0][0])
            elif self._is_thai_word(word):
                pos_tags.append('NN')  # Default Thai word to noun
            else:
                pos_tags.append('XX')  # Unknown foreign word
        
        return pos_tags
    
    def save_model(self, model_path: str):
        """Save trained model"""
        if self.model is None:
            raise ValueError("No model to save")
        
        print(f"Saving model to: {model_path}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save word-to-POS mapping for reference
        mapping_path = model_path.replace('.pkl', '_word_to_pos.pkl')
        with open(mapping_path, 'wb') as f:
            pickle.dump(dict(self.word_to_pos), f)
        
        print("Model and word-to-POS mapping saved successfully!")
    
    def load_model(self, model_path: str):
        """Load trained model"""
        print(f"Loading POS model: {model_path}")
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        # Load word-to-POS mapping if exists
        mapping_path = model_path.replace('.pkl', '_word_to_pos.pkl')
        if os.path.exists(mapping_path):
            with open(mapping_path, 'rb') as f:
                self.word_to_pos = defaultdict(Counter, pickle.load(f))
        
        print("POS model loaded successfully!")
    
    def get_best_possible_tag(self, word: str, context_words: List[str]) -> str:
        """
        Get best possible POS tag for unknown word using context and linguistic rules
        
        Thai POS heuristics for common patterns:
        - Thai adjectives: สวยงาย, สวยงมาก, ดี, สวย, งาม, สวยฝ้าย, etc.
        - Thai adverbs: มาก, น้อย, เร็วๆ, เสมอ, ดังๆ, etc.
        - Thai negators: ไม่
        - Thai classifiers: คน, วัน, ตัว, ปี, เดือน, ชิ้น, etc.
        """
        if word in self.word_to_pos:
            return self.word_to_pos[word].most_common(1)[0][0]
        
        # Thai-specific heuristics for unknown words
        # Check for adjective patterns
        adj_patterns = ['งาย', 'สวย', 'ฝ้าย', 'สวยง']
        if any(pattern in word for pattern in adj_patterns):
            return 'JJ'  # Adjective
        
        # Check for adverb patterns  
        adv_patterns = ['มาก', 'น้อย', 'เร็วๆ', 'ดังๆ', 'เสมอ', 'จริง']
        if any(pattern in word for pattern in adv_patterns):
            return 'AV'  # Adverb
        
        # Check for negator
        if word == 'ไม่':
            return 'NG'  # Negator
        
        # Check for classifiers (follows numbers)
        classifier_words = ['คน', 'วัน', 'ตัว', 'ปี', 'เดือน', 'ชิ้น']
        if word in classifier_words:
            return 'CLS'  # Classifier
        
        # Context-based prediction
        left_words = context_words[:context_words.index(word)]
        right_words = context_words[context_words.index(word)+1:]
        
        # Count POS tags in context
        pos_counts = defaultdict(int)
        for context_word in left_words + right_words:
            if context_word in self.word_to_pos:
                for pos, count in self.word_to_pos[context_word].items():
                    pos_counts[pos] += count
        
        if pos_counts:
            return max(pos_counts.items(), key=lambda x: x[1])[0]
        
        # Default fallback
        return 'NN'  # Default to Noun for unknown Thai words
    
    def _pattern_based_prediction(self, word: str, left_words: List[str], right_words: List[str]) -> str:
        """
        Pattern-based POS prediction using linguistic rules
        """
        # Thai POS prediction rules
        
        # Number detection
        if word.isdigit() or all(c in '๐๑๒๓๔๕๖๗๘๙' for c in word):
            return 'NU'
        
        # Punctuation
        if self._is_punctuation(word):
            return 'PU'
        
        # Common Thai prefixes
        noun_prefixes = ['การ', 'ความ', 'ผู้', 'แม่', 'นัก', 'ที่']
        for prefix in noun_prefixes:
            if word.startswith(prefix):
                return 'NN'
        
        # Common Thai suffixes  
        verb_suffixes = ['กัน', 'ครั้ง', 'มาก', 'อย่าง', 'ลง']
        for suffix in verb_suffixes:
            if word.endswith(suffix):
                return 'VV'
        
        # Adjective suffixes
        adj_suffixes = ['ที่สุด', 'มาก', 'น้อย']
        for suffix in adj_suffixes:
            if word.endswith(suffix):
                return 'JJ'
        
        # Adverb words
        adv_words = ['มาก', 'น้อย', 'เร็วๆ', 'เสมอ', 'ดังๆ']
        if word in adv_words:
            return 'AV'
        
        # Negator
        if word == 'ไม่':
            return 'NG'
        
        # Default to noun for Thai words
        if self._is_thai_word(word):
            return 'NN'
        
        # Default unknown for foreign words
        return 'XX'
    
    def get_model_info(self) -> Dict:
        """Get information about trained model"""
        if self.model is None:
            return {"status": "not_trained"}
        
        return {
            "status": "trained",
            "word_to_pos_size": len(self.word_to_pos),
            "pos_tags": LST20_TAGS,
            "feature_count": len(next(iter(self.word_to_pos), {})) if self.word_to_pos else 0
        }


def main():
    """
    Main training and evaluation pipeline
    """
    parser = argparse.ArgumentParser(description='CRF POS Tagger for Thai Words')
    parser.add_argument('--train', type=str, help='Training data file path')
    parser.add_argument('--test', type=str, help='Test data file path')
    parser.add_argument('--model', type=str, help='Model output path')
    parser.add_argument('--mode', choices=['train', 'eval', 'predict', 'test'], default='train',
                       help='Operation mode: train, eval, predict, or test')
    parser.add_argument('--epochs', type=int, default=100, help='Training epochs')
    parser.add_argument('--retrain', action='store_true', help='Retrain with accumulated learning data')
    
    args = parser.parse_args()
    
    tagger = CRFPOSTagger()
    
    if args.mode == 'train':
        if not args.train or not args.model:
            print("Error: --train and --model required")
            return
        
        tagger.train(args.train, args.test if args.test else None)
        tagger.save_model(args.model)
        
    elif args.mode == 'eval':
        if not args.test or not args.model:
            print("Error: --test and --model required for evaluation")
            return
        
        tagger.load_model(args.model)
        tagger.evaluate(args.test)
        
    elif args.mode == 'predict':
        if not args.model:
            print("Error: --model required for prediction")
            return
        
        tagger.load_model(args.model)
        
        # Example prediction
        test_words = ['ผม', 'ชอบ', 'มันฝรั่ง', 'ทอด', 'สวย', 'มาก']
        pos_tags = tagger.predict(test_words)
        
        print("Sample predictions:")
        for word, pos in zip(test_words, pos_tags):
            print(f"{word:12} -> {pos}")
    
    elif args.mode == 'test':
        # Run quick test evaluation
        model_path = args.model or os.path.join(os.path.dirname(__file__), '..', 'models', 'pos_crf_model.pkl')
        test_path = args.test or r"D:\project\word_wrapping\script\data\AIFORTHAI-LST20Corpus\LST20_Corpus\eval"
        
        if os.path.exists(model_path) and os.path.exists(test_path):
            tagger.load_model(model_path)
            tagger.evaluate(test_path)
        else:
            print(f"Model or test file not found")
            print(f"Model: {model_path}")
            print(f"Test: {test_path}")
    
    elif args.retrain:
        # Retrain with accumulated learning data
        model_path = args.model or os.path.join(os.path.dirname(__file__), '..', 'models', 'pos_crf_model.pkl')
        training_data = os.path.join(os.path.dirname(__file__), '..', 'models', 'crf_retraining_data.json')
        
        if os.path.exists(training_data):
            print(f"🔄 Retraining POS model with accumulated data...")
            tagger.train(training_data, None)
            tagger.save_model(model_path)
            print("✅ POS model retraining complete")
        else:
            print(f"❌ No retraining data found at: {training_data}")
    
    else:
        print(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()