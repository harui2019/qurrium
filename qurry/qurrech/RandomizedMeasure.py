"""
===========================================================
Loschmidt Echo - Randomized Measure
===========================================================

"""
import time
import warnings
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Type, Any
import numpy as np
import tqdm
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator

from ..exceptions import QurryCythonImportError, QurryCythonUnavailableWarning
from ..qurrium import (
    QurryV5Prototype,
    ExperimentPrototype,
    AnalysisPrototype,
    qubit_selector
)
from ..qurrium.utils.randomized import (
    random_unitary,
    qubit_operator_to_pauli_coeff,
    ensemble_cell,
)
from ..tools import (
    qurryProgressBar,
    ProcessManager,
    workers_distribution,
    DEFAULT_POOL_SIZE
)
try:
    from ..boost.randomized import echoCellCore  # type: ignore
    CYTHON_AVAILABLE = True
    FAILED_PYX_IMPORT = None
except ImportError as err:
    FAILED_PYX_IMPORT = err
    CYTHON_AVAILABLE = False
    # pylint: disable=invalid-name, unused-argument

    def echoCellCore(*args, **kwargs):
        """Dummy function for purityCellCore."""
        raise QurryCythonImportError(
            "Cython is not available, using python to calculate purity cell." +
            f" More infomation about this error: {FAILED_PYX_IMPORT}")
    # pylint: enable=invalid-name, unused-argument


def _echo_cell_cy(
    idx: int,
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
) -> tuple[int, float]:

    return idx, echoCellCore(
        dict(first_counts), dict(second_counts), bitstring_range, subsystem_size)


def _echo_cell(
    idx: int,
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
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

    shots = sum(first_counts.values())
    shots2 = sum(second_counts.values())
    assert shots == shots2, f"shots {shots} does not match shots2 {shots2}"

    first_counts_under_degree = dict.fromkeys(
        [k[bitstring_range[0]:bitstring_range[1]] for k in first_counts], 0)
    for bitstring in list(first_counts):
        first_counts_under_degree[
            bitstring[bitstring_range[0]:bitstring_range[1]]
        ] += first_counts[bitstring]

    second_counts_under_degree = dict.fromkeys(
        [k[bitstring_range[0]:bitstring_range[1]] for k in second_counts], 0)
    for bitstring in list(second_counts):
        second_counts_under_degree[
            bitstring[bitstring_range[0]:bitstring_range[1]]
        ] += second_counts[bitstring]

    echo_cell = np.float64(0)
    for s_i, s_i_meas in first_counts_under_degree.items():
        for s_j, s_j_meas in second_counts_under_degree.items():
            echo_cell += ensemble_cell(
                s_i, s_i_meas, s_j, s_j_meas, subsystem_size, shots)

    return idx, echo_cell


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
        subsystem_size = degree
        degree = qubit_selector(
            len(list(counts[0].keys())[0]), degree=degree)

    elif isinstance(degree, (tuple, list)):
        subsystem_size = max(degree) - min(degree)

    else:
        raise ValueError(
            f"'degree' must be 'int' or 'tuple[int, int]', but get '{degree}'.")

    if measure is None:
        measure = qubit_selector(len(list(counts[0].keys())[0]))

    if (min(degree) < min(measure)) or (max(degree) > max(measure)):
        raise ValueError(
            f"Measure range '{measure}' does not contain subsystem '{degree}'.")

    bitstring_range = (min(degree) - min(measure), max(degree) - min(measure))
    print(
        f"| Subsystem size: {subsystem_size}, bitstring range: {bitstring_range}, measure range: {measure}.")

    times = len(counts)/2
    assert times == int(times), f"counts {len(counts)} is not even."
    times = int(times)
    counts_pair = list(zip(counts[:times], counts[times:]))

    begin_time = time.time()

    msg = (
        f"| Partition: {bitstring_range}, Measure: {measure}"
    )

    if not (CYTHON_AVAILABLE and use_cython):
        warnings.warn(
            "Cython is not available, using python to calculate purity cell." +
            f" More infomation about this error: {FAILED_PYX_IMPORT}",
            category=QurryCythonUnavailableWarning,
        )
    cell_calculator = (_echo_cell_cy if (
        use_cython and CYTHON_AVAILABLE) else _echo_cell)

    if launch_worker == 1:
        echo_cell_items = []
        msg += f", single process, {times} overlaps, it will take a lot of time."
        if not _hide_print:
            print(msg)
        for i, (c1, c2) in enumerate(counts_pair):
            if not _hide_print:
                print(" "*150, end="\r")
                print(
                    f"| Calculating overlap {i} and {times+i} " +
                    f"by summarize {len(c1)*len(c2)} values - {i+1}/{times}" +
                    f" - {round(time.time() - begin_time, 3)}s.", end="\r")
            echo_cell_items.append(cell_calculator(
                i, c1, c2, bitstring_range, subsystem_size))

        if not _hide_print:
            print(" "*150, end="\r")
        take_time = round(time.time() - begin_time, 3)
    else:
        msg += f", {launch_worker} workers, {times} overlaps."

        pool = ProcessManager(launch_worker)
        echo_cell_items = pool.starmap(
            cell_calculator, [
                (i, c1, c2, bitstring_range, subsystem_size) 
            for i, (c1, c2) in enumerate(counts_pair)])
        take_time = round(time.time() - begin_time, 3)

    if not _hide_print:
        print(f"| Calculating overlap end - {take_time}s.")

    purity_cell_dict = dict(echo_cell_items)
    return purity_cell_dict, bitstring_range, measure, msg, take_time


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
        echo_cell_dict,
        bitstring_range,
        measure_range,
        msg_of_process,
        takeTime,
    ) = _overlap_echo_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        workers_num=workers_num,
        use_cython=use_cython,
    )
    echo_cell_list = list(echo_cell_dict.values())

    echo = np.mean(echo_cell_list, dtype=np.float64)
    purity_sd = np.std(echo_cell_list, dtype=np.float64)

    quantity = {
        'echo': echo,
        'echoCells': echo_cell_dict,
        'echoSD': purity_sd,

        'degree': degree,
        'measureActually': measure_range,
        'bitStringRange': bitstring_range,

        'countsNum': len(counts),
    }

    return quantity


