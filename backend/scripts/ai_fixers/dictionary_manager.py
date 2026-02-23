"""
Dictionary Management Interface
Handles adding new words to dictionary from user feedback
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Set

class DictionaryManager:
    """Manages dictionary updates from user feedback"""
    
    def __init__(self, dictionary_path: str):
        self.dictionary_path = dictionary_path
        self.dictionary_json_path = dictionary_path.replace('.pkl', '.json')
        self.pending_additions = []
        
    def load_dictionary_data(self) -> Dict:
        """Load dictionary from JSON"""
        if os.path.exists(self.dictionary_json_path):
            with open(self.dictionary_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                'words': [],
                'word_to_pos': {},
                'compounds': [],
                'stats': {
                    'total_words': 0,
                    'unique_words': 0,
                    'compounds_generated': 0
                },
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
    
    def add_words_from_feedback(self, feedback_data: Dict):
        """Add new words based on user feedback"""
        dictionary_data = self.load_dictionary_data()
        words_set = set(dictionary_data['words'])
        word_to_pos = dictionary_data['word_to_pos']
        
        # Process user corrections
        if 'user_corrections' in feedback_data:
            corrections = feedback_data['user_corrections']
            
            for correction in corrections:
                corrected_word = correction.get('corrected_word', '')
                pos_suggestion = correction.get('pos_suggestion', 'NN')  # Default to noun
                
                if corrected_word and corrected_word not in words_set:
                    # Add new word
                    words_set.add(corrected_word)
                    
                    # Add POS mapping
                    if corrected_word not in word_to_pos:
                        word_to_pos[corrected_word] = {}
                    
                    word_to_pos[corrected_word][pos_suggestion] = word_to_pos[corrected_word].get(pos_suggestion, 0) + 1
                    
                    # Track addition
                    self.pending_additions.append({
                        'word': corrected_word,
                        'pos': pos_suggestion,
                        'source': 'user_feedback',
                        'timestamp': datetime.now().isoformat(),
                        'original_segmentation': correction.get('original_segmentation', [])
                    })
                    
                    print(f"➕ Added new word: {corrected_word} ({pos_suggestion})")
        
        # Update dictionary data
        dictionary_data['words'] = list(words_set)
        dictionary_data['word_to_pos'] = word_to_pos
        dictionary_data['stats']['unique_words'] = len(words_set)
        dictionary_data['last_updated'] = datetime.now().isoformat()
        
        # Save updated dictionary
        self.save_dictionary(dictionary_data)
        
        return {
            'words_added': len(self.pending_additions),
            'total_words': len(words_set),
            'pending_additions': self.pending_additions
        }
    
    def add_compound_words(self, compound_list: List[str]):
        """Add compound words to dictionary"""
        dictionary_data = self.load_dictionary_data()
        words_set = set(dictionary_data['words'])
        word_to_pos = dictionary_data['word_to_pos']
        compounds_set = set(dictionary_data.get('compounds', []))
        
        compounds_added = 0
        for compound in compound_list:
            if compound and compound not in words_set:
                words_set.add(compound)
                compounds_set.add(compound)
                
                # Add as noun by default
                word_to_pos[compound] = {'NN': 1}
                
                compounds_added += 1
                print(f"🔗 Added compound: {compound}")
        
        # Update dictionary data
        dictionary_data['words'] = list(words_set)
        dictionary_data['compounds'] = list(compounds_set)
        dictionary_data['word_to_pos'] = word_to_pos
        dictionary_data['stats']['compounds_generated'] = len(compounds_set)
        dictionary_data['last_updated'] = datetime.now().isoformat()
        
        # Save updated dictionary
        self.save_dictionary(dictionary_data)
        
        return {
            'compounds_added': compounds_added,
            'total_compounds': len(compounds_set)
        }
    
    def save_dictionary(self, dictionary_data: Dict):
        """Save dictionary to JSON"""
        with open(self.dictionary_json_path, 'w', encoding='utf-8') as f:
            json.dump(dictionary_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Dictionary updated: {self.dictionary_json_path}")
        print(f"📊 Total words: {len(dictionary_data['words']):,}")
        print(f"🔗 Total compounds: {len(dictionary_data.get('compounds', [])):,}")
    
    def generate_retraining_package(self) -> Dict:
        """Generate package for CRF retraining with new words"""
        dictionary_data = self.load_dictionary_data()
        
        # Collect new words learned from feedback
        training_samples = []
        
        for word, pos_data in dictionary_data['word_to_pos'].items():
            if pos_data:
                # Get most common POS
                best_pos = max(pos_data.items(), key=lambda x: x[1])
                pos_tag, frequency = best_pos
                
                # Generate character features for CRF
                chars = list(word)
                char_features = []
                
                for i, char in enumerate(chars):
                    feature = {
                        'char': char,
                        'position': i,
                        'is_consonant': char in 'กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ',
                        'is_vowel': char in 'ัาำิีึืุูเแโใไฤๅฯๆ',
                        'is_tone': char in '่้๊๋',
                        'prev_char': chars[i-1] if i > 0 else '<START>',
                        'next_char': chars[i+1] if i < len(chars)-1 else '<END>'
                    }
                    char_features.append(feature)
                
                training_samples.append({
                    'word': word,
                    'pos_tag': pos_tag,
                    'frequency': frequency,
                    'features': char_features
                })
        
        # Save retraining package
        retraining_path = self.dictionary_json_path.replace('.json', '_retraining.json')
        retraining_data = {
            'training_samples': training_samples,
            'metadata': {
                'total_samples': len(training_samples),
                'created_from_dictionary': self.dictionary_json_path,
                'created_at': datetime.now().isoformat(),
                'purpose': 'CRF_retraining_with_new_words'
            }
        }
        
        with open(retraining_path, 'w', encoding='utf-8') as f:
            json.dump(retraining_data, f, ensure_ascii=False, indent=2)
        
        print(f"🎯 Retraining package created: {retraining_path}")
        print(f"📚 Generated {len(training_samples)} training samples")
        
        return retraining_data