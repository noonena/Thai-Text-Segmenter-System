# Same character classification as training
from typing import List



CONSONANTS = set("ก ข ฃ ค ฅ ฆ ง จ ฉ ช ซ ฌ ญ ฎ ฏ ฐ ฑ ฒ ณ ด ต ถ ท ธ น บ ป ผ ฝ พ ฟ ภ ม ย ร ล ว ศ ษ ส ห ฬ อ ฮ".split())
NON_SUFFIX_CONSONANTS = set("ฃ ฅ ฆ ฉ ช ซ ฌ ญ ฑ ฒ ณ ต ผ ฝ ฟ ภ".split())
FRONT_VOWELS = set("เ แ โ ไ ใ".split())
UPPER_VOWELS = set("ิ ี ึ ื".split())
SPECIAL_VOWELS = set("ั ็".split())
REAR_VOWELS = set("า ๅ ะ ำ".split())
LOWER_VOWELS = set("ุ ู".split())
TONES = set("่ ้ ๊ ๋".split())
KARAN = "์"
SPECIAL_SYMBOLS = set("ๆ ฯ ํ".split())
DIGITS = set("0123456789๐๑๒๓๔๕๖๗๘๙")

# อักษรนำ: silent ห pairs — ห is silent, the second consonant is the real onset
AKSON_NAM_CLUSTERS = {'หง', 'หน', 'หม', 'หย', 'หร', 'หล', 'หว', 'หณ', 'หญ'}

ALL_VOWELS = FRONT_VOWELS | UPPER_VOWELS | SPECIAL_VOWELS | REAR_VOWELS | LOWER_VOWELS | {KARAN}


def is_number(s: str) -> bool:
    """Check if string is entirely numeric (Arabic or Thai digits)."""
    return bool(s) and all(c in DIGITS for c in s)


def is_valid_thai_word(word: str) -> bool:
    """Check if word contains Thai consonants and has reasonable structure."""
    if not word:
        return False
    has_consonant = any(c in CONSONANTS for c in word)
    has_vowel = any(c in ALL_VOWELS for c in word)
    return has_consonant and (has_vowel or len(word) <= 2 or any(c in CONSONANTS for c in word[-2:]))


def get_char_type(ch: str) -> str:
    if ch in CONSONANTS: return "C"
    if ch in NON_SUFFIX_CONSONANTS: return "N"
    if ch in FRONT_VOWELS: return "F"
    if ch in UPPER_VOWELS: return "U"
    if ch in SPECIAL_VOWELS: return "S"
    if ch in REAR_VOWELS: return "B"
    if ch in LOWER_VOWELS: return "L"
    if ch in TONES: return "T"
    if ch == KARAN: return "K"
    if ch in SPECIAL_SYMBOLS: return "O"
    if ch in DIGITS: return "D"
    if ch in (" ", "\t"): return "G"
    return "Q"


def get_compound_vowel_length(chars: List[str], i: int) -> int:
    """
    Return the length of a compound vowel (สระประสม) starting at position i, or 0.
      อัว : ั + ว  → 2
      เ-ีย: ี + ย  → 2
      เ-ือ: ื + อ  → 2
    """
    if i >= len(chars):
        return 0
    ch = chars[i]
    if i + 1 < len(chars):
        nxt = chars[i + 1]
        if ch == 'ั' and nxt == 'ว':   # อัว
            return 2
        if ch == 'ี' and nxt == 'ย':   # เ-ีย
            return 2
        if ch == 'ื' and nxt == 'อ':   # เ-ือ
            return 2
    return 0