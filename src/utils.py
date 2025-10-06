"""Miscellaneous helper utilities for the project."""

from __future__ import annotations

from typing import List

__all__ = ["tokens_from_sentence"]


def tokens_from_sentence(sentence: str, lowercase: bool = False) -> List[str]:
    """Split a sentence into tokens using whitespace.

    Parameters
    ----------
    sentence:
        Input string.
    lowercase:
        If true, the returned tokens are converted to lowercase.
    """

    tokens = sentence.strip().split()
    if lowercase:
        tokens = [tok.lower() for tok in tokens]
    return tokens
