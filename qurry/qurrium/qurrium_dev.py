"""
===========================================================
Qurry - A Qiskit Macro
(:mod:`qurry.qurry.qurrium.qurrium`)

===========================================================
"""

import gc
import warnings
from abc import abstractmethod, ABC
from typing import Literal, Union, Optional, Hashable, Any, TypeVar, Type
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend
from qiskit.transpiler.passmanager import PassManager

from ..tools import qurry_progressbar
from ..tools.backend import GeneralSimulator
from ..tools.datetime import DatetimeDict
from ..declare.default import managerRunConfig, contain_checker
from .experiment.experiment_dev import ExperimentPrototype
from .container import WaveContainer, ExperimentContainer
from .multimanager import (
    MultiManager,
    PendingTargetProviderLiteral,
    PendingStrategyLiteral,
)
from .runner import ExtraBackendAccessor, retrieve_counter
from .utils import get_counts_and_exceptions
from ..exceptions import QurryResetAccomplished, QurryResetSecurityActivated


ExpsT = TypeVar("ExpsT", bound=ExperimentPrototype)


class QurriumPrototype(ABC):
    """Qurrium, A qiskit Macro.
    ~Create countless adventure, legacy and tales.~
    """

    __name__ = "QurriumPrototype"
    shortName = "qurrium"

    # Wave
    def add(
        self,
        wave: QuantumCircuit,
        key: Optional[Hashable] = None,
        replace: Literal[True, False, "duplicate"] = False,
    ) -> Hashable:
        """Add new wave function to measure.

        Args:
            wave (QuantumCircuit): The wave functions or circuits want to measure.
            key (Optional[Hashable], optional):
                Given a specific key to add to the wave function or circuit,
                if `key == None`, then generate a number as key.
                Defaults to `None`.
            replace (Literal[True, False, &#39;duplicate&#39;], optional):
                If the key is already in the wave function or circuit,
                then replace the old wave function or circuit when `True`,
                or duplicate the wave function or circuit when `'duplicate'`,
                otherwise only changes `.lastwave`.
                Defaults to `False`.

        Returns:
            Optional[Hashable]: Key of given wave function in `.waves`.
        """
        return self.waves.add(wave=wave, key=key, replace=replace)

    def remove(self, key: Hashable) -> None:
        """Remove wave function from `.waves`.

        Args:
            wave (Hashable): The key of wave in `.waves`.
        """
        self.waves.remove(key)

    def has(self, wavename: Hashable) -> bool:
        """Is there a wave with specific name.

        Args:
            wavename (Hashable): Name of wave which is used in `.waves`

        Returns:
            bool: Exist or not.
        """
        return self.waves.has(wavename)

    @property
    @abstractmethod
    def experiment(self) -> Type[ExperimentPrototype]:
        """The instance of experiment."""
        raise NotImplementedError("The experiment is not defined.")

    def __init__(
        self,
    ) -> None:
        self.waves: WaveContainer = WaveContainer()
        """The wave functions container."""

        self.exps: ExperimentContainer[ExpsT] = ExperimentContainer()
        """The experiments container."""

        self.multimanagers: dict[str, MultiManager] = {}
        """The last multimanager be called.
        Replace the property :prop:`multiNow`. in :cls:`QurryV4`"""

        self.accessor: Optional[ExtraBackendAccessor] = None
        """The accessor of extra backend.
        It will be None if no extra backend is loaded.
        """

        self.passmanagers: dict[str, PassManager] = {}
        """The collection of pass managers."""

    def build(
        self,
        circuits: list[Union[QuantumCircuit, Hashable]],
        backend: Optional[Backend] = None,
        passmanager: Optional[Union[str, PassManager, tuple[str, PassManager]]] = None,
        export: bool = False,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonable: bool = False,
        pbar: Optional[tqdm.tqdm] = None,
        **custom_and_main_kwargs: Any,
    ) -> str:
        """Build the experiment.

        Args:
            circuits (list[Union[QuantumCircuit, Hashable]]):
                The circuits or keys of circuits in `.waves`.
            backend (Optional[Backend], optional):
                The quantum backend. Defaults to None.
            passmanager (Optional[Union[str, PassManager, tuple[str, PassManager]]], optional):
                The passmanager. Defaults to None.
            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Optional[Union[Path, str]], optional):
                The location to save the experiment. Defaults to None.
            mode (str, optional):
                The mode to open the file. Defaults to 'w+'.
            indent (int, optional):
                The indent of json file. Defaults to 2.
            encoding (str, optional):
                The encoding of json file. Defaults to 'utf-8'.
            jsonable (bool, optional):
                Whether to jsonablize the experiment output. Defaults to False.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.
            custom_and_main_kwargs (Any):
                Other custom arguments.

        Returns:
            ExperimentPrototype: The experiment.
        """
        if isinstance(passmanager, str):
            if passmanager not in self.passmanagers:
                raise KeyError(f"Passmanager {passmanager} not found in {self.passmanagers}")
            passmanager_pair = passmanager, self.passmanagers[passmanager]
        elif isinstance(passmanager, PassManager):
            passmanager_pair = f"pass_{len(self.passmanagers)}", passmanager
            self.passmanagers[passmanager_pair[0]] = passmanager_pair[1]
        elif isinstance(passmanager, tuple):
            if len(passmanager) != 2:
                raise ValueError(f"Invalid passmanager: {passmanager}")
            if not isinstance(passmanager[1], PassManager) or not isinstance(passmanager[0], str):
                raise ValueError(f"Invalid passmanager: {passmanager}")
            passmanager_pair = passmanager
            self.passmanagers[passmanager_pair[0]] = passmanager_pair[1]
        elif passmanager is None:
            passmanager_pair = None
        else:
            raise ValueError(f"Invalid passmanager: {passmanager}")

        circuits_maps = {}
        for _circuit in circuits:
            if isinstance(_circuit, QuantumCircuit):
                key = self.add(wave=_circuit)
                circuits_maps[key] = self.waves[key]
            elif isinstance(_circuit, Hashable):
                if self.has(_circuit):
                    circuits_maps[_circuit] = self.waves[_circuit]
                else:
                    raise KeyError(f"Wave {_circuit} not found in {self.waves}")
            else:
                raise ValueError(f"Invalid type of circuit: {_circuit}, type: {type(_circuit)}")

        new_exps = self.experiment.build(
            circuits_maps=circuits_maps,
            backend=backend,
            passmanager_pair=passmanager_pair,
            export=export,
            save_location=save_location,
            mode=mode,
            indent=indent,
            encoding=encoding,
            jsonable=jsonable,
            pbar=pbar,
            **custom_and_main_kwargs,
        )

        self.exps[new_exps.commons.exp_id] = new_exps
        return new_exps.commons.exp_id

    def result(
        self,
        *args,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonablize: bool = False,
        _pbar: Optional[tqdm.tqdm] = None,
        **other_kwargs: Any,
    ) -> str:
        """Export the result after running the job.

        Args:
            save_location (Optional[Union[Path, str]], optional):
                The location to save the experiment. If None, will not save.
                Defaults to None.
            mode (str, optional):
                The mode to open the file. Defaults to 'w+'.
            indent (int, optional):
                The indent of json file. Defaults to 2.
            encoding (str, optional):
                The encoding of json file. Defaults to 'utf-8'.
            jsonablize (bool, optional):
                Whether to jsonablize the experiment output. Defaults to False.

            allArgs:
                all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            Hashable: The ID of the experiment.
        """

        if len(args) > 0:
            raise ValueError(f"{self.__name__} can't be initialized with positional arguments.")

        # preparing
        id_now = self.run(
            save_location=save_location,
            mode=mode,
            indent=indent,
            encoding=encoding,
            jsonablize=jsonablize,
            _pbar=_pbar,
            **other_kwargs,
        )
        assert id_now in self.exps, f"ID {id_now} not found."
        assert self.exps[id_now].commons.exp_id == id_now
        current_exp = self.exps[id_now]
        assert len(current_exp.afterwards.result) == 1, "Result should be only one."

        # afterwards
        num = len(current_exp.beforewards.circuit)
        counts, exceptions = get_counts_and_exceptions(
            result=current_exp.afterwards.result[0],
            num=num,
        )
        if len(exceptions) > 0:
            if "exceptions" not in current_exp.outfields:
                current_exp.outfields["exceptions"] = {}
            for result_id, exception_item in exceptions.items():
                current_exp.outfields["exceptions"][result_id] = exception_item
        for _c in counts:
            current_exp.afterwards.counts.append(_c)

        # default analysis
        if len(current_exp.commons.default_analysis) > 0:
            for _analysis in current_exp.commons.default_analysis:
                current_exp.analyze(**_analysis)

        if isinstance(save_location, (Path, str)):
            if isinstance(_pbar, tqdm.tqdm):
                _pbar.set_description_str("Exporting data... ")
            current_exp.write(
                save_location=save_location,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonablize,
            )

        return id_now

    def output(
        self,
        *args,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonablize: bool = False,
        _pbar: Optional[tqdm.tqdm] = None,
        **other_kwargs: Any,
    ):
        """Export the result after running the job.
        ## The second finishing point.

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
            save_location (Optional[Union[Path, str]], optional):
                The location to save the experiment. If None, will not save.
                Defaults to None.
            mode (str, optional):
                The mode to open the file. Defaults to 'w+'.
            indent (int, optional):
                The indent of json file. Defaults to 2.
            encoding (str, optional):
                The encoding of json file. Defaults to 'utf-8'.
            jsonablize (bool, optional):
                Whether to jsonablize the experiment output. Defaults to False.

            other_kwargs (Any):
                Other arguments.

        Returns:
            dict: The output.
        """

        if len(args) > 0:
            raise ValueError(f"{self.__name__} can't be initialized with positional arguments.")

        id_now = self.result(
            save_location=save_location,
            mode=mode,
            indent=indent,
            encoding=encoding,
            jsonablize=jsonablize,
            _pbar=_pbar,
            **other_kwargs,
        )
        assert id_now in self.exps, f"ID {id_now} not found."
        assert self.exps[id_now].commons.exp_id == id_now
        current_exp = self.exps[id_now]

        if len(current_exp.afterwards.result) > 0:
            return id_now

        return id_now

    def _params_control_multi(
        self,
        config_list: list[dict[str, Any]],
        summoner_name: Optional[str] = None,
        summoner_id: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralSimulator(),
        tags: Optional[list[str]] = None,
        save_location: Union[Path, str] = Path("./"),
        jobstype: PendingTargetProviderLiteral = "local",
        pending_strategy: PendingStrategyLiteral = "tags",
        manager_run_args: Optional[dict[str, Any]] = None,
        is_retrieve: bool = False,
        is_read: bool = False,
        read_from_tarfile: bool = False,
    ) -> tuple[list[dict[str, Any]], str]:
        """Control the experiment's parameters for running multiple jobs.

        Args:
            configList (list, optional):
                The list of default configurations of multiple experiment.
            summoner_name (str, optional):
                Name for multimanager. Defaults to 'exps'.
            summoner_id (Optional[str], optional):
                Name for multimanager. Defaults to None.
            shots (int, optional):
                Shots of the job.
                Defaults to `1024`.
            backend (Backend, optional):
                The quantum backend.
                Defaults to AerSimulator().
            tags (list[str], optional):
                Given the experiment multiple tags to make a dictionary for recongnizing it.
                This also can be used on diving the jobs into multiple pendings.

            save_location (Union[Path, str], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            filetype (TagList._availableFileType, optional):
                The file type of export data. Defaults to 'json' (recommended).
            manager_run_args (dict, optional):
                defaultConfig of :func:`IBMQJobManager().run`.
                Defaults to `{
                    'max_experiments_per_job': 200,
                }`.
            jobstype (Literal[
                'local', 'IBMQ', 'AWS_Bracket', 'Azure_Q'
            ], optional):
                What types of the backend will run on. Defaults to "local".
            is_retrieve (bool, optional):
                Whether this jobs will retrieve the pending experiment after initializing.
                Defaults to `False`.
            is_read (bool, optional):
                Whether this jobs will read the existed experiment data during initializing.
                Defaults to False.

        Returns:
            tuple[list[dict[str, Any]], str]:
                The list of formated configuration of
                each experimemt and summoner_id (ID of multimanager).
        """

        if summoner_id in self.multimanagers:
            current_multimanager = self.multimanagers[summoner_id]
            return (
                list(current_multimanager.beforewards.exps_config.values()),
                current_multimanager.summoner_id,
            )

        if summoner_name is None:
            summoner_name = "exps"
        if tags is None:
            tags = []
        if manager_run_args is None:
            manager_run_args = {
                "max_experiments_per_job": 200,
            }

        is_read = is_retrieve | is_read

        for config, checker in [
            (manager_run_args, managerRunConfig),
        ]:
            contain_checker(config, checker)

        if is_read:
            current_multimanager = MultiManager(
                summoner_id=None,
                summoner_name=summoner_name,
                is_read=is_read,
                read_from_tarfile=read_from_tarfile,
                save_location=save_location,
            )
        else:
            current_multimanager = MultiManager(
                summoner_id=summoner_id,
                summoner_name=summoner_name,
                shots=shots,
                backend=backend,
                # provider=provider,
                tags=tags,
                save_location=save_location,
                files={},
                jobstype=jobstype,
                pending_strategy=pending_strategy,
                manager_run_args=manager_run_args,
                datetimes=DatetimeDict(),
            )

        self.multimanagers[current_multimanager.summoner_id] = current_multimanager

        initial_config_list: list[dict[str, Any]] = []
        for serial, config in enumerate(config_list):
            initial_config_list.append(
                {
                    **config,
                    "shots": shots,
                    "backend": backend,
                    # 'provider': provider,
                    "exp_name": current_multimanager.multicommons.summoner_name,
                    "save_location": current_multimanager.multicommons.save_location,
                    "serial": serial,
                    "summoner_id": current_multimanager.multicommons.summoner_id,
                    "summoner_name": current_multimanager.multicommons.summoner_name,
                }
            )

        return initial_config_list, current_multimanager.summoner_id

    # pylint: disable=invalid-name
    def multiBuild(
        self,
        config_list: list[dict[str, Any]],
        summoner_name: str = "exps",
        summoner_id: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralSimulator(),
        tags: Optional[list[str]] = None,
        manager_run_args: Optional[dict[str, Any]] = None,
        save_location: Union[Path, str] = Path("./"),
        jobstype: Union[Literal["local"], PendingTargetProviderLiteral] = "local",
        pending_strategy: PendingStrategyLiteral = "tags",
    ) -> str:
        """Buling the experiment's parameters for running multiple jobs.

        Args:
            configList (list, optional):
                The list of default configurations of multiple experiment.
                Defaults to [].
            summoner_name (str, optional):
                Name for multimanager. Defaults to 'exps'.
            summoner_id (Optional[str], optional):
                Name for multimanager. Defaults to None.
            shots (int, optional):
                Shots of the job.
                Defaults to `1024`.
            backend (Backend, optional):
                The quantum backend.
                Defaults to AerSimulator().
            manager_run_args (dict, optional):
                defaultConfig of :func:`IBMQJobManager().run`.
                Defaults to `{}`.
            save_location (Union[Path, str], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            jobstype (Literal[
                'local', 'IBMQ', 'AWS_Bracket', 'Azure_Q'
            ], optional):
                What types of the backend will run on. Defaults to "local".

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """
        if tags is None:
            tags = []
        if manager_run_args is None:
            manager_run_args = {}

        print("| MultiManager building...")
        initial_config_list, besummonned = self._params_control_multi(
            config_list=config_list,
            shots=shots,
            backend=backend,
            tags=tags,
            manager_run_args=manager_run_args,
            summoner_name=summoner_name,
            summoner_id=summoner_id,
            save_location=save_location,
            jobstype=jobstype,
            pending_strategy=pending_strategy,
            is_retrieve=False,
            is_read=False,
        )
        current_multimanager = self.multimanagers[besummonned]
        assert current_multimanager.summoner_id == besummonned
        initial_config_list_progress = qurry_progressbar(initial_config_list)

        initial_config_list_progress.set_description_str("MultiManager building...")
        for config in initial_config_list_progress:
            new_exps = self.experiment.build(
                **config,
                export=False,  # export later for it's not efficient for one by one
                pbar=initial_config_list_progress,
            )
            initial_config_list_progress.set_description_str("Loading data to multimanager...")
            current_multimanager.register(
                current_id=new_exps.commons.exp_id,
                config=config,
                exps_instance=new_exps,  # type: ignore # TODO: remove when complete
            )
            self.exps[new_exps.commons.exp_id] = new_exps
        initial_config_list_progress.set_description_str("MultiManager writing...")
        current_multimanager.write(
            exps_container=self.exps,
        )

        assert len(current_multimanager.beforewards.pending_pool) == 0
        assert len(current_multimanager.beforewards.circuits_map) == 0
        assert len(current_multimanager.beforewards.job_id) == 0

        return current_multimanager.multicommons.summoner_id

    def multiOutput(
        self,
        config_list: list[dict[str, Any]],
        summoner_name: str = "exps",
        summoner_id: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralSimulator(),
        tags: Optional[list[str]] = None,
        save_location: Union[Path, str] = Path("./"),
        compress: bool = False,
    ) -> Hashable:
        """Running multiple jobs on local backend and output the analysis.

        Args:
            configList (list, optional):
                The list of default configurations of multiple experiment.
                Defaults to [].
            summoner_name (str, optional):
                Name for multimanager. Defaults to 'exps'.
            summoner_id (Optional[str], optional):
                Name for multimanager. Defaults to None.
            shots (int, optional):
                Shots of the job.
                Defaults to `1024`.
            backend (Backend, optional):
                The quantum backend.
                Defaults to AerSimulator().
            save_location (Union[Path, str], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            compress (bool, optional):
                Whether to compress the export file.
            defaultMultiAnalysis (list[dict[str, Any]], optional):
                The default configurations of multiple analysis,
                if it's given, then will run automatically after the experiment results are ready.
                Defaults to [].
            analysisName (str, optional):
                The name of the analysis.
                Defaults to 'report'.

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """
        if tags is None:
            tags = []

        print("| MultiOutput running...")
        besummonned = self.multiBuild(
            config_list=config_list,
            shots=shots,
            backend=backend,
            # provider=provider,
            tags=tags,
            manager_run_args={},
            summoner_name=summoner_name,
            summoner_id=summoner_id,
            save_location=save_location,
            jobstype="local",
        )
        current_multimanager = self.multimanagers[besummonned]
        assert current_multimanager.summoner_id == besummonned
        circ_serial: list[int] = []

        experiment_progress = qurry_progressbar(current_multimanager.beforewards.exps_config)

        for id_exec in experiment_progress:
            experiment_progress.set_description_str("Experiments running...")
            current_id = self.output(
                exp_id=id_exec,
                save_location=current_multimanager.multicommons.save_location,
            )

            circ_serial_len = len(circ_serial)
            tmp_circ_serial = [
                idx + circ_serial_len
                for idx in range(len(self.exps[current_id].beforewards.circuit))
            ]

            circ_serial += tmp_circ_serial
            current_multimanager.beforewards.pending_pool[current_id] = tmp_circ_serial
            current_multimanager.beforewards.circuits_map[current_id] = tmp_circ_serial
            current_multimanager.beforewards.job_id.append((current_id, "local"))

            current_multimanager.afterwards.allCounts[current_id] = self.exps[
                current_id
            ].afterwards.counts
        current_multimanager.multicommons.datetimes.add_serial("output")
        bewritten = self.multiWrite(besummonned, compress=compress)
        assert bewritten == besummonned

        return current_multimanager.multicommons.summoner_id

    def multiPending(
        self,
        config_list: list[dict[str, Any]],
        summoner_name: str = "exps",
        summoner_id: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralSimulator(),
        tags: Optional[list[str]] = None,
        manager_run_args: Optional[dict[str, Any]] = None,
        save_location: Union[Path, str] = Path("./"),
        jobstype: PendingTargetProviderLiteral = "IBM",
        pending_strategy: PendingStrategyLiteral = "tags",
    ) -> str:
        """Pending the multiple jobs on IBMQ backend or other remote backend.

        Args:
            configList (list, optional):
                The list of default configurations of multiple experiment.
                Defaults to [].
            summoner_name (str, optional):
                Name for multimanager. Defaults to 'exps'.
            summoner_id (Optional[str], optional):
                Name for multimanager. Defaults to None.
            shots (int, optional):
                Shots of the job.
                Defaults to `1024`.
            backend (Backend, optional):
                The quantum backend.
                Defaults to AerSimulator().
            manager_run_args (dict, optional):
                defaultConfig of :func:`IBMQJobManager().run`.
                Defaults to `{}`.
            save_location (Union[Path, str], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            pendingStrategy (Literal['default', 'onetime', 'each', 'tags'], optional):
                The strategy of pending for distributing experiments on jobs.

        Returns:
            str: SummonerID (ID of multimanager).
        """
        besummonned = self.multiBuild(
            config_list=config_list,
            shots=shots,
            backend=backend,
            tags=tags,
            manager_run_args=manager_run_args,
            summoner_name=summoner_name,
            summoner_id=summoner_id,
            save_location=save_location,
            jobstype=jobstype,
            pending_strategy=pending_strategy,
        )
        current_multimanager = self.multimanagers[besummonned]
        assert current_multimanager.summoner_id == besummonned

        print("| MultiPending running...")
        self.accessor = ExtraBackendAccessor(
            multimanager=current_multimanager,
            experiment_container=self.exps,
            backend=backend,
            backend_type=jobstype,
        )
        self.accessor.pending(
            pending_strategy=pending_strategy,
        )
        bewritten = self.multiWrite(besummonned)
        assert bewritten == besummonned

        return current_multimanager.multicommons.summoner_id

    def multiAnalysis(
        self,
        summoner_id: str,
        analysis_name: str = "report",
        no_serialize: bool = False,
        specific_analysis_args: Optional[dict[Hashable, Union[dict[str, Any], bool]]] = None,
        compress: bool = False,
        write: bool = True,
        **analysis_args: Any,
    ) -> str:
        """Run the analysis for multiple experiments.

        Args:
            summoner_id (str): Name for multimanager.
            analysisName (str, optional):
                The name of the analysis.
                Defaults to 'report'.
            specificAnalysisArgs (Optional[dict[Hashable, dict[str, Any]]], optional):
                Specific some experiment to run the analysis arguments for each experiment.
                Defaults to {}.

        Raises:
            ValueError: No positional arguments allowed except `summoner_id`.
            ValueError: summoner_id not in multimanagers.
            ValueError: No counts in multimanagers, which experiments are not ready.

        Returns:
            str: SummonerID (ID of multimanager).
        """
        if specific_analysis_args is None:
            specific_analysis_args = {}

        if summoner_id in self.multimanagers:
            current_multimanager = self.multimanagers[summoner_id]
        else:
            raise ValueError("No such summoner_id in multimanagers.")

        report_name = current_multimanager.analyze(
            self.exps,
            analysis_name=analysis_name,
            no_serialize=no_serialize,
            specific_analysis_args=specific_analysis_args,
            **analysis_args,
        )
        print(f'| "{report_name}" has been completed.')

        if write:
            self.multiWrite(
                summoner_id=summoner_id,
                only_quantity=True,
                compress=compress,
            )

        return current_multimanager.multicommons.summoner_id

    def multiWrite(
        self,
        summoner_id: str,
        save_location: Optional[Union[Path, str]] = None,
        compress: bool = False,
        compress_overwrite: bool = False,
        remain_only_compressed: bool = False,
        only_quantity: bool = False,
        export_transpiled_circuit: bool = False,
    ) -> str:
        """Write the multimanager to the file.

        Args:
            summoner_id (str): Name for multimanager.
            save_location (Union[Path, str], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            compress (bool, optional):
                Whether to compress the export file.
                Defaults to False.
            compress_overwrite (bool, optional):
                Whether to overwrite the compressed file.
                Defaults to False.
            remain_only_compressed (bool, optional):
                Whether to remain only compressed file.
                Defaults to False.
            only_quantity (bool, optional):
                Whether to export only the quantity of the experiment.
                Defaults to False.
            export_transpiled_circuit (bool, optional):
                Whether to export the transpiled circuit.
                Defaults to False.

        Raises:
            ValueError: summoner_id not in multimanagers.

        Returns:
            str: SummonerID (ID of multimanager).
        """

        if summoner_id not in self.multimanagers:
            raise ValueError("No such summoner_id in multimanagers.", summoner_id)

        current_multimanager = self.multimanagers[summoner_id]
        assert current_multimanager.summoner_id == summoner_id

        current_multimanager.write(
            save_location=save_location,
            exps_container=self.exps,
            export_transpiled_circuit=export_transpiled_circuit,
            _only_quantity=only_quantity,
        )

        if compress:
            current_multimanager.compress(
                compress_overwrite=compress_overwrite,
                remain_only_compressed=remain_only_compressed,
            )
        else:
            if compress_overwrite or remain_only_compressed:
                warnings.warn(
                    "'compressOverwrite' or 'remainOnlyCompressed' is set to True, "
                    + "but 'compress' is False."
                )

        return current_multimanager.multicommons.summoner_id

    def multiRead(
        self,
        summoner_name: Optional[str] = None,
        summoner_id: Optional[str] = None,
        save_location: Union[Path, str] = Path("./"),
        reload: bool = False,
        read_from_tarfile: bool = False,
        # defaultMultiAnalysis: list[dict[str, Any]] = []
        # analysisName: str = 'report',
    ) -> str:
        """Read the multimanager from the file.

        Args:
            summoner_name (Optional[str], optional):
                Name for multimanager. Defaults to 'exps'.
            summoner_id (Optional[str], optional):
                Name for multimanager. Defaults to None.
            save_location (Union[Path, str], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            reload (bool, optional):
                Whether to reload the multimanager.
                Defaults to False.
            read_from_tarfile (bool, optional):
                Whether to read from the tarfile.
                Defaults to False.

        Returns:
            str: SummonerID (ID of multimanager).
        """

        if summoner_id in self.multimanagers:
            if not reload:
                print("| MultiRead found existed multimanager.")
                return summoner_id
            print("| MultiRead reloading...")
            del self.multimanagers[summoner_id]
        else:
            print("| MultiRead running...")

        _, besummonned = self._params_control_multi(
            config_list=[],
            summoner_name=summoner_name,
            summoner_id=summoner_id,
            save_location=save_location,
            is_read=True,
            read_from_tarfile=read_from_tarfile,
        )

        assert besummonned in self.multimanagers
        assert self.multimanagers[besummonned].multicommons.summoner_id == besummonned

        quene: list[ExperimentPrototype] = self.experiment.read(
            save_location=self.multimanagers[besummonned].multicommons.save_location,
            name_or_id=self.multimanagers[besummonned].multicommons.summoner_name,
        )
        for exp in quene:
            self.exps[exp.exp_id] = exp

        return besummonned

    def multiRetrieve(
        self,
        summoner_name: Optional[str] = None,
        summoner_id: Optional[str] = None,
        backend: Optional[Backend] = None,
        save_location: Union[Path, str] = Path("./"),
        refresh: bool = False,
        overwrite: bool = False,
        reload: bool = False,
        read_from_tarfile: bool = False,
        compress: bool = False,
    ) -> Hashable:
        """Retrieve the multimanager from the remote backend.

        Args:
            summoner_name (Optional[str], optional):
                Name for multimanager. Defaults to 'exps'.
            summoner_id (Optional[str], optional):
                Name for multimanager. Defaults to None.
            backend (IBMBackend, optional):
                The quantum backend.
                Defaults to IBMBackend().
            provider (Optional[AccountProvider], optional):
                :cls:`AccountProvider` of current backend for running :cls:`IBMQJobManager`.
                Defaults to `None`.
            save_location (Union[Path, str], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            refresh (bool, optional):
                The feature of :cls:`IBMQJobManager`.
                If ``True``, re-query the server for the job set information.
                Otherwise return the cached value.
                Defaults to False.
            overwrite (bool, optional):
                Overwrite the local file if it exists.
                Defaults to False.
            reload (bool, optional):
                Whether to reload the multimanager.
                Defaults to False.
            read_from_tarfile (bool, optional):
                Whether to read from the tarfile.
                Defaults to False.
            compress (bool, optional):
                Whether to compress the export file.
                Defaults to False.

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """

        besummonned = self.multiRead(
            summoner_name=summoner_name,
            summoner_id=summoner_id,
            save_location=save_location,
            reload=reload,
            read_from_tarfile=read_from_tarfile,
        )
        current_multimanager = self.multimanagers[besummonned]
        assert current_multimanager.summoner_id == besummonned

        print("| MultiRetrieve running...")
        jobs_type = current_multimanager.multicommons.jobstype
        if backend is None:
            raise ValueError("backend is None.")

        self.accessor = ExtraBackendAccessor(
            multimanager=current_multimanager,
            experiment_container=self.exps,
            backend=backend,
            backend_type=jobs_type,
        )

        if jobs_type == "IBMQ":
            self.accessor.retrieve(
                overwrite=overwrite,
                refresh=refresh,
            )
        elif jobs_type == "IBM":
            self.accessor.retrieve(
                overwrite=overwrite,
            )

        else:
            warnings.warn(
                f"Jobstype of '{besummonned}' is "
                + f"{current_multimanager.multicommons.jobstype} which is not supported."
            )
            return besummonned

        retrieve_times = retrieve_counter(current_multimanager.multicommons.datetimes)

        if retrieve_times > 0:
            if overwrite:
                print(f"| Retrieve {current_multimanager.summoner_name} overwrite.")
            else:
                print(f"| Retrieve skip for {current_multimanager.summoner_name} existed.")
                return besummonned
        else:
            print(f"| Retrieve {current_multimanager.summoner_name} completed.")
        bewritten = self.multiWrite(besummonned, compress=compress)
        assert bewritten == besummonned

        return current_multimanager.multicommons.summoner_id

    def reset(
        self,
        *,
        keepWave: bool = True,
        security: bool = False,
    ) -> None:
        """Reset the measurement and release memory.

        Args:
            security (bool, optional): Security for reset. Defaults to `False`.
        """

        tmp_wave_container = dict(self.waves.items()) if keepWave else {}

        if security and isinstance(security, bool):
            # pylint: disable=unnecessary-dunder-call
            self.__init__()
            # pylint: enable=unnecessary-dunder-call
            gc.collect()
            for k, v in tmp_wave_container.items():
                self.add(v, k)
            warnings.warn(
                "The measurement has reset and release memory allocating.",
                QurryResetAccomplished,
            )
        else:
            warnings.warn(
                "Reset does not execute to prevent executing accidentally, "
                + "if you are sure to do this, then use '.reset(security=True)'.",
                QurryResetSecurityActivated,
            )


# pylint: enable=invalid-name
