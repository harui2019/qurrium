"""
===========================================================
Second Renyi Entropy - Randomized Measurement 
(:mod:`qurry.qurrent.RandomizedMeasure`)
===========================================================

"""
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Type, Literal, Any
import numpy as np
import tqdm

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator

from ..qurrium import (
    QurryV5Prototype,
    ExperimentPrototype,
    AnalysisPrototype,
)
from ..qurrium.utils.randomized import (
    random_unitary,
    local_random_unitary_operators,
    local_random_unitary_pauli_coeff,
)
from ..qurrium.utils.construct import qubit_selector
from ..tools import qurry_progressbar, ProcessManager, DEFAULT_POOL_SIZE
from .postprocess import (
    ExistingProcessBackendLabel,
    DEFAULT_PROCESS_BACKEND,
    depolarizing_error_mitgation,
    entangled_entropy_core,
)


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

    allSystemSource: Optional[Union[str, Literal["independent"]]] = None
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

    takingTime: Optional[float] = None
    """The taking time of the selected system."""
    takingTimeAllSys: Optional[float] = None
    """The taking time of the all system if it is calculated, 
    it will be 0 when use the all system from other analysis."""

    def __repr__(self):
        return (
            f"AnalysisContent(purity={self.purity}, entropy={self.entropy}, and others)"
        )


def randomized_entangled_entropy_complex(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    all_system_source: Optional["EntropyRandomizedAnalysis"] = None,
    backend: ExistingProcessBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: Optional[int] = None,
    pbar: Optional[tqdm.tqdm] = None,
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
        degree (Optional[Union[tuple[int, int], int]]): Degree of the subsystem.
        measure (Optional[tuple[int, int]], optional):
            Measuring range on quantum circuits. Defaults to None.
        all_system_source (Optional['EntropyRandomizedAnalysis'], optional):
            The source of the all system. Defaults to None.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
        workers_num (Optional[int], optional):
            Number of multi-processing workers, it will be ignored if backend is Rust.
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            Defaults to None.
        pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.

    Returns:
        dict[str, float]: A dictionary contains
            purity, entropy, a list of each overlap, puritySD,
            purity of all system, entropy of all system,
            a list of each overlap in all system, puritySD of all system,
            degree, actual measure range, actual measure range in all system, bitstring range.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(f"Calculate specific degree {degree} by {backend}.")
    (
        purity_cell_dict,
        bitstring_range,
        measure_range,
        msg,
        taken,
    ) = entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        backend=backend,
        multiprocess_pool_size=workers_num,
    )
    purity_cell_list = list(purity_cell_dict.values())

    if all_system_source is None:
        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(f"Calculate all system by {backend}.")
        (
            purity_cell_dict_allsys,
            bitstring_range_allsys,
            measure_range_allsys,
            _msg_allsys,
            taken_allsys,
        ) = entangled_entropy_core(
            shots=shots,
            counts=counts,
            degree=None,
            measure=measure,
            backend=backend,
            multiprocess_pool_size=workers_num,
        )
        purity_cell_list_allsys = list(purity_cell_dict_allsys.values())
        source = "independent"
    else:
        content: EntropyAnalysisContent = all_system_source.content
        source = str(all_system_source.header)
        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(f"Using existing all system from '{source}'")
        purity_cell_dict_allsys = content.purityCellsAllSys
        assert (
            purity_cell_dict_allsys is not None
        ), "all_system_source.content.purityCells is None"
        purity_cell_list_allsys = list(purity_cell_dict_allsys.values())
        bitstring_range_allsys = content.bitStringRange
        measure_range_allsys = content.measureActually
        _msg_allsys = f"Use all system from {source}."
        taken_allsys = 0

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(
            f"Preparing error mitigation of {bitstring_range} on {measure}"
        )

    purity: float = np.mean(purity_cell_list, dtype=np.float64)
    purity_allsys: float = np.mean(purity_cell_list_allsys, dtype=np.float64)
    purity_sd = np.std(purity_cell_list, dtype=np.float64)
    purity_sd_allsys = np.std(purity_cell_list_allsys, dtype=np.float64)

    entropy = -np.log2(purity, dtype=np.float64)
    entropy_sd = purity_sd / np.log(2) / purity
    entropy_allsys = -np.log2(purity_allsys, dtype=np.float64)
    entropy_sd_allsys = purity_sd_allsys / np.log(2) / purity_allsys

    if measure is None:
        measure_info = "not specified, use all qubits"
    else:
        measure_info = f"measure range: {measure}"

    num_qubits = len(list(counts[0].keys())[0])
    if isinstance(degree, tuple):
        subsystem = max(degree) - min(degree)
    else:
        subsystem = degree

    error_mitgation_info = depolarizing_error_mitgation(
        meas_system=purity,
        all_system=purity_allsys,
        n_a=subsystem,
        system_size=num_qubits,
    )

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(msg[2:-1] + " with mitigation.")

    quantity = {
        # target system
        "purity": purity,
        "entropy": entropy,
        "purityCells": purity_cell_dict,
        "puritySD": purity_sd,
        "entropySD": entropy_sd,
        "bitStringRange": bitstring_range,
        # all system
        "allSystemSource": source,  # 'independent' or 'header of analysis'
        "purityAllSys": purity_allsys,
        "entropyAllSys": entropy_allsys,
        "purityCellsAllSys": purity_cell_dict_allsys,
        "puritySDAllSys": purity_sd_allsys,
        "entropySDAllSys": entropy_sd_allsys,
        "bitsStringRangeAllSys": bitstring_range_allsys,
        # mitigated
        "errorRate": error_mitgation_info["errorRate"],
        "mitigatedPurity": error_mitgation_info["mitigatedPurity"],
        "mitigatedEntropy": error_mitgation_info["mitigatedEntropy"],
        # info
        "degree": degree,
        "num_qubits": num_qubits,
        "measure": measure_info,
        "measureActually": measure_range,
        "measureActuallyAllSys": measure_range_allsys,
        "countsNum": len(counts),
        "takingTime": taken,
        "takingTimeAllSys": taken_allsys,
    }
    return quantity


