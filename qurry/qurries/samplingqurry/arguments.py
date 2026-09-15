"""SamplingExecuter - Arguments (:mod:`qurry.qurries.samplingqurry.arguments`)"""

from dataclasses import dataclass

from qiskit import QuantumCircuit

from ...qurrium import ArgumentsPrototype, BasicArgs, OutputArgs, WCKeyable


@dataclass(frozen=True)
class SEArguments(ArgumentsPrototype):
    """Arguments for :class:`~qurry.qurries.samplingqurry.experiment.SEExperiment`."""

    sampling: int = 1
    """The number of sampling."""


class SEMeasureArgs(BasicArgs, total=False):
    """Input fields for
    :meth:`~qurry.qurries.samplingqurry.qurry.QurryV14.measure`
    and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`."""

    wave: QuantumCircuit | WCKeyable
    """The key or the circuit to execute."""
    sampling: int
    """The number of sampling."""


class SEOutputArgs(OutputArgs):
    """Output arguments for :meth:`~qurry.qurries.samplingqurry.qurry.QurryV14.output`."""

    sampling: int
    """The number of sampling."""


SHORT_NAME = "sampling_executer"
"""The short name of :class:`~qurry.qurries.samplingqurry.qurry.QurryV14`."""
ACRONYM = "SE"
"""The abbreviation of :class:`~qurry.qurries.samplingqurry.qurry.QurryV14`."""
