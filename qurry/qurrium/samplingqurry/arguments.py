"""
================================================================
SamplingExecuter - Arguments
(:mod:`qurry.qurrium.samplingqurry.arguments`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from dataclasses import dataclass

from ..experiment import ArgumentsPrototype
from ...declare import BasicArgs


@dataclass(frozen=True)
class QurryArguments(ArgumentsPrototype):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class."""

    sampling: int = 1


class QurryMeasureArgs(BasicArgs):
    """Output arguments for :meth:`output`."""

    sampling: int


SHORT_NAME = "sampling_executer"
"""The short name for this qurry instance."""
