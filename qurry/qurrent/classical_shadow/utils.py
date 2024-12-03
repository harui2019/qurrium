"""
===========================================================
ShadowUnveil - Utils
(:mod:`qurry.qurrent.classical_shadow.utils`)
===========================================================

"""

from collections.abc import Hashable

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from ...process.classical_shadow.unitary_set import U_M_GATES


def circuit_method_core(
    idx: int,
    target_circuit: QuantumCircuit,
    target_key: Hashable,
    exp_name: str,
    registers_mapping: dict[int, int],
    single_unitary_um: dict[int, int],
) -> QuantumCircuit:
    """Build the circuit for the experiment.

    Args:
        idx (int):
            Index of the quantum circuit.
        target_circuit (QuantumCircuit):
            Target circuit.
        target_key (Hashable):
            Target key.
        exp_name (str):
            Experiment name.
        registers_mapping (dict[int, int]):
            The mapping of the index of selected qubits to the index of the classical register.
        single_unitary_dict (dict[int, Operator]):
            The dictionary of the unitary operator.

    Returns:
        QuantumCircuit: The circuit for the experiment.
    """

    num_qubits = target_circuit.num_qubits
    old_name = "" if isinstance(target_circuit.name, str) else target_circuit.name

    q_func1 = QuantumRegister(num_qubits, "q1")
    c_meas1 = ClassicalRegister(len(registers_mapping), "c1")
    qc_exp1 = QuantumCircuit(q_func1, c_meas1)
    qc_exp1.name = (
        f"{exp_name}_{idx}" + ""
        if len(str(target_key)) < 1
        else f".{target_key}" + "" if len(old_name) < 1 else f".{old_name}"
    )

    # TODO: When tatget has more clbits or qubits than dest, it will raise an error.
    # See qiskit/circuit/quantumcircuit.py:1961
    # if other.num_qubits > dest.num_qubits or other.num_clbits > dest.num_clbits:
    qc_exp1.compose(target_circuit, [q_func1[i] for i in range(num_qubits)], inplace=True)

    qc_exp1.barrier()
    for qi, um in single_unitary_um.items():
        qc_exp1.append(U_M_GATES[um], [qi])

    for qi, ci in registers_mapping.items():
        qc_exp1.measure(q_func1[qi], c_meas1[ci])

    return qc_exp1
