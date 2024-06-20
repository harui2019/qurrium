"""
================================================================
Qurrech - Wave Function Overlap
(:mod:`qurry.qurrech`)
================================================================

"""
from typing import Literal, Union, overload

from .hadamard_test import EchoHadamardTest
from .randomized_measure import EchoRandomizedListen


# pylint: disable=invalid-name
@overload
def EchoListen(*args, method: Literal["hadamard"], **kwargs) -> EchoHadamardTest:
    ...


@overload
def EchoListen(
    *args, method: Union[Literal["randomized", "base"], str] = "randomized", **kwargs
) -> EchoRandomizedListen:
    ...


def EchoListen(
    *args,
    method="randomized",
    **kwargs,
):
    """Call `EchoListen` methods.

    Args:
        method (Literal[&#39;randomized&#39;, &#39;hadamard&#39], optional):

            - randomized: running by haar randomized measure.
            - hadamard: running by hadamard test.
            Defaults to 'randomized'.

    Returns:
        EchoListenBase: method.
    """
    if method == "hadamard":
        return EchoHadamardTest(*args, **kwargs)
    return EchoRandomizedListen(*args, **kwargs)


@overload
def WaveFunctionOverlap(*args, method: Literal["hadamard"], **kwargs) -> EchoHadamardTest:
    ...


@overload
def WaveFunctionOverlap(
    *args, method: Union[Literal["randomized", "base"], str] = "randomized", **kwargs
) -> EchoRandomizedListen:
    ...


def WaveFunctionOverlap(
    *args,
    method="randomized",
    **kwargs,
):
    """Call `WaveFunctionOverlap` methods, another name of `EchoListen`.

    Args:
        method (Literal[&#39;randomized&#39;, &#39;hadamard&#39], optional):

            - randomized: running by haar randomized measure.
            - hadamard: running by hadamard test.
            Defaults to 'randomized'.

    Returns:
        WaveFunctionOverlapBase: method.
    """
    if method == "hadamard":
        return EchoHadamardTest(*args, **kwargs)
    return EchoRandomizedListen(*args, **kwargs)
