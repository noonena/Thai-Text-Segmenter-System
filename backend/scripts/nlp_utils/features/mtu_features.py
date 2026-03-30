try:
    from .char_utils import get_char_type, get_compound_vowel_length, AKSON_NAM_CLUSTERS
except ImportError:
    from char_utils import get_char_type, get_compound_vowel_length, AKSON_NAM_CLUSTERS
import pickle
from typing import List, Dict

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
                
                # NEW: Compound vowel feature - helps CRF recognize compound vowels
                compound_len = get_compound_vowel_length(chars, i)
                if compound_len > 0:
                    features['compound_vowel'] = True
                    features['compound_vowel_len'] = compound_len
                    features['char_type'] = 'CV'  # Override type for compound vowels
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


def label_chars(word: str) -> List[str]:
    """
    Improved MTU label generator that reduces over-segmentation
    Creates fewer, larger MTUs to improve recall
    """
    chars = list(word)
    n = len(chars)
    
    if n == 0:
        return []
    
    if n == 1:
        return ["S"]
    
    # Track MTU boundaries - True means "start of new MTU"
    boundaries = [True] + [False] * (n - 1)
    i = 0
    while i < n:
        ch = chars[i]
        ct = get_char_type(ch)

        # NEW: Rule for consecutive digits - keep them together
        if ct == "D":
            # Find end of digit sequence
            j = i + 1
            while j < n and get_char_type(chars[j]) == "D":
                j += 1
            
            # Mark boundary after last digit
            if j < n:
                boundaries[j] = True
            i = j
            continue
        
        # Rule 11: "ๆ" is always singleton
        if ch == "ๆ":
            if i + 1 < n:
                boundaries[i + 1] = True
            i += 1
            continue
        
        # Rule 12: "ฯ" patterns
        if ch == "ฯ":
            # Check for ฯลฯ
            if i + 2 < n and chars[i:i+3] == ["ฯ", "ล", "ฯ"]:
                if i + 3 < n:
                    boundaries[i + 3] = True
                i += 3
                continue
            # Check for ฯพณพฯ
            elif i + 4 < n and chars[i:i+5] == ["ฯ", "พ", "ณ", "พ", "ฯ"]:
                if i + 5 < n:
                    boundaries[i + 5] = True
                i += 5
                continue
            else:
                if i + 1 < n:
                    boundaries[i + 1] = True
                i += 1
                continue
        
        # Rule 10: "ฤ" and "ฦ"
        if ch in {"ฤ", "ฦ"}:
            if i + 1 < n and chars[i + 1] == "ๅ":
                if i + 2 < n:
                    boundaries[i + 2] = True
                i += 2
            else:
                if i + 1 < n:
                    boundaries[i + 1] = True
                i += 1
            continue
        
        # Rule 16: Common function words stay together
        if i + 1 < n:
            pair = ch + chars[i + 1]
            if pair in {"ก็", "บ่"}:
                if i + 2 < n:
                    boundaries[i + 2] = True
                i += 2
                continue
        
        # Rule 1: Front vowel grabs following consonant(s)
        if ct == "F":
            if i + 1 < n and get_char_type(chars[i + 1]) in {"C", "N"}:
                j = i + 2
                while j < n:
                    jt = get_char_type(chars[j])

                    # Special vowel needs consonant after (Rule 3)
                    if jt == "S":
                        if j + 1 < n and get_char_type(chars[j + 1]) == "T":
                            j += 1
                        if j + 1 < n and get_char_type(chars[j + 1]) in {"C", "N"}:
                            j += 1
                        j += 1
                        break

                    elif jt in {"U", "L"}:
                        vowel_char = chars[j]
                        j += 1
                        if j < n and get_char_type(chars[j]) == "T":
                            j += 1
                        # Compound vowel: ีย (เ-ีย) or ือ (เ-ือ)
                        if j < n and ((vowel_char == 'ี' and chars[j] == 'ย') or
                                      (vowel_char == 'ื' and chars[j] == 'อ')):
                            j += 1
                            # Triphthong เ-ียว: ว after ีย is part of vowel, not coda
                            if vowel_char == 'ี' and j < n and chars[j] == 'ว':
                                j += 1
                                break
                        # Coda consonant
                        if j < n and get_char_type(chars[j]) in {"C", "N"}:
                            if j + 1 >= n or get_char_type(chars[j + 1]) not in {"U", "L", "S", "B"}:
                                j += 1
                        break

                    elif jt in {"T", "B"}:
                        j += 1

                    elif jt in {"C", "N"}:
                        # อักษรนำ: silent ห + real onset — consume and keep going
                        if chars[j - 1] + chars[j] in AKSON_NAM_CLUSTERS:
                            j += 1
                            continue
                        # If next char is tone/vowel, this consonant is onset of next syllable
                        if j + 1 < n and get_char_type(chars[j + 1]) in {"T", "U", "L", "S", "B", "F"}:
                            break
                        # Regular coda consonant
                        j += 1
                        # Silent consonant + karan after coda (e.g. ร์ in เสาร์)
                        if j + 1 < n and get_char_type(chars[j]) in {"C", "N"} and get_char_type(chars[j + 1]) == "K":
                            j += 2
                        elif j < n and get_char_type(chars[j]) == "K":
                            j += 1
                        break

                    else:
                        break

                if j < n:
                    boundaries[j] = True
                i = j
                continue
        
        # Rules 2-6: Consonant with dependent characters - MODIFIED
        if ct in {"C", "N"}:
            j = i + 1

            # Special handling for รร patterns
            if (
                i + 2 < n
                and chars[i + 1] == "ร"
                and chars[i + 2] == "ร"
            ):
                j = i + 3
                if j < n:
                    boundaries[j] = True
                i = j
                continue
            
            # Attach dependent characters more aggressively
            max_attach = 3  # Allow longer attachments
            attached = 0
            
            while j < n and attached < max_attach:
                jt = get_char_type(chars[j])
                
                # Rule 2: Upper/lower vowels attach + optional final consonant
                # Only consume final C if NOT followed by a vowel (i.e. it's a coda, not an onset)
                if jt in {"U", "L"}:
                    j += 1
                    attached += 1
                    if j < n and get_char_type(chars[j]) == "T":
                        j += 1
                    if j < n and get_char_type(chars[j]) in {"C", "N"}:
                        if j + 1 >= n or get_char_type(chars[j + 1]) not in {"U", "L", "S", "B"}:
                            j += 1
                    break

                # Rule 3: Special vowels need consonant after
                elif jt == "S":
                    j += 1
                    attached += 1
                    if j < n and get_char_type(chars[j]) == "T":
                        j += 1
                    if j < n and get_char_type(chars[j]) in {"C", "N"}:
                        j += 1
                        # Silent consonant + karan after coda (e.g. ย์ in ทรัพย์)
                        if j + 1 < n and get_char_type(chars[j]) in {"C", "N"} and get_char_type(chars[j + 1]) == "K":
                            j += 2
                        elif j < n and get_char_type(chars[j]) == "K":
                            j += 1
                    break
                
                # Rule 4: Rear vowels attach + optional final consonant (coda)
                elif jt == "B":
                    j += 1
                    attached += 1
                    if j < n and chars[j - 1] == "า" and chars[j] == "ะ":
                        j += 1
                    elif j < n and get_char_type(chars[j]) in {"C", "N"}:
                        if j + 1 >= n or get_char_type(chars[j + 1]) not in {"U", "L", "S", "B"}:
                            j += 1
                            # Silent consonant + karan after coda (e.g. ย์ in กาพย์)
                            if j + 1 < n and get_char_type(chars[j]) in {"C", "N"} and get_char_type(chars[j + 1]) == "K":
                                j += 2
                            elif j < n and get_char_type(chars[j]) == "K":
                                j += 1
                    break
                
                # Rule 6: Tones attach
                elif jt == "T":
                    j += 1
                    attached += 1
                    if j < n and get_char_type(chars[j]) == "B":
                        j += 1
                    break
                
                # Rule 13: Karan attaches
                elif jt == "K":
                    j += 1
                    attached += 1
                    break
                
                elif jt in {"C", "N"} and attached == 0:
                    break
                
                else:
                    break
            
            if j < n:
                boundaries[j] = True
            i = j
            continue
        
        # Default: move to next character
        if i + 1 < n:
            boundaries[i + 1] = True
        i += 1
    
    # Convert boundaries to B/M/E/S labels
    labels = []
    i = 0
    while i < n:
        # Find the end of current MTU
        j = i + 1
        while j < n and not boundaries[j]:
            j += 1
        
        # Assign labels for this MTU
        mtu_len = j - i
        if mtu_len == 1:
            labels.append("S")
        else:
            labels.append("B")
            for k in range(1, mtu_len - 1):
                labels.append("M")
            labels.append("E")
        
        i = j
    
    return labels


