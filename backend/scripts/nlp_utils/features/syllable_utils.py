"""
Syllable utilities and feature extraction for the syllable CRF.

Contains:
- orthographic_syllabify : rule-based syllabifier (used as a feature signal)
- extract_features_for_sentence : CRF feature extraction for syllable boundaries
"""

from typing import List

try:
    from .char_utils import (
        FRONT_VOWELS, CONSONANTS, UPPER_VOWELS, TONES,
        get_compound_vowel_length, get_char_type, AKSON_NAM_CLUSTERS,
    )
except ImportError:
    from char_utils import (
        FRONT_VOWELS, CONSONANTS, UPPER_VOWELS, TONES,
        get_compound_vowel_length, get_char_type, AKSON_NAM_CLUSTERS,
    )


CC_ONSET_CLUSTERS = {
    'กร', 'กล', 'กว', 'ขร', 'ขล', 'ขว', 'คร', 'คล', 'คว',
    'ตร', 'ปร', 'ปล', 'ผล', 'ผว', 'พร', 'พล', 'พว',
    'ฝร', 'ภร', 'ภล', 'ภว', 'ทร',
    'สร', 'สล', 'สว', 'ศร',
}


def _is_coda(chars: list, i: int, n: int) -> bool:
    """True if chars[i] is a coda consonant (not the onset of the next syllable)."""
    if i >= n or get_char_type(chars[i]) != 'C':
        return False
    if i + 1 < n and get_char_type(chars[i + 1]) in ('U', 'L', 'S', 'B', 'T'):
        return False
    return True


def orthographic_syllabify(text: str) -> List[str]:
    """
    Split Thai text into orthographic syllable units based solely on visible
    written patterns — no implicit (underlying) vowel inference is performed.

    This is NOT full phonological syllabification.  Words whose first
    consonant carries an implicit short vowel (e.g. สบาย → สะ+บาย,
    สนุก → สะ+นุก, ตลาด → ตะ+ลาด) will still be split into two written
    units because there is no visible vowel diacritic on the first consonant.
    That split is intentional and acceptable: the goal is subword chunks
    derived from the spelling, usable as CRF features or rough segmentation.

    What IS handled (explicit written patterns only):
      CC onset clusters   → one unit  (ประ, กลาง, ขวัญ, เกลียว, เกวียน)
      อักษรนำ ห-pairs     → one unit  (หลับ, หนาว, หมู)
      Front-vowel frames  → one unit  (เกาะ, แกลง, โกรก, ไกล)
      รร vowel            → one unit  (กรรม, สรร)
      C + อ + C           → one unit  (นอน, กอง, ขอบ)
      Compound vowels     → one unit  (เกลียว, เกวียน, กลัว)
      Coda reattachment   → one unit  (ข้าว, เขียว)
    """
    chars = list(text)
    n = len(chars)
    syllables: List[str] = []
    i = 0

    def ct(idx: int) -> str:
        return get_char_type(chars[idx]) if 0 <= idx < n else ''

    def consume_rear_vowel(pos: int) -> int:
        if pos < n and ct(pos) == 'B':
            pos += 1
            if pos < n and chars[pos] == 'ะ':
                pos += 1
        return pos

    def consume_coda(pos: int) -> int:
        if _is_coda(chars, pos, n):
            pos += 1
            if pos < n and ct(pos) == 'K':
                pos += 1
            while pos + 1 < n and ct(pos) == 'C' and ct(pos + 1) == 'K':
                pos += 2
        return pos

    def consume_onset(pos: int) -> int:
        if pos >= n or ct(pos) != 'C':
            return pos
        c0 = chars[pos]
        if c0 == 'ห' and pos + 1 < n and c0 + chars[pos + 1] in AKSON_NAM_CLUSTERS:
            return pos + 2
        if (pos + 1 < n and ct(pos + 1) == 'C'
                and c0 + chars[pos + 1] in CC_ONSET_CLUSTERS
                and not (chars[pos + 1] == 'ร' and pos + 2 < n and chars[pos + 2] == 'ร')):
            return pos + 2
        return pos + 1

    while i < n:
        t = ct(i)

        if t in ('G', 'D', 'Q', 'O'):
            syllables.append(chars[i])
            i += 1
            continue

        syl_start = i

        if t == 'F':
            i += 1
            i = consume_onset(i)
            while i < n and ct(i) in ('U', 'L', 'S', 'T'):
                i += 1
            if i < n and chars[i] in ('ย', 'อ', 'ว'):
                if i + 1 >= n or ct(i + 1) not in ('U', 'L', 'S', 'B'):
                    i += 1
            i = consume_rear_vowel(i)
            i = consume_coda(i)

        elif t == 'C':
            i = consume_onset(i)
            while i < n and ct(i) in ('U', 'L', 'S', 'T'):
                i += 1
            if i < n and chars[i] == 'ร' and i + 1 < n and chars[i + 1] == 'ร':
                i += 2
                i = consume_coda(i)
            elif i < n and chars[i] == 'อ' and i + 1 < n and ct(i + 1) == 'C':
                i += 1
                i = consume_coda(i)
            elif i < n and ct(i) == 'B':
                i = consume_rear_vowel(i)
                if i < n and chars[i] == 'ว' and (
                        i + 1 >= n or ct(i + 1) not in ('U', 'L', 'S', 'T', 'B', 'F', 'C')):
                    i += 1
                else:
                    i = consume_coda(i)
            elif i < n and chars[i] in ('ว', 'ย'):
                if i + 1 >= n or ct(i + 1) not in ('U', 'L', 'S', 'T', 'B', 'F', 'C'):
                    i += 1
            else:
                _m = 0
                _k = i
                while _k < n and ct(_k) == 'C':
                    if _k + 1 < n and ct(_k + 1) in ('U', 'L', 'S', 'B', 'T'):
                        break
                    _m += 1
                    _k += 1
                if _m % 2 == 1:
                    i = consume_coda(i)

        else:
            i += 1

        syl = ''.join(chars[syl_start:i])
        if syl:
            syllables.append(syl)

    return syllables

