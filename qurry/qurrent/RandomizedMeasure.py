from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator

import time
import tqdm
import numpy as np
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Type, Literal, overload, Any

from ..qurrium import (
    QurryV5Prototype,
    ExperimentPrototype,
    AnalysisPrototype,
    qubit_selector
)
from ..qurrium.utils.randomized import (
    ensembleCell,
    cycling_slice,
    random_unitary,

    local_random_unitary,
    local_random_unitary_operators,
    local_random_unitary_pauli_coeff
)
from ..tools import (
    qurryProgressBar,
    ProcessManager,
    workers_distribution,
    DEFAULT_POOL_SIZE
)
from ..boost.randomized import purityCellCore


class EntropyAnalysisContent(NamedTuple):
    """The content of the analysis."""

    purity: Optional[float] = None
    """The purity of the subsystem."""
    entropy: Optional[float] = None
    """The entanglement entropy of the subsystem."""
    puritySD: Optional[float] = None
    """The standard deviation of the purity of the subsystem."""
    entropySD: Optional[float] = None
    """The standard deviation of the entanglement entropy of the subsystem."""
    purityCells: Optional[dict[int, float]] = None
    """The purity of each cell of the subsystem."""
    bitStringRange: Optional[tuple[int, int]] = None
    """The qubit range of the subsystem."""

    allSystemSource: Optional[Union[str, Literal['independent']]] = None
    """The source of the all system."""
    purityAllSys: Optional[float] = None
    """The purity of the system."""
    entropyAllSys: Optional[float] = None
    """The entanglement entropy of the system."""
    puritySDAllSys: Optional[float] = None
    """The standard deviation of the purity of the system."""
    entropySDAllSys: Optional[float] = None
    """The standard deviation of the entanglement entropy of the system."""
    purityCellsAllSys: Optional[dict[int, float]] = None
    """The purity of each cell of the system."""
    bitsStringRangeAllSys: Optional[tuple[int, int]] = None
    """The qubit range of the all system."""

    errorRate: Optional[float] = None
    """The error rate of the measurement from depolarizing error migigation calculated."""
    mitigatedPurity: Optional[float] = None
    """The mitigated purity of the subsystem."""
    mitigatedEntropy: Optional[float] = None
    """The mitigated entanglement entropy of the subsystem."""

    num_qubits: Optional[int] = None
    """The number of qubits of the system."""
    measure: Optional[tuple[int, int]] = None
    """The qubit range of the measurement."""
    measureActually: Optional[tuple[int, int]] = None
    """The qubit range of the measurement actually used."""
    measureActuallyAllSys: Optional[tuple[int, int]] = None
    """The qubit range of the measurement actually used in the all system."""

    countsNum: Optional[int] = None
    """The number of counts of the experiment."""

    def __repr__(self):
        return f"analysisContent(purity={self.purity}, entropy={self.entropy}, and others)"


def _purityCellCy(
    idx: int,
    singleCounts: dict[str, int],
    bitStringRange: tuple[int, int],
    subsystemSize: int,
) -> tuple[int, float]:

    return idx, purityCellCore(dict(singleCounts), bitStringRange, subsystemSize)


