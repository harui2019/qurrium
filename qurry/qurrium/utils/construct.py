"""
================================================================
Construct (:mod:`qurry.qurrium.utils.construct`)
================================================================

"""
import warnings
from typing import Union, Hashable, Optional, Literal

from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.exceptions import QiskitError

from ...exceptions import QurryRustImportError, QurryCountLost

try:
    # from ...boorust.randomized import (  # type: ignore
    #     ensemble_cell_rust as ensemble_cell_rust_source,  # type: ignore
    #     hamming_distance_rust as hamming_distance_rust_source,  # type: ignore
    # )
    # from qurry.boorust.construct import (
    #     cycling_slice_rust as cycling_slice_rust_source,  # type: ignore
    # )
    from ...boorust import construct  # type: ignore

    qubit_selector_rust_source = construct.qubit_selector_rust  # type: ignore

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def qubit_selector_rust_source(*args, **kwargs):
        """Dummy function for cycling_slice_rust."""
        raise QurryRustImportError(
            "Rust is not available, using python to calculate cycling slice."
            + f" More infomation about this error: {FAILED_RUST_IMPORT}",
        )


ExistingProcessBackendLabel = Literal["Rust", "Python"]
BackendAvailabilities: dict[ExistingProcessBackendLabel, Union[bool, ImportError]] = {
    "Rust": RUST_AVAILABLE if RUST_AVAILABLE else FAILED_RUST_IMPORT,
    "Python": True,
}


def qubit_selector_rust(
    num_qubits: int,
    degree: Union[int, tuple[int, int], None] = None,
) -> tuple[int, int]:
    """Determint the qubits to be used.

    Args:
        num_qubits (int): Number of qubits.
        degree (Union[int, tuple[int, int], None], optional):
            Degree of freedom or specific subsystem range.
            Defaults to None then will use number of qubits as degree.

    Raises:
        ValueError: The specific degree of subsystem qubits
            beyond number of qubits which the wave function has.
        ValueError: The number of qubits of subsystem A is not a natural number.
        ValueError: Invalid input for subsystem range defined by only two integers.
        ValueError: Degree of freedom is not given.

    Returns:
        tuple[int]: The range of qubits to be used.
    """
    return qubit_selector_rust_source(num_qubits, degree)


def qubit_selector(
    num_qubits: int,
    degree: Union[int, tuple[int, int], None] = None,
) -> tuple[int, int]:
    """Determint the qubits to be used.

    Args:
        num_qubits (int): Number of qubits.
        degree (Union[int, tuple[int, int], None], optional):
            Degree of freedom or specific subsystem range.
            Defaults to None then will use number of qubits as degree.

    Raises:
        ValueError: The specific degree of subsystem qubits
            beyond number of qubits which the wave function has.
        ValueError: The number of qubits of subsystem A is not a natural number.
        ValueError: Invalid input for subsystem range defined by only two integers.
        ValueError: Degree of freedom is not given.

    Returns:
        tuple[int]: The range of qubits to be used.
    """
    subsystem = list(range(num_qubits))

    if degree is None:
        degree = num_qubits

    if isinstance(degree, int):
        if degree > num_qubits:
            raise ValueError(
                f"The subsystem A includes {degree} qubits "
                + f"beyond {num_qubits} which the wave function has."
            )
        if degree < 0:
            raise ValueError(
                "The number of qubits of subsystem A has to be natural number."
            )

        item_range = (num_qubits - degree, num_qubits)
        subsystem = subsystem[num_qubits - degree : num_qubits]

    elif isinstance(degree, (tuple, list)):
        if len(degree) == 2:
            deg_parsed = [
                (d % num_qubits if d != num_qubits else num_qubits) for d in degree
            ]
            item_range = (min(deg_parsed), max(deg_parsed))
            subsystem = subsystem[min(deg_parsed) : max(deg_parsed)]

        else:
            raise ValueError(
                "Subsystem range is defined by only two integers, "
                + f"but there is {len(degree)} integers in '{degree}'."
            )

    else:
        raise ValueError(
            f"'degree' must be 'int' or 'tuple[int, int]', but get '{degree}'."
        )

    return item_range


