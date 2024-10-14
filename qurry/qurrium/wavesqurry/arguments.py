"""
================================================================
WavesExecuter - Arguments 
(:mod:`qurry.qurrium.wavesqurry.arguments`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from typing import Optional, Union
from collections.abc import Hashable
from dataclasses import dataclass

from qiskit import QuantumCircuit

from ..experiment import ArgumentsPrototype
from ...declare import BasicArgs


@dataclass(frozen=True)
class WavesExecuterArguments(ArgumentsPrototype):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class."""


class WavesExecuterMeasureArgs(BasicArgs):
    """Output arguments for :meth:`output`."""

    waves: Optional[list[Union[QuantumCircuit, Hashable]]]


SHORT_NAME = "waves_executer"
"""The short name for this qurry instance."""
