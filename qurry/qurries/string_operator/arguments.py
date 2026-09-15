"""StringOperator - Arguments (:mod:`qurry.qurries.string_operator.arguments`)"""

from dataclasses import dataclass

from qiskit import QuantumCircuit

from .utils import StringOperatorLibType, StringOperatorDirection
from ...qurrium import ArgumentsPrototype, BasicArgs, OutputArgs, WCKeyable


@dataclass(frozen=True)
class SOArguments(ArgumentsPrototype):
    """Arguments for
    :class:`~qurry.qurries.string_operator.experiment.SOExperiment`."""

    exp_name: str
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    num_qubits: int
    """The number of qubits."""
    i: int
    """The index of beginning qubits in the quantum circuit."""
    k: int
    """The index of ending qubits in the quantum circuit."""
    str_op: StringOperatorLibType = "i"
    """The string operator."""
    on_dir: StringOperatorDirection = "x"
    """The direction of the string operator, either 'x' or 'y'."""


class SOMeasureArgs(BasicArgs, total=False):
    """Input fields for
    :meth:`~qurry.qurries.string_operator.qurry.StringOperator.measure`
    and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`."""

    wave: QuantumCircuit | WCKeyable
    """The key or the circuit to execute."""
    i: int | None
    """The index of beginning qubits in the quantum circuit."""
    k: int | None
    """The index of ending qubits in the quantum circuit."""
    str_op: StringOperatorLibType
    """The string operator."""
    on_dir: StringOperatorDirection
    """The direction of the string operator, either 'x' or 'y'."""


class SOOutputArgs(OutputArgs):
    """Output arguments for
    :meth:`~qurry.qurries.string_operator.qurry.StringOperator.output`."""

    i: int | None
    """The index of beginning qubits in the quantum circuit."""
    k: int | None
    """The index of ending qubits in the quantum circuit."""
    str_op: StringOperatorLibType
    """The string operator."""
    on_dir: StringOperatorDirection
    """The direction of the string operator, either 'x' or 'y'."""


SHORT_NAME = "string_operator"
"""The short name of :class:`~qurry.qurries.string_operator.qurry.StringOperator`."""

ACRONYM = "SO"
"""The abbreviation of :class:`~qurry.qurries.string_operator.qurry.StringOperator`."""
