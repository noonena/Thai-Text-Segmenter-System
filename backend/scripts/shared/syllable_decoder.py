"""
BMES Syllable Decoder

Single source of truth for assembling syllables from MTU sequences
and BMES label predictions.

Used by: complete_pipeline.py, resegment_corpus.py,
         evaluate_pipeline.py, syllable_trainer.py
"""

from typing import List


def bmes_to_syllables(mtus: List[str], labels: List[str]) -> List[str]:
    """
    Convert a list of MTUs and their BMES labels into syllable strings.

    Labels:
      S — single-MTU syllable
      B — beginning of multi-MTU syllable
      M — middle
      E — end (flush current group)
    """
    syllables: List[str] = []
    current:   List[str] = []

    for mtu, label in zip(mtus, labels):
        if label == 'S':
            if current:
                syllables.append(''.join(current))
                current = []
            syllables.append(mtu)
        elif label == 'B':
            current = [mtu]
        elif label == 'M':
            current.append(mtu)
        elif label == 'E':
            current.append(mtu)
            syllables.append(''.join(current))
            current = []

    if current:
        syllables.append(''.join(current))

    return syllables
