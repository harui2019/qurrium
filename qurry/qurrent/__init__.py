"""
================================================================
Qurrent - Second Renyi Entropy Measurement
(:mod:`qurry.qurrent`)
================================================================

"""
from typing import Literal, Union, overload

from .randomized_measure import EntropyRandomizedMeasure
from .hadamard_test import EntropyHadamardTest


# pylint: disable=invalid-name
@overload
def EntropyMeasure(*args, method: Literal["hadamard"], **kwargs) -> EntropyHadamardTest:
    ...


@overload
def EntropyMeasure(
    *args, method: Union[Literal["randomized", "base"], str] = "randomized", **kwargs
) -> EntropyRandomizedMeasure:
    ...


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
        return EntropyRandomizedMeasure(*args, **kwargs)
    if method == "hadamard":
        return EntropyHadamardTest(*args, **kwargs)
    return EntropyRandomizedMeasure(*args, **kwargs)


# pylint: enable=invalid-name
