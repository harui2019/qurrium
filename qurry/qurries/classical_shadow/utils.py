"""ShadowUnveil - Utils (:mod:`qurry.qurries.classical_shadow.utils`)"""

from typing import Literal
from collections.abc import Iterable
from qiskit import QuantumCircuit, ClassicalRegister

from ...qurrium import WCKeyable, naming_circuit
from ...process.classical_shadow import ShadowRandomBasis, convert_to_basis_spin


DEFAULT_CLASSICAL_REGISTER_NAME = "m0"
"""The default name for classical register used for measurement."""


def make_samplied_circuit(
    idx: int,
    target_circuit: QuantumCircuit,
    target_key: WCKeyable,
    exp_name: str,
    registers_mapping: dict[int, int],
    single_random_basis: dict[int, int],
    shadow_basis: ShadowRandomBasis,
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
        single_random_basis (dict[int, int]):
            The single random basis for each qubit.
        shadow_basis (ShadowRandomBasis):
            The shadow random basis.

    Returns:
        QuantumCircuit: The circuit for the experiment.
    """
    if not isinstance(shadow_basis, ShadowRandomBasis):
        raise TypeError(
            "The shadow_basis should be an instance of ShadowRandomBasis, "
            + f"but get {type(shadow_basis)}"
        )

    qc_exp1 = target_circuit.copy(naming_circuit(target_circuit, target_key, f"{exp_name}_{idx}"))
    c_meas1 = ClassicalRegister(len(registers_mapping), DEFAULT_CLASSICAL_REGISTER_NAME)
    qc_exp1.add_register(c_meas1)

    qc_exp1.barrier()

    for qi, um in single_random_basis.items():
        for g in shadow_basis.gates_tuple[um]:
            qc_exp1.append(g.copy(), [qi])

    for qi, ci in registers_mapping.items():
        qc_exp1.measure(qc_exp1.qubits[qi], c_meas1[ci])

    assert qc_exp1.cregs[-1] == c_meas1, (
        f"The last classical register should be the measurement register {c_meas1},"
        + f" but get {qc_exp1.cregs[-1]} in {qc_exp1.cregs}. From {exp_name} on index {idx}."
    )

    return qc_exp1


def get_random_basis_array(
    registers_mapping: dict[int, int],
    random_basis: dict[int, dict[int, int]],
    counts_used: Iterable[int] | None = None,
) -> list[list[Literal[0, 1, 2] | int]]:
    """Get the random basis array from the random basis,
    register mapping, and counts used.

    The random basis follow normal register mapping
    for it does not need to consider extra classical registers
    but effect by count_used.

    Args:
        registers_mapping (dict[int, int]):
            The mapping of the classical registers of measurement with quantum registers.
        random_basis (dict[int, dict[int, int]]):
            The random basis mapping.
        counts_used (Iterable[int] | None, optional):
            The counts used. Defaults to None.

    Returns:
        The random basis array.
    """
    all_clregs = sorted(registers_mapping.values())

    random_basis_array: list[list[Literal[0, 1, 2] | int]] = []
    for i in range(len(random_basis) if counts_used is None else max(counts_used) + 1):
        tmp = {ci: random_basis[i][n_u_qi] for n_u_qi, ci in registers_mapping.items()}
        random_basis_array.append([tmp[j] for j in all_clregs])

    return random_basis_array


def get_basis_spin(
    shots: int,
    counts: list[dict[str, int]],
    registers_mapping: dict[int, int],
    random_basis: dict[int, dict[int, int]],
    counts_used: Iterable[int] | None = None,
) -> tuple[list[list[int]], list[list[int]]]:
    """Convert the random basis to basis-spin format,
    which uses in `Predicting Properties of Quantum Many-Body Systems
    <https://github.com/hsinyuan-huang/predicting-quantum-properties>`_ .

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The counts from the experiment.
        registers_mapping (dict[int, int]):
            The mapping of the classical registers of measurement with quantum registers.
        random_basis (dict[int, dict[int, int]]):
            The random basis mapping.
        counts_used (Iterable[int] | None, optional):
            The counts used. Defaults to None.

    Returns:
        A tuple containing a list of pauli basis and a list of spin outcomes.
    """

    return convert_to_basis_spin(
        shots, counts, get_random_basis_array(registers_mapping, random_basis, counts_used)
    )