def _purityCell(
    idx: int,
    singleCounts: dict[str, int],
    bitStringRange: tuple[int, int],
    subsystemSize: int,
) -> tuple[int, float]:
    """Calculate the purity cell, one of overlap, of a subsystem.

    Args:
        idx (int): Index of the cell (counts).
        singleCounts (dict[str, int]): Counts measured by the single quantum circuit.
        bitStringRange (tuple[int, int]): The range of the subsystem.
        subsystemSize (int): Subsystem size included.

    Returns:
        tuple[int, float]: Index, one of overlap purity.
    """

    shots = sum(singleCounts.values())

    dummyString = ''.join(str(ds) for ds in range(subsystemSize))
    if dummyString[bitStringRange[0]:bitStringRange[1]] == cycling_slice(
            dummyString, bitStringRange[0], bitStringRange[1], 1):

        singleCountsUnderDegree = dict.fromkeys(
            [k[bitStringRange[0]:bitStringRange[1]] for k in singleCounts], 0)
        for bitString in list(singleCounts):
            singleCountsUnderDegree[
                bitString[bitStringRange[0]:bitStringRange[1]]
            ] += singleCounts[bitString]

    else:
        singleCountsUnderDegree = dict.fromkeys(
            [cycling_slice(k, bitStringRange[0], bitStringRange[1], 1) for k in singleCounts], 0)
        for bitString in list(singleCounts):
            singleCountsUnderDegree[
                cycling_slice(
                    bitString, bitStringRange[0], bitStringRange[1], 1)
            ] += singleCounts[bitString]

    purityCell = np.float64(0)
    for sAi, sAiMeas in singleCountsUnderDegree.items():
        for sAj, sAjMeas in singleCountsUnderDegree.items():
            purityCell += ensembleCell(
                sAi, sAiMeas, sAj, sAjMeas, subsystemSize, shots)

    return idx, purityCell


def _entangled_entropy_core(
    shots: int,
    counts: list[dict[str, int]],
    degree: Union[tuple[int, int], int],
    measure: tuple[int, int] = None,
    workers_num: Optional[int] = None,
    use_cython: bool = True,
    _hide_print: bool = False,
) -> tuple[dict[int, float], tuple[int, int], tuple[int, int], str, int]:
    """The core function of entangled entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Union[tuple[int, int], int]): Degree of the subsystem.
        measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
        workers_num (Optional[int], optional): 
            Number of multi-processing workers, 
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
            Defaults to None.
        use_cython (bool, optional): Use cython to calculate purity cell. Defaults to True.
        _hide_print (bool, optional): Hide print. Defaults to False.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        tuple[list[float], tuple[int, int], tuple[int, int], str, int]: 
            Purity of each cell, Partition range, Measuring range, Message, Time to calculate.
    """

    # check shots
    sample_shots = sum(counts[0].values())
    assert sample_shots == shots, f"shots {shots} does not match sample_shots {sample_shots}"

    # Determine worker number
    launch_worker = workers_distribution(workers_num)

    # Determine degree
    if degree is None:
        degree = qubit_selector(len(list(counts[0].keys())[0]))

    # Determine subsystem size
    allsystemSize = len(list(counts[0].keys())[0])
    if isinstance(degree, int):
        subsystemSize = degree
        degree = qubit_selector(
            len(list(counts[0].keys())[0]), degree=degree)

    elif isinstance(degree, (tuple, list)):
        subsystemSize = max(degree) - min(degree)

    else:
        raise ValueError(
            f"'degree' must be 'int' or 'tuple[int, int]', but get '{degree}'.")

    bitStringRange = degree
    bitStringCheck = {
        'b > a': (bitStringRange[1] > bitStringRange[0]),
        'a >= -allsystemSize': bitStringRange[0] >= -allsystemSize,
        'b <= allsystemSize': bitStringRange[1] <= allsystemSize,
        'b-a <= allsystemSize': ((bitStringRange[1] - bitStringRange[0]) <= allsystemSize),
    }
    if all(bitStringCheck.values()):
        ...
    else:
        raise ValueError(
            f"Invalid 'bitStringRange = {bitStringRange} for allsystemSize = {allsystemSize}'. " +
            "Available range 'bitStringRange = [a, b)' should be" +
            ", ".join([f" {k};" for k, v in bitStringCheck.items() if not v]))

    if measure is None:
        measure = qubit_selector(len(list(counts[0].keys())[0]))

    dummyString = ''.join(str(ds) for ds in range(allsystemSize))
    dummyStringSlice = cycling_slice(
        dummyString, bitStringRange[0], bitStringRange[1], 1)
    isAvtiveCyclingSlice = dummyString[bitStringRange[0]                                       :bitStringRange[1]] != dummyStringSlice
    if isAvtiveCyclingSlice:
        assert len(dummyStringSlice) == subsystemSize, (
            f"| All system size '{subsystemSize}' does not match dummyStringSlice '{dummyStringSlice}'")

    msg = (
        f"| Partition: " +
        ("cycling-" if isAvtiveCyclingSlice else "") +
        f"{bitStringRange}, " +
        f"Measure: {measure}"
    )

    times = len(counts)
    Begin = time.time()

    cellCalculator = (_purityCellCy if use_cython else _purityCell)

    if launch_worker == 1:
        purityCellItems = []
        msg += f", single process, {times} overlaps, it will take a lot of time."
        if not _hide_print:
            print(msg)
        for i, c in enumerate(counts):
            if not _hide_print:
                print(" "*150, end="\r")
                print(
                    f"| Calculating overlap {i} and {i} " +
                    f"by summarize {len(c)**2} values - {i+1}/{times}" +
                    f" - {round(time.time() - Begin, 3)}s.", end="\r")
            purityCellItems.append(cellCalculator(
                i, c, bitStringRange, subsystemSize))

        if not _hide_print:
            print(" "*150, end="\r")
        takeTime = round(time.time() - Begin, 3)

    else:
        msg += f", {launch_worker} workers, {times} overlaps."

        pool = ProcessManager(launch_worker)
        purityCellItems = pool.starmap(
            cellCalculator, [(i, c, bitStringRange, subsystemSize) for i, c in enumerate(counts)])
        takeTime = round(time.time() - Begin, 3)

    if not _hide_print:
        print(f"| Calculating overlap end - {takeTime}s.")
    purityCellDict = {k: v for k, v in purityCellItems}
    return purityCellDict, bitStringRange, measure, msg, takeTime


