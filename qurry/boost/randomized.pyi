"""
================================================================
Randomized in Cython
(:mod:`qurry.boost.randomized`)
================================================================

"""

# pylint: disable=invalid-name, missing-function-docstring, unused-argument
def ensembleCell(
    sAi: str,
    sAiMeas: int,
    sAj: str,
    sAjMeas: int,
    aNum: int,
    shots: int,
) -> float: ...
def cycling_slice(
    target: str,
    start: int,
    end: int,
    step: int,
) -> str: ...
def purityCellCore(
    singleCounts: dict[str, int],
    bitStringRange: tuple[int, int],
    subsystemSize: int,
) -> float: ...
def echoCellCore(
    firstCounts: dict[str, int],
    secondCounts: dict[str, int],
    bitStringRange: tuple[int, int],
    subsystemSize: int,
) -> float: ...

# pylint: enable=invalid-name, missing-function-docstring, unused-argument