def word_to_mtu_debug(word: str, out=None) -> None:
    """
    Same logic as label_chars but prints every decision step.
    Shows char types and which rule fired BEFORE BMES is assigned.
    out: file object to also write to (optional)
    """
    def p(*args, **kwargs):
        print(*args, **kwargs)
        if out:
            print(*args, **{**kwargs, "file": out})

    chars = list(word)
    n = len(chars)
    p(f"\n  Word: '{word}'  ({n} chars)")

    # Show all chars and their types first
    p(f"  {'i':<4} {'char':<6} {'type':<5}")
    p(f"  {'-'*4} {'-'*6} {'-'*5}")
    for idx, ch in enumerate(chars):
        p(f"  {idx:<4} {ch:<6} {get_char_type(ch):<5}")

    if n == 0:
        p("  (empty)")
        return
    if n == 1:
        p("  → single char → label: S")
        return

    boundaries = [True] + [False] * (n - 1)
    rule_log   = {}   # i → rule name that fired

    i = 0
    while i < n:
        ch = chars[i]
        ct = get_char_type(ch)

        if ct == "D":
            j = i + 1
            while j < n and get_char_type(chars[j]) == "D":
                j += 1
            if j < n:
                boundaries[j] = True
            rule_log[i] = f"DIGIT  chars[{i}:{j}]={''.join(chars[i:j])}"
            i = j
            continue

        if ch == "ๆ":
            if i + 1 < n:
                boundaries[i + 1] = True
            rule_log[i] = "Rule 11 ๆ singleton"
            i += 1
            continue

        if ch == "ฯ":
            if i + 2 < n and chars[i:i+3] == ["ฯ", "ล", "ฯ"]:
                if i + 3 < n:
                    boundaries[i + 3] = True
                rule_log[i] = "Rule 12 ฯลฯ"
                i += 3
            elif i + 4 < n and chars[i:i+5] == ["ฯ", "พ", "ณ", "พ", "ฯ"]:
                if i + 5 < n:
                    boundaries[i + 5] = True
                rule_log[i] = "Rule 12 ฯพณพฯ"
                i += 5
            else:
                if i + 1 < n:
                    boundaries[i + 1] = True
                rule_log[i] = "Rule 12 ฯ singleton"
                i += 1
            continue

        if ch in {"ฤ", "ฦ"}:
            if i + 1 < n and chars[i + 1] == "ๅ":
                if i + 2 < n:
                    boundaries[i + 2] = True
                rule_log[i] = "Rule 10 ฤ/ฦๅ"
                i += 2
            else:
                if i + 1 < n:
                    boundaries[i + 1] = True
                rule_log[i] = "Rule 10 ฤ/ฦ alone"
                i += 1
            continue

        if i + 1 < n:
            pair = ch + chars[i + 1]
            if pair in {"ก็", "บ่"}:
                if i + 2 < n:
                    boundaries[i + 2] = True
                rule_log[i] = f"Rule 16 function-word '{pair}'"
                i += 2
                continue

        if ct in {"C", "N"} and i + 2 < n:
            three_str = ''.join(chars[i:i+3])

        if ct == "F":
            if i + 1 < n and get_char_type(chars[i + 1]) in {"C", "N"}:
                j = i + 2
                while j < n:
                    jt = get_char_type(chars[j])
                    if jt == "S":
                        if j + 1 < n and get_char_type(chars[j + 1]) == "T":
                            j += 1
                        if j + 1 < n and get_char_type(chars[j + 1]) in {"C", "N"}:
                            j += 1
                        j += 1
                        break
                    elif jt in {"U", "L", "T", "B"}:
                        j += 1
                        if jt in {"U", "L"} and j < n and get_char_type(chars[j]) == "T":
                            j += 1
                    else:
                        # Consume at most one final consonant, then stop
                        if jt in {"C", "N"}:
                            # If next char is tone/vowel, this consonant is onset of next syllable
                            if j + 1 < n and get_char_type(chars[j + 1]) in {"T", "U", "L", "S", "B", "F"}:
                                break
                            j += 1
                        break
                if j < n:
                    boundaries[j] = True
                rule_log[i] = f"Rule 1 front-vowel  chars[{i}:{j}]={''.join(chars[i:j])}"
                i = j
                continue

        if ct in {"C", "N"}:
            j = i + 1
            if i + 2 < n and chars[i + 1] == "ร" and chars[i + 2] == "ร":
                j = i + 3
                if j < n:
                    boundaries[j] = True
                rule_log[i] = f"รร-pattern chars[{i}:{j}]={''.join(chars[i:j])}"
                i = j
                continue

            max_attach = 3
            attached = 0
            sub_rule = "?"
            while j < n and attached < max_attach:
                jt = get_char_type(chars[j])
                if jt in {"U", "L"}:
                    j += 1
                    attached += 1
                    if j < n and get_char_type(chars[j]) == "T":
                        j += 1
                    if j < n and get_char_type(chars[j]) in {"C", "N"}:
                        j += 1
                    sub_rule = "Rule 2 upper/lower vowel"
                    break
                elif jt == "S":
                    j += 1
                    attached += 1
                    if j < n and get_char_type(chars[j]) == "T":
                        j += 1
                    if j < n and get_char_type(chars[j]) in {"C", "N"}:
                        j += 1
                    sub_rule = "Rule 3 special vowel"
                    break
                elif jt == "B":
                    j += 1
                    attached += 1
                    if j > i + 1 and chars[j - 1] == "า" and j < n and chars[j] == "ะ":
                        j += 1
                    sub_rule = "Rule 4 rear vowel"
                    break
                elif jt == "T":
                    j += 1
                    attached += 1
                    # Check for rear vowel after tone
                    if j < n and get_char_type(chars[j]) == "B":
                        j += 1
                    # NEW: Check for consonant after tone (e.g., ชั่ว, ข่ว, etc.)
                    if j < n and get_char_type(chars[j]) in {"C", "N"}:
                        j += 1
                        attached += 1
                    sub_rule = "Rule 6 tone"
                    break
                elif jt == "K":
                    j += 1
                    attached += 1
                    sub_rule = "Rule 13 karan"
                    break
                elif jt in {"C", "N"} and attached == 0:
                    sub_rule = "no-attach (C+C)"
                    break
                else:
                    sub_rule = "no-attach (default)"
                    break

            if j < n:
                boundaries[j] = True
            rule_log[i] = f"Rules 2-6 consonant [{sub_rule}]  chars[{i}:{j}]='{''.join(chars[i:j])}'"
            i = j
            continue

        if i + 1 < n:
            boundaries[i + 1] = True
        rule_log[i] = f"DEFAULT  '{ch}' ({ct})"
        i += 1

    # Print rule decisions
    p(f"\n  Rule decisions:")
    p(f"  {'i':<4} {'rule'}")
    p(f"  {'-'*4} {'-'*50}")
    for pos, rule in sorted(rule_log.items()):
        p(f"  {pos:<4} {rule}")

    # Print boundaries array
    p(f"\n  Boundaries: {boundaries}")

    # Print resulting MTU groups (BEFORE BMES)
    p(f"\n  MTU groups (before BMES):")
    j = 0
    mtu_idx = 0
    while j < n:
        k = j + 1
        while k < n and not boundaries[k]:
            k += 1
        group = ''.join(chars[j:k])
        types = [get_char_type(c) for c in chars[j:k]]
        p(f"  MTU[{mtu_idx}]  '{group}'  types={types}")
        mtu_idx += 1
        j = k

def format_mtus(mtus: List[List[str]]) -> str:
    """Format MTUs for display"""
    return ' | '.join([''.join(mtu) for mtu in mtus])

