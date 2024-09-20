"""
================================================================
Sampling Qurry - Arguments
(:mod:`qurry.qurrium.samplingqurry.arguments`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from ..experiment import ArgumentsPrototype
from ...declare import BasicOutputArgs


class QurryArguments(ArgumentsPrototype):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class."""

    sampling: int = 1


class QurryOutputArgs(BasicOutputArgs):
    """Output arguments for :meth:`output`."""

    sampling: int
