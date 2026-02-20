try:
    from .char_utils import get_char_type
except ImportError:
    from char_utils import get_char_type
import pickle
import sys
from typing import List, Dict

# =====================================================
# TCC (Thai Character Cluster) rules
# These are deterministic — no model needed.
# =====================================================

# อักษรนำ (leading consonant) pairs where ห is silent — always one cluster.
# Regular onset clusters (กร, กล, สว...) are NOT included: each consonant
# starts its own TCC unless it has dependent vowel characters of its own.
_CONSONANT_CLUSTERS = {
    'หง', 'หน', 'หม', 'หย', 'หร', 'หล', 'หว', 'หณ', 'หญ',
}


def apply_tcc_rules(text: str) -> List[str]:
    """
    Apply Thai Character Cluster (TCC) rules to segment text into MTUs.
    Deterministic — no model needed. Replaces the MTU CRF.

    Rules:
      - Digits:        consecutive digits → one cluster
      - ฯลฯ:          always one cluster
      - Special/other: standalone
      - Front vowel:   F + C (+ optional onset cluster) + vowel modifiers
      - Consonant:     C (+ optional onset cluster) + vowel modifiers
      - Everything else: standalone
    """
    chars = list(text)
    n = len(chars)
    clusters = []
    i = 0

    while i < n:
        ch = chars[i]
        ct = get_char_type(ch)

        # Digits: keep consecutive digits together
        if ct == 'D':
            j = i + 1
            while j < n and get_char_type(chars[j]) == 'D':
                j += 1
            clusters.append(''.join(chars[i:j]))
            i = j
            continue

        # ฯลฯ: stays as one unit
        if ch == 'ฯ' and i + 2 < n and chars[i+1] == 'ล' and chars[i+2] == 'ฯ':
            clusters.append('ฯลฯ')
            i += 3
            continue

        # Special symbols (ๆ ฯ ํ), spaces, non-Thai: standalone
        if ct in {'O', 'G', 'Q'}:
            clusters.append(ch)
            i += 1
            continue

        # ฤ / ฦ: optionally followed by ๅ
        if ch in {'ฤ', 'ฦ'}:
            if i + 1 < n and chars[i+1] == 'ๅ':
                clusters.append(ch + 'ๅ')
                i += 2
            else:
                clusters.append(ch)
                i += 1
            continue

        # ── Front vowel pattern: F + C (+ cluster C) + modifiers ──────────
        if ct == 'F':
            j = i + 1
            if j < n and get_char_type(chars[j]) in {'C', 'N'}:
                j += 1
                # Consonant cluster after front vowel (e.g. เกร-, เปล-)
                if j < n and get_char_type(chars[j]) in {'C', 'N'}:
                    if chars[j-1] + chars[j] in _CONSONANT_CLUSTERS:
                        j += 1
                # Attach vowel modifiers
                if j < n:
                    jt = get_char_type(chars[j])
                    if jt == 'S':
                        # special vowel (ั ็): optional tone + required final C
                        j += 1
                        if j < n and get_char_type(chars[j]) == 'T':
                            j += 1
                        if j < n and get_char_type(chars[j]) in {'C', 'N'}:
                            j += 1
                    elif jt == 'U':
                        # upper vowel: optional tone; ื/ึ may take final C
                        vowel_ch = chars[j]
                        j += 1
                        if j < n and get_char_type(chars[j]) == 'T':
                            j += 1
                        if vowel_ch in {'ื', 'ึ'} and j < n and get_char_type(chars[j]) in {'C', 'N'}:
                            j += 1
                    elif jt == 'L':
                        # lower vowel: optional tone
                        j += 1
                        if j < n and get_char_type(chars[j]) == 'T':
                            j += 1
                    elif jt == 'B':
                        # rear vowel; าะ combination
                        j += 1
                        if j < n and chars[j-1] == 'า' and chars[j] == 'ะ':
                            j += 1
                    elif jt == 'T':
                        j += 1
                    elif jt == 'K':
                        j += 1
                clusters.append(''.join(chars[i:j]))
                i = j
            else:
                # Front vowel with no following consonant: standalone
                clusters.append(ch)
                i += 1
            continue

        # ── Consonant-initial pattern ──────────────────────────────────────
        if ct in {'C', 'N'}:
            j = i + 1

            # รร pattern (C + รร + optional karan)
            if j + 1 < n and chars[j] == 'ร' and chars[j+1] == 'ร':
                j += 2
                if j < n and get_char_type(chars[j]) == 'K':
                    j += 1
                clusters.append(''.join(chars[i:j]))
                i = j
                continue

            # Consonant cluster at onset
            if j < n and get_char_type(chars[j]) in {'C', 'N'}:
                if ch + chars[j] in _CONSONANT_CLUSTERS:
                    j += 1

            # Attach vowel modifiers
            if j < n:
                jt = get_char_type(chars[j])
                if jt == 'S':
                    # special vowel (ั ็): optional tone + required final C
                    j += 1
                    if j < n and get_char_type(chars[j]) == 'T':
                        j += 1
                    if j < n and get_char_type(chars[j]) in {'C', 'N'}:
                        j += 1
                elif jt == 'U':
                    # upper vowel: optional tone; ื/ึ may take final C
                    vowel_ch = chars[j]
                    j += 1
                    if j < n and get_char_type(chars[j]) == 'T':
                        j += 1
                    if vowel_ch in {'ื', 'ึ'} and j < n and get_char_type(chars[j]) in {'C', 'N'}:
                        j += 1
                elif jt == 'L':
                    # lower vowel: optional tone
                    j += 1
                    if j < n and get_char_type(chars[j]) == 'T':
                        j += 1
                elif jt == 'B':
                    # rear vowel; าะ combination
                    j += 1
                    if j < n and chars[j-1] == 'า' and chars[j] == 'ะ':
                        j += 1
                elif jt == 'T':
                    # tone mark: optional trailing rear vowel
                    j += 1
                    if j < n and get_char_type(chars[j]) == 'B':
                        j += 1
                elif jt == 'K':
                    j += 1

            clusters.append(''.join(chars[i:j]))
            i = j
            continue

        # Anything else: standalone
        clusters.append(ch)
        i += 1

    return clusters


