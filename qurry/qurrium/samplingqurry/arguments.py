"""
================================================================
SamplingExecuter - Arguments
(:mod:`qurry.qurrium.samplingqurry.arguments`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from typing import Optional, Union
from collections.abc import Hashable
from dataclasses import dataclass

from qiskit import QuantumCircuit

from ..experiment import ArgumentsPrototype
from ...declare import BasicArgs, OutputArgs


@dataclass(frozen=True)
class QurryArguments(ArgumentsPrototype):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class."""

    sampling: int = 1
    """The number of sampling."""


class QurryMeasureArgs(BasicArgs):
    """Output arguments for :meth:`output`."""

    wave: Optional[Union[QuantumCircuit, Hashable]]
    """The key or the circuit to execute."""
    sampling: int
    """The number of sampling."""


class QurryOutputArgs(OutputArgs):
    """Output arguments for :meth:`output`."""

    sampling: int
    """The number of sampling."""


SHORT_NAME = "sampling_executer"
"""The short name for this qurry instance."""