def entangled_entropy(
    shots: int,
    counts: list[dict[str, int]],
    degree: Union[tuple[int, int], int],
    measure: tuple[int, int] = None,
    workers_num: Optional[int] = None,
    pbar: Optional[tqdm.tqdm] = None,
    use_cython: bool = True,
) -> dict[str, float]:
    """Calculate entangled entropy.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

    - Reference:
        - Used in:
            Statistical correlations between locally randomized measurements: 
            A toolbox for probing entanglement in many-body quantum states - 
            A. Elben, B. Vermersch, C. F. Roos, and P. Zoller, 
            [PhysRevA.99.052323](https://doi.org/10.1103/PhysRevA.99.052323)

        - `bibtex`:

    ```bibtex
        @article{PhysRevA.99.052323,
            title = {Statistical correlations between locally randomized measurements: 
            A toolbox for probing entanglement in many-body quantum states},
            author = {Elben, A. and Vermersch, B. and Roos, C. F. and Zoller, P.},
            journal = {Phys. Rev. A},
            volume = {99},
            issue = {5},
            pages = {052323},
            numpages = {12},
            year = {2019},
            month = {May},
            publisher = {American Physical Society},
            doi = {10.1103/PhysRevA.99.052323},
            url = {https://link.aps.org/doi/10.1103/PhysRevA.99.052323}
        }
        ```

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Union[tuple[int, int], int]): Degree of the subsystem.
        measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
        workers_num (Optional[int], optional): 
            Number of multi-processing workers, 
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
            Defaults to None.
        pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.
        use_cython (bool, optional): Use cython to calculate purity cell. Defaults to True.

    Returns:
        dict[str, float]: A dictionary contains purity, entropy, 
            a list of each overlap, puritySD, degree, actual measure range, bitstring range.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(f"Calculate specific degree {degree}.")
    (
        purityCellDict,
        bitStringRange,
        measureRange,
        msgOfProcess,
        takeTime,
    ) = _entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        workers_num=workers_num,
        _hide_print=True,
        use_cython=use_cython,
    )
    purityCellList = list(purityCellDict.values())

    purity = np.mean(purityCellList, dtype=np.float64)
    puritySD = np.std(purityCellList, dtype=np.float64)
    entropy = -np.log2(purity, dtype=np.float64)
    entropySD = puritySD/np.log(2)/purity

    quantity = {
        'purity': purity,
        'entropy': entropy,
        'purityCells': purityCellDict,
        'puritySD': puritySD,
        'entropySD': entropySD,

        'degree': degree,
        'measureActually': measureRange,
        'bitStringRange': bitStringRange,

        'countsNum': len(counts),
    }

    return quantity


@overload
def solve_p(
    meas_series: np.ndarray,
    nA: int
) -> tuple[np.ndarray, np.ndarray]:
    ...


@overload
def solve_p(
    meas_series: float,
    nA: int
) -> tuple[float, float]:
    ...


def solve_p(meas_series, nA):

    b = np.float64(1)/2**(nA-1)-2
    a = np.float64(1)+1/2**nA-1/2**(nA-1)
    c = 1-meas_series
    ppser = (-b+np.sqrt(b**2-4*a*c))/2/a
    pnser = (-b-np.sqrt(b**2-4*a*c))/2/a

    return ppser, pnser


@overload
def mitigation_equation(
    pser: np.ndarray,
    meas_series: np.ndarray,
    nA: int
) -> np.ndarray:
    ...


@overload
def mitigation_equation(
    pser: float,
    meas_series: float,
    nA: int
) -> float:
    ...


def mitigation_equation(pser, meas_series, nA):
    psq = np.square(pser, dtype=np.float64)
    return (
        meas_series-psq/2**nA - (pser-psq)/2**(nA-1)
    ) / np.square(1-pser, dtype=np.float64)


@overload
def depolarizing_error_mitgation(
    measSystem: float,
    allSystem: float,
    nA: int,
    systemSize: int,
) -> dict[str, float]:
    ...


@overload
def depolarizing_error_mitgation(
    measSystem: np.ndarray,
    allSystem: np.ndarray,
    nA: int,
    systemSize: int,
) -> dict[str, np.ndarray]:
    ...


def depolarizing_error_mitgation(measSystem, allSystem, nA, systemSize):
    """Depolarizing error mitigation.

    Args:
        measSystem (Union[float, np.ndarray]): Value of the measured subsystem.
        allSystem (Union[float, np.ndarray]): Value of the whole system.
        nA (int): The size of the subsystem.
        systemSize (int): The size of the system.

    Returns:
        Union[dict[str, float], dict[str, np.ndarray]]: _description_
    """

    pp, pn = solve_p(allSystem, systemSize)
    mitiga = mitigation_equation(pn, measSystem, nA)

    return {
        'errorRate': pn,
        'mitigatedPurity': mitiga,
        'mitigatedEntropy': -np.log2(mitiga, dtype=np.float64)
    }


def entangled_entropy_complex(
    shots: int,
    counts: list[dict[str, int]],
    degree: Union[tuple[int, int], int],
    measure: tuple[int, int] = None,
    workers_num: Optional[int] = None,
    pbar: Optional[tqdm.tqdm] = None,
    all_system_source: Optional['EntropyRandomizedAnalysis'] = None,
    use_cython: bool = True,
) -> dict[str, float]:
    """Calculate entangled entropy with more information combined.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

    - Reference:
        - Used in:
            Simple mitigation of global depolarizing errors in quantum simulations - 
            Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self, Christopher and Kim, M. S. and Knolle, Johannes,
            [PhysRevE.104.035309](https://link.aps.org/doi/10.1103/PhysRevE.104.035309)

        - `bibtex`:

    ```bibtex
        @article{PhysRevE.104.035309,
            title = {Simple mitigation of global depolarizing errors in quantum simulations},
            author = {Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self, Christopher and Kim, M. S. and Knolle, Johannes},
            journal = {Phys. Rev. E},
            volume = {104},
            issue = {3},
            pages = {035309},
            numpages = {8},
            year = {2021},
            month = {Sep},
            publisher = {American Physical Society},
            doi = {10.1103/PhysRevE.104.035309},
            url = {https://link.aps.org/doi/10.1103/PhysRevE.104.035309}
        }
    ```

    - Error mitigation:

        We use depolarizing error mitigation.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Union[tuple[int, int], int]): Degree of the subsystem.
        measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
        workers_num (Optional[int], optional): 
            Number of multi-processing workers, 
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
            Defaults to None.
        pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.
        all_system_source (Optional['EntropyRandomizedAnalysis'], optional):
            The source of the all system. Defaults to None.
        use_cython (bool, optional): Use cython to calculate purity cell. Defaults to True.

    Returns:
        dict[str, float]: A dictionary contains 
            purity, entropy, a list of each overlap, puritySD, 
            purity of all system, entropy of all system, a list of each overlap in all system, puritySD of all system,
            degree, actual measure range, actual measure range in all system, bitstring range.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(
            f"Calculate specific partition" +
            ("." if use_cython else " by Pure Python, it may take a long time."))
    (
        purityCellDict,
        bitStringRange,
        measureRange,
        msgOfProcess,
        takeTime,
    ) = _entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        workers_num=workers_num,
        _hide_print=True,
    )
    purityCellList = list(purityCellDict.values())

    if all_system_source is None:
        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(
                f"Calculate all system" +
                ("." if use_cython else " by Pure Python, it may take a long time."))
        (
            purityCellDictAllSys,
            bitStringRangeAllSys,
            measureRangeAllSys,
            msgOfProcessAllSys,
            takeTimeAllSys,
        ) = _entangled_entropy_core(
            shots=shots,
            counts=counts,
            degree=None,
            measure=measure,
            workers_num=workers_num,
            _hide_print=True,
        )
        purityCellListAllSys = list(purityCellDictAllSys.values())
        source = 'independent'
    else:
        content: EntropyAnalysisContent = all_system_source.content
        source = str(all_system_source.header)
        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(
                "Using existing all system from '{}'".format(source))
        purityCellDictAllSys = content.purityCellsAllSys
        assert purityCellDictAllSys is not None, "all_system_source.content.purityCells is None"
        purityCellListAllSys = list(purityCellDictAllSys.values())
        bitStringRangeAllSys = content.bitStringRange
        measureRangeAllSys = content.measureActually
        msgOfProcessAllSys = f"Use all system from {source}."
        takeTimeAllSys = 0

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(
            f"Preparing error mitigation of {bitStringRange} on {measure}")
    purity: float = np.mean(purityCellList, dtype=np.float64)
    purityAllSys: float = np.mean(purityCellListAllSys, dtype=np.float64)
    puritySD = np.std(purityCellList, dtype=np.float64)
    puritySDAllSys = np.std(purityCellListAllSys, dtype=np.float64)

    entropy = -np.log2(purity, dtype=np.float64)
    entropySD = puritySD/np.log(2)/purity
    entropyAllSys = -np.log2(purityAllSys, dtype=np.float64)
    entropySDAllSys = puritySDAllSys/np.log(2)/purityAllSys

    if measure is None:
        measureInfo = 'not specified, use all qubits'
    else:
        measureInfo = f'measure range: {measure}'

    num_qubits = len(list(counts[0].keys())[0])
    if isinstance(degree, tuple):
        subsystem = max(degree) - min(degree)
    else:
        subsystem = degree
    error_mitgation_info = depolarizing_error_mitgation(
        measSystem=purity,
        allSystem=purityAllSys,
        nA=subsystem,
        systemSize=num_qubits,
    )

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(msgOfProcess[2:-1]+" with mitigation.")

    quantity = {
        # target system
        'purity': purity,
        'entropy': entropy,
        'purityCells': purityCellDict,
        'puritySD': puritySD,
        'entropySD': entropySD,
        'bitStringRange': bitStringRange,
        # all system
        'allSystemSource': source,  # 'independent' or 'header of analysis'
        'purityAllSys': purityAllSys,
        'entropyAllSys': entropyAllSys,
        'purityCellsAllSys': purityCellDictAllSys,
        'puritySDAllSys': puritySDAllSys,
        'entropySDAllSys': entropySDAllSys,
        'bitsStringRangeAllSys': bitStringRangeAllSys,
        # mitigated
        'errorRate': error_mitgation_info['errorRate'],
        'mitigatedPurity': error_mitgation_info['mitigatedPurity'],
        'mitigatedEntropy': error_mitgation_info['mitigatedEntropy'],
        # info
        'degree': degree,
        'num_qubits': num_qubits,
        'measure': measureInfo,
        'measureActually': measureRange,
        'measureActuallyAllSys': measureRangeAllSys,

        'countsNum': len(counts),
    }
    return quantity


