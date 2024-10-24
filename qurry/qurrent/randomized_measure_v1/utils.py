"""
===========================================================
EntropyMeasureRandomizedV1 - Utility
(:mod:`qurry.qurrent.randomized_measure_v1.utils`)
===========================================================

"""

from typing import Union, Optional
from collections.abc import Hashable
import tqdm

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator


from .analysis import EntropyMeasureRandomizedV1Analysis
from ...process.randomized_measure.entangled_entropy_v1 import (
    randomized_entangled_entropy_mitigated_deprecated as randomized_entangled_entropy_mitigated,
    RandomizedEntangledEntropyMitigatedComplex,
    ExistingAllSystemSource,
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)


def randomized_entangled_entropy_complex(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    all_system_source: Optional[EntropyMeasureRandomizedV1Analysis] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: Optional[int] = None,
    pbar: Optional[tqdm.tqdm] = None,
) -> RandomizedEntangledEntropyMitigatedComplex:
    """Randomized entangled entropy with complex.

    Args:
        shots (int): The number of shots.
        counts (list[dict[str, int]]): The counts of the experiment.
        degree (Optional[Union[tuple[int, int], int]]): The degree of the experiment.
        measure (Optional[tuple[int, int]], optional): The measure range. Defaults to None.
        all_system_source (Optional[EntropyRandomizedAnalysis], optional):
            The source of all system. Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            The backend label. Defaults to DEFAULT_PROCESS_BACKEND.
        workers_num (Optional[int], optional): The number of workers. Defaults to None.
        pbar (Optional[tqdm.tqdm], optional): The progress bar. Defaults to None.

    Returns:
        RandomizedEntangledEntropyMitigatedComplex: The result of the experiment.
    """

    if all_system_source is not None:
        source = str(all_system_source.header)
        assert (
            all_system_source.content.purityCellsAllSys is not None
        ), f"purityCellsAllSys of {source} is None"
        assert (
            all_system_source.content.bitStringRange is not None
        ), f"bitStringRange of {source} is None"
        assert (
            all_system_source.content.measureActually is not None
        ), f"measureActually of {source} is None"

        existed_all_system: Optional[ExistingAllSystemSource] = {
            "bitStringRange": all_system_source.content.bitStringRange,
            "measureActually": all_system_source.content.measureActually,
            "purityCellsAllSys": all_system_source.content.purityCellsAllSys,
            "source": source,
        }
    else:
        existed_all_system = None

    return randomized_entangled_entropy_mitigated(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        backend=backend,
        workers_num=workers_num,
        existed_all_system=existed_all_system,
        pbar=pbar,
    )


def circuit_method_core(
    idx: int,
    target_circuit: QuantumCircuit,
    target_key: Hashable,
    exp_name: str,
    unitary_loc: tuple[int, int],
    unitary_sublist: dict[int, Operator],
    measure: tuple[int, int],
) -> QuantumCircuit:
    """Build the circuit for the experiment.

    Args:
        idx (int): Index of the randomized unitary.
        target_circuit (QuantumCircuit): Target circuit.
        target_key (Hashable): Target key.
        exp_name (str): Experiment name.
        unitary_loc (tuple[int, int]): Unitary operator location.
        unitary_sublist (dict[int, Operator]): Unitary operator list.
        measure (tuple[int, int]): Measure range.

    Returns:
        QuantumCircuit: The circuit for the experiment.
    """

    num_qubits = target_circuit.num_qubits
    old_name = "" if isinstance(target_circuit.name, str) else target_circuit.name

    q_func1 = QuantumRegister(num_qubits, "q1")
    c_meas1 = ClassicalRegister(measure[1] - measure[0], "c1")
    qc_exp1 = QuantumCircuit(q_func1, c_meas1)
    qc_exp1.name = (
        f"{exp_name}_{idx}" + ""
        if len(str(target_key)) < 1
        else f".{target_key}" + "" if len(old_name) < 1 else f".{old_name}"
    )

    qc_exp1.compose(target_circuit, [q_func1[i] for i in range(num_qubits)], inplace=True)

    qc_exp1.barrier()
    for j in range(*unitary_loc):
        qc_exp1.append(unitary_sublist[j].to_instruction(), [j])

    for j in range(*measure):
        qc_exp1.measure(q_func1[j], c_meas1[j - measure[0]])

    return qc_exp1
