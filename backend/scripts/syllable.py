"""
Syllable Identification - Fixed and Simplified
Based on Section 3.3.2 of the dissertation

Takes MTUs as input and groups them into syllables.
"""

import os
import pickle
from typing import List, Dict, Tuple

# Character classification
CONSONANTS = set("ก ข ฃ ค ฅ ฆ ง จ ฉ ช ซ ฌ ญ ฎ ฏ ฐ ฑ ฒ ณ ด ต ถ ท ธ น บ ป ผ ฝ พ ฟ ภ ม ย ร ล ว ศ ษ ส ห ฬ อ ฮ".split())
FRONT_VOWELS = set("เ แ โ ไ ใ".split())
TONES = set("่ ้ ๊ ๋".split())


def has_consonant(mtu: str) -> bool:
    """Check if MTU contains consonant"""
    return any(c in CONSONANTS for c in mtu)


def has_front_vowel(mtu: str) -> bool:
    """Check if MTU contains front vowel"""
    return any(c in FRONT_VOWELS for c in mtu)


def has_tone(mtu: str) -> bool:
    """Check if MTU contains tone marker"""
    return any(c in TONES for c in mtu)


def starts_with_front_vowel(mtu: str) -> bool:
    """Check if MTU starts with front vowel"""
    return len(mtu) > 0 and mtu[0] in FRONT_VOWELS


def simple_syllable_grouping(mtus: List[str]) -> List[List[str]]:
    """
    Simple heuristic syllable grouping.
    
    Heuristics:
    1. MTU starting with front vowel often starts new syllable
    2. MTU with tone often ends syllable
    3. Otherwise, group MTUs together
    
    This is SIMPLIFIED - proper approach needs trained CRF with BEST2010 data.
    """
    if len(mtus) == 0:
        return []
    
    if len(mtus) == 1:
        return [mtus]
    
    syllables = []
    current_syllable = []
    
    for i, mtu in enumerate(mtus):
        # Start new syllable if MTU begins with front vowel
        if starts_with_front_vowel(mtu) and len(current_syllable) > 0:
            syllables.append(current_syllable)
            current_syllable = [mtu]
        else:
            current_syllable.append(mtu)
        
        # End syllable if MTU has tone
        if has_tone(mtu):
            syllables.append(current_syllable)
            current_syllable = []
    
    # Add remaining MTUs
    if current_syllable:
        syllables.append(current_syllable)
    
    return syllables


def syllable_to_labels(mtus: List[str], syllables: List[List[str]]) -> List[str]:
    """
    Convert syllable grouping to B/M/E/S labels for each MTU.
    
    Args:
        mtus: Original list of MTUs
        syllables: Grouped MTUs by syllable
    
    Returns:
        List of labels (B/M/E/S) for each MTU
    """
    labels = []
    
    for syllable in syllables:
        if len(syllable) == 1:
            labels.append("S")
        else:
            labels.append("B")
            for _ in range(len(syllable) - 2):
                labels.append("M")
            labels.append("E")
    
    return labels


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("Syllable Identification - Simple Heuristic Approach")
    print("=" * 80)
    
    # Example MTU sequences
    test_cases = [
        (["ส", "วัส", "ดี"], "สวัสดี"),
        (["กา", "แฟ"], "กาแฟ"),
        (["กา", "ร", "เชื่อ", "ม", "ต่", "อ"], "การเชื่อมต่อ"),
        (["นั่น", "มือ", "ถือ", "อะ", "ไร"], "นั่นมือถืออะไร"),
        (["ไม่"], "ไม่"),
    ]
    
    print("\n📋 Testing Syllable Grouping:")
    print("-" * 80)
    
    for mtus, original in test_cases:
        # Group MTUs into syllables
        syllables = simple_syllable_grouping(mtus)
        
        # Get labels
        labels = syllable_to_labels(mtus, syllables)
        
        # Format output
        mtu_str = " | ".join(mtus)
        syl_str = " | ".join(["".join(syl) for syl in syllables])
        label_str = " ".join(labels)
        
        print(f"Original: {original}")
        print(f"MTUs:      {mtu_str}")
        print(f"Syllables: {syl_str}")
        print(f"Labels:    {label_str}")
        print()
    
    print("=" * 80)
    print("\n⚠️  IMPORTANT NOTES:")
    print("1. This uses SIMPLE HEURISTICS, not a trained CRF")
    print("2. For production, you need syllable-labeled training data (BEST2010)")
    print("3. This is good enough for testing the pipeline")
    print("=" * 80)