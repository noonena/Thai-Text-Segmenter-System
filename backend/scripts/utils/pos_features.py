"""
POS Tagging Feature Extraction
Extracts features from words for CRF-based POS tagging
"""

def word2features(words, i):
    """
    Extract features for word at position i
    
    Features based on Table 4.6 from methodology:
    - Word itself
    - Word shape (has digits, symbols, etc.)
    - Prefix patterns (การ, ความ, etc.)
    - Context (previous/next words)
    """
    word = words[i]
    
    features = {
        # 1. Current word
        'word.lower()': word.lower(),
        'word[-3:]': word[-3:],  # Last 3 chars
        'word[-2:]': word[-2:],  # Last 2 chars
        'word[:2]': word[:2],    # First 2 chars
        
        # 2. Word shape features
        'word.isdigit()': word.isdigit(),
        'word.has_digit': any(c.isdigit() for c in word),
        'word.has_thai': any('\u0e00' <= c <= '\u0e7f' for c in word),
        
        # 3. Prefix patterns (CP = Common Prefix)
        'word.startswith(การ)': word.startswith('การ'),
        'word.startswith(ความ)': word.startswith('ความ'),
        'word.startswith(ผู้)': word.startswith('ผู้'),
        'word.startswith(นัก)': word.startswith('นัก'),
        'word.startswith(แม่)': word.startswith('แม่'),
        
        # 4. Word length
        'word.length': len(word),
        'word.is_short': len(word) <= 2,
        'word.is_long': len(word) >= 5,
    }
    
    # 5. Context features - Previous word (Unigram)
    if i > 0:
        word_prev = words[i-1]
        features.update({
            '-1:word.lower()': word_prev.lower(),
            '-1:word[-2:]': word_prev[-2:],
        })
    else:
        features['BOS'] = True  # Beginning of sentence
    
    # 6. Context features - Next word (Unigram)
    if i < len(words) - 1:
        word_next = words[i+1]
        features.update({
            '+1:word.lower()': word_next.lower(),
            '+1:word[:2]': word_next[:2],
        })
    else:
        features['EOS'] = True  # End of sentence
    
    # 7. Bigram features (word pairs)
    if i > 0:
        features['-1:word+word'] = f"{words[i-1]}+{word}"
    
    if i < len(words) - 1:
        features['word+1:word'] = f"{word}+{words[i+1]}"
    
    return features


def extract_features(words):
    """Extract features for all words in sentence"""
    return [word2features(words, i) for i in range(len(words))]


def extract_labels(pos_tags):
    """Extract labels (POS tags)"""
    return pos_tags