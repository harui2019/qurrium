"""
===========================================================
EntropyMeasureRandomized - Utility
(:mod:`qurry.qurrent.randomized_measure.utils`)
===========================================================

"""

from typing import Optional
from collections.abc import Hashable
import tqdm

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator


from .analysis import EntropyMeasureRandomizedAnalysis
from ...process.randomized_measure.entangled_entropy import (
    randomized_entangled_entropy_mitigated,
    EntangledEntropyResultMitigated,
    ExistedAllSystemInfo,
    ExistedAllSystemInfoInput,
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)


def randomized_entangled_entropy_complex(
    shots: int,
    counts: list[dict[str, int]],
    selected_classical_registers: Optional[list[int]] = None,
    all_system_source: Optional[EntropyMeasureRandomizedAnalysis] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: Optional[tqdm.tqdm] = None,
) -> EntangledEntropyResultMitigated:
    """Randomized entangled entropy with complex.

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The counts of the experiment.
        selected_classical_registers (Optional[list[int]], optional):
            The selected classical registers. Defaults to None.
        all_system_source (Optional[EntropyRandomizedAnalysis], optional):
            The source of all system. Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            The backend label. Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (Optional[tqdm.tqdm], optional):
            The progress bar. Defaults to None.

    Returns:
        EntangledEntropyResultMitigated: The result of the entangled entropy.
    """

    if all_system_source is None:
        existed_all_system = None
    elif isinstance(all_system_source, EntropyMeasureRandomizedAnalysis):
        checked_input: ExistedAllSystemInfoInput = {}
        for k in ExistedAllSystemInfo._fields:
            checked_input[k] = (
                str(all_system_source.header)
                if k == "source"
                else getattr(all_system_source.content, k)
            )

        existed_all_system = ExistedAllSystemInfo(**checked_input)
    else:
        raise ValueError(
            "all_system_source should be None or EntropyMeasureRandomizedAnalysis, "
            + f"but get {type(all_system_source)}."
        )

    return randomized_entangled_entropy_mitigated(
        shots=shots,
        counts=counts,
        selected_classical_registers=selected_classical_registers,
        backend=backend,
        existed_all_system=existed_all_system,
        pbar=pbar,
    )


def circuit_method_core(
    idx: int,
    target_circuit: QuantumCircuit,
    target_key: Hashable,
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
    for qj, opertor in single_unitary_dict.items():
        qc_exp1.append(opertor.to_instruction(), [qj])

    for qi, ci in registers_mapping.items():
        qc_exp1.measure(q_func1[qi], c_meas1[ci])

    return qc_exp1
