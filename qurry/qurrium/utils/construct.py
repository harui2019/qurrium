"""
================================================================
Construct (qurry.qurry.qurrium.utils.construct)
================================================================

"""
import warnings
from typing import Union, Hashable, Optional
from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.exceptions import QiskitError


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
                f"The subsystem A includes {degree} qubits " +
                f"beyond {num_qubits} which the wave function has.")
        if degree < 0:
            raise ValueError(
                "The number of qubits of subsystem A has to be natural number.")

        item_range = (num_qubits-degree, num_qubits)
        subsystem = subsystem[num_qubits-degree:num_qubits]

    elif isinstance(degree, (tuple, list)):
        if len(degree) == 2:
            deg_parsed = [(d % num_qubits if d !=
                           num_qubits else num_qubits) for d in degree]
            item_range = (min(deg_parsed), max(deg_parsed))
            subsystem = subsystem[min(deg_parsed):max(deg_parsed)]

        else:
            raise ValueError(
                "Subsystem range is defined by only two integers, " +
                f"but there is {len(degree)} integers in '{degree}'.")

    else:
        raise ValueError(
            f"'degree' must be 'int' or 'tuple[int, int]', but get '{degree}'.")

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
    return decomposer(qc, decompose).draw('text')


def get_counts(
    result: Union[Result, None],
    num: Optional[int] = None,
    result_idx_list: Optional[list[int]] = None,
) -> list[dict[str, int]]:
    """Computing specific squantity.
    Where should be overwritten by each construction of new measurement.

    Returns:
        tuple[dict, dict]:
            Counts, purity, entropy of experiment.
    """
    counts: list[dict[str, int]] = []
    if result is None:
        counts.append({})
        print("| Failed Job result skip.")
        return counts

    try:
        if num is None and result_idx_list is None:
            get: Union[list[dict[str, int]],
                       dict[str, int]] = result.get_counts()
            if isinstance(get, list):
                counts: list[dict[str, int]] = get
            else:
                counts.append(get)
        else:
            if result_idx_list is None:
                result_idx_list = list(range(num))
            elif num is None:
                ...
            else:
                if num != len(result_idx_list):
                    warnings.warn(
                        "The number of result is not equal to the length of " +
                        "'result_idx_list', use length of 'result_idx_list'.")

            for i in result_idx_list:
                all_meas = result.get_counts(i)
                counts.append(all_meas)

    except QiskitError as err:
        counts.append({})
        print("| Failed Job result skip, Job ID:", result.job_id, err)

    return counts
