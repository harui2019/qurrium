"""Magnetic Square - Utility (:mod:`qurry.qurries.magnet_square.utils`)"""

from typing import Literal

from qiskit import QuantumCircuit, ClassicalRegister
from qiskit.circuit import Gate
from qiskit.quantum_info import Operator

from ...qurrium import WCKeyable, naming_circuit

DEFAULT_CLASSICAL_REGISTER_NAME = "m0"
"""The default name for classical register used for measurement."""


def circuit_method(
    idx: int,
    target_circuit: QuantumCircuit,
    target_key: WCKeyable,
    exp_name: str,
    unitary_operator: Operator | Gate | Literal["x", "y", "z"],
    i: int,
    j: int,
) -> QuantumCircuit:
    """Build the circuit for the experiment.

    Args:
        idx (int): Index of the quantum circuit.
        target_circuit (QuantumCircuit): Target circuit.
        target_key (WCKeyable): Target key.
        exp_name (str): Experiment name.
        unitary_operator (Operator | Gate | Literal["x", "y", "z"]):
            The unitary operator to apply.
            It can be a `qiskit.quantum_info.Operator`, a `qiskit.circuit.Gate`, or a string
            representing the axis of rotation ('x', 'y', or 'z').
        i (int): The index of the target qubit.
        j (int): The index of the target qubit.

    Returns:
        QuantumCircuit: The circuit for the experiment.
    """

    qc_exp1 = target_circuit.copy(
        naming_circuit(target_circuit, target_key, f"{exp_name}_{idx}_{i}_{j}")
    )
    c_meas1 = ClassicalRegister(2, DEFAULT_CLASSICAL_REGISTER_NAME)
    qc_exp1.add_register(c_meas1)

    qc_exp1.barrier()

    if isinstance(unitary_operator, Operator):
        qc_exp1.unitary(unitary_operator, [qc_exp1.qubits[i]], label="U")
        qc_exp1.unitary(unitary_operator, [qc_exp1.qubits[j]], label="U")
    elif isinstance(unitary_operator, Gate):
        qc_exp1.append(unitary_operator, [qc_exp1.qubits[i]])
        qc_exp1.append(unitary_operator, [qc_exp1.qubits[j]])
    elif unitary_operator == "x":
        qc_exp1.x(qc_exp1.qubits[i])
        qc_exp1.x(qc_exp1.qubits[j])
    elif unitary_operator == "y":
        qc_exp1.y(qc_exp1.qubits[i])
        qc_exp1.y(qc_exp1.qubits[j])
    elif unitary_operator == "z":
        ...
    else:
        raise ValueError(
            f"Invalid unitary operator: {unitary_operator}. "
            "It should be an Operator, Gate, or one of 'x', 'y', 'z'."
        )

    qc_exp1.measure(qc_exp1.qubits[i], c_meas1[0])
    qc_exp1.measure(qc_exp1.qubits[j], c_meas1[1])

    return qc_exp1
