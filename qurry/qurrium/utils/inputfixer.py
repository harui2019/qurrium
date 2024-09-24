"""
================================================================
Input Fixer
(:mod:`qurry.qurrium.utils.inputfixer`)
================================================================
"""

import warnings
from typing import Any, Sequence

from ...exceptions import QurryWarning, QurryUnrecongnizedArguments

try:
    from ...boost.inputfixer import damerau_levenshtein_distance_cy  # type: ignore

    CYTHON_AVAILABLE = True
except ImportError:
    CYTHON_AVAILABLE = False

    def damerau_levenshtein_distance_cy(*args, **kwargs):
        """Dummy function for Cython version of `damerau_levenshtein_distance`"""
        raise NotImplementedError(
            "Cython version of `damerau_levenshtein_distance` is not available, "
            + "please re-install qurry with `pip install qurry[cython]`."
        )


# pylint: disable=line-too-long


def damerau_levenshtein_distance_py(
    seq1: Sequence[str],
    seq2: Sequence[str],
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
    and inspired by https://github.com/lanl/pyxDamerauLevenshtein,
    a Cython implementation of same algorithm.

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
    # pylint: enable=line-too-long
    if seq1 is None:
        return len(seq2)
    if seq2 is None:
        return len(seq1)

    first_differing_index = 0
    while all(
        [
            first_differing_index < len(seq1) - 1,
            first_differing_index < len(seq2) - 1,
            seq1[first_differing_index] == seq2[first_differing_index],
        ]
    ):
        first_differing_index += 1

    seq1 = seq1[first_differing_index:]
    seq2 = seq2[first_differing_index:]

    two_ago, one_ago, this_row = [], [], (list(range(1, len(seq2) + 1)) + [0])
    for x, _ in enumerate(seq1):
        two_ago, one_ago, this_row = one_ago, this_row, [0] * len(seq2) + [x + 1]
        for y, _ in enumerate(seq2):
            del_cost = one_ago[y] + 1
            add_cost = this_row[y - 1] + 1
            sub_cost = one_ago[y - 1] + (seq1[x] != seq2[y])
            # fun fact: isinstance(bool(...), int) == True
            this_row[y] = min(del_cost, add_cost, sub_cost)

            if all(
                [
                    x > 0,
                    y > 0,
                    seq1[x] == seq2[y - 1],
                    seq1[x - 1] == seq2[y],
                    seq1[x] != seq2[y],
                ]
            ):
                this_row[y] = min(this_row[y], two_ago[y - 2] + 1)

    return this_row[len(seq2) - 1]


def damerau_levenshtein_distance(
    seq1: Sequence[str],
    seq2: Sequence[str],
) -> int:
    """Calculate the Damerau-Levenshtein distance between sequences.
    This distance is the number of additions, deletions, substitutions,

    If you want to compare long strings,
    we recommend using `RapidFuzz` instead of this function.
    This function is designed for input suggestion for short string.
    which is hard to handle very long string.

    Args:
        seq1 (Iterable): Sequence of items to be compared.
        seq2 (Iterable): Sequence of items to be compared.

    Returns:
        int: The distance between the two sequences.
    """

    if len(seq1) > 100 or len(seq2) > 100:
        warnings.warn(
            "If you want to compare long strings, "
            + "we recommend using `RapidFuzz` instead of this function."
            + "This function is designed for input suggestion for short string."
            + "which is hard to handle very long string. ",
            QurryWarning,
        )

    if CYTHON_AVAILABLE:
        return damerau_levenshtein_distance_cy(seq1, seq2)

    return damerau_levenshtein_distance_py(seq1, seq2)


def outfields_check(
    outfields: dict[str, Any],
    infields: Sequence[str],
    simialrity_threshold: int = 2,
) -> tuple[dict[str, list[str]], list[str]]:
    """Check if the outfields are in the infields but just typing wrong
    by Damerau-Levenshtein distance.

    Args:
        outfields (dict[str, Any]): The outfields of the experiment.
        infields (Iterable[str]): The infields of the experiment.
        simialrity_threshold (int, optional): Similarity threshold. Defaults to 2.

    Returns:
        tuple[dict[str, list[str]], list[str]]:
            outfields_maybe:
                The outfields that may be in the infields but typing wrong.
            outfields_unknown:
                The outfields that are not in the infields.
    """

    if len(outfields) == 0:
        return {}, []

    outfield_maybe = {}
    for k in outfields.keys():
        tmp = []
        for k2 in infields:
            if damerau_levenshtein_distance(k, k2) <= simialrity_threshold:
                tmp.append(k2)
        if len(tmp) > 0:
            outfield_maybe[k] = tmp
    outfields_unknown = [k for k in outfields.keys() if k not in outfield_maybe]

    return outfield_maybe, outfields_unknown


def outfields_hint(
    outfields_maybe: dict[str, list[str]],
    outfields_unknown: list[str],
    mute_outfields_warning: bool = False,
) -> None:
    """Print the outfields that may be in the infields but typing wrong.

    Args:
        outfields_maybe (dict[str, list[str]]):
            The outfields that may be in the infields but typing wrong.
        outfields_unknown (list[str]):
            The outfields that are not in the infields.
        mute_outfields_warning (bool, optional):
            Mute the warning of unrecognized arguments. Defaults to False.
    """
    if len(outfields_maybe) + len(outfields_unknown) == 0:
        return None

    if not mute_outfields_warning:
        warnings.warn(
            "| The following keys are not recognized as arguments for main process of experiment, "
            + "but still kept in experiment record."
            + " Similar: ["
            + ", ".join([f"'{k}' maybe '{v}'" for k, v in outfields_maybe.items()])
            + "]. Unknown: ["
            + ", ".join([f"'{k}'" for k in outfields_unknown])
            + "].",
            QurryUnrecongnizedArguments,
        )
    return None
