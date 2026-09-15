"""ZDirMagnetSquare - Utility (:mod:`qurry.qurries.magnet_square_z.utils`)"""

from qiskit import QuantumCircuit, ClassicalRegister

from ...qurrium import WCKeyable, naming_circuit


DEFAULT_CLASSICAL_REGISTER_NAME = "m0"
"""The default name for classical register used for measurement."""


def circuit_method(
    target_circuit: QuantumCircuit, target_key: WCKeyable, exp_name: str
) -> QuantumCircuit:
    """Build the circuit for the experiment.

    Args:
        target_circuit (QuantumCircuit): Target circuit.
        target_key (WCKeyable): Target key.
        exp_name (str): Experiment name.

    Returns:
        QuantumCircuit: The circuit for the experiment.
    """

    qc_exp1 = target_circuit.copy(naming_circuit(target_circuit, target_key, f"{exp_name}_zdir"))
    c_meas1 = ClassicalRegister(qc_exp1.num_qubits, DEFAULT_CLASSICAL_REGISTER_NAME)
    qc_exp1.add_register(c_meas1)
    qc_exp1.barrier()
    qc_exp1.measure(qc_exp1.qubits, c_meas1)

    return qc_exp1
