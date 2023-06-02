from qiskit import QuantumCircuit
from qiskit.result import Result

import warnings
from multiprocessing import cpu_count
from typing import Literal, Union, Hashable, Optional

def workers_distribution(
    workers_num: Optional[int] = None,
    default: int = cpu_count()-2,
) -> int:
    if default < 1:
        warnings.warn(
            f"| Available worker number {cpu_count()} is equal orsmaller than 2."+
            "This computer may not be able to run this program for the program will allocate all available threads.")
        default = cpu_count()
    
    if workers_num is None:
        launch_worker = default
    else:
        if workers_num > cpu_count():
            warnings.warn(
                f"| Worker number {workers_num} is larger than cpu count {cpu_count()}.")
            launch_worker = default
        elif workers_num < 1:
            warnings.warn(
                f"| Worker number {workers_num} is smaller than 1. Use single worker.")
            launch_worker = 1
        else:
            launch_worker = workers_num
    
    return launch_worker


def qubit_selector(
    num_qubits: int,
    degree: Union[int, tuple[int, int], None] = None,
    as_what: Literal['degree', 'unitary_set',
                     'unitary_loc', 'measure range'] = 'degree',
) -> tuple[int, int]:
    """Determint the qubits to be used.

    Args:
        num_qubits (int): Number of qubits.
        degree (Union[int, tuple[int, int], None], optional): 
            Degree of freedom or specific subsystem range. Defaults to None then will use number of qubits as degree.
        as_what (Literal[&#39;degree&#39;, &#39;unitary_set&#39;, &#39;unitary_loc&#39;, &#39;measure range&#39;], optional): For what is qubit range. Defaults to 'degree'.

    Raises:
        ValueError: The specific degree of subsystem qubits beyond number of qubits which the wave function has.
        ValueError: The number of qubits of subsystem A is not a natural number.
        ValueError: Invalid input for subsystem range defined by only two integers.
        ValueError: Degree of freedom is not given.

    Returns:
        tuple[int]: _description_
    """
    subsystem = [i for i in range(num_qubits)]
    item_range = ()

    if degree is None:
        degree = num_qubits

    if isinstance(degree, int):
        if degree > num_qubits:
            raise ValueError(
                f"The subsystem A includes {degree} qubits beyond {num_qubits} which the wave function has.")
        elif degree < 0:
            raise ValueError(
                f"The number of qubits of subsystem A has to be natural number.")

        item_range = (num_qubits-degree, num_qubits)
        subsystem = subsystem[num_qubits-degree:num_qubits]

    elif isinstance(degree, (tuple, list)):
        if len(degree) == 2:
            degParsed = [(d % num_qubits if d !=
                         num_qubits else num_qubits) for d in degree]
            item_range = (min(degParsed), max(degParsed))
            subsystem = subsystem[min(degParsed):max(degParsed)]
            print(
                f"| - Qubits: '{subsystem}' will be selected as {as_what}.")

        else:
            raise ValueError(
                f"Subsystem range is defined by only two integers, but there is {len(degree)} integers in '{degree}'.")

    else:
        raise ValueError("Degree of freedom is not given.")

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
    elif wave == None:
        wave = qurry.lastWave
        print(f"| Autofill will use '.lastWave' as key")
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

    qcResult = qc
    for t in range(decompose):
        qcResult = qcResult.decompose()
    return qcResult


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
    resultIdxList: Optional[list[int]] = None,
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
        if num is None and resultIdxList is None:
            get: Union[list[dict[str, int]],
                       dict[str, int]] = result.get_counts()
            if isinstance(get, list):
                counts: list[dict[str, int]] = get
            else:
                counts.append(get)
        else:
            if resultIdxList is None:
                resultIdxList = [i for i in range(num)]
            elif num is None:
                ...
            else:
                if num != len(resultIdxList):
                    warnings.warn(
                        "The number of result is not equal to the length of resultIdxList, use resultIdxList.")

            for i in resultIdxList:
                allMeas = result.get_counts(i)
                counts.append(allMeas)

    except Exception as err:
        counts.append({})
        print("| Failed Job result skip, Job ID:", result.job_id, err)

    return counts
