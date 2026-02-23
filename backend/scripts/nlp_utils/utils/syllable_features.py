"""
Syllable Feature Extraction
Extract features from MTUs for syllable boundary detection
Based on Table 3.9
"""

def extract_mtu_features(mtus, i):
    """
    Extract features for MTU at position i
    
    Args:
        mtus: List of MTU strings
        i: Position of MTU to analyze
    
    Returns:
        Dictionary of features
    """
    mtu = mtus[i]
    
    features = {
        # Character-level features for this MTU
        'RV1': has_rear_vowel_no_consonant(mtu),
        'RV2': has_rear_vowel_with_consonant(mtu),
        'M': has_maitaikoo(mtu),      # ็
        'G': has_garund(mtu),          # ์
        'P': has_paiyarn(mtu),         # ฯ
        'CV': has_combined_vowel(mtu),
        'T': has_tone(mtu),            # ่ ้ ๊ ๋
        'S': is_space(mtu),
        'FC': mtu[0] if mtu else '',   # First character
        'LC': mtu[-1] if mtu else '',  # Last character
        'D': len(mtu),                 # Number of characters
    }
    
    # Context features (Unigram: -4 to +4)
    for offset in range(-4, 5):
        if offset == 0:
            continue
        idx = i + offset
        if 0 <= idx < len(mtus):
            features[f'MTU[{offset}]'] = mtus[idx]
        else:
            features[f'MTU[{offset}]'] = 'BOS' if offset < 0 else 'EOS'
    
    # Bigram features
    if i > 0:
        features['MTU[-1,0]'] = f"{mtus[i-1]}_{mtu}"
    if i < len(mtus) - 1:
        features['MTU[0,1]'] = f"{mtu}_{mtus[i+1]}"
    
    return features


def has_rear_vowel_no_consonant(mtu):
    """Check if has rear vowel without trailing consonant (RV1)"""
    rear_vowels = set('าๅะ')
    if not mtu:
        return 'N'
    # Check if ends with rear vowel
    return 'Y' if mtu[-1] in rear_vowels else 'N'


def has_rear_vowel_with_consonant(mtu):
    """Check if has rear vowel that can have consonant after (RV2)"""
    rear_vowels_with_cons = set('วำ')
    return 'Y' if any(v in mtu for v in rear_vowels_with_cons) else 'N'


def has_maitaikoo(mtu):
    """Check for Maitaikoo (็)"""
    return 'Y' if '็' in mtu else 'N'


def has_garund(mtu):
    """Check for Garund (์)"""
    return 'Y' if '์' in mtu else 'N'


def has_paiyarn(mtu):
    """Check for Paiyarn (ฯ)"""
    return 'Y' if 'ฯ' in mtu else 'N'


def has_combined_vowel(mtu):
    """Check if can combine with other vowels"""
    # Upper vowels can combine: ิ ี ึ ื
    combining_vowels = set('ิีึื')
    return 'Y' if any(v in mtu for v in combining_vowels) else 'N'


def has_tone(mtu):
    """Check for tone marks (่ ้ ๊ ๋)"""
    tones = set('่้๊๋')
    return 'Y' if any(t in mtu for t in tones) else 'N'


def is_space(mtu):
    """Check if is whitespace"""
    return 'Y' if mtu.strip() == '' else 'N'


def extract_features_for_sentence(mtus):
    """Extract features for all MTUs in sentence"""
    return [extract_mtu_features(mtus, i) for i in range(len(mtus))]