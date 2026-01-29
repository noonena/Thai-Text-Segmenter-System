# Same character classification as training
CONSONANTS = set("ก ข ฃ ค ฅ ฆ ง จ ฉ ช ซ ฌ ญ ฎ ฏ ฐ ฑ ฒ ณ ด ต ถ ท ธ น บ ป ผ ฝ พ ฟ ภ ม ย ร ล ว ศ ษ ส ห ฬ อ ฮ".split())
NON_SUFFIX_CONSONANTS = set("ฃ ฅ ฆ ฉ ช ซ ฌ ญ ฑ ฒ ณ ต ผ ฝ ฟ ภ".split())
FRONT_VOWELS = set("เ แ โ ไ ใ".split())
UPPER_VOWELS = set("ิ ี ึ ื".split())
SPECIAL_VOWELS = set("ั ็".split())
REAR_VOWELS = set("า ๅ ว ะ ำ".split())
LOWER_VOWELS = set("ุ ู".split())
TONES = set("่ ้ ๊ ๋".split())
KARAN = "์"
SPECIAL_SYMBOLS = set("ๆ ฯ ํ".split())
DIGITS = set("0123456789๐๑๒๓๔๕๖๗๘๙")


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