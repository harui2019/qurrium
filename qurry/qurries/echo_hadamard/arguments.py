"""EchoListenHadamard - Arguments (:mod:`qurry.qurries.echo_hadamard.arguments`)"""

from typing import Any
from dataclasses import dataclass

from qiskit import QuantumCircuit

from ...qurrium import ArgumentsPrototype, BasicArgs, OutputArgs, WCKeyable


@dataclass(frozen=True)
class ELHArguments(ArgumentsPrototype):
    """Arguments for :class:`~qurry.qurries.echo_hadamard.experiment.ELHExperiment`."""

    exp_name: str
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    degree: tuple[int, int]
    """The degree range."""

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw read dictionary.
        """

        return cls(exp_name=raw_dict["exp_name"], degree=tuple(raw_dict["degree"]))


class ELHMeasureArgs(BasicArgs, total=False):
    """Input fields for
    :meth:`~qurry.qurries.echo_hadamard.qurry.EchoListenHadamard.measure`
    and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`."""

    wave1: QuantumCircuit | WCKeyable
    """The key or the circuit to execute."""
    wave2: QuantumCircuit | WCKeyable
    """The key or the circuit to execute."""
    degree: int | tuple[int, int] | None
    """The degree range."""


class ELHOutputArgs(OutputArgs):
    """Output arguments for
    :meth:`~qurry.qurries.echo_hadamard.qurry.EchoListenHadamard.output`."""

    degree: int | tuple[int, int] | None
    """The degree range."""


SHORT_NAME = "echo_hadamard"
"""The short name of :class:`~qurry.qurries.echo_hadamard.qurry.EchoListenHadamard`."""

ACRONYM = "ELH"
"""The abbreviation of :class:`~qurry.qurries.echo_hadamard.qurry.EchoListenHadamard`."""