def circuit_method_core(
    idx: int,
    target_circuit: QuantumCircuit,
    exp_name: str,
    unitary_loc: tuple[int, int],
    unitary_sublist: dict[int, Operator],
    measure: tuple[int, int],
) -> QuantumCircuit:
    """Build the circuit for the experiment.

    Args:
        idx (int): Index of the randomized unitary.
        target_circuit (QuantumCircuit): Target circuit.
        exp_name (str): Experiment name.
        unitary_loc (tuple[int, int]): Unitary operator location.
        unitary_sublist (dict[int, Operator]): Unitary operator list.
        measure (tuple[int, int]): Measure range.

    Returns:
        QuantumCircuit: The circuit for the experiment.
    """

    num_qubits = target_circuit.num_qubits

    q_func1 = QuantumRegister(num_qubits, "q1")
    c_meas1 = ClassicalRegister(measure[1] - measure[0], "c1")
    qc_exp1 = QuantumCircuit(q_func1, c_meas1)
    qc_exp1.name = f"{exp_name}-{idx}"

    qc_exp1.append(target_circuit, [q_func1[i] for i in range(num_qubits)])

    qc_exp1.barrier()
    for j in range(*unitary_loc):
        qc_exp1.append(unitary_sublist[j], [j])

    for j in range(*measure):
        qc_exp1.measure(q_func1[j], c_meas1[j - measure[0]])

    return qc_exp1


class EntropyRandomizedAnalysis(AnalysisPrototype):
    """The container for the analysis of :cls:`EntropyRandomizedExperiment`."""

    __name__ = "qurrentRandomized.Analysis"
    shortName = "qurrent_haar.report"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

        degree: tuple[int, int]
        shots: int
        unitary_loc: tuple[int, int] = None

    AnalysisContent = EntropyAnalysisContent
    """The content of the analysis."""
    # It works ...

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return [
            "purityCells",
            "purityCellsAllSys",
        ]


