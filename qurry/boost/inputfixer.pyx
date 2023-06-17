
cpdef int damerau_levenshtein_distance_cy(seq1, seq2):
    """Calculate the Damerau-Levenshtein distance between sequences.

    This distance is the number of additions, deletions, substitutions,
    and transpositions needed to transform the first sequence into the
    second. Although generally used with strings, any sequences of
    comparable objects wil l work.

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
    if seq1 is None or len(seq1) == 0:
        return len(seq2)
    if seq2 is None or len(seq2) == 0:
        return len(seq1)

    cdef Py_ssize_t first_differing_index = 0
    for _ in range(min(len(seq1), len(seq2))):
        if seq1[first_differing_index] == seq2[first_differing_index]:
            first_differing_index += 1

    seq1 = seq1[first_differing_index:]
    seq2 = seq2[first_differing_index:]

    cdef Py_ssize_t x, y, delCost, addCost, subCost
    cdef list twoAgo, oneAgo, thisRow

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