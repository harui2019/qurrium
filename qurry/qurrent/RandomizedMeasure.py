from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

import time
import warnings
import numpy as np
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, Iterable, Type, overload, Any

from ..qurrium import (
    QurryV5Prototype,
    ExperimentPrototype,
    AnalysisPrototype,
    qubit_selector
)
from ..qurrium.utils.randomized import (
    random_unitary,
    qubitOpToPauliCoeff,
    ensembleCell,
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

    singleCountsUnderDegree = dict.fromkeys(
        [k[bitStringRange[0]:bitStringRange[1]] for k in singleCounts], 0)
    for bitString in list(singleCounts):
        singleCountsUnderDegree[bitString[bitStringRange[0]:bitStringRange[1]]] += singleCounts[bitString]

    purityCell = 0
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
    _worker_num: Optional[int] = None,
) -> tuple[list[float], tuple[int, int], tuple[int, int]]:
    """The core function of entangled entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Union[tuple[int, int], int]): Degree of the subsystem.
        measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
        _worker_num (Optional[int], optional): 
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
    if _worker_num is None:
        launch_worker = int(cpu_count()/4*3)
    else:
        if _worker_num > cpu_count():
            warnings.warn(
                f"Worker number {_worker_num} is larger than cpu count {cpu_count()}.")
            launch_worker = int(cpu_count()-4)
        elif _worker_num < 1:
            warnings.warn(
                f"Worker number {_worker_num} is smaller than 1. Use single worker.")
            launch_worker = 1
        else:
            launch_worker = _worker_num

    # Determine degree
    if degree is None:
        degree = qubit_selector(len(list(counts[0].keys())[0]))

    # Determine subsystem size
    if isinstance(degree, int):
        subsystemSize = degree
        print('quantity core: int', degree)
        degree = qubit_selector(
            len(list(counts[0].keys())[0]), degree=degree)

    elif isinstance(degree, (tuple, list)):
        subsystemSize = max(degree) - min(degree)
        print('quantity core: tuple, list', degree)

    else:
        raise ValueError(
            f"'degree' must be 'int' or 'tuple[int, int]', but get '{degree}'.")

    if measure is None:
        measure = qubit_selector(len(list(counts[0].keys())[0]))

    if (min(degree) < min(measure)) or (max(degree) > max(measure)):
        raise ValueError(
            f"Measure range '{measure}' does not contain subsystem '{degree}'.")

    bitStringRange = (min(degree) - min(measure), max(degree) - min(measure))
    print(
        f"| Subsystem size: {subsystemSize}, bitstring range: {bitStringRange}, measure range: {measure}.")

    times = len(counts)
    Begin = time.time()

    if launch_worker == 1:
        purityCellList = []
        print(
            f"| Without multi-processing to calculate overlap of {times} counts. It will take a lot of time to complete.")
        for i, c in enumerate(counts):
            print(" "*150, end="\r")
            print(
                f"| Calculating overlap {i} and {i} " +
                f"by summarize {len(c)**2} values - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s.", end="\r")
            purityCellList.append(_purityCell(
                i, c, bitStringRange, subsystemSize))

        print(" "*150, end="\r")
        print(
            f"| Calculating overlap end - {times}/{times}" +
            f" - {round(time.time() - Begin, 3)}s.")
    else:
        print(
            f"| With {launch_worker} workers to calculate overlap of {times} counts.")
        pool = Pool(launch_worker)
        purityCellList = pool.starmap(
            _purityCell, [(i, c, bitStringRange, subsystemSize) for i, c in enumerate(counts)])
        print(f"| Calculating overlap end - {round(time.time() - Begin, 3)}s.")

    return purityCellList, bitStringRange, measure


def entangled_entropy(
    shots: int,
    counts: list[dict[str, int]],
    degree: Union[tuple[int, int], int],
    measure: tuple[int, int] = None,
    _workers_num: Optional[int] = None,
) -> dict[str, float]:
    """Calculate entangled entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Union[tuple[int, int], int]): Degree of the subsystem.
        measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
        _worker_num (Optional[int], optional): 
            Number of multi-processing workers, 
            if sets to 1, then disable to using multi-processing;
            if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
            Defaults to None.

    Returns:
        dict[str, float]: A dictionary contains purity, entropy, 
            a list of each overlap, puritySD, degree, actual measure range, bitstring range.
    """

    purityCellList, bitStringRange, measureRange = _entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        _workers_num=_workers_num,
    )

    purity = np.mean(purityCellList)
    puritySD = np.std(purityCellList)
    entropy = -np.log2(purity)

    quantity = {
        'purity': purity,
        'entropy': entropy,
        'purityCellList': purityCellList,
        'puritySD': puritySD,

        'degree': degree,
        'measureActually': measureRange,
        'bitStringRange': bitStringRange,
    }

    return quantity


def entangled_entropy_complex(
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
        _worker_num (Optional[int], optional): 
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

    purityCellList, bitStringRange, measureRange = _entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        _workers_num=_workers_num,
    )

    purityCellListAllSys, bitStringRangeAllSys, measureRangeAllSys = _entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=None,
        measure=measure,
        _workers_num=_workers_num,
    )

    purity = np.mean(purityCellList)
    purityAllSys = np.mean(purityCellListAllSys)
    puritySD = np.std(purityCellList)
    puritySDAllSys = np.std(purityCellListAllSys)

    entropy = -np.log2(purity)
    entropyAllSys = -np.log2(purityAllSys)

    if measure is None:
        measureInfo = 'not specified, use all qubits'
    else:
        measureInfo = measure

    quantity = {
        # target system
        'purity': purity,
        'entropy': entropy,
        'entropy': entropy,
        'purityCellList': purityCellList,
        'puritySD': puritySD,
        # all system
        'purityAllSys': purityAllSys,
        'entropyAllSys': entropyAllSys,
        'purityCellListAllSys': purityCellListAllSys,
        'puritySDAllSys': puritySDAllSys,
        'bitsStringRangeAllSys': bitStringRangeAllSys,
        # mitigated
        # errorMitigatedPurity:
        # errorMitigatedEntropy:
        # errorMitigatedPuritySD:
        # errorMitigatedPurityCellList:
        # info
        'degree': degree,
        'measure': measureInfo,
        'measureActually': measureRange,
        'measureActuallyAllSys': measureRangeAllSys,
        'bitStringRange': bitStringRange,
    }
    return quantity


class EntropyRandomizedAnalysis(AnalysisPrototype):

    __name__ = 'qurrent.RandomizedAnalysis'

    class analysisInput(NamedTuple):
        """To set the analysis."""

        degree: tuple[int, int]

    class analysisContent(NamedTuple):
        """The content of the analysis."""

        purtiy: float
        """The purity of the system."""
        entropy: float
        purtiySD: float
        purityCellList: list[float]
        bitStringRange: tuple[int, int]

        purityAllSys: float
        entropyAllSys: float
        purityCellListAllSys: list[float]
        puritySDAllSys: float
        bitsStringRangeAllSys: tuple[int, int]

        # errorMitigatedPurity: float
        # errorMitigatedEntropy: float
        # errorMitigatedPuritySD: float
        # errorMitigatedPurityCellList: list[float]

        degree: tuple[int, int]
        measure: tuple[int, int]

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return [
            'purityCellList',
            'purityCellListAllSys',
            'errorMitigatedPurityCellList'
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
            _worker_num (Optional[int], optional): 
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
            _worker_num=_workers_num,
        )


class EntropyRandomizedExperiment(ExperimentPrototype):

    __name__ = 'qurrent.RandomizedExperiment'
    shortName = 'qurrent'

    class arguments(NamedTuple):
        """Arguments for the experiment."""
        expName: str = 'exps'
        times: int = 100
        measure: tuple[int, int] = None
        unitary_loc: tuple[int, int] = None

    @classmethod
    @property
    def analysis_container(cls) -> Type[EntropyRandomizedAnalysis]:
        """The container class responding to this QurryV5 class.
        """
        return EntropyRandomizedAnalysis
    
    


class EntropyRandomizedMeasure(QurryV5Prototype):

    __name__ = 'qurrent.Randomized'

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
        numQubits = self.waves[waveKey].num_qubits
        if measure is None:
            measure = numQubits
        measure = qubit_selector(
            numQubits, degree=measure, as_what='measure range')

        if unitary_loc is None:
            unitary_loc = numQubits
        unitary_loc = qubit_selector(
            numQubits, degree=unitary_loc, as_what='unitary_set')

        expName = f"w={waveKey}-at={times}.{self.shortName}"

        return self.experiment.filter(
            expName=expName,
            waveKey=waveKey,
            times=times,
            measure=measure,
            unitary_loc=unitary_loc,
            **otherArgs,
        )

    def method(self) -> list[QuantumCircuit]:

        assert self.lastExp is not None
        args: EntropyRandomizedExperiment.arguments = self.lastExp.args
        commons: EntropyRandomizedExperiment.commonparams = self.lastExp.commons
        circuit = self.waves[commons.waveKey]
        numQubits = circuit.num_qubits

        qcList = []
        unitaryList = {i: {
            j: random_unitary(2) for j in range(*args.unitary_loc)
        } for i in range(args.times)}

        print(f"| Build circuit: {commons.waveKey}", end="\r")
        for i in range(args.times):
            qFunc1 = QuantumRegister(numQubits, 'q1')
            cMeas1 = ClassicalRegister(
                args.measure[1]-args.measure[0], 'c1')
            qcExp1 = QuantumCircuit(qFunc1, cMeas1)
            qcExp1.name = f"{args.expName}-{i}"

            qcExp1.append(self.waves.call(
                wave=commons.waveKey,
            ), [qFunc1[i] for i in range(numQubits)])

            qcExp1.barrier()
            for j in range(*args.unitary_loc):
                qcExp1.append(unitaryList[i][j], [j])

            for j in range(*args.measure):
                qcExp1.measure(qFunc1[j], cMeas1[j-args.measure[0]])

            qcList.append(qcExp1)

        self.lastExp.beforewards.sideProduct['unitaryOP'] = unitaryList
        self.lastExp.beforewards.sideProduct['randomized'] = {i: {
            j: qubitOpToPauliCoeff(
                unitaryList[i][j])
            for j in range(*args.unitary_loc)
        } for i in range(args.times)}

        return qcList

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Union[int, tuple[int, int], None] = None,
        times: int = 100,
        measure: Union[int, tuple[int, int], None] = None,
        unitary_set: Union[int, tuple[int, int], None] = None,
        expName: str = 'exps',
        *args,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
        **otherArgs: any
    ):
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
            degree=degree,
            times=times,
            measure=measure,
            unitary_set=unitary_set,
            saveLocation=None,
            **otherArgs,
        )
        assert IDNow == self.lastID
        assert self.lastExp is not None

        if isinstance(saveLocation, (Path, str)):
            self.lastExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonablize=jsonablize,
            )

        return IDNow
