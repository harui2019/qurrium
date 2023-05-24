from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator

import time
import numpy as np
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Type, overload, Any

from ..qurrium import (
    QurryV5Prototype,
    ExperimentPrototype,
    AnalysisPrototype,
    qubit_selector
)
from ..qurrium.utils import workers_distribution
from ..qurrium.utils.randomized import (
    random_unitary,
    qubitOpToPauliCoeff,
    ensembleCell,
    cycling_slice
)


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
    _workers_num: Optional[int] = None,
) -> tuple[dict[int, float], tuple[int, int], tuple[int, int]]:
    """The core function of entangled entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Union[tuple[int, int], int]): Degree of the subsystem.
        measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
        _workers_num (Optional[int], optional): 
            Number of multi-processing workers, 
            if sets to 1, then disable to using multi-processing;
            if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
            Defaults to None.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        tuple[list[float], tuple[int, int], tuple[int, int]]: _description_
    """

    # check shots
    sample_shots = sum(counts[0].values())
    assert sample_shots == shots, f"shots {shots} does not match sample_shots {sample_shots}"

    # Determine worker number
    launch_worker = workers_distribution(_workers_num)

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
    isAvtiveCyclingSlice = dummyString[bitStringRange[0]
        :bitStringRange[1]] != dummyStringSlice
    if isAvtiveCyclingSlice:
        assert len(dummyStringSlice) == subsystemSize, (
            f"allsystemSize {subsystemSize} does not match dummyStringSlice {dummyStringSlice}")

    print(
        f"| Subsystem size: {subsystemSize}, AllsystemSize: {allsystemSize}" +
        ("cycling" if isAvtiveCyclingSlice else "")+", "
        f"bitstring range: {bitStringRange}, " +
        f"measure range: {measure}.")

    times = len(counts)
    Begin = time.time()

    if launch_worker == 1:
        purityCellItems = []
        print(
            f"| Without multi-processing to calculate overlap of {times} counts. It will take a lot of time to complete.")
        for i, c in enumerate(counts):
            print(" "*150, end="\r")
            print(
                f"| Calculating overlap {i} and {i} " +
                f"by summarize {len(c)**2} values - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s.", end="\r")
            purityCellItems.append(_purityCell(
                i, c, bitStringRange, subsystemSize))

        print(" "*150, end="\r")
        print(
            f"| Calculating overlap end - {times}/{times}" +
            f" - {round(time.time() - Begin, 3)}s.")
    else:
        print(
            f"| With {launch_worker} workers to calculate overlap of {times} counts.")
        pool = Pool(launch_worker)
        purityCellItems = pool.starmap(
            _purityCell, [(i, c, bitStringRange, subsystemSize) for i, c in enumerate(counts)])
        print(f"| Calculating overlap end - {round(time.time() - Begin, 3)}s.")

    purityCellDict = {k: v for k, v in purityCellItems}
    return purityCellDict, bitStringRange, measure


def entangled_entropy(
    shots: int,
    counts: list[dict[str, int]],
    degree: Union[tuple[int, int], int],
    measure: tuple[int, int] = None,
    _workers_num: Optional[int] = None,
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
        _workers_num (Optional[int], optional): 
            Number of multi-processing workers, 
            if sets to 1, then disable to using multi-processing;
            if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
            Defaults to None.

    Returns:
        dict[str, float]: A dictionary contains purity, entropy, 
            a list of each overlap, puritySD, degree, actual measure range, bitstring range.
    """

    purityCellDict, bitStringRange, measureRange = _entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        _workers_num=_workers_num,
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
    _workers_num: Optional[int] = None,
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
        _workers_num (Optional[int], optional): 
            Number of multi-processing workers, 
            if sets to 1, then disable to using multi-processing;
            if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
            Defaults to None.

    Returns:
        dict[str, float]: A dictionary contains 
            purity, entropy, a list of each overlap, puritySD, 
            purity of all system, entropy of all system, a list of each overlap in all system, puritySD of all system,
            degree, actual measure range, actual measure range in all system, bitstring range.
    """

    purityCellDict, bitStringRange, measureRange = _entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        _workers_num=_workers_num,
    )
    purityCellList = list(purityCellDict.values())

    purityCellDictAllSys, bitStringRangeAllSys, measureRangeAllSys = _entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=None,
        measure=measure,
        _workers_num=_workers_num,
    )
    purityCellListAllSys = list(purityCellDictAllSys.values())

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

    quantity = {
        # target system
        'purity': purity,
        'entropy': entropy,
        'purityCells': purityCellDict,
        'puritySD': puritySD,
        'entropySD': entropySD,
        'bitStringRange': bitStringRange,
        # all system
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

    class analysisContent(NamedTuple):
        """The content of the analysis."""
        # TODO: args hint

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
        _workers_num: Optional[int] = None,
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
            _workers_num (Optional[int], optional): 
                Number of multi-processing workers, 
                if sets to 1, then disable to using multi-processing;
                if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
                Defaults to None.

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
            _workers_num=_workers_num,
        )


