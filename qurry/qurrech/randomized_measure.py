"""
===========================================================
Loschmidt Echo - Randomized Measure
===========================================================

"""
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Type, Any
import tqdm
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator

from ..qurrium import (
    QurryV5Prototype,
    ExperimentPrototype,
    AnalysisPrototype,
)
from ..qurrium.utils.randomized import (
    local_random_unitary_operators,
    local_random_unitary_pauli_coeff,
    random_unitary,
)
from ..process.utils import qubit_selector
from ..process.randomized_measure.wavefunction_overlap import (
    randomized_overlap_echo,
    ExistingProcessBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)
from ..tools import (
    qurry_progressbar,
    ProcessManager,
    DEFAULT_POOL_SIZE,
)


def circuit_method_core(
    idx: int,
    target_circuit: QuantumCircuit,
    exp_name: str,
    unitary_loc: tuple[int, int],
    unitary_sub_list: dict[int, Operator],
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
        qc_exp1.append(unitary_sub_list[j], [j])

    for j in range(*measure):
        qc_exp1.measure(q_func1[j], c_meas1[j - measure[0]])

    return qc_exp1


class EchoRandomizedAnalysis(AnalysisPrototype):
    """The analysis of loschmidt echo."""

    __name__ = "qurrechRandomized.Analysis"
    shortName = "qurrech_haar.report"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

        degree: tuple[int, int]
        shots: int
        unitary_loc: tuple[int, int] = None

    class AnalysisContent(NamedTuple):
        """The content of the analysis."""

        echo: float
        """The purity of the system."""
        echoSD: float
        """The standard deviation of the purity of the system."""
        echoCells: dict[int, float]
        """The echo of each cell of the system."""
        bitStringRange: tuple[int, int]
        """The qubit range of the subsystem."""

        measureActually: Optional[tuple[int, int]] = None
        """The qubit range of the measurement actually used."""
        countsNum: Optional[int] = None
        """The number of counts of the experiment."""
        takingTime: Optional[float] = None
        """The taking time of the selected system."""

        def __repr__(self):
            return f"AnalysisContent(echo={self.echo}, and others)"

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return [
            "echoCells",
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

    __name__ = "qurrechRandomized.Experiment"
    shortName = "qurrech_haar.exp"

    class Arguments(NamedTuple):
        """Arguments for the experiment."""

        exp_name: str = "exps"
        wave_key_2: Hashable = None
        times: int = 100
        measure: tuple[int, int] = None
        unitary_loc: tuple[int, int] = None
        workers_num: int = DEFAULT_POOL_SIZE

    @classmethod
    @property
    def analysis_container(cls) -> Type[EchoRandomizedAnalysis]:
        """The container class responding to this QurryV5 class."""
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
            raise ValueError("degree must be specified, but get None.")

        self.args: EchoRandomizedExperiment.Arguments
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
        backend: ExistingProcessBackendLabel = DEFAULT_PROCESS_BACKEND,
        workers_num: Optional[int] = None,
        pbar: Optional[tqdm.tqdm] = None,
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
        if shots is None or counts is None:
            raise ValueError("shots and counts should be specified.")

        return randomized_overlap_echo(
            shots=shots,
            counts=counts,
            degree=degree,
            measure=measure,
            backend=backend,
            workers_num=workers_num,
            pbar=pbar,
        )


class EchoRandomizedListen(QurryV5Prototype):
    """Randomized measure experiment."""

    __name__ = "qurrechRandomized"
    shortName = "qurrech_haar"

    tqdm_handleable = True
    """The handleable of tqdm."""

    @classmethod
    @property
    def experiment(cls) -> Type[EchoRandomizedExperiment]:
        """The container class responding to this QurryV5 class."""
        return EchoRandomizedExperiment

    def params_control(
        self,
        wave_key: Hashable = None,
        wave_key_2: Union[Hashable, QuantumCircuit] = None,
        exp_name: str = "exps",
        times: int = 100,
        measure: tuple[int, int] = None,
        unitary_loc: tuple[int, int] = None,
        **other_kwargs: any,
    ) -> tuple[
        EchoRandomizedExperiment.Arguments,
        EchoRandomizedExperiment.Commonparams,
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

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """
        # wave
        if isinstance(wave_key_2, QuantumCircuit):
            wave_key_2 = self.add(wave_key_2)
        elif isinstance(wave_key_2, Hashable):
            if wave_key_2 is None:
                ...
            elif not self.has(wave_key_2):
                raise KeyError(f"Wave '{wave_key_2}' not found in '.waves'")
        else:
            raise TypeError(
                f"'{wave_key_2}' is a '{type(wave_key_2)}' "
                + "instead of 'QuantumCircuit' or 'Hashable'"
            )

        num_qubits = self.waves[wave_key].num_qubits
        num_qubits2 = self.waves[wave_key_2].num_qubits
        if num_qubits != num_qubits2:
            raise ValueError(
                "The number of qubits of two wave functions must be the same, "
                + f"but {wave_key}: {num_qubits} != {wave_key_2}: {num_qubits2}."
            )

        # times
        if not isinstance(times, int):
            raise ValueError(f"times should be an integer, but got {times}.")

        # measure and unitary location
        num_qubits = self.waves[wave_key].num_qubits
        num_qubits2 = self.waves[wave_key_2].num_qubits
        if num_qubits != num_qubits2:
            raise ValueError(
                "The number of qubits of two wave functions must be the same, "
                + f"but {wave_key}: {num_qubits} != {wave_key_2}: {num_qubits2}."
            )

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

        exp_name = f"w={wave_key}+{wave_key_2}.with{times}random.{self.shortName}"

        return self.experiment.filter(
            exp_name=exp_name,
            wave_key=wave_key,
            wave_key_2=wave_key_2,
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
        args: EchoRandomizedExperiment.Arguments = self.exps[exp_id].args
        commons: EchoRandomizedExperiment.Commonparams = self.exps[exp_id].commons
        circuit = self.waves[commons.wave_key]
        circuit2 = self.waves[args.wave_key_2]

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Preparing {args.times} random unitary with {args.workers_num} workers."
            )

        unitary_dict = {
            i: {j: random_unitary(2) for j in range(*args.unitary_loc)}
            for i in range(args.times)
        }

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Building {args.times} circuits with {args.workers_num} workers."
            )

        pool = ProcessManager(args.workers_num)
        qc_list = pool.starmap(
            circuit_method_core,
            [
                (
                    i,
                    circuit,
                    args.exp_name,
                    args.unitary_loc,
                    unitary_dict[i],
                    args.measure,
                )
                for i in range(args.times)
            ]
            + [
                (
                    i + args.times,
                    circuit2,
                    args.exp_name,
                    args.unitary_loc,
                    unitary_dict[i],
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
            [(args.unitary_loc, unitary_dict[i]) for i in range(args.times)],
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
        current_exp.beforewards.side_product["randomized"] = dict(
            enumerate(randomized_list)
        )

        # currentExp.beforewards.side_product['randomized'] = {i: {
        #     j: qubitOpToPauliCoeff(
        #         unitaryList[i][j])
        #     for j in range(*args.unitary_loc)
        # } for i in range(args.times)}

        return qc_list

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        times: int = 100,
        measure: Union[int, tuple[int, int], None] = None,
        unitary_loc: Union[int, tuple[int, int], None] = None,
        exp_name: str = "exps",
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

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The output.
        """

        id_now = self.result(
            wave=wave,  # First wave will be taken by _paramsControlMain
            wave_key_2=wave2,  # Second wave will be taken by paramsControl
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
