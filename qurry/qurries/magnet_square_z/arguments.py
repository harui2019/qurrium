"""ZDirMagnetSquare - Arguments (:mod:`qurry.qurries.magnet_square_z.arguments`)"""

from dataclasses import dataclass

from qiskit import QuantumCircuit

from ...qurrium import ArgumentsPrototype, BasicArgs, OutputArgs, WCKeyable


@dataclass(frozen=True)
class ZMSArguments(ArgumentsPrototype):
    """Arguments for :class:`~qurry.qurries.magnet_square_z.experiment.ZMSExperiment`."""

    exp_name: str = "exps"
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    """
    num_qubits: int = 0
    """The number of qubits."""


class ZMSMeasureArgs(BasicArgs, total=False):
    """Input fields for
    :meth:`~qurry.qurries.magnet_square_z.qurry.ZDirMagnetSquare.measure`
    and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`."""

    wave: QuantumCircuit | WCKeyable
    """The key or the circuit to execute."""


class ZMSOutputArgs(OutputArgs):
    """Output arguments for
    :meth:`~qurry.qurries.magnet_square_z.qurry.ZDirMagnetSquare.output`."""


SHORT_NAME = "magnet_square_z"
"""The short name of :class:`~qurry.qurries.magnet_square_z.qurry.ZDirMagnetSquare`."""

ACRONYM = "ZMS"
"""The abbreviation of :class:`~qurry.qurries.magnet_square_z.qurry.ZDirMagnetSquare`."""
