from .char_utils import get_char_type
import pickle
import sys
from typing import List, Dict

def char2features(chars: List[str], i: int) -> Dict[str, any]:
    char = chars[i]
    features = {
        'bias': 1.0,
        'char': char,
        'char_type': get_char_type(char),
    }
    
    # Unigram features C[-3:3]
    for offset in [-3, -2, -1, 0, 1, 2, 3]:
        pos = i + offset
        if 0 <= pos < len(chars):
            features[f'char[{offset:+d}]'] = chars[pos]
            features[f'type[{offset:+d}]'] = get_char_type(chars[pos])
        else:
            features[f'char[{offset:+d}]'] = 'BOS' if pos < 0 else 'EOS'
            features[f'type[{offset:+d}]'] = 'BOUNDARY'
    
    # Bigram feature C[-1,1]
    if i > 0:
        features['char[-1,0]'] = chars[i-1] + char
        features['type[-1,0]'] = get_char_type(chars[i-1]) + get_char_type(char)
    
    if i < len(chars) - 1:
        features['char[0,+1]'] = char + chars[i+1]
        features['type[0,+1]'] = get_char_type(char) + get_char_type(chars[i+1])
    
    return features

def load_model(model_path: str):
    """Load trained CRF model"""
    with open(model_path, 'rb') as f:
        crf = pickle.load(f)
    return crf

def segment_text_to_mtus(text: str, crf):
    chars = list(text)
    features = [char2features(chars, i) for i in range(len(chars))]
    labels = crf.predict([features])[0]

    mtus = []
    current_mtu = []
    current_labels = []
    mtu_labels = []  # store BMES per MTU

    for char, label in zip(chars, labels):
        if label == 'S':
            mtus.append([char])
            mtu_labels.append(['S'])
        elif label == 'B':
            current_mtu = [char]
            current_labels = ['B']
        elif label in ['M', 'E']:
            current_mtu.append(char)
            current_labels.append(label)
            if label == 'E':
                mtus.append(current_mtu)
                mtu_labels.append(current_labels)
                current_mtu = []
                current_labels = []

    if current_mtu:
        mtus.append(current_mtu)
        mtu_labels.append(current_labels)

    return mtus, labels, mtu_labels

def format_mtus(mtus: List[List[str]]) -> str:
    """Format MTUs for display"""
    return ' | '.join([''.join(mtu) for mtu in mtus])

