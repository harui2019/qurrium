"""
================================================================
WavesExecuter - Arguments 
(:mod:`qurry.qurrium.wavesqurry.arguments`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from dataclasses import dataclass

from ..experiment import ArgumentsPrototype
from ...declare import BasicOutputArgs


@dataclass(frozen=True)
class WavesExecuterArguments(ArgumentsPrototype):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class."""


class WavesExecuterOutputArgs(BasicOutputArgs):
    """Output arguments for :meth:`output`."""


SHORT_NAME = "waves_executer"
"""The short name for this qurry instance."""
