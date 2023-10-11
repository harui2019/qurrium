from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator

import time
import tqdm
import numpy as np
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Type, Any

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
from ..tools import (
    qurryProgressBar,
    ProcessManager,
    workers_distribution,
    DEFAULT_POOL_SIZE
)
from ..boost.randomized import echoCellCore


def _echoCellCy(
    idx: int,
    firstCounts: dict[str, int],
    secondCounts: dict[str, int],
    bitStringRange: tuple[int, int],
    subsystemSize: int,
) -> tuple[int, float]:

    return idx, echoCellCore(
        dict(firstCounts), dict(secondCounts), bitStringRange, subsystemSize)


def _echoCell(
    idx: int,
    firstCounts: dict[str, int],
    secondCounts: dict[str, int],
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

    shots = sum(firstCounts.values())
    shots2 = sum(secondCounts.values())
    assert shots == shots2, f"shots {shots} does not match shots2 {shots2}"

    firstCountsUnderDegree = dict.fromkeys(
        [k[bitStringRange[0]:bitStringRange[1]] for k in firstCounts], 0)
    for bitString in list(firstCounts):
        firstCountsUnderDegree[
            bitString[bitStringRange[0]:bitStringRange[1]]
        ] += firstCounts[bitString]

    secondCountsUnderDegree = dict.fromkeys(
        [k[bitStringRange[0]:bitStringRange[1]] for k in secondCounts], 0)
    for bitString in list(secondCounts):
        secondCountsUnderDegree[
            bitString[bitStringRange[0]:bitStringRange[1]]
        ] += secondCounts[bitString]

    echoCell = np.float64(0)
    for sAi, sAiMeas in firstCountsUnderDegree.items():
        for sAj, sAjMeas in secondCountsUnderDegree.items():
            echoCell += ensembleCell(
                sAi, sAiMeas, sAj, sAjMeas, subsystemSize, shots)

    return idx, echoCell


def _overlap_echo_core(
    shots: int,
    counts: list[dict[str, int]],
    degree: Union[tuple[int, int], int],
    measure: tuple[int, int] = None,
    workers_num: Optional[int] = None,
    use_cython: bool = True,
    _hide_print: bool = False,
) -> tuple[dict[int, float], tuple[int, int], tuple[int, int]]:
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
        tuple[list[float], tuple[int, int], tuple[int, int]]: _description_
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
    if isinstance(degree, int):
        subsystemSize = degree
        degree = qubit_selector(
            len(list(counts[0].keys())[0]), degree=degree)

    elif isinstance(degree, (tuple, list)):
        subsystemSize = max(degree) - min(degree)

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

    times = len(counts)/2
    assert times == int(times), f"counts {len(counts)} is not even."
    times = int(times)
    countsPair = list(zip(counts[:times], counts[times:]))

    Begin = time.time()

    msg = (
        f"| Partition: {bitStringRange}, Measure: {measure}"
    )

    cellCalculator = (_echoCellCy if use_cython else _echoCell)

    if launch_worker == 1:
        echoCellItems = []
        msg += f", single process, {times} overlaps, it will take a lot of time."
        if not _hide_print:
            print(msg)
        for i, (c1, c2) in enumerate(countsPair):
            if not _hide_print:
                print(" "*150, end="\r")
                print(
                    f"| Calculating overlap {i} and {times+i} " +
                    f"by summarize {len(c1)*len(c2)} values - {i+1}/{times}" +
                    f" - {round(time.time() - Begin, 3)}s.", end="\r")
            echoCellItems.append(cellCalculator(
                i, c1, c2, bitStringRange, subsystemSize))

        if not _hide_print:
            print(" "*150, end="\r")
        takeTime = round(time.time() - Begin, 3)
    else:
        msg += f", {launch_worker} workers, {times} overlaps."

        pool = ProcessManager(launch_worker)
        echoCellItems = pool.starmap(
            cellCalculator, [(i, c1, c2, bitStringRange, subsystemSize) for i, (c1, c2) in enumerate(countsPair)])
        takeTime = round(time.time() - Begin, 3)

    if not _hide_print:
        print(f"| Calculating overlap end - {takeTime}s.")

    purityCellDict = {k: v for k, v in echoCellItems}
    return purityCellDict, bitStringRange, measure, msg, takeTime


def overlap_echo(
    shots: int,
    counts: list[dict[str, int]],
    degree: Union[tuple[int, int], int],
    measure: tuple[int, int] = None,
    workers_num: Optional[int] = None,
    pbar: Optional[tqdm.tqdm] = None,
    use_cython: bool = True,
) -> dict[str, float]:
    """Calculate entangled entropy.

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
        all_system_source (Optional['EntropyRandomizedAnalysis'], optional):
            The source of the all system. Defaults to None.
        use_cython (bool, optional): Use cython to calculate purity cell. Defaults to True.

    Returns:
        dict[str, float]: A dictionary contains purity, entropy, 
            a list of each overlap, puritySD, degree, actual measure range, bitstring range.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(
            f"Calculate overlap with {len(counts)} counts.")

    (
        echoCellDict,
        bitStringRange,
        measureRange,
        msgOfProcess,
        takeTime,
    ) = _overlap_echo_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        workers_num=workers_num,
        use_cython=use_cython,
    )
    echoCellList = list(echoCellDict.values())

    echo = np.mean(echoCellList, dtype=np.float64)
    puritySD = np.std(echoCellList, dtype=np.float64)

    quantity = {
        'echo': echo,
        'echoCells': echoCellDict,
        'echoSD': puritySD,

        'degree': degree,
        'measureActually': measureRange,
        'bitStringRange': bitStringRange,

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


class EchoRandomizedAnalysis(AnalysisPrototype):

    __name__ = 'qurrentRandomized.Analysis'
    shortName = 'qurrent_haar.report'

    class analysisInput(NamedTuple):
        """To set the analysis."""

        degree: tuple[int, int]
        shots: int
        unitary_loc: tuple[int, int] = None

    class analysisContent(NamedTuple):
        """The content of the analysis."""

        purity: float
        """The purity of the system."""
        entropy: float
        """The entanglement entropy of the system."""
        puritySD: float
        """The standard deviation of the purity of the system."""
        purityCells: dict[int, float]
        """The purity of each cell of the system."""
        bitStringRange: tuple[int, int]
        """The qubit range of the subsystem."""

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
        workers_num: Optional[int] = None,
        pbar: Optional[tqdm.tqdm] = None,
        use_cython: bool = True,
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
            pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.
            use_cython (bool, optional): Use cython to calculate purity cell. Defaults to True.
            
        Returns:
            dict[str, float]: A dictionary contains 
                purity, entropy, a list of each overlap, puritySD, 
                purity of all system, entropy of all system, a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """

        return overlap_echo(
            shots=shots,
            counts=counts,
            degree=degree,
            measure=measure,
            workers_num=workers_num,
            pbar=pbar,
            _hide_print=True,
            use_cython=use_cython,
        )


class EchoRandomizedExperiment(ExperimentPrototype):

    __name__ = 'qurrechRandomized.Experiment'
    shortName = 'qurrech_haar.exp'

    class arguments(NamedTuple):
        """Arguments for the experiment."""
        expName: str = 'exps'
        waveKey2: Hashable = None
        times: int = 100
        measure: tuple[int, int] = None
        unitary_loc: tuple[int, int] = None
        workers_num: int = DEFAULT_POOL_SIZE

    @classmethod
    @property
    def analysis_container(cls) -> Type[EchoRandomizedAnalysis]:
        """The container class responding to this QurryV5 class.
        """
        return EchoRandomizedAnalysis

    def analyze(
        self,
        degree: Union[tuple[int, int], int],
        workers_num: Optional[int] = None,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> EchoRandomizedAnalysis:
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

        self.args: EchoRandomizedExperiment.arguments
        shots = self.commons.shots
        measure = self.args.measure
        unitary_loc = self.args.unitary_loc
        counts = self.afterwards.counts

        if isinstance(pbar, tqdm.tqdm):
            qs = self.analysis_container.quantities(
                shots=shots,
                counts=counts,
                degree=degree,
                measure=measure,
                workers_num=workers_num,
                pbar=pbar,
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


class EchoRandomizedListen(QurryV5Prototype):

    __name__ = 'qurrechRandomized'
    shortName = 'qurrech_haar'

    tqdm_handleable = True
    """The handleable of tqdm."""

    @classmethod
    @property
    def experiment(cls) -> Type[EchoRandomizedExperiment]:
        """The container class responding to this QurryV5 class.
        """
        return EchoRandomizedExperiment

    def paramsControl(
        self,
        expName: str = 'exps',
        waveKey: Hashable = None,
        waveKey2: Hashable = None,
        times: int = 100,
        measure: tuple[int, int] = None,
        unitary_loc: tuple[int, int] = None,
        **otherArgs: any
    ) -> tuple[EchoRandomizedExperiment.arguments, EchoRandomizedExperiment.commonparams, dict[str, Any]]:
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
        num_qubits2 = self.waves[waveKey2].num_qubits
        if num_qubits != num_qubits2:
            raise ValueError(
                f"The number of qubits of two wave functions must be the same, but {waveKey}: {num_qubits} != {waveKey2}: {num_qubits2}.")

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

        expName = f"w={waveKey}+{waveKey2}.with{times}random.{self.shortName}"

        return self.experiment.filter(
            expName=expName,
            waveKey=waveKey,
            waveKey2=waveKey2,
            times=times,
            measure=measure,
            unitary_loc=unitary_loc,
            **otherArgs,
        )

    def method(
        self,
        expID: str,
    ) -> list[QuantumCircuit]:

        assert expID in self.exps
        assert self.exps[expID].commons.expID == expID
        currentExp = self.exps[expID]
        args: EchoRandomizedExperiment.arguments = self.exps[expID].args
        commons: EchoRandomizedExperiment.commonparams = self.exps[expID].commons
        circuit = self.waves[commons.waveKey]
        circuit2 = self.waves[args.waveKey2]

        unitaryList = {i: {
            j: random_unitary(2) for j in range(*args.unitary_loc)
        } for i in range(args.times)}

        if isinstance(commons.serial, int):
            ...
        else:
            print(f"| Build circuit: {commons.waveKey}.", end="\r")
        # for i in range(args.times):
        #     qFunc1 = QuantumRegister(num_qubits, 'q1')
        #     cMeas1 = ClassicalRegister(
        #         args.measure[1]-args.measure[0], 'c1')
        #     qcExp1 = QuantumCircuit(qFunc1, cMeas1)
        #     qcExp1.name = f"{args.expName}-{i}"

        #     qcExp1.append(self.waves.call(
        #         wave=commons.waveKey,
        #     ), [qFunc1[i] for i in range(num_qubits)])

        #     qcExp1.barrier()
        #     for j in range(*args.unitary_loc):
        #         qcExp1.append(unitaryList[i][j], [j])

        #     for j in range(*args.measure):
        #         qcExp1.measure(qFunc1[j], cMeas1[j-args.measure[0]])

        #     qcList.append(qcExp1)

        pool = ProcessManager(args.workers_num)
        qcList = pool.starmap(
            _circuit_method_core, [(
                i, circuit, args.expName, args.unitary_loc, unitaryList[i], args.measure
            ) for i in range(args.times)]+[(
                i+args.times, circuit2, args.expName, args.unitary_loc, unitaryList[i], args.measure
            ) for i in range(args.times)])
        if isinstance(commons.serial, int):
            ...
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
        wave2: Union[QuantumCircuit, any, None] = None,
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
            wave2=wave2,
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
