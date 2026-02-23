# """
# POS Tagging Feature Extraction
# Extracts features from words for CRF-based POS tagging
# """

# def word2features(words, i):
#     """
#     Extract features for word at position i
    
#     Features based on Table 4.6 from methodology:
#     - Word itself
#     - Word shape (has digits, symbols, etc.)
#     - Prefix patterns (การ, ความ, etc.)
#     - Context (previous/next words)
#     """
#     word = words[i]
    
#     features = {
#         # 1. Current word
#         'word.lower()': word.lower(),
#         'word[-3:]': word[-3:],  # Last 3 chars
#         'word[-2:]': word[-2:],  # Last 2 chars
#         'word[:2]': word[:2],    # First 2 chars
        
#         # 2. Word shape features
#         'word.isdigit()': word.isdigit(),
#         'word.has_digit': any(c.isdigit() for c in word),
#         'word.has_thai': any('\u0e00' <= c <= '\u0e7f' for c in word),
        
#         # 3. Prefix patterns (CP = Common Prefix)
#         'word.startswith(การ)': word.startswith('การ'),
#         'word.startswith(ความ)': word.startswith('ความ'),
#         'word.startswith(ผู้)': word.startswith('ผู้'),
#         'word.startswith(นัก)': word.startswith('นัก'),
#         'word.startswith(แม่)': word.startswith('แม่'),
        
#         # 4. Word length
#         'word.length': len(word),
#         'word.is_short': len(word) <= 2,
#         'word.is_long': len(word) >= 5,
#     }
    
#     # 5. Context features - Previous word (Unigram)
#     if i > 0:
#         word_prev = words[i-1]
#         features.update({
#             '-1:word.lower()': word_prev.lower(),
#             '-1:word[-2:]': word_prev[-2:],
#         })
#     else:
#         features['BOS'] = True  # Beginning of sentence
    
#     # 6. Context features - Next word (Unigram)
#     if i < len(words) - 1:
#         word_next = words[i+1]
#         features.update({
#             '+1:word.lower()': word_next.lower(),
#             '+1:word[:2]': word_next[:2],
#         })
#     else:
#         features['EOS'] = True  # End of sentence
    
#     # 7. Bigram features (word pairs)
#     if i > 0:
#         features['-1:word+word'] = f"{words[i-1]}+{word}"
    
#     if i < len(words) - 1:
#         features['word+1:word'] = f"{word}+{words[i+1]}"
    
#     return features


# def extract_features(words):
#     """Extract features for all words in sentence"""
#     return [word2features(words, i) for i in range(len(words))]


# def extract_labels(pos_tags):
#     """Extract labels (POS tags)"""
#     return pos_tags
"""
POS Tagging Feature Extraction
Extracts features from words for CRF-based POS tagging

Implements the 13 word-level feature flags described in Table 4.6 and
uses a wider context window (n±2) as described in Table 4.7.
"""

import unicodedata
from typing import Dict, List


# --- Thai character helpers ---
THAI_START = "\u0e00"
THAI_END = "\u0e7f"

THAI_CONSONANTS = set(
    "กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ"
)

NEGATOR = "ไม่"
COMMON_PREFIXES_CONTAIN = ("การ", "ความ")  # CP = contains
PREFIXES_BEGIN = ("การ", "ความ", "ผู้", "นัก", "แม่")  # PF = begins with


def _is_thai_char(c: str) -> bool:
    return THAI_START <= c <= THAI_END


def _is_symbol_char(c: str) -> bool:
    # P* = punctuation, S* = symbols
    return unicodedata.category(c).startswith(("P", "S"))


def _is_only_number(word: str) -> bool:
    # .isdigit() covers Thai numerals too
    return bool(word) and word.isdigit()


def _begins_with_number(word: str) -> bool:
    return bool(word) and word[0].isdigit()


def _ends_with_number(word: str) -> bool:
    return bool(word) and word[-1].isdigit()


