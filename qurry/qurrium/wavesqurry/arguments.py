"""
================================================================
Waves Qurry - Arguments 
(:mod:`qurry.qurrium.wavesqurry.arguments`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from ..experiment import ArgumentsPrototype
from ...declare import BasicOutputArgs


class WavesQurryArguments(ArgumentsPrototype):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class."""


class WaveQurryOutputArgs(BasicOutputArgs):
    """Output arguments for :meth:`output`."""
