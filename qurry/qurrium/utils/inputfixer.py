"""Input Fixer (:mod:`qurry.qurrium.utils.inputfixer`)

Now Qurrium includes 
`pyxDamerauLevenshtein <https://github.com/lanl/pyxDamerauLevenshtein>`_,
instead of use a copy in our package.

For why I used a copy for a long time, it's because I just need the original
Python implementation for short string comparision, which Cython implementation
is not necessary for me. Also I concerned there will be some maintaining issues 
on this package which less updated in the future.

But based on the respect for original Author, I think it's better 
to include it as our dependency. And its maintaining works well for now.

- The very original implementation by Michael Homer:
    https://web.archive.org/web/20150909134357/\
http://mwh.geek.nz:80/2009/04/26/python-damerau-levenshtein-distance

- A Cython implementation of the same algorithm, where our implementation is based on:
    https://github.com/lanl/pyxDamerauLevenshtein

"""

import warnings
from typing import Any
from collections.abc import Sequence

from ..exceptions import UnknownArgumentsKept

try:
    from pyxdameraulevenshtein import damerau_levenshtein_distance
except ImportError:
    # Just in case for the package encouter some issues

    def damerau_levenshtein_distance(seq1: Sequence[str], seq2: Sequence[str]) -> int:
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

        This implementation is based on `Michael Homer's implementation
        <https://web.archive.org/web/20150909134357/\
    http://mwh.geek.nz:80/2009/04/26/python-damerau-levenshtein-distance/>`_,
        and based on `pyxDamerauLevenshtein <https://github.com/lanl/pyxDamerauLevenshtein>`_,
        a Cython implementation of same algorithm.

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
        return

    if not mute_outfields_warning:
        warnings.warn(
            "| The following keys are not recognized as arguments for main process of experiment, "
            + "but still kept in experiment record."
            + " Similar: ["
            + ", ".join([f"'{k}' maybe '{v}'" for k, v in outfields_maybe.items()])
            + "]. Unknown: ["
            + ", ".join([f"'{k}'" for k in outfields_unknown])
            + "].",
            UnknownArgumentsKept,
        )
    return