class EntropyRandomizedExperiment(ExperimentPrototype):

    __name__ = 'qurrentRandomized.Experiment'
    shortName = 'qurrent_haar.exp'

    class arguments(NamedTuple):
        """Arguments for the experiment."""
        expName: str = 'exps'
        times: int = 100
        measure: tuple[int, int] = None
        unitary_loc: tuple[int, int] = None
        workers_num: int = int(cpu_count() - 2)

    @classmethod
    @property
    def analysis_container(cls) -> Type[EntropyRandomizedAnalysis]:
        """The container class responding to this QurryV5 class.
        """
        return EntropyRandomizedAnalysis

    def analyze(
        self,
        degree: Union[tuple[int, int], int],
        _workers_num: Optional[int] = None
    ) -> EntropyRandomizedAnalysis:
        """Calculate entangled entropy with more information combined.

        Args:
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            _workers_num (Optional[int], optional): 
                Number of multi-processing workers, 
                if sets to 1, then disable to using multi-processing;
                if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
                Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains 
                purity, entropy, a list of each overlap, puritySD, 
                purity of all system, entropy of all system, a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """

        self.args: EntropyRandomizedExperiment.arguments
        shots = self.commons.shots
        measure = self.args.measure
        unitary_loc = self.args.unitary_loc
        counts = self.afterwards.counts

        qs = self.analysis_container.quantities(
            shots=shots,
            counts=counts,
            degree=degree,
            measure=measure,
            _workers_num=_workers_num,
        )

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
        expID: Hashable,
    ) -> list[QuantumCircuit]:

        assert expID in self.exps
        assert self.exps[expID].commons.expID == expID
        currentExp = self.exps[expID]
        args: EntropyRandomizedExperiment.arguments = self.exps[expID].args
        commons: EntropyRandomizedExperiment.commonparams = self.exps[expID].commons
        circuit = self.waves[commons.waveKey]
        num_qubits = circuit.num_qubits

        unitaryList = {i: {
            j: random_unitary(2) for j in range(*args.unitary_loc)
        } for i in range(args.times)}

        if isinstance(commons.serial, int):
            print((
                f"| Build circuit: {commons.waveKey}, worker={args.workers_num}," +
                f" serial={commons.serial}, by={commons.summonerName}."
            ), end="\r")
        else:
            print(f"| Build circuit: {commons.waveKey}.", end="\r")

        pool = Pool(args.workers_num)
        qcList = pool.starmap(
            _circuit_method_core, [(
                i, circuit, args.expName, args.unitary_loc, unitaryList[i], args.measure
            ) for i in range(args.times)])
        if isinstance(commons.serial, int):
            print(
                f"| Build circuit: {commons.waveKey}, worker={args.workers_num}," +
                f" serial={commons.serial}, by={commons.summonerName} done."
            )
        else:
            print(f"| Build circuit: {commons.waveKey} done.", end="\r")

        currentExp.beforewards.sideProduct['unitaryOP'] = {
            k: {i: np.array(v[i]).tolist() for i in range(*args.unitary_loc)}
            for k, v in unitaryList.items()}
        currentExp.beforewards.sideProduct['randomized'] = {i: {
            j: qubitOpToPauliCoeff(
                unitaryList[i][j])
            for j in range(*args.unitary_loc)
        } for i in range(args.times)}

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
    ) -> Hashable:
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