def _is_only_symbol(word: str) -> bool:
    return bool(word) and all(_is_symbol_char(c) for c in word)


def _begins_with_symbol(word: str) -> bool:
    return bool(word) and _is_symbol_char(word[0])


def _ends_with_symbol(word: str) -> bool:
    return bool(word) and _is_symbol_char(word[-1])


def _is_foreign(word: str) -> bool:
    # "foreign language" ≈ contains alphabetic chars outside Thai block (e.g., Latin)
    return any(c.isalpha() and not _is_thai_char(c) for c in word)


def _has_karan(word: str) -> bool:
    # garun/karan (์)
    return "์" in word


def _has_common_prefix_seq(word: str) -> bool:
    return any(seq in word for seq in COMMON_PREFIXES_CONTAIN)


def _begins_with_prefix_seq(word: str) -> bool:
    return any(word.startswith(p) for p in PREFIXES_BEGIN)


def _has_negator(word: str) -> bool:
    return NEGATOR in word


def _begins_with_negator(word: str) -> bool:
    return word.startswith(NEGATOR)


def _has_one_thai_consonant(word: str) -> bool:
    # "contains one Thai consonant" (TH) – count Thai consonant letters in the token
    cons_count = sum(1 for c in word if c in THAI_CONSONANTS)
    return cons_count == 1


def _add_flag_features(features: Dict, word: str, prefix: str = "") -> None:
    key = (lambda k: f"{prefix}{k}") if prefix else (lambda k: k)

    features.update(
        {
            key("WD"): word,
            key("NC"): len(word),
            key("N"): _is_only_number(word),
            key("BN"): _begins_with_number(word),
            key("EN"): _ends_with_number(word),
            key("S"): _is_only_symbol(word),
            key("BS"): _begins_with_symbol(word),
            key("ES"): _ends_with_symbol(word),
            key("F"): _is_foreign(word),
            key("G"): _has_karan(word),
            key("CP"): _has_common_prefix_seq(word),
            key("PF"): _begins_with_prefix_seq(word),
            key("NG"): _has_negator(word),
            key("BG"): _begins_with_negator(word),
            key("TH"): _has_one_thai_consonant(word),
        }
    )

    # Small extra surface hints (cheap + useful)
    if word:
        features[key("W[:2]")] = word[:2]
        features[key("W[-2:]")] = word[-2:]
        features[key("W[-3:]")] = word[-3:]
        features[key("lower")] = word.lower()


def word2features(words: List[str], i: int) -> Dict:
    """
    Extract POS features for word at position i.

    Word-level feature flags follow Table 4.6:
    WD, NC, N, BN, EN, S, BS, ES, F, G, CP, PF, NG, BG, TH

    Context window follows Table 4.7 (expanded here at word-level): n±2.
    """
    word = words[i]

    features: Dict = {}

    # 1) Current word features (Table 4.6)
    _add_flag_features(features, word)

    # 2) Context: previous 1 and 2
    if i - 1 >= 0:
        _add_flag_features(features, words[i - 1], prefix="-1:")
        features["-1:WD+WD"] = f"{words[i-1]}+{word}"
    else:
        features["BOS"] = True

    if i - 2 >= 0:
        _add_flag_features(features, words[i - 2], prefix="-2:")

    # 3) Context: next 1 and 2
    if i + 1 < len(words):
        _add_flag_features(features, words[i + 1], prefix="+1:")
        features["WD+1:WD"] = f"{word}+{words[i+1]}"
    else:
        features["EOS"] = True

    if i + 2 < len(words):
        _add_flag_features(features, words[i + 2], prefix="+2:")

    return features


def extract_features(words: List[str]):
    """Extract features for all words in sentence"""
    return [word2features(words, i) for i in range(len(words))]


def extract_labels(pos_tags: List[str]):
    """Extract labels (POS tags)"""
    return pos_tags
