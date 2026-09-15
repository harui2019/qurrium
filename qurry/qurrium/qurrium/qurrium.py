"""Qurrium Runtime Instance (:mod:`qurry.qurrium.qurrium.qurrium`)"""

from abc import abstractmethod, ABC
from typing import Literal, Any, Generic
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend

from .mm_container import MultiManagerContainer
from .exps_wrapper import ExperimentContainerWrapper
from ..container import (
    RunArgsType,
    ConfigListType,
    _MA,
    _OA,
    TranspileArgs,
    PassManagerContainer,
    PassManagerType,
    WaveContainer,
    WCKeyable,
    passmanager_processor,
)
from ..analysis import SpecificAnalyzeArgs, _RA
from ..multimanager import (
    MultiManager,
    PendingTargetProviderLiteral,
    PendingStrategyLiteral,
    ExperimentContainer,
    _E,
)
from ..utils.build import check_cregs_name_collision
from ...tools import qurry_progressbar
from ...tools.backend import GeneralSimulator
from ...tools.qiskit_version import qiskit_version_v0_check
from ...capsule import DEFAULT_INDENT


class QurriumPrototype(ABC, Generic[_E, _MA, _OA, _RA]):
    """Qurrium

    *~ Create countless adventure, legacy and tales. ~*
    """

    __name__ = "QurriumPrototype"
    """The name of Qurrium."""
    short_name = "qurrium"
    """The short name of Qurrium."""
    reserved_register_names: set[str] = set()
    """The set of reserved classical register names."""

    # Wave
    def add(
        self,
        wave: QuantumCircuit,
        key: WCKeyable | None = None,
        replace: Literal[True, False, "duplicate"] = True,
    ) -> WCKeyable:
        """Add new wave function to measure.

        Args:
            wave (QuantumCircuit): The wave functions or circuits want to measure.
            key (WCKeyable | None, optional):
                Given a specific key to add to the wave function or circuit,
                if `key == None`, then generate a number as key.
                Defaults to None.
            replace (Literal[True, False, 'duplicate'], optional):
                If the key is already in the wave function or circuit,
                then replace the old wave function or circuit when `True`,
                or duplicate the wave function or circuit when `'duplicate'`.
                Defaults to `True`.

        Returns:
            WCKeyable | None: Key of given wave function in `.waves`.
        """
        if len(self.reserved_register_names) > 0:
            for creg in wave.cregs:
                check_cregs_name_collision(wave, creg.name)
        return self.waves.add(wave=wave, key=key, replace=replace)

    def remove(self, key: WCKeyable) -> None:
        """Remove wave function from `.waves`.

        Args:
            wave (WCKeyable): The key of wave in `.waves`.
        """
        self.waves.remove(key)

    def has(self, wavename: WCKeyable) -> bool:
        """Is there a wave with specific name.

        Args:
            wavename (WCKeyable): Name of wave which is used in `.waves`

        Returns:
            bool: Exist or not.
        """
        return self.waves.has(wavename)

    @property
    @abstractmethod
    def experiment_instance(self) -> type[_E]:
        """The instance of experiment."""
        raise NotImplementedError("The experiment is not defined.")

    def __init__(self) -> None:
        self.waves: WaveContainer = WaveContainer()
        """The wave functions container."""

        self.orphan_exps: ExperimentContainer[_E] = ExperimentContainer()
        """The orphan experiments container."""

        self.multimanagers: MultiManagerContainer[_E] = MultiManagerContainer()
        """The last multimanager be called."""

        self.passmanagers: PassManagerContainer = PassManagerContainer()
        """The collection of pass managers."""

        self.exps: ExperimentContainerWrapper[_E] = ExperimentContainerWrapper(
            orphan_exps=self.orphan_exps,
            multimanagers=self.multimanagers,
        )
        """The wrapper of experiments container from orphan_exps and multimanagers."""

        if hasattr(self, "__post_init__"):
            # Call the __post_init__ method if it exists
            getattr(self, "__post_init__")()

        qiskit_version_v0_check()

    def build(
        self,
        circuits: list[QuantumCircuit | WCKeyable],
        shots: int = 1024,
        backend: Backend | None = None,
        exp_name: str = "experiment",
        run_args: RunArgsType = None,
        transpile_args: TranspileArgs | None = None,
        passmanager: PassManagerType | None = None,
        tags: tuple[str, ...] | None = None,
        # process tool
        qasm_version: Literal["qasm2", "qasm3"] = "qasm3",
        export: bool = False,
        save_location: Path | str | None = None,
        pbar: tqdm.tqdm | None = None,
        **custom_and_main_kwargs: Any,
    ) -> str:
        """Build the experiment.

        Args:
            circuits (list[QuantumCircuit | WCKeyable]):
                The circuits or keys of circuits in `.waves`.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend, optional):
                The quantum backend. Defaults to AerSimulator().
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it
                when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            run_args (RunArgsType, optional):
                Arguments for :meth:`Backend.run`. Defaults to None.
            transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`~qiskit.compiler.transpile`.
                Defaults to None.
            passmanager (PassManagerType | None, optional):
                The passmanager. Defaults to None.
            tags (tuple[str, ...] | None, optional):
                Given tags for the experiment to describe it.

            qasm_version (Literal["qasm2", "qasm3"], optional):
                The export version of OpenQASM. Defaults to 'qasm3'.
            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Path | str | None, optional):
                The location to save the experiment. Defaults to None.
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment. Defaults to None.
            custom_and_main_kwargs (Any):
                Other custom arguments.

        Returns:
            str: The ID of the experiment.
        """
        passmanager_pair = passmanager_processor(
            passmanager=passmanager, passmanager_container=self.passmanagers
        )
        targets = self.waves.process(circuits)

        new_exps = self.experiment_instance.build(
            targets=targets,
            shots=shots,
            backend=backend,
            exp_name=exp_name,
            run_args=run_args,
            transpile_args=transpile_args,
            passmanager_pair=passmanager_pair,
            tags=tags,
            # process tool
            qasm_version=qasm_version,
            export=export,
            save_location=save_location,
            pbar=pbar,
            **custom_and_main_kwargs,
        )

        self.orphan_exps[new_exps.commons.exp_id] = new_exps
        return new_exps.exp_id

    def output(
        self,
        # create new exp
        circuits: list[QuantumCircuit | WCKeyable] | None = None,
        shots: int = 1024,
        backend: Backend | None = None,
        exp_name: str = "experiment",
        run_args: RunArgsType = None,
        transpile_args: TranspileArgs | None = None,
        passmanager: PassManagerType | None = None,
        tags: tuple[str, ...] | None = None,
        # already built exp
        exp_id: str | None = None,
        # process tool
        qasm_version: Literal["qasm2", "qasm3"] = "qasm3",
        export: bool = False,
        save_location: Path | str | None = None,
        pbar: tqdm.tqdm | None = None,
        **custom_and_main_kwargs: Any,
    ) -> str:
        """Output the experiment.

        Args:
            circuits (list[QuantumCircuit | WCKeyable] | None, optional):
                The circuits or keys of circuits in `.waves`. Defaults to None.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend | None, optional):
                The quantum backend. Defaults to None.
            exp_name (str, optional):
                Naming this experiment to recognize it
                when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            run_args (RunArgsType, optional):
                Arguments for :meth:`Backend.run`. Defaults to None.
            transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`~qiskit.compiler.transpile`. Defaults to None.
            passmanager (PassManagerType | None, optional):
                The passmanager. Defaults to None.
            tags (tuple[str, ...] | None, optional):
                Given tags for the experiment to describe it. Defaults to None.

            exp_id (str | None, optional):
                The ID of experiment. Defaults to None.

            qasm_version (Literal["qasm2", "qasm3"], optional):
                The export version of OpenQASM. Defaults to 'qasm3'.
            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Path | str | None, optional):
                The location to save the experiment. Defaults to None.
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment. Defaults to None.
            custom_and_main_kwargs (Any):
                Other custom arguments.

        Returns:
            str: The ID of the experiment.
        """

        if exp_id is None and circuits is None:
            raise ValueError("No circuits or exp_id given.")
        if exp_id is not None and circuits is not None:
            raise ValueError("Both circuits and exp_id are given.")

        if exp_id is None:
            assert circuits is not None, (
                "No circuits given, but it should be given for passing check."
            )
            exp_id = self.build(
                circuits=circuits,
                shots=shots,
                backend=backend,
                exp_name=exp_name,
                run_args=run_args,
                transpile_args=transpile_args,
                passmanager=passmanager,
                tags=tags,
                # process tool
                qasm_version=qasm_version,
                export=export,
                save_location=save_location,
                pbar=pbar,
                **custom_and_main_kwargs,
            )

        runned_exp_id = self.orphan_exps[exp_id].run(pbar=pbar)

        return self.orphan_exps[runned_exp_id].result(export=export, save_location=save_location)

    @abstractmethod
    def measure_to_output(self) -> _OA:
        """Trasnform :meth:`measure` arguments form into :meth:`output` form."""
        raise NotImplementedError("The method is not defined.")

    @abstractmethod
    def prepare(self) -> _E:
        """Prepare the experiment."""
        raise NotImplementedError("The method is not defined.")

    @abstractmethod
    def measure(self) -> _E:
        """Execute the experiment."""
        raise NotImplementedError("The method is not defined.")

    def read(
        self,
        exp_or_summoner_name: Path | str,
        save_location: Path | str | None = Path("./"),
        multiprocess: bool = True,
    ) -> dict[str, _E]:
        """Read the experiment from file.

        Args:
            exp_or_summoner_name (Path | str):
                The experiment name or multimanager name to be read.
            save_location (Path | str | None, optional):
                The location of the experiment to be read. Defaults to Path('./').
            multiprocess (bool, optional):
                Whether to use multiprocessing. Defaults to `True`.

        Raises:
            ValueError: 'save_location' needs to be the type of 'str' or 'Path'.
            FileNotFoundError: When `save_location` is not available.

        Returns:
            dict[str, _E]: The dictionary of experiment instances read from file,
        """

        reading_results = self.experiment_instance.read(
            exp_or_summoner_name=exp_or_summoner_name,
            save_location=save_location,
            multiprocess=multiprocess,
        )
        exp_ids = [exp.commons.exp_id for exp in reading_results]
        self.orphan_exps.update({exp.exp_id: exp for exp in reading_results})

        return {exp_id: self.orphan_exps[exp_id] for exp_id in exp_ids}

    # pylint: disable=invalid-name
    def multiBuild(
        self,
        config_list: ConfigListType[_MA],
        summoner_name: str | None = None,
        summoner_id: str | None = None,
        shots: int = 1024,
        backend: Backend = GeneralSimulator(),
        tags: tuple[str, ...] | None = None,
        manager_run_args: RunArgsType = None,
        save_location: Path | str = Path("./"),
        jobstype: Literal["local"] | PendingTargetProviderLiteral = "local",
        pending_strategy: PendingStrategyLiteral = "tags",
        skip_build_write: bool = True,
        multiprocess_build: bool = False,
        multiprocess_write: bool = True,
    ) -> str:
        """Build the multimanager.

        Args:
            config_list (ConfigListType[_BA]):
                The list of default configurations of multiple experiment.
            summoner_name (str | None, optional):
                Name of experiment of
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                When `None`, it will be set to their coresponding :attr:`short_name`.
            summoner_id (str | None, optional):
                Id for multimanager. Defaults to None.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend, optional):
                The backend to run. Defaults to GeneralSimulator().
            tags (tuple[str, ...] | None, optional):
                Tags of experiment of
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                Defaults to None.
            manager_run_args (BaseRunArgs | dict[str, Any] | None, optional):
                The extra arguments for running the job, but for all experiments
                in the :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`
                for :meth:`~qiskit.providers.backend.BackendV2.run`.
                Defaults to None.
            save_location (Path | str, optional):
                Where to save the export content as `json` file. Defaults to Path('./').
            jobstype (Literal['local'] | PendingTargetProviderLiteral, optional):
                Type of jobs to run multiple experiments.
                jobstype: "local", "IBMQ", "IBM", "AWS_Bracket", "Azure_Q"
                Defaults to "local".
            pending_strategy (PendingStrategyLiteral, optional):
                Type of pending strategy.
                pendingStrategy: "default", "onetime", "each", "tags"
                Defaults to "tags".
            skip_build_write (bool, optional):
                Whether to skip the file writing during the building. Defaults to True.
            multiprocess_build (bool, optional):
                Whether use multiprocess for building. Defaults to False.
            multiprocess_write (bool, optional):
                Whether use multiprocess for writing. Defaults to True.
        Returns:
            str: The summoner_id of multimanager.
        """

        if summoner_id in self.multimanagers:
            assert isinstance(summoner_id, str), "summoner_id should be string here."
            return summoner_id
        if summoner_id is not None:
            raise ValueError("Unknow summoner_id in multimanagers.")
        if summoner_name is None:
            summoner_name = self.short_name

        ready_config_list: list[dict[str, Any]] = []
        for raw_config in config_list:
            config = self.measure_to_output(**raw_config)
            circuits = config["circuits"]
            config.pop("circuits")
            # circuits = config.pop("circuits") # which can not keep type
            config_targets = {
                "targets": self.waves.process(circuits),
                "passmanager_pair": passmanager_processor(
                    passmanager=config.pop("passmanager"), passmanager_container=self.passmanagers
                ),
            }
            config_targets.update(config)
            ready_config_list.append(config_targets)

        print("| MultiManager building...")
        current_multimanager: MultiManager[_E] = MultiManager.build(
            config_list=ready_config_list,
            experiment_instance=self.experiment_instance,
            summoner_name=summoner_name,
            shots=shots,
            backend=backend,
            tags=tags,
            manager_run_args=manager_run_args,
            jobstype=jobstype,
            pending_strategy=pending_strategy,
            save_location=save_location,
            skip_writing=skip_build_write,
            multiprocess_build=multiprocess_build,
            multiprocess_write=multiprocess_write,
        )
        assert len(current_multimanager.beforewards.pending_pool) == 0
        assert len(current_multimanager.beforewards.circuits_map) == 0

        self.multimanagers[current_multimanager.summoner_id] = current_multimanager

        return current_multimanager.multicommons.summoner_id

    def multiOutput(
        self,
        config_list: ConfigListType[_MA],
        summoner_name: str | None = None,
        summoner_id: str | None = None,
        shots: int = 1024,
        backend: Backend = GeneralSimulator(),
        tags: tuple[str, ...] | None = None,
        manager_run_args: RunArgsType = None,
        save_location: Path | str = Path("./"),
        skip_build_write: bool = True,
        skip_output_write: bool = False,
        multiprocess_build: bool = False,
        multiprocess_write: bool = True,
    ) -> str:
        """Output the multiple experiments.

        Args:
            config_list (ConfigListType[_BA]):
                The list of default configurations of multiple experiment.
            summoner_name (str | None, optional):
                Name for multimanager. Defaults to None.
                When `None`, it will be set to their coresponding :attr:`short_name`.
            summoner_id (str | None, optional):
                Id for multimanager. Defaults to None.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend, optional):
                The backend to run. Defaults to GeneralSimulator().
            tags (tuple[str, ...] | None, optional):
                Tags of experiment of
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                Defaults to None.
            manager_run_args (BaseRunArgs | dict[str, Any] | None, optional):
                The extra arguments for running the job, but for all experiments
                in the :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`
                for :meth:`~qiskit.providers.backend.BackendV2.run`.
                Defaults to None.
            save_location (Path | str, optional):
                Where to save the export content as `json` file. Defaults to Path('./').
            skip_build_write (bool, optional):
                Whether to skip the file writing during the building. Defaults to True.
            skip_output_write (bool, optional):
                Whether to skip the file writing during the output. Defaults to False.
            multiprocess_build (bool, optional):
                Whether use multiprocess for building. Defaults to False.
            multiprocess_write (bool, optional):
                Whether use multiprocess for writing. Defaults to True.

        Returns:
            str: The summoner_id of multimanager.
        """

        if tags is None:
            tags = ()

        besummonned = self.multiBuild(
            config_list=config_list,
            shots=shots,
            backend=backend,
            tags=tags,
            manager_run_args=manager_run_args,
            summoner_name=summoner_name,
            summoner_id=summoner_id,
            save_location=save_location,
            jobstype="local",
            pending_strategy="tags",
            skip_build_write=skip_build_write,
            multiprocess_build=multiprocess_build,
            multiprocess_write=multiprocess_write,
        )
        current_multimanager = self.multimanagers[besummonned]
        assert current_multimanager.summoner_id == besummonned

        print("| MultiOutput running...")
        circ_serial: list[int] = []
        experiment_progress = qurry_progressbar(current_multimanager.exps.items())

        is_call_auto_multianalysis = False
        for exp_id, exp_instance in experiment_progress:
            experiment_progress.set_description_str("Experiments running...")

            current_id = exp_instance.run(pbar=experiment_progress)
            assert current_id == exp_id, f"exps_id output: {current_id} != exp_id: {exp_id}"

            current_id = exp_instance.result(
                export=False,
                save_location=current_multimanager.multicommons.save_location,
            )
            assert current_id == exp_id, f"exps_id output: {current_id} != exp_id: {exp_id}"
            is_call_auto_multianalysis = (
                exp_instance.is_auto_analysis and exp_instance.is_hold_by_multimanager
            )

            circ_serial_len = len(circ_serial)
            tmp_circ_serial = [
                idx + circ_serial_len for idx, _ in enumerate(exp_instance.beforewards.circuit)
            ]
            circ_serial += tmp_circ_serial

            # current_multimanager.beforewards.pending_pool[exp_id] = tmp_circ_serial
            # current_multimanager.beforewards.circuits_map[exp_id] = tmp_circ_serial
            # current_multimanager.beforewards.job_id.append((exp_id, "local"))
        current_multimanager.multicommons.datetimes.add_serial("output")

        if is_call_auto_multianalysis:
            print("| Auto analysis is called, running analysis...")
            current_multimanager.analyze(analysis_name="auto_report", no_serialize=True)
        if not skip_output_write:
            bewritten = self.multiWrite(besummonned, multiprocess_write=multiprocess_write)
            assert bewritten == besummonned

        return current_multimanager.multicommons.summoner_id

    def multiAnalysis(
        self,
        summoner_id: str,
        *,
        analysis_name: str = "report",
        no_serialize: bool = False,
        specific_analysis_args: SpecificAnalyzeArgs[_RA] = None,
        skip_write: bool = False,
        multiprocess_write: bool = False,
        **analysis_args: Any,
    ) -> tuple[str, str]:
        """Run the analysis for multiple experiments.

        Args:
            summoner_id (str): The summoner_id of multimanager.
            analysis_name (str, optional):
                The name of analysis. Defaults to 'report'.
            no_serialize (bool, optional):
                Whether to serialize the analysis. Defaults to False.
            specific_analysis_args(SpecificAnalsisArgs[_RA, optional):
                The specific arguments for analysis. Defaults to None.
            skip_write (bool, optional):
                Whether to skip the file writing during the analysis. Defaults to False.
            multiprocess_write (bool, optional):
                Whether use multiprocess for writing. Defaults to False.
            analysis_args (Any, optional):
                Other arguments for analysis.

        Returns:
            The summoner_id of multimanager and the report name.
        """
        if specific_analysis_args is None:
            specific_analysis_args = {}
        if summoner_id not in self.multimanagers:
            raise ValueError("No such summoner_id in multimanagers.")
        current_multimanager = self.multimanagers[summoner_id]

        report_name = current_multimanager.analyze(
            analysis_name=analysis_name,
            no_serialize=no_serialize,
            specific_analysis_args=specific_analysis_args,
            **analysis_args,
        )

        if not skip_write:
            self.multiWrite(summoner_id=summoner_id, multiprocess_write=multiprocess_write)

        return current_multimanager.multicommons.summoner_id, report_name

    def multiWrite(
        self,
        summoner_id: str,
        save_location: Path | str | None = None,
        export_transpiled_circuit: bool = False,
        skip_exps: bool = False,
        skip_quantities: bool = False,
        multiprocess_write: bool = True,
    ) -> str:
        """Write the multimanager to the file.

        Args:
            summoner_id (str): The summoner_id of multimanager.
            save_location (Path | str | None, optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            export_transpiled_circuit (bool, optional):
                Whether to export the transpiled circuit. Defaults to False.
            skip_exps (bool, optional):
                Skip the experiments. Defaults to False.
            skip_quantities (bool, optional):
                Skip the quantities container. Defaults to False.
            multiprocess_write (bool, optional):
                Whether to use multiprocess to write the file. Defaults to True.

        Raises:
            ValueError: summoner_id not in multimanagers.

        Returns:
            str: The summoner_id of multimanager.
        """

        if summoner_id not in self.multimanagers:
            raise ValueError("No such summoner_id in multimanagers.", summoner_id)

        current_multimanager = self.multimanagers[summoner_id]
        assert current_multimanager.summoner_id == summoner_id

        current_multimanager.write(
            save_location=save_location,
            export_transpiled_circuit=export_transpiled_circuit,
            skip_exps=skip_exps,
            skip_quantities=skip_quantities,
            multiprocess=multiprocess_write,
        )

        return current_multimanager.multicommons.summoner_id

    def multiRead(
        self,
        summoner_name: str,
        save_location: Path | str = Path("./"),
        reload: bool = False,
        multiprocess: bool = True,
    ) -> str:
        """Read the multimanager from the file.

        Args:
            summoner_name (str): Name for multimanager.
            save_location (Path | str, optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            reload (bool, optional):
                Whether to reload the multimanager. Defaults to False.
            multiprocess (bool, optional):
                Whether use multiprocess for reading. Defaults to True.

        Returns:
            str: The summoner_id of multimanager.
        """

        filtered_summoner_id_names = [
            (k, v.summoner_name) for k, v in self.multimanagers.items() if v == summoner_name
        ]
        if len(filtered_summoner_id_names) == 1:
            assert filtered_summoner_id_names[0][0] in self.multimanagers
            if not reload:
                print(
                    "| Found existed multimanager: "
                    + f"{filtered_summoner_id_names[0][0]}: {filtered_summoner_id_names[0][1]}."
                )
                return filtered_summoner_id_names[0][0]
            print("| MultiRead reloading...")
            del self.multimanagers[filtered_summoner_id_names[0][0]]
        elif len(filtered_summoner_id_names) > 1:
            raise ValueError(
                f"Multiple multimanager found for '{summoner_name}': {filtered_summoner_id_names}."
            )

        current_multimanager: MultiManager[_E] = MultiManager.read(
            summoner_name=summoner_name,
            experiment_instance=self.experiment_instance,
            save_location=save_location,
            is_read_or_retrieve=True,
            multiprocess=multiprocess,
        )
        self.multimanagers[current_multimanager.summoner_id] = current_multimanager

        return current_multimanager.multicommons.summoner_id

    def __repr__(self):
        return (
            f"<{self.__name__}("
            f"waves={self.waves._repr_oneline()}, "
            f"exps={self.exps._repr_oneline()}, "
            f"multimanagers_num={len(self.multimanagers)}, "
            f"passmanagers_len={len(self.passmanagers)})>"
        )

    def _repr_pretty_(self, p, cycle):
        # pylint: disable=protected-access
        len_multimanagers = len(self.multimanagers)
        len_passmanagers = len(self.passmanagers)
        if cycle:
            p.text(f"<{self.__name__}(...)>")
        else:
            with p.group(DEFAULT_INDENT, f"<{self.__name__}(", ")>"):
                p.breakable()
                p.text(f"waves={self.waves._repr_oneline()},")
                p.breakable()
                p.text(f"exps={self.exps._repr_oneline()},")
                p.breakable()
                with p.group(
                    DEFAULT_INDENT,
                    "multimanagers=MultiManagers({",
                    "}" + f", num={len_multimanagers}), ",
                ):
                    for i, (k, v) in enumerate(self.multimanagers.items()):
                        p.breakable()
                        p.text(f"'{k}': {v._repr_oneline_no_id()}")
                        if i != len_multimanagers - 1:
                            p.text(",")
                p.breakable()
                with p.group(
                    DEFAULT_INDENT,
                    "passmanagers=PassManagers({",
                    "}" + f", num={len_passmanagers})",
                ):
                    for i, (k, v) in enumerate(self.passmanagers.items()):
                        p.breakable()
                        p.text(f"'{k}': {v}")
                        if i != len_passmanagers - 1:
                            p.text(",")
            p.break_()
        # pylint: enable=protected-access


# pylint: enable=invalid-name
