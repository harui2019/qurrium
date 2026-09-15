"""MagnetSquare - Arguments (:mod:`qurry.qurries.magnet_square.arguments`)"""

from typing import Literal, Any
from dataclasses import dataclass
import numpy as np

from qiskit.circuit import Gate
from qiskit.quantum_info import Operator

from ..magnet_square_z.arguments import ZMSArguments, ZMSMeasureArgs, ZMSOutputArgs


@dataclass(frozen=True)
class MSArguments(ZMSArguments):
    """Arguments for :class:`~qurry.qurries.magnet_square.experiment.MSExperiment`."""

    unitary_operator: Operator | Gate | Literal["x", "y", "z"] = "z"
    """The unitary operator to apply.
    It can be a :class:`~qiskit.quantum_info.Operator`,
    a :class:`~qiskit.circuit.Gate`, or a string
    representing the axis of rotation ('x', 'y', or 'z'). 
    Defaults to 'z'."""

    def export(self):
        """Export the arguments to a dictionary.

        Returns:
            dict[str, Any]: The exported dictionary.
        """
        unitary_operator_converted = (
            self.unitary_operator
            if isinstance(self.unitary_operator, str)
            else np.array(self.unitary_operator, dtype=np.complex128)
        )
        unitary_operator_converted = np.array(unitary_operator_converted, dtype=str).tolist()

        return {
            "exp_name": self.exp_name,
            "num_qubits": self.num_qubits,
            "unitary_operator": unitary_operator_converted,
        }

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Ingest the arguments from a dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw dictionary.

        Returns:
            MSArguments: The ingested arguments.
        """
        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {missing_fields}")

        unitary_operator = raw_dict["unitary_operator"]
        if isinstance(unitary_operator, list):
            unitary_operator = Operator(np.array(unitary_operator, dtype=np.complex128))
        elif unitary_operator not in {"x", "y", "z"}:
            raise TypeError(
                "unitary_operator must be of type 'list' or the string 'x', 'y', 'z'. "
                + f"Got {type(unitary_operator)} instead."
            )
        unitary_operator: Operator | Literal["x", "y", "z"]

        return cls(
            exp_name=raw_dict["exp_name"],
            num_qubits=raw_dict["num_qubits"],
            unitary_operator=unitary_operator,
        )


class MSMeasureArgs(ZMSMeasureArgs, total=False):
    """Input fields for
    :meth:`~qurry.qurries.magnet_square.qurry.MagnetSquare.measure`
    and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`."""

    unitary_operator: Operator | Gate | Literal["x", "y", "z"]
    """The unitary operator to apply.
    It can be a :class:`~qiskit.quantum_info.Operator`,
    a :class:`~qiskit.circuit.Gate`, or a string
    representing the axis of rotation ('x', 'y', or 'z'). 
    Defaults to 'z'."""


class MSOutputArgs(ZMSOutputArgs):
    """Output arguments for
    :meth:`~qurry.qurries.magnet_square.qurry.MagnetSquare.output`."""

    unitary_operator: Operator | Gate | Literal["x", "y", "z"]
    """The unitary operator to apply.
    It can be a :class:`~qiskit.quantum_info.Operator`,
    a :class:`~qiskit.circuit.Gate`, or a string
    representing the axis of rotation ('x', 'y', or 'z'). 
    Defaults to 'z'."""


SHORT_NAME = "magnet_square"
"""The short name of :class:`~qurry.qurries.magnet_square.qurry.MagnetSquare`."""

ACRONYM = "MS"
"""The acronym of :class:`~qurry.qurries.magnet_square.qurry.MagnetSquare`."""
