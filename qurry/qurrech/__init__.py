"""
================================================================
Qurrech - Wave Function Overlap
(:mod:`qurry.qurrech`)
================================================================

"""

from typing import Literal, Union, overload

from .hadamard_test import EchoListenHadamard
from .randomized_measure import EchoListenRandomized


# pylint: disable=invalid-name
@overload
def EchoListen(*args, method: Literal["hadamard"], **kwargs) -> EchoListenHadamard: ...


@overload
def EchoListen(
    *args, method: Union[Literal["randomized", "base"], str] = "randomized", **kwargs
) -> EchoListenRandomized: ...


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
        return EchoListenHadamard(*args, **kwargs)
    return EchoListenRandomized(*args, **kwargs)


@overload
def WaveFunctionOverlap(*args, method: Literal["hadamard"], **kwargs) -> EchoListenHadamard: ...


@overload
def WaveFunctionOverlap(
    *args, method: Union[Literal["randomized", "base"], str] = "randomized", **kwargs
) -> EchoListenRandomized: ...


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
        return EchoListenHadamard(*args, **kwargs)
    return EchoListenRandomized(*args, **kwargs)
