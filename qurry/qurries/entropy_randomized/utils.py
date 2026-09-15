"""EntropyMeasureRandomized - Utility (:mod:`qurry.qurries.entropy_randomized.utils`)"""

from qiskit import QuantumCircuit, ClassicalRegister
from qiskit.quantum_info import Operator

from .arguments import EMRArguments
from .tales import RandomizedMeasureTales
from ...qurrium import WCKeyable, naming_circuit
from ...process.randomized_measure import generate_random_unitary


DEFAULT_CLASSICAL_REGISTER_NAME = "m0"
"""The default name for classical register used for measurement."""


def make_samplied_circuit(
    idx: int,
    target_circuit: QuantumCircuit,
    target_key: WCKeyable,
    exp_name: str,
    registers_mapping: dict[int, int],
    single_unitary_dict: dict[int, Operator],
) -> QuantumCircuit:
    """Build the circuit for the experiment.

    Args:
        idx (int):
            Index of the quantum circuit.
        target_circuit (QuantumCircuit):
            Target circuit.
        target_key (WCKeyable):
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

    qc_exp1 = target_circuit.copy(naming_circuit(target_circuit, target_key, f"{exp_name}_{idx}"))
    c_meas1 = ClassicalRegister(len(registers_mapping), DEFAULT_CLASSICAL_REGISTER_NAME)
    qc_exp1.add_register(c_meas1)

    qc_exp1.barrier()

    for qi, operator in single_unitary_dict.items():
        qc_exp1.append(operator.to_instruction(), [qi])

    for qi, ci in registers_mapping.items():
        qc_exp1.measure(qc_exp1.qubits[qi], c_meas1[ci])

    assert qc_exp1.cregs[-1] == c_meas1, (
        f"The last classical register should be the measurement register {c_meas1},"
        + f" but get {qc_exp1.cregs[-1]} in {qc_exp1.cregs}. From {exp_name} on index {idx}."
    )

    return qc_exp1


def method_process(
    targets: list[tuple[WCKeyable, QuantumCircuit]],
    arguments: EMRArguments,
) -> tuple[list[QuantumCircuit], RandomizedMeasureTales]:
    """The process method for building the circuits of the experiment.

    Args:
        targets (list[tuple[WCKeyable, QuantumCircuit]]):
            The circuits of the experiment.
        arguments (EMRArguments):
            The arguments of the experiment.

    Returns:
        A tuple containing a list of quantum circuits and a dictionary of additional information.
    """

    target_key, target_circuit = targets[0]
    target_key = target_key if isinstance(target_key, int) else str(target_key)

    unitary_dicts = generate_random_unitary(
        times=arguments.times,
        unitary_located=arguments.unitary_located,
        random_unitary_seeds=arguments.random_unitary_seeds,
    )

    return [
        make_samplied_circuit(
            n_u_i,
            target_circuit,
            target_key,
            arguments.exp_name,
            arguments.registers_mapping,
            unitary_dicts[n_u_i],
        )
        for n_u_i in range(arguments.times)
    ], RandomizedMeasureTales.make(unitary_dicts)