# Rear vowels that end a syllable without a following consonant (RV1)
_REAR_VOWELS_OPEN = set('าๅะ')
# Rear vowels that can be followed by a consonant coda (RV2)
_REAR_VOWELS_CODA = set('วำ')


def get_nfa_boundaries(mtus: list) -> list:
    """
    Run orthographic_syllabify on joined MTUs and return a bool list:
    nfa[i] = True if the NFA places a syllable boundary AFTER mtus[i].
    """
    text = "".join(mtus)
    syllables = orthographic_syllabify(text)

    syl_ends = set()
    pos = 0
    for syl in syllables:
        pos += len(syl)
        syl_ends.add(pos)

    boundaries = []
    char_pos = 0
    for mtu in mtus:
        char_pos += len(mtu)
        boundaries.append(char_pos in syl_ends)
    return boundaries


def has_rear_vowel_no_consonant(mtu):
    """Check if MTU ends with an open rear vowel (RV1: า ๅ ะ)."""
    if not mtu:
        return 'N'
    return 'Y' if mtu[-1] in _REAR_VOWELS_OPEN else 'N'


def has_rear_vowel_with_consonant(mtu):
    """Check if MTU contains a rear vowel that can precede a coda (RV2: ว ำ)."""
    return 'Y' if any(v in mtu for v in _REAR_VOWELS_CODA) else 'N'


def has_maitaikoo(mtu):
    """Check for Maitaikoo (็)."""
    return 'Y' if '็' in mtu else 'N'


def has_garund(mtu):
    """Check for Karan (์)."""
    return 'Y' if '์' in mtu else 'N'


def has_paiyarn(mtu):
    """Check for Paiyarn (ฯ)."""
    return 'Y' if 'ฯ' in mtu else 'N'


def has_combined_vowel(mtu):
    """Check if MTU contains an upper vowel that can combine (ิ ี ึ ื)."""
    return 'Y' if any(v in mtu for v in UPPER_VOWELS) else 'N'


def has_tone(mtu):
    """Check for tone marks (่ ้ ๊ ๋)."""
    return 'Y' if any(t in mtu for t in TONES) else 'N'


def is_space(mtu):
    """Check if MTU is whitespace."""
    return 'Y' if mtu.strip() == '' else 'N'


def is_consonant(mtu):
    """Check if MTU contains at least one consonant."""
    return any(c in CONSONANTS for c in mtu)


def extract_mtu_features(mtus, i, nfa_boundaries=None):
    """
    Extract features for MTU at position i.
    nfa_boundaries: precomputed list from get_nfa_boundaries(mtus).
    """
    mtu = mtus[i]

    features = {
        'RV1': has_rear_vowel_no_consonant(mtu),
        'RV2': has_rear_vowel_with_consonant(mtu),
        'M':   has_maitaikoo(mtu),
        'G':   has_garund(mtu),
        'P':   has_paiyarn(mtu),
        'CV':  has_combined_vowel(mtu),
        'T':   has_tone(mtu),
        'S':   is_space(mtu),
        'FC':  mtu[0] if mtu else '',
        'LC':  mtu[-1] if mtu else '',
        'D':   len(mtu),
    }

    if mtu:
        compound_len = get_compound_vowel_length(list(mtu), 0)
        if compound_len > 0:
            features['compound_vowel'] = 'Y'
            features['compound_len'] = compound_len

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

    # RULE: rear vowel followed by consonant → syllable boundary
    if i < len(mtus) - 1:
        has_rv1 = has_rear_vowel_no_consonant(mtu) == 'Y'
        next_is_cons = is_consonant(mtus[i + 1])
        features['RV1_CONS'] = 'Y' if (has_rv1 and next_is_cons) else 'N'

        # RULE: rear vowel followed by front vowel → combine
        next_starts_front = mtus[i + 1][0] in FRONT_VOWELS if mtus[i + 1] else False
        features['RV1_FV'] = 'Y' if (has_rv1 and next_starts_front) else 'N'

    # RULE: consonant cluster followed by vowel → combine (no boundary)
    if i < len(mtus) - 1:
        curr_is_cons = is_consonant(mtu)
        next_has_vowel = (
            has_rear_vowel_no_consonant(mtus[i + 1]) == 'Y' or
            has_combined_vowel(mtus[i + 1]) == 'Y'
        )
        features['CONS_V'] = 'Y' if (curr_is_cons and next_has_vowel) else 'N'

    # NFA feature: orthographic_syllabify boundary decision
    if nfa_boundaries is not None:
        features['NFA_BOUNDARY'] = 'Y' if nfa_boundaries[i] else 'N'
        if i > 0:
            features['NFA_BOUNDARY[-1]'] = 'Y' if nfa_boundaries[i - 1] else 'N'
        if i < len(mtus) - 1:
            features['NFA_BOUNDARY[+1]'] = 'Y' if nfa_boundaries[i + 1] else 'N'

    return features


def extract_features_for_sentence(mtus):
    """Extract features for all MTUs in a sentence."""
    nfa_boundaries = get_nfa_boundaries(mtus)
    return [extract_mtu_features(mtus, i, nfa_boundaries) for i in range(len(mtus))]