class EntropyRandomizedExperiment(ExperimentPrototype):
    """The instance for the experiment of :cls:`EntropyRandomizedMeasure`."""

    __name__ = "qurrentRandomized.Experiment"
    shortName = "qurrent_haar.exp"

    tqdm_handleable = True
    """The handleable of tqdm."""

    class Arguments(NamedTuple):
        """Arguments for the experiment."""

        exp_name: str = "exps"
        times: int = 100
        measure: tuple[int, int] = None
        unitary_loc: tuple[int, int] = None
        workers_num: int = DEFAULT_POOL_SIZE

    @classmethod
    @property
    def analysis_container(cls) -> Type[EntropyRandomizedAnalysis]:
        """The container class responding to this QurryV5 class."""
        return EntropyRandomizedAnalysis

    def analyze(
        self,
        degree: Union[tuple[int, int], int] = None,
        workers_num: Optional[int] = None,
        independent_all_system: bool = False,
        backend: ExistingProcessBackendLabel = DEFAULT_PROCESS_BACKEND,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> EntropyRandomizedAnalysis:
        """Calculate entangled entropy with more information combined.

        Args:
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            workers_num (Optional[int], optional):
                Number of multi-processing workers,
                if sets to 1, then disable to using multi-processing;
                if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
                Defaults to None.
            independent_all_system (bool, optional):
                If True, then calculate the all system independently.
            backend (ExistingProcessBackendLabel, optional):
                Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
            pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy, a list of each overlap, puritySD,
                purity of all system, entropy of all system,
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """
        if degree is None:
            raise ValueError("degree should be specified.")

        self.args: EntropyRandomizedExperiment.Arguments
        self.reports: dict[int, EntropyRandomizedAnalysis]
        shots = self.commons.shots
        measure = self.args.measure
        unitary_loc = self.args.unitary_loc
        counts = self.afterwards.counts

        available_all_system_source = [
            k
            for k, v in self.reports.items()
            if v.content.allSystemSource == "independent"
        ]

        if len(available_all_system_source) > 0 and not independent_all_system:
            all_system_source = self.reports[available_all_system_source[-1]]
        else:
            all_system_source = None

        if isinstance(pbar, tqdm.tqdm):
            qs = self.quantities(
                shots=shots,
                counts=counts,
                degree=degree,
                measure=measure,
                all_system_source=all_system_source,
                backend=backend,
                workers_num=workers_num,
                pbar=pbar,
            )

        else:
            pbar_selfhost = qurry_progressbar(
                range(1),
                bar_format="simple",
            )

            with pbar_selfhost as pb_self:
                qs = self.quantities(
                    shots=shots,
                    counts=counts,
                    degree=degree,
                    measure=measure,
                    all_system_source=all_system_source,
                    backend=backend,
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
        degree: Optional[Union[tuple[int, int], int]] = None,
        measure: Optional[tuple[int, int]] = None,
        all_system_source: Optional["EntropyRandomizedAnalysis"] = None,
        backend: ExistingProcessBackendLabel = DEFAULT_PROCESS_BACKEND,
        workers_num: Optional[int] = None,
        pbar: Optional[tqdm.tqdm] = None,
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
            degree (Optional[Union[tuple[int, int], int]]): Degree of the subsystem.
            measure (Optional[tuple[int, int]], optional):
                Measuring range on quantum circuits. Defaults to None.
            all_system_source (Optional['EntropyRandomizedAnalysis'], optional):
                The source of the all system. Defaults to None.
            backend (ExistingProcessBackendLabel, optional):
                Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
            workers_num (Optional[int], optional):
                Number of multi-processing workers, it will be ignored if backend is Rust.
                if sets to 1, then disable to using multi-processing;
                if not specified, then use the number of all cpu counts by `os.cpu_count()`.
                Defaults to None.
            pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy, a list of each overlap, puritySD,
                purity of all system, entropy of all system,
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """

        if shots is None or counts is None:
            raise ValueError("shots and counts should be specified.")

        return randomized_entangled_entropy_complex(
            shots=shots,
            counts=counts,
            degree=degree,
            measure=measure,
            all_system_source=all_system_source,
            backend=backend,
            workers_num=workers_num,
            pbar=pbar,
        )


class EntropyRandomizedMeasure(QurryV5Prototype):
    """Randomized Measure Experiment.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

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

    __name__ = "qurrentRandomized"
    shortName = "qurrent_haar"

    @classmethod
    @property
    def experiment(cls) -> Type[EntropyRandomizedExperiment]:
        """The container class responding to this QurryV5 class."""
        return EntropyRandomizedExperiment

    def params_control(
        self,
        wave_key: Hashable = None,
        exp_name: str = "exps",
        times: int = 100,
        measure: tuple[int, int] = None,
        unitary_loc: tuple[int, int] = None,
        **other_kwargs,
    ) -> tuple[
        EntropyRandomizedExperiment.Arguments,
        EntropyRandomizedExperiment.Commonparams,
        dict[str, Any],
    ]:
        """Handling all arguments and initializing a single experiment.

        Args:
            wave_key (Hashable):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            exp_name (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            other_kwargs (any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """

        # times
        if not isinstance(times, int):
            raise ValueError(f"times should be an integer, but got {times}.")

        # measure and unitary location
        num_qubits = self.waves[wave_key].num_qubits
        if measure is None:
            measure = num_qubits
        measure = qubit_selector(num_qubits, degree=measure)

        if unitary_loc is None:
            unitary_loc = num_qubits
        unitary_loc = qubit_selector(num_qubits, degree=unitary_loc)

        if (min(measure) < min(unitary_loc)) or (max(measure) > max(unitary_loc)):
            raise ValueError(
                f"unitary_loc range '{unitary_loc}' does not contain measure range '{measure}'."
            )

        exp_name = f"w={wave_key}.with{times}random.{self.shortName}"

        return self.experiment.filter(
            exp_name=exp_name,
            wave_key=wave_key,
            times=times,
            measure=measure,
            unitary_loc=unitary_loc,
            **other_kwargs,
        )

    def method(
        self,
        exp_id: str,
        _pbar: Optional[tqdm.tqdm] = None,
    ) -> list[QuantumCircuit]:
        assert exp_id in self.exps
        assert self.exps[exp_id].commons.exp_id == exp_id
        current_exp = self.exps[exp_id]
        args: EntropyRandomizedExperiment.Arguments = self.exps[exp_id].args
        commons: EntropyRandomizedExperiment.Commonparams = self.exps[exp_id].commons
        circuit = self.waves[commons.wave_key]
        _num_qubits = circuit.num_qubits

        pool = ProcessManager(args.workers_num)

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Preparing {args.times} random unitary with {args.workers_num} workers."
            )

        # DO NOT USE MULTI-PROCESSING HERE !!!!!
        # See https://github.com/numpy/numpy/issues/9650
        # And https://github.com/harui2019/qurry/issues/78
        # The random seed will be duplicated in each process,
        # and it will make duplicated result.
        # unitaryList = pool.starmap(
        #     local_random_unitary, [(args.unitary_loc, None) for _ in range(args.times)])

        unitary_list = {
            i: {j: random_unitary(2) for j in range(*args.unitary_loc)}
            for i in range(args.times)
        }

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Building {args.times} circuits with {args.workers_num} workers."
            )
        qc_list = pool.starmap(
            circuit_method_core,
            [
                (
                    i,
                    circuit,
                    args.exp_name,
                    args.unitary_loc,
                    unitary_list[i],
                    args.measure,
                )
                for i in range(args.times)
            ],
        )

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Writing 'unitaryOP' with {args.workers_num} workers."
            )
        unitary_operator_list = pool.starmap(
            local_random_unitary_operators,
            [(args.unitary_loc, unitary_list[i]) for i in range(args.times)],
        )
        current_exp.beforewards.side_product["unitaryOP"] = dict(
            enumerate(unitary_operator_list)
        )

        # currentExp.beforewards.side_product['unitaryOP'] = {
        #     k: {i: np.array(v[i]).tolist() for i in range(*args.unitary_loc)}
        #     for k, v in unitaryList.items()}

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Writing 'randomized' with {args.workers_num} workers."
            )
        randomized_list = pool.starmap(
            local_random_unitary_pauli_coeff,
            [(args.unitary_loc, unitary_operator_list[i]) for i in range(args.times)],
        )
        current_exp.beforewards.side_product["randomized"] = {
            i: v for i, v in enumerate(randomized_list)
        }

        # currentExp.beforewards.side_product['randomized'] = {i: {
        #     j: qubitOpToPauliCoeff(
        #         unitaryList[i][j])
        #     for j in range(*args.unitary_loc)
        # } for i in range(args.times)}

        return qc_list

    def measure(
        self,
        wave: Union[QuantumCircuit, any],
        times: int = 100,
        measure: Union[int, tuple[int, int], None] = None,
        unitary_loc: Union[int, tuple[int, int], None] = None,
        exp_name: str = "exps",
        *,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonablize: bool = False,
        **other_kwargs: any,
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

            exp_name (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            other_kwargs (any):
                Other arguments.

        Returns:
            dict: The output.
        """

        id_now = self.result(
            wave=wave,
            exp_name=exp_name,
            times=times,
            measure=measure,
            unitary_loc=unitary_loc,
            save_location=None,
            **other_kwargs,
        )
        assert id_now in self.exps, f"ID {id_now} not found."
        assert self.exps[id_now].commons.exp_id == id_now
        current_exp = self.exps[id_now]

        if isinstance(save_location, (Path, str)):
            current_exp.write(
                save_location=save_location,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonablize,
            )

        return id_now