def segment_text_to_mtus_rules(text: str):
    """
    Rule-based drop-in replacement for segment_text_to_mtus(text, crf).
    Returns (mtus, labels, mtu_labels) in the same format — no model needed.
    """
    cluster_strings = apply_tcc_rules(text)

    # mtus: list of character lists (same format as CRF version)
    mtus = [list(c) for c in cluster_strings]

    # Flat character-level BMES labels
    labels = []
    for c in cluster_strings:
        ln = len(c)
        if ln == 1:
            labels.append('S')
        else:
            labels.append('B')
            labels.extend(['M'] * (ln - 2))
            labels.append('E')

    # Per-MTU BMES label lists
    mtu_labels = []
    for c in cluster_strings:
        ln = len(c)
        if ln == 1:
            mtu_labels.append(['S'])
        else:
            mtu_labels.append(['B'] + ['M'] * (ln - 2) + ['E'])

    return mtus, labels, mtu_labels

def char2features(chars: List[str], i: int) -> Dict[str, any]:
    char = chars[i]
    char_type = get_char_type(char)
    
    features = {
        'bias': 1.0,
        'char': char,
        'char_type': char_type,
    }
    
    # Unigram features C[-2:2] - reduced context for better learning
    for offset in [-2, -1, 0, 1, 2]:
        pos = i + offset
        if 0 <= pos < len(chars):
            c = chars[pos]
            ct = get_char_type(c)
            features[f'char[{offset:+d}]'] = c
            features[f'type[{offset:+d}]'] = ct
            
            # Add position-specific features
            if offset == 0:
                features['is_consonant'] = ct in {'C', 'N'}
                features['is_vowel'] = ct in {'F', 'U', 'L', 'B', 'S'}
                features['is_tone'] = ct == 'T'
                features['is_digit'] = ct == 'D'
        else:
            features[f'char[{offset:+d}]'] = 'BOS' if pos < 0 else 'EOS'
            features[f'type[{offset:+d}]'] = 'BOUNDARY'
    
    # Bigram features
    if i > 0:
        prev_char = chars[i-1]
        prev_type = get_char_type(prev_char)
        features['char[-1,0]'] = prev_char + char
        features['type[-1,0]'] = prev_type + char_type
        
        # Important patterns
        features['prev_is_consonant'] = prev_type in {'C', 'N'}
        features['prev_is_vowel'] = prev_type in {'F', 'U', 'L', 'B', 'S'}
    
    if i < len(chars) - 1:
        next_char = chars[i+1]
        next_type = get_char_type(next_char)
        features['char[0,+1]'] = char + next_char
        features['type[0,+1]'] = char_type + next_type
        
        # Important patterns
        features['next_is_consonant'] = next_type in {'C', 'N'}
        features['next_is_vowel'] = next_type in {'F', 'U', 'L', 'B', 'S'}
    
    # Special pattern features for Thai
    if i > 0 and i < len(chars) - 1:
        # Check for common patterns
        three_chars = chars[i-1] + char + chars[i+1]
        if 'รร' in three_chars:
            features['has_rr'] = True
        if char in {'ๆ', 'ฯ'}:
            features['is_special_symbol'] = True
        if char_type == 'S' and i > 0 and get_char_type(chars[i-1]) in {'C', 'N'}:
            features['special_vowel_after_consonant'] = True
    
    # Word boundary indicators
    if i == 0:
        features['is_word_start'] = True
    if i == len(chars) - 1:
        features['is_word_end'] = True
    
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