def _circuit_method_core(
    idx: int,
    target_circuit: QuantumCircuit,
    expName: str,
    unitary_loc: tuple[int, int],
    unitary_sub_list: dict[int, Operator],
    measure: tuple[int, int],
) -> QuantumCircuit:

    num_qubits = target_circuit.num_qubits

    q_func1 = QuantumRegister(num_qubits, 'q1')
    c_meas1 = ClassicalRegister(
        measure[1]-measure[0], 'c1')
    qc_exp1 = QuantumCircuit(q_func1, c_meas1)
    qc_exp1.name = f"{expName}-{idx}"

    qc_exp1.append(target_circuit, [q_func1[i] for i in range(num_qubits)])

    qc_exp1.barrier()
    for j in range(*unitary_loc):
        qc_exp1.append(unitary_sub_list[j], [j])

    for j in range(*measure):
        qc_exp1.measure(q_func1[j], c_meas1[j-measure[0]])

    return qc_exp1


class EchoRandomizedAnalysis(AnalysisPrototype):
    """The analysis of loschmidt echo.
    """

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


class EchoRandomizedExperiment(ExperimentPrototype):
    """Randomized measure experiment.

    - Reference:
        - Used in:
            Simple mitigation of global depolarizing errors in quantum simulations - 
            Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self, 
            Christopher and Kim, M. S. and Knolle, Johannes,
            [PhysRevE.104.035309](https://link.aps.org/doi/10.1103/PhysRevE.104.035309)

        - `bibtex`:

    ```bibtex
        @article{PhysRevE.104.035309,
            title = {Simple mitigation of global depolarizing errors in quantum simulations},
            author = {Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self, 
            Christopher and Kim, M. S. and Knolle, Johannes},
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
        degree: Optional[Union[tuple[int, int], int]] = None,
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
                purity of all system, entropy of all system, 
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """

        if degree is None:
            raise ValueError(
                "degree must be specified, but get None.")

        self.args: EchoRandomizedExperiment.arguments
        shots = self.commons.shots
        measure = self.args.measure
        unitary_loc = self.args.unitary_loc
        counts = self.afterwards.counts

        if isinstance(pbar, tqdm.tqdm):
            qs = self.quantities(
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
                qs = self.quantities(
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

    @classmethod
    def quantities(
        cls,
        shots: int = None,
        counts: list[dict[str, int]] = None,
        degree: Union[tuple[int, int], int] = None,
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
            measure (tuple[int, int], optional): 
                Measuring range on quantum circuits. Defaults to None.
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
                purity of all system, entropy of all system, 
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """
        if any(i is None for i in [shots, counts, degree]):
            raise ValueError(
                "shots, counts, degree must be specified, but get None.")

        return overlap_echo(
            shots=shots,
            counts=counts,
            degree=degree,
            measure=measure,
            workers_num=workers_num,
            pbar=pbar,
            use_cython=use_cython,
        )


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
            j: qubit_operator_to_pauli_coeff(
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
            waveKey=wave,
            waveKey2=wave2,
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
                jsonable=jsonablize,
            )

        return IDNow
