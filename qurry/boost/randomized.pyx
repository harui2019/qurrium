from libc.math cimport pow

cpdef double ensembleCell(
    str sAi,
    int sAiMeas,
    str sAj,
    int sAjMeas,
    int aNum,
    int shots
):
    """Calculate the value of two counts from qubits in ensemble average.
    """
    cdef int diff = sum([s1 != s2 for s1, s2 in zip(sAi, sAj)])
    cdef double tmp = pow(2, aNum) * pow(-2, -diff) * (sAiMeas / shots) * (sAjMeas / shots)
    return tmp

cpdef str cycling_slice(str target, int start, int end, int step=1):
    cdef int length = len(target)
    cdef dict sliceCheck = {
        'start <= -length': (start <= -length),
        'end >= length ': (end >= length),
    }
    cdef str newString

    if all(sliceCheck.values()):
        raise IndexError(
            "Slice out of range" +
            ", ".join([f" {k};" for k, v in sliceCheck.items() if not v]))
    if length <= 0:
        newString = target
    elif start < 0 and end >= 0:
        newString = target[start:] + target[:end]
    else:
        newString = target[start:end]

    return newString[::step]

cpdef double purityCellCore(
    dict singleCounts,
    (int, int) bitStringRange,
    int subsystemSize
):
    cdef int shots = sum(singleCounts.values())
    cdef str dummyString = ''.join([str(ds) for ds in range(subsystemSize)])
    cdef dict singleCountsUnderDegree
    
    if dummyString[bitStringRange[0]:bitStringRange[1]] == cycling_slice(
            dummyString, bitStringRange[0], bitStringRange[1], 1):
        
        singleCountsUnderDegree = dict.fromkeys(
            [k[bitStringRange[0]:bitStringRange[1]] for k in singleCounts], 0)
        for bitString in list(singleCounts):
            singleCountsUnderDegree[
                bitString[bitStringRange[0]:bitStringRange[1]]
            ] += singleCounts[bitString]
    else:
        singleCountsUnderDegree = dict.fromkeys(
            [cycling_slice(k, bitStringRange[0], bitStringRange[1], 1) for k in singleCounts], 0)
        for bitString in list(singleCounts):
            singleCountsUnderDegree[
                cycling_slice(
                    bitString, bitStringRange[0], bitStringRange[1], 1)
            ] += singleCounts[bitString]

    cdef double purityCell = 0.0
    for sAi, sAiMeas in singleCountsUnderDegree.items():
        for sAj, sAjMeas in singleCountsUnderDegree.items():
            purityCell += ensembleCell(
                sAi, sAiMeas, sAj, sAjMeas, subsystemSize, shots)

    return purityCell

cpdef double echoCellCore(
    dict firstCounts,
    dict secondCounts,
    (int, int) bitStringRange,
    int subsystemSize
):
    cdef int shots = sum(firstCounts.values())
    cdef int shots2 = sum(secondCounts.values())
    assert shots == shots2, f"shots {shots} does not match shots2 {shots2}"

    cdef dict firstCountsUnderDegree = dict.fromkeys(
        [k[bitStringRange[0]:bitStringRange[1]] for k in firstCounts], 0)
    for bitString in list(firstCounts):
        firstCountsUnderDegree[
            bitString[bitStringRange[0]:bitStringRange[1]]
        ] += firstCounts[bitString]

    cdef dict secondCountsUnderDegree = dict.fromkeys(
        [k[bitStringRange[0]:bitStringRange[1]] for k in secondCounts], 0)
    for bitString in list(secondCounts):
        secondCountsUnderDegree[
            bitString[bitStringRange[0]:bitStringRange[1]]
        ] += secondCounts[bitString]

    cdef double echoCell = 0.0

    for sAi, sAiMeas in firstCountsUnderDegree.items():
        for sAj, sAjMeas in secondCountsUnderDegree.items():
            echoCell += ensembleCell(
                sAi, sAiMeas, sAj, sAjMeas, subsystemSize, shots)

    return echoCell