def wave_selector(
    qurry,
    wave: Union[QuantumCircuit, any, None] = None,
) -> Hashable:
    """Select wave.

    Args:
        qurry (Union[QurryV4, QurryV3]):
            The target qurry object.
        wave (Union[QuantumCircuit, int, None], optional):
            The index of the wave function in `self.waves` or add new one to calaculation,
            then choose one of waves as the experiment material.
            If input is `QuantumCircuit`, then add and use it.
            If input is the key in `.waves`, then use it.
            If input is `None` or something illegal, then use `.lastWave'.
            Defaults to None.

    Returns:
        Hashable: wave
    """
    if isinstance(wave, QuantumCircuit):
        wave = qurry.addWave(wave)
        print(f"| Add new wave with key: {wave}")
    elif wave is None:
        wave = qurry.lastWave
        print("| Autofill will use '.lastWave' as key")
    else:
        try:
            qurry.waves[wave]
        except KeyError as e:
            warnings.warn(f"'{e}', use '.lastWave' as key")
            wave = qurry.lastWave

    return wave


def decomposer(
    qc: QuantumCircuit,
    decompose: int = 2,
) -> QuantumCircuit:
    """Decompose the circuit with giving times.

    Args:
        qc (QuantumCircuit): The circuit wanted to be decomposed.
        decompose (int, optional):  Decide the times of decomposing the circuit.
            Draw quantum circuit with composed circuit. Defaults to 2.

    Returns:
        QuantumCircuit: The decomposed circuit.
    """

    qc_result = qc
    for _ in range(decompose):
        qc_result = qc_result.decompose()
    return qc_result


def decomposer_and_drawer(
    qc: QuantumCircuit,
    decompose: int = 2,
) -> str:
    """Decompose the circuit with giving times and draw it.

    Args:
        qc (QuantumCircuit): The circuit wanted to be decomposed.
        decompose (int, optional):  Decide the times of decomposing the circuit.
            Draw quantum circuit with composed circuit. Defaults to 2.

    Returns:
        str: The drawing of decomposed circuit.
    """
    return decomposer(qc, decompose).draw("text")


def get_counts_and_exceptions(
    result: Optional[Result],
    num: Optional[int] = None,
    result_idx_list: Optional[list[int]] = None,
) -> tuple[list[dict[str, int]], dict[str, Exception]]:
    """Get counts and exceptions from result.
    
    Args:
        result (Optional[Result]): The result of job.
        num (Optional[int], optional): The number of counts wanted to be extracted.
            Defaults to None.
        result_idx_list (Optional[list[int]], optional): The index of counts wanted to be extracted.
            Defaults to None.

    Returns:
        tuple[list[dict[str, int]], dict[str, Exception]]:
            Counts and exceptions.
    """
    counts: list[dict[str, int]] = []
    exceptions: dict[str, Exception] = {}
    if num is None and result_idx_list is None:
        idx_list = []
    elif result_idx_list is None:
        idx_list = list(range(num))
    elif num is None:
        idx_list = result_idx_list
    else:
        if num != len(result_idx_list):
            warnings.warn(
                "The number of result is not equal to the length of "
                + "'result_idx_list', use length of 'result_idx_list'."
            )
        else:
            warnings.warn(
                "The 'num' is not None, but 'result_idx_list' is not None, "
                + "use 'result_idx_list'."
            )
        idx_list = result_idx_list

    if result is None:
        exceptions["None"] = QurryCountLost("Result is None")
        print("| Failed Job result skip.")
        for _ in idx_list:
            counts.append({})
        return counts, exceptions

    if len(idx_list) == 0:
        try:
            get: Union[list[dict[str, int]], dict[str, int]] = result.get_counts()
            if isinstance(get, list):
                counts: list[dict[str, int]] = get
            else:
                counts.append(get)
        except QiskitError as err_1:
            exceptions[result.job_id] = err_1
            print("| Failed Job result skip, Job ID:", result.job_id, err_1)
        return counts, exceptions

    for i in idx_list:
        try:
            all_meas = result.get_counts(i)
        except QiskitError as err_2:
            exceptions[f"{result.job_id}.{i}"] = err_2
            print(
                "| Failed Job result skip, Job ID/which counts:",
                result.job_id,
                i,
                err_2,
            )
            all_meas = {}
        counts.append(all_meas)

    return counts, exceptions