def _circuit_method_core(
    idx: int,
    tgtCircuit: QuantumCircuit,
    expName: str,
    unitary_loc: tuple[int, int],
    unitarySubList: dict[int, Operator],
    measure: tuple[int, int],
) -> QuantumCircuit:

    num_qubits = tgtCircuit.num_qubits

    qFunc1 = QuantumRegister(num_qubits, 'q1')
    cMeas1 = ClassicalRegister(
        measure[1]-measure[0], 'c1')
    qcExp1 = QuantumCircuit(qFunc1, cMeas1)
    qcExp1.name = f"{expName}-{idx}"

    qcExp1.append(tgtCircuit, [qFunc1[i] for i in range(num_qubits)])

    qcExp1.barrier()
    for j in range(*unitary_loc):
        qcExp1.append(unitarySubList[j], [j])

    for j in range(*measure):
        qcExp1.measure(qFunc1[j], cMeas1[j-measure[0]])

    return qcExp1


class EntropyRandomizedAnalysis(AnalysisPrototype):

    __name__ = 'qurrentRandomized.Analysis'
    shortName = 'qurrent_haar.report'

    class analysisInput(NamedTuple):
        """To set the analysis."""

        degree: tuple[int, int]
        shots: int
        unitary_loc: tuple[int, int] = None

    analysisContent = EntropyAnalysisContent
    """The content of the analysis."""
    # It works ...

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return [
            'purityCells',
            'purityCellsAllSys',
        ]

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[dict[str, int]],
        degree: Union[tuple[int, int], int],
        measure: tuple[int, int] = None,
        workers_num: Optional[int] = None,
        pbar: Optional[tqdm.tqdm] = None,
        all_system_source: Optional['EntropyRandomizedAnalysis'] = None,
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
            workers_num (Optional[int], optional): 
                Number of multi-processing workers, 
                if sets to 1, then disable to using multi-processing;
                if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
                Defaults to None.
            pbar (Optional[tqdm.tqdm], optional): The tqdm handle. Defaults to None.
            independent_all_system (bool, optional): The source of all system to calculate error mitigation. Defaults to False.

        Returns:
            dict[str, float]: A dictionary contains 
                purity, entropy, a list of each overlap, puritySD, 
                purity of all system, entropy of all system, a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """

        return entangled_entropy_complex(
            shots=shots,
            counts=counts,
            degree=degree,
            measure=measure,
            workers_num=workers_num,
            pbar=pbar,
            all_system_source=all_system_source,
        )


class EntropyRandomizedExperiment(ExperimentPrototype):

    __name__ = 'qurrentRandomized.Experiment'
    shortName = 'qurrent_haar.exp'

    tqdm_handleable = True
    """The handleable of tqdm."""

    class arguments(NamedTuple):
        """Arguments for the experiment."""
        expName: str = 'exps'
        times: int = 100
        measure: tuple[int, int] = None
        unitary_loc: tuple[int, int] = None
        workers_num: int = DEFAULT_POOL_SIZE

    @classmethod
    @property
    def analysis_container(cls) -> Type[EntropyRandomizedAnalysis]:
        """The container class responding to this QurryV5 class.
        """
        return EntropyRandomizedAnalysis

    def analyze(
        self,
        degree: Union[tuple[int, int], int],
        workers_num: Optional[int] = None,
        pbar: Optional[tqdm.tqdm] = None,
        independent_all_system: bool = False,
    ) -> EntropyRandomizedAnalysis:
        """Calculate entangled entropy with more information combined.

        Args:
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            workers_num (Optional[int], optional): 
                Number of multi-processing workers, 
                if sets to 1, then disable to using multi-processing;
                if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
                Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains 
                purity, entropy, a list of each overlap, puritySD, 
                purity of all system, entropy of all system, a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """

        self.args: EntropyRandomizedExperiment.arguments
        self.reports: dict[int, EntropyRandomizedAnalysis]
        shots = self.commons.shots
        measure = self.args.measure
        unitary_loc = self.args.unitary_loc
        counts = self.afterwards.counts

        available_all_system_source = [
            k for k, v in self.reports.items()
            if v.content.allSystemSource == 'independent'
        ]

        if len(available_all_system_source) > 0 and not independent_all_system:
            all_system_source = self.reports[available_all_system_source[-1]]
        else:
            all_system_source = None

        if isinstance(pbar, tqdm.tqdm):
            qs = self.analysis_container.quantities(
                shots=shots,
                counts=counts,
                degree=degree,
                measure=measure,
                workers_num=workers_num,
                pbar=pbar,
                all_system_source=all_system_source,
            )

        else:
            pbar_selfhost = qurryProgressBar(
                range(1),
                bar_format='simple',
            )

            with pbar_selfhost as pb_self:
                qs = self.analysis_container.quantities(
                    shots=shots,
                    counts=counts,
                    degree=degree,
                    measure=measure,
                    workers_num=workers_num,
                    pbar=pb_self,
                )
                pb_self.update()

        serial = len(self.reports)
        analysis = self.analysis_container(
            serial=serial,
            shots=shots,
            unitary_loc=unitary_loc,
            **qs,
        )

        self.reports[serial] = analysis
        return analysis


class EntropyRandomizedMeasure(QurryV5Prototype):
    """Randomized Measure Experiment.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

    - Reference:
        - Used in:
            Simple mitigation of global depolarizing errors in quantum simulations - 
            Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self, Christopher and Kim, M. S. and Knolle, Johannes,
            [PhysRevE.104.035309](https://link.aps.org/doi/10.1103/PhysRevE.104.035309)

        - `bibtex`:

    ```bibtex
        @article{PhysRevE.104.035309,
            title = {Simple mitigation of global depolarizing errors in quantum simulations},
            author = {Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self, Christopher and Kim, M. S. and Knolle, Johannes},
            journal = {Phys. Rev. E},
            volume = {104},
            issue = {3},
            pages = {035309},
            numpages = {8},
            year = {2021},
            month = {Sep},
            publisher = {American Physical Society},
            doi = {10.1103/PhysRevE.104.035309},
            url = {https://link.aps.org/doi/10.1103/PhysRevE.104.035309}
        }
    ```
    """

    __name__ = 'qurrentRandomized'
    shortName = 'qurrent_haar'

    @classmethod
    @property
    def experiment(cls) -> Type[EntropyRandomizedExperiment]:
        """The container class responding to this QurryV5 class.
        """
        return EntropyRandomizedExperiment

    def paramsControl(
        self,
        expName: str = 'exps',
        waveKey: Hashable = None,
        times: int = 100,
        measure: tuple[int, int] = None,
        unitary_loc: tuple[int, int] = None,
        **otherArgs: any
    ) -> tuple[EntropyRandomizedExperiment.arguments, EntropyRandomizedExperiment.commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            waveKey (Hashable):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            expName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """

        # times
        if not isinstance(times, int):
            raise ValueError(f"times should be an integer, but got {times}.")

        # measure and unitary location
        num_qubits = self.waves[waveKey].num_qubits
        if measure is None:
            measure = num_qubits
        measure = qubit_selector(
            num_qubits, degree=measure, as_what='measure range')

        if unitary_loc is None:
            unitary_loc = num_qubits
        unitary_loc = qubit_selector(
            num_qubits, degree=unitary_loc, as_what='unitary_loc')

        if (min(measure) < min(unitary_loc)) or (max(measure) > max(unitary_loc)):
            raise ValueError(
                f"unitary_loc range '{unitary_loc}' does not contain measure range '{measure}'.")

        expName = f"w={waveKey}.with{times}random.{self.shortName}"

        return self.experiment.filter(
            expName=expName,
            waveKey=waveKey,
            times=times,
            measure=measure,
            unitary_loc=unitary_loc,
            **otherArgs,
        )

    def method(
        self,
        expID: str,
        _pbar: Optional[tqdm.tqdm] = None,
    ) -> list[QuantumCircuit]:

        assert expID in self.exps
        assert self.exps[expID].commons.expID == expID
        currentExp = self.exps[expID]
        args: EntropyRandomizedExperiment.arguments = self.exps[expID].args
        commons: EntropyRandomizedExperiment.commonparams = self.exps[expID].commons
        circuit = self.waves[commons.waveKey]
        num_qubits = circuit.num_qubits

        pool = ProcessManager(args.workers_num)

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Preparing {args.times} random unitary with {args.workers_num} workers.")

        # DO NOT USE MULTI-PROCESSING HERE !!!!!
        # See https://github.com/numpy/numpy/issues/9650
        # And https://github.com/harui2019/qurry/issues/78
        # The random seed will be duplicated in each process,
        # and it will make duplicated result.
        # unitaryList = pool.starmap(
        #     local_random_unitary, [(args.unitary_loc, None) for _ in range(args.times)])

        unitaryList = {i: {
            j: random_unitary(2) for j in range(*args.unitary_loc)
        } for i in range(args.times)}

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Building {args.times} circuits with {args.workers_num} workers.")
        qcList = pool.starmap(
            _circuit_method_core, [(
                i, circuit, args.expName, args.unitary_loc, unitaryList[i], args.measure
            ) for i in range(args.times)])

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Writing 'unitaryOP' with {args.workers_num} workers.")
        unitaryOPList = pool.starmap(
            local_random_unitary_operators,
            [(args.unitary_loc, unitaryList[i]) for i in range(args.times)])
        currentExp.beforewards.sideProduct['unitaryOP'] = {
            i: v for i, v in enumerate(unitaryOPList)}

        # currentExp.beforewards.sideProduct['unitaryOP'] = {
        #     k: {i: np.array(v[i]).tolist() for i in range(*args.unitary_loc)}
        #     for k, v in unitaryList.items()}

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Writing 'randomized' with {args.workers_num} workers.")
        randomizedList = pool.starmap(
            local_random_unitary_pauli_coeff,
            [(args.unitary_loc, unitaryOPList[i]) for i in range(args.times)])
        currentExp.beforewards.sideProduct['randomized'] = {
            i: v for i, v in enumerate(randomizedList)}

        # currentExp.beforewards.sideProduct['randomized'] = {i: {
        #     j: qubitOpToPauliCoeff(
        #         unitaryList[i][j])
        #     for j in range(*args.unitary_loc)
        # } for i in range(args.times)}

        return qcList

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        times: int = 100,
        measure: Union[int, tuple[int, int], None] = None,
        unitary_loc: Union[int, tuple[int, int], None] = None,
        expName: str = 'exps',
        *args,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
        **otherArgs: any
    ) -> str:
        """

        Args:
            wave (Union[QuantumCircuit, int, None], optional):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            expName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The output.
        """

        IDNow = self.result(
            wave=wave,
            expName=expName,
            times=times,
            measure=measure,
            unitary_loc=unitary_loc,
            saveLocation=None,
            **otherArgs,
        )
        assert IDNow in self.exps, f"ID {IDNow} not found."
        assert self.exps[IDNow].commons.expID == IDNow
        currentExp = self.exps[IDNow]

        if isinstance(saveLocation, (Path, str)):
            currentExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonablize=jsonablize,
            )

        return IDNow
