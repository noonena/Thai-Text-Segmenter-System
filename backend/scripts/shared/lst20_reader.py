"""
LST20 Corpus Reader

Single source of truth for reading LST20-format files.
All trainers and evaluators import from here instead of each defining their own.

LST20 format:
  word<TAB>pos[<TAB>ne<TAB>cluster...]
  (blank line or '_' token marks sentence boundary)
"""

import os
import glob
from typing import List, Tuple


def read_lst20_file(filepath: str) -> List[Tuple[List[str], List[str]]]:
    """
    Read one LST20 .txt file.
    Returns list of (words, tags) sentences.
    Sentences are delimited by blank lines; '_' tokens are skipped.
    """
    sentences = []
    words: List[str] = []
    tags:  List[str] = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                if words:
                    sentences.append((words, tags))
                    words, tags = [], []
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                word, pos = parts[0], parts[1]
                if word == '_':
                    continue
                words.append(word)
                tags.append(pos)

    if words:
        sentences.append((words, tags))

    return sentences


def read_lst20_dir(
    directory: str,
    max_sentences: int = None,
) -> List[Tuple[List[str], List[str]]]:
    """
    Read all .txt files in a directory.
    Returns list of (words, tags) sentences, up to max_sentences if given.
    """
    sentences = []
    for filepath in sorted(glob.glob(os.path.join(directory, '*.txt'))):
        for sent in read_lst20_file(filepath):
            sentences.append(sent)
            if max_sentences and len(sentences) >= max_sentences:
                return sentences
    return sentences
