"""Qurries - All Qurrium Runtime Realization (:mod:`qurry.qurries`)

.. tip::

    1.  The name "qurrent" was the second proposed name for this package.
        It's not simply "current" with a "q" replacing the "c",
        but rather a combination of "qurr" and "ent", where "ent" abbreviates "entropy",
        and "qurr" is a coined prefix beginning with "qu" to imply "quantum".

    2.  The initial proposed name for the package was "xproc", short for "experimental process".

    3.  Another module, which has been merged, "qurrech", combines "qurr" with "ech",
        where "ech" is short for "echo",
        the Loschmidt echo being a key concept in quantum information theory.
        This inspired us to adopt "qurry", derived from "qurr" and the suffix "ry",
        to resemble words like "query" or "curry".

    4.  Since a package named "qurry" already exists on PyPI,
        and many projects on GitHub also use this name,
        we changed the suffix from "y" to "ium", creating "qurrium".
        "Qurrium" is unique and easily searchable,
        with no prior use on PyPI or in general web searches.

    5.  So there is the evolution of the package name:
        xproc -> qurrent -> qurry -> qurrium

    6. Emoji: Qurry 🍛 / Qurrium 📏

.. tip::

    How to name a new Qurrium Runtime Realization:

    - For the short name of a new Qurrium Runtime, please follow the rules below:
        1.  Use a descriptive short name that clearly indicates the realization's function.
            For example:
            - "entropy_randomized" for "entropy" "randomized measure"
            - "echo_hadamard" for Loschmidt "echo" "hadamard test"
            - "wave_function_overlap" for "wave function" "overlap", the another name of "echo"
            - "classical_shadow" for classical shadow realizations.
        2.  Use lowercase letters and separate words with underscores (_).
        3.  Ensure the short name is unique within the Qurrium framework to avoid conflicts.
        4.  Use this short name as the module name in the `qurry.qurries` package.

    - For the :class:`~qurrium.qurrium.QurriumPrototype` subclass name,
        please follow the rules below:
        1.  Use a descriptive name that clearly indicates the realization's function.
            It's better for a combination of two words that reflect the purpose.
            In particular, a noun followed by a verb or gerund is preferred.
            For example:
            - "EntropyMeasure" for "entropy" "measure"
            - "EchoListen" for Loschmidt "echo" "listen"
                (Although it's just a name, not real sound here.)
            - "WaveFunctionOverlap" for "wave function" "overlap", the another name of "EchoListen"
            - "ShadowUnveil" for classical shadow realizations. (Unveil the classical shadow.)
        2.  Capitalize the first letter of each word in the name (CamelCase).
        3.  Ensure the name is unique within the Qurrium framework to avoid conflicts.

"""

from typing import Literal, overload

from .entropy_randomized import EntropyMeasureRandomized, EMRMeasureArgs
from .entropy_hadamard import EntropyMeasureHadamard, EMHMeasureArgs
from .echo_hadamard import EchoListenHadamard, ELHMeasureArgs
from .echo_randomized import EchoListenRandomized, ELRMeasureArgs
from .samplingqurry import SamplingExecuter, SEMeasureArgs
from .wavesqurry import WavesExecuter, WEMeasureArgs
from .magnet_square import MagnetSquare, MSMeasureArgs
from .magnet_square_z import ZDirMagnetSquare, ZMSMeasureArgs
from .string_operator import StringOperator, SOMeasureArgs
from .classical_shadow import ShadowUnveil, SUMeasureArgs

# from .twisted_operator import TwistedOperator
# from .position_distribution import PositionDistribution


# pylint: disable=invalid-name
@overload
def EntropyMeasure(method: Literal["hadamard"]) -> EntropyMeasureHadamard: ...
@overload
def EntropyMeasure(method: Literal["randomized"] = "randomized") -> EntropyMeasureRandomized: ...


def EntropyMeasure(method="randomized"):
    """Call :func:`EntropyMeasure` methods.

    Args:
        method (Literal["randomized", "hadamard"], optional):
            The method to use for entropy measurement.

            - randomized: running by haar randomized measure.
            - hadamard: running by hadamard test.

            Defaults to 'randomized'.
    """
    if method == "hadamard":
        return EntropyMeasureHadamard()
    return EntropyMeasureRandomized()


@overload
def EchoListen(method: Literal["hadamard"]) -> EchoListenHadamard: ...
@overload
def EchoListen(method: Literal["randomized"] = "randomized") -> EchoListenRandomized: ...


def EchoListen(method="randomized"):
    """Call :func:`EchoListen` methods.

    Args:
        method (Literal["randomized", "hadamard"], optional):
            The method to use for wave function overlap measurement.

            - randomized: running by haar randomized measure.
            - hadamard: running by hadamard test.

            Defaults to 'randomized'.

    Returns:
        EchoListenBase: method.
    """
    if method == "hadamard":
        return EchoListenHadamard()
    return EchoListenRandomized()


@overload
def WaveFunctionOverlap(method: Literal["hadamard"]) -> EchoListenHadamard: ...
@overload
def WaveFunctionOverlap(method: Literal["randomized"] = "randomized") -> EchoListenRandomized: ...


def WaveFunctionOverlap(method="randomized"):
    """Call :func:`WaveFunctionOverlap` methods, another name of :func:`EchoListen`.

    Args:
        method (Literal["randomized", "hadamard"], optional):
            The method to use for wave function overlap measurement.

            - randomized: running by haar randomized measure.
            - hadamard: running by hadamard test.

            Defaults to 'randomized'.

    Returns:
        WaveFunctionOverlapBase: method.
    """
    if method == "hadamard":
        return EchoListenHadamard()
    return EchoListenRandomized()


__all__ = [
    "EntropyMeasureRandomized",
    "EntropyMeasureHadamard",
    "EntropyMeasure",
    "EchoListenHadamard",
    "EchoListenRandomized",
    "EchoListen",
    "WaveFunctionOverlap",
    "SamplingExecuter",
    "WavesExecuter",
    "MagnetSquare",
    "ZDirMagnetSquare",
    "StringOperator",
    "ShadowUnveil",
    "EMRMeasureArgs",
    "EMHMeasureArgs",
    "ELHMeasureArgs",
    "ELRMeasureArgs",
    "SEMeasureArgs",
    "WEMeasureArgs",
    "MSMeasureArgs",
    "ZMSMeasureArgs",
    "SOMeasureArgs",
    "SUMeasureArgs",
]
