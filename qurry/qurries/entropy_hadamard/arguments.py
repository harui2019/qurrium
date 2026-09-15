"""EntropyMeasureHadamard - Arguments (:mod:`qurry.qurries.entropy_hadamard.arguments`)"""

from typing import Any
from dataclasses import dataclass

from qiskit import QuantumCircuit

from ...qurrium import ArgumentsPrototype, BasicArgs, OutputArgs, WCKeyable


@dataclass(frozen=True)
class EMHArguments(ArgumentsPrototype):
    """Arguments for :class:`~qurry.qurries.entropy_hadamard.experiment.EMHExperiment`."""

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


class EMHMeasureArgs(BasicArgs, total=False):
    """Input fields for
    :meth:`~qurry.qurries.entropy_hadamard.qurry.EntropyMeasureHadamard.measure`
    and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`."""

    wave: QuantumCircuit | WCKeyable
    """The key or the circuit to execute."""
    degree: int | tuple[int, int] | None
    """The degree range."""


class EMHOutputArgs(OutputArgs):
    """Output arguments for
    :meth:`~qurry.qurries.entropy_hadamard.qurry.EntropyMeasureHadamard.output`."""

    degree: int | tuple[int, int] | None
    """The degree range."""


SHORT_NAME = "entropy_hadamard"
"""The short name of :class:`~qurry.qurries.entropy_hadamard.qurry.EntropyMeasureHadamard`."""

ACRONYM = "EMH"
"""The abbreviation of :class:`~qurry.qurries.entropy_hadamard.qurry.EntropyMeasureHadamard`."""
