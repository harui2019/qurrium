from ...exceptions import QurryWarning, QurryUnrecongnizedArguments
try:
    from ...boost.inputfixer import damerau_levenshtein_distance_cy
    useCython = True
except ImportError:
    useCython = False

import warnings
from typing import Iterable, Any


def damerau_levenshtein_distance_py(
    seq1: Iterable[str],
    seq2: Iterable[str],
) -> int:
    """Calculate the Damerau-Levenshtein distance between sequences.

    This distance is the number of additions, deletions, substitutions,
    and transpositions needed to transform the first sequence into the
    second. Although generally used with strings, any sequences of
    comparable objects will work.

    Transpositions are exchanges of *consecutive* characters; all other
    operations are self-explanatory.

    This implementation is O(N*M) time and O(M) space, for N and M the
    lengths of the two sequences.

    >>> dameraulevenshtein('ba', 'abc')
    2
    >>> dameraulevenshtein('fee', 'deed')
    2

    It works with arbitrary sequences too:
    >>> dameraulevenshtein('abcd', ['b', 'a', 'c', 'd', 'e'])
    2

    This implementation is based on Michael Homer's implementation
    (https://web.archive.org/web/20150909134357/http://mwh.geek.nz:80/2009/04/26/python-damerau-levenshtein-distance/)
    and inspired by https://github.com/lanl/pyxDamerauLevenshtein, a Cython implementation of same algorithm.

    For more powerful string comparison, including Levenshtein distance,
    We recommend using the https://github.com/maxbachmann/RapidFuzz,
    It's a library that wraps the C++ Levenshtein algorithm and other string processing functions.
    The most efficient Python implementation (using Cython) currently.

    Args:
        seq1 (Iterable): Sequence of items to be compared.
        seq2 (Iterable): Sequence of items to be compared.

    Returns:
        int: The distance between the two sequences.
    """
    if seq1 is None:
        return len(seq2)
    if seq2 is None:
        return len(seq1)

    first_differing_index = 0
    while all([
        first_differing_index < len(seq1),
        first_differing_index < len(seq2),
        seq1[first_differing_index] == seq2[first_differing_index]
    ]):
        first_differing_index += 1

    seq1 = seq1[first_differing_index:]
    seq2 = seq2[first_differing_index:]

    twoAgo, oneAgo, thisRow = [], [
    ], ([i for i in range(1, len(seq2) + 1)] + [0])
    for x in range(len(seq1)):
        twoAgo, oneAgo, thisRow = oneAgo, thisRow, [0] * len(seq2) + [x + 1]
        for y in range(len(seq2)):
            delCost = oneAgo[y] + 1
            addCost = thisRow[y - 1] + 1
            subCost = oneAgo[y - 1] + (seq1[x] != seq2[y])
            # fun fact: isinstance(bool(...), int) == True
            thisRow[y] = min(delCost, addCost, subCost)

            if all([
                x > 0, y > 0,
                seq1[x] == seq2[y - 1],
                seq1[x - 1] == seq2[y],
                seq1[x] != seq2[y]
            ]):
                thisRow[y] = min(thisRow[y], twoAgo[y - 2] + 1)

    return thisRow[len(seq2) - 1]


def damerau_levenshtein_distance(
    seq1: Iterable[str],
    seq2: Iterable[str],
) -> int:
    if len(seq1) > 100 or len(seq2) > 100:
        warnings.warn(
            "If you want to compare long strings, we recommend using `RapidFuzz` instead of this function." +
            "This function is designed for input suggestion for short string." +
            "which is hard to handle very long string. ",
            QurryWarning)

    if useCython:
        return damerau_levenshtein_distance_cy(seq1, seq2)
    else:   
        return damerau_levenshtein_distance_py(seq1, seq2)


def outfields_check(
    outfields: dict[str, Any],
    infields: Iterable[str],
) -> tuple[dict[str, list[str]], list[str]]:

    if len(outfields) == 0:
        return {}, []

    outfield_maybe = {}
    for k in outfields.keys():
        tmp = []
        for k2 in infields:
            if damerau_levenshtein_distance(k, k2) <= 2:
                tmp.append(k2)
        if len(tmp) > 0:
            outfield_maybe[k] = tmp
    outfields_unknown = [k for k in outfields.keys() if k not in outfield_maybe.keys()]

    return outfield_maybe, outfields_unknown


def outfields_hint(
    outfields_maybe: dict[str, list[str]],
    outfields_unknown: list[str],
    muteOutfieldsWarning: bool = False,
) -> None:
    if len(outfields_maybe)+len(outfields_unknown) == 0:
        return None

    if not muteOutfieldsWarning:
        warnings.warn(
            f"| The following keys are not recognized as arguments for main process of experiment " +
            ', but still kept in experiment record.',
            QurryUnrecongnizedArguments
        )
    print('| Maybe you want to use these arguments: ')
    for k, v in outfields_maybe.items():
        print(f"| - '{k}' maybe {v}")
    if len(outfields_unknown) > 0:
        print('| The following are not recognized as arguments:', outfields_unknown)
