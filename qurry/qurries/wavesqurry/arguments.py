"""WavesExecuter - Arguments (:mod:`qurry.qurries.wavesqurry.arguments`)"""

from dataclasses import dataclass

from qiskit import QuantumCircuit

from ...qurrium import ArgumentsPrototype, BasicArgs, OutputArgs, WCKeyable


@dataclass(frozen=True)
class WEArguments(ArgumentsPrototype):
    """Arguments for :class:`~qurry.qurries.wavesqurry.experiment.WEExperiment`."""


class WEMeasureArgs(BasicArgs, total=False):
    """Input fields for
    :meth:`~qurry.qurries.wavesqurry.qurry.WavesExecuter.measure`
    and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`."""

    waves: list[QuantumCircuit | WCKeyable]
    """The keys or the circuits to execute."""


class WEOutputArgs(OutputArgs):
    """Output arguments for :meth:`qurry.qurries.wavesqurry.qurry.WavesExecuter.output`."""


SHORT_NAME = "waves_executer"
"""The short name of :class:`~qurry.qurries.wavesqurry.qurry.WavesExecuter`."""
ACRONYM = "WE"
"""The abbreviation of :class:`~qurry.qurries.wavesqurry.qurry.WavesExecuter`."""
