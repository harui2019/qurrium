"""
================================================================
Qurrent - Second Renyi Entropy Measurement
(:mod:`qurry.qurrent`)
================================================================

"""

from typing import Literal, Union, overload

from .randomized_measure import EntropyMeasureRandomized
from .randomized_measure_v1 import EntropyMeasureRandomizedV1
from .hadamard_test import EntropyMeasureHadamard


# pylint: disable=invalid-name
@overload
def EntropyMeasure(*args, method: Literal["hadamard"], **kwargs) -> EntropyMeasureHadamard: ...


@overload
def EntropyMeasure(
    *args, method: Literal["randomized_v1"], **kwargs
) -> EntropyMeasureRandomizedV1: ...


@overload
def EntropyMeasure(
    *args, method: Union[Literal["randomized", "haar", "base"], str] = "randomized", **kwargs
) -> EntropyMeasureRandomized: ...


def EntropyMeasure(
    *args,
    method="randomized",
    **kwargs,
):
    """Call `EntropyMeasure` methods.

    Args:
        method (Literal[&#39;randomized&#39;, &#39;hadamard&#39;, &#39;base&#39;], optional):

            - randomized: running by haar randomized measure.
            - hadamard: running by hadamard test.
            - base: the base of `EntropyMeasure`.
            Defaults to 'randomized'.

    Returns:
        Union[EntropyMeasureBase, EntropyMeasureV2Base]: method.
    """
    if method in ("randomized", "haar"):
        return EntropyMeasureRandomized(*args, **kwargs)
    if method == "randomized_v1":
        return EntropyMeasureRandomizedV1(*args, **kwargs)
    if method == "hadamard":
        return EntropyMeasureHadamard(*args, **kwargs)
    return EntropyMeasureRandomized(*args, **kwargs)


# pylint: enable=invalid-name
