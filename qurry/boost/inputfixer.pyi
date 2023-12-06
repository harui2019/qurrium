"""
================================================================
Inputfixer in Cython
(:mod:`qurry.boost.inputfixer`)
================================================================
"""
from typing import Iterable

# pylint: disable=unused-argument

def damerau_levenshtein_distance_cy(seq1: Iterable[str], seq2: Iterable[str]) -> int:
    """Damerau-Levenshtein distance between two iterables."""

# pylint: enable=unused-argument
