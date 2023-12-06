"""
===========================================================
Qurry - A Qiskit Macro
(:mod:`qurry.qurry.qurrium.qurryV5`)
===========================================================
"""
import gc
import inspect
import warnings
from abc import abstractmethod, abstractproperty, ABC
from typing import Literal, Union, Optional, Hashable, Type, Any, overload
from pathlib import Path
import tqdm

from qiskit import execute, transpile, QuantumCircuit
from qiskit.providers import Backend, JobV1 as Job

from ..tools import qurry_progressbar, ProcessManager
from ..capsule.mori import TagList
from ..tools.backend import GeneralAerSimulator
from ..tools.datetime import current_time, DatetimeDict
from ..declare.default import (
    transpileConfig,
    runConfig,
    managerRunConfig,
    contain_checker,
)
from .experiment import ExperimentPrototype, QurryExperiment
from .container import WaveContainer, ExperimentContainer
from .multimanager import MultiManager
from .runner import BackendChoiceLiteral, ExtraBackendAccessor

from .utils import get_counts, decomposer_and_drawer
from .utils.inputfixer import outfields_check, outfields_hint
from ..exceptions import QurryResetAccomplished, QurryResetSecurityActivated

# Qurry V0.5.0 - a Qiskit Macro


class QurryV5Prototype(ABC):
    """QurryV5
    A qiskit Macro.
    ~Create countless adventure, legacy and tales.~
    """

    __name__ = "QurryV5Prototype"
    shortName = "qurry"

    # container
    @classmethod
    @abstractproperty
    def experiment(cls) -> Type[ExperimentPrototype]:
        """The container class responding to this QurryV5 class."""
        raise NotImplementedError

    # Wave
    def add(
        self,
        wave: QuantumCircuit,
        key: Optional[Hashable] = None,
        replace: Literal[True, False, "duplicate"] = False,
    ) -> Hashable:
        """Add new wave function to measure.

        Args:
            waveCircuit (QuantumCircuit): The wave functions or circuits want to measure.
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

    def has(
        self,
        wavename: Hashable,
    ) -> bool:
        """Is there a wave with specific name.

        Args:
            wavename (Hashable): Name of wave which is used in `.waves`

        Returns:
            bool: Exist or not.
        """
        return self.waves.has(wavename)

    def __init__(
        self,
    ) -> None:
        self.waves: WaveContainer = WaveContainer()
        """The wave functions container."""

        self.exps: ExperimentContainer = ExperimentContainer()
        """The experiments container."""

        self.multimanagers: dict[str, MultiManager] = {}
        """The last multimanager be called.
        Replace the property :prop:`multiNow`. in :cls:`QurryV4`"""

        self.accessor: Optional[ExtraBackendAccessor] = None
        """The accessor of extra backend.
        It will be None if no extra backend is loaded.
        """

    @abstractmethod
    def params_control(
        self, wave_key: Hashable, **other_kwargs
    ) -> tuple[
        ExperimentPrototype.Arguments, ExperimentPrototype.Commonparams, dict[str, Any]
    ]:
        """Control the experiment's parameters."""
        raise NotImplementedError

    def _params_control_core(
        self,
        wave: Union[QuantumCircuit, Hashable, None] = None,
        exp_id: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralAerSimulator(),
        # provider: Optional[AccountProvider] = None,
        run_args: Optional[dict[str, Any]] = None,
        transpile_args: Optional[dict[str, Any]] = None,
        tags: tuple = (),
        default_analysis: Optional[list[dict[str, Any]]] = None,
        serial: Optional[int] = None,
        summoner_id: Optional[Hashable] = None,
        summoner_name: Optional[str] = None,
        mute_outfields_warning: bool = False,
        _pbar: Optional[tqdm.tqdm] = None,
        **other_kwargs: Any,
    ) -> str:
        """Control the experiment's general parameters.

        Args:
            wave (Union[QuantumCircuit, Hashable, None], optional):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.
            exp_id (Optional[str], optional):
                If input is `None`, then create an new experiment.
                If input is a existed experiment ID, then use it.
                Otherwise, use the experiment with given specific ID.
                Defaults to None.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend, optional):
                The quantum backend. Defaults to AerSimulator().
            run_args (dict, optional):
                defaultConfig of :func:`qiskit.execute`. Defaults to `{}`.
            runBy (Literal[&#39;gate&#39;, &#39;operator&#39;], optional):
                Construct wave function via :cls:`Operater`
                for "operator" or :cls:`Gate` for "gate".
                When use 'IBMQBackend' only allowed to use wave function
                as `Gate` instead of `Operator`.
                Defaults to "gate".
            transpile_args (dict, optional):
                defaultConfig of :func:`qiskit.transpile`. Defaults to `{}`.
            decompose (Optional[int], optional):
                Running `QuantumCircuit` which be decomposed given times. Defaults to 2.
            tags (tuple, optional):
                Given the experiment multiple tags to make a dictionary for recongnizing it.
                Defaults to ().
            default_analysis (list[dict[str, Any]], optional):
                The analysis methods will be excuted after counts has been computed.
                Defaults to [].
            serial (Optional[int], optional):
                Index of experiment in a multiOutput.
                **!!ATTENTION, this should only be used by `Multimanager`!!**
                Defaults to None.
            summoner_id (Optional[Hashable], optional):
                ID of experiment of the multiManager.
                **!!ATTENTION, this should only be used by `Multimanager`!!**
                Defaults to None.
            summoner_name (Optional[str], optional):
                Name of experiment of the multiManager.
                **!!ATTENTION, this should only be used by `Multimanager`!!**
                _description_. Defaults to None.
            muteOutfieldsWarning (bool, optional):
                Mute the warning when there are unused arguments detected and stored in outfields.
                Defaults to False.

        Raises:
            KeyError: Giving an not existed wave key.
            TypeError:
                Neither `QuantumCircuit` for directly adding new wave
                nor `Hashable` for key is given.
            TypeError: One of default_analysis is not a dict.
            ValueError: One of default_analysis is invalid.

        Returns:
            Hashable: The ID of the experiment.
        """
        if exp_id in self.exps:
            return exp_id

        if run_args is None:
            run_args = {}
        if transpile_args is None:
            transpile_args = {}
        if default_analysis is None:
            default_analysis = []

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Generating experiment... ")

        # wave
        if isinstance(wave, QuantumCircuit):
            wave_key = self.add(wave)
        elif isinstance(wave, Hashable):
            if wave is None:
                ...
            elif not self.has(wave):
                raise KeyError(f"Wave '{wave}' not found in '.waves'")
            wave_key = wave
        else:
            raise TypeError(
                f"'{wave}' is a '{type(wave)}' instead of 'QuantumCircuit' or 'Hashable'"
            )

        ctrl_args: ExperimentPrototype.Arguments
        commons: ExperimentPrototype.Commonparams
        outfields: dict[str, Any]
        # Given parameters and default parameters
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Prepaing parameters...")
        ctrl_args, commons, outfields = self.params_control(
            wave_key=wave_key,
            exp_id=exp_id,
            shots=shots,
            backend=backend,
            # provider=provider,
            run_args=run_args,
            transpile_args=transpile_args,
            tags=tags,
            default_analysis=default_analysis,
            save_location=Path("./"),
            filename="",
            files={},
            serial=serial,
            summoner_id=summoner_id,
            summoner_name=summoner_name,
            datetimes=DatetimeDict(),
            **other_kwargs,
        )

        outfield_maybe, outfields_unknown = outfields_check(
            outfields, ctrl_args._fields + commons._fields
        )
        outfields_hint(outfield_maybe, outfields_unknown, mute_outfields_warning)

        if len(commons.default_analysis) > 0:
            for index, analyze_input in enumerate(commons.default_analysis):
                if not isinstance(analyze_input, dict):
                    raise TypeError(
                        "Each element of 'default_analysis' must be a dict, "
                        + f"not {type(analyze_input)}, for index {index} in 'default_analysis'"
                    )
                try:
                    self.experiment.analysis_container.input_filter(**analyze_input)
                except TypeError as e:
                    raise ValueError(
                        f'analysis input filter found index {index} in "default_analysis"'
                    ) from e

        # config check
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Checking parameters... ")
        contain_checker(commons.transpile_args, transpileConfig)
        contain_checker(commons.run_args, runConfig)

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Create experiment instance... ")
        new_exps = self.experiment(
            **ctrl_args._asdict(),
            **commons._asdict(),
            **outfields,
        )

        self.exps[new_exps.commons.exp_id] = new_exps
        assert len(self.exps[new_exps.commons.exp_id].beforewards.circuit) == 0
        assert len(self.exps[new_exps.commons.exp_id].beforewards.fig_original) == 0
        assert len(self.exps[new_exps.commons.exp_id].afterwards.result) == 0
        assert len(self.exps[new_exps.commons.exp_id].afterwards.counts) == 0

        return new_exps.commons.exp_id

    # Circuit
    @overload
    @abstractmethod
    def method(
        self,
        exp_id: str,
        _pbar: Optional[tqdm.tqdm] = None,
    ) -> list[QuantumCircuit]:
        ...

    @abstractmethod
    def method(
        self,
        exp_id: str,
    ) -> list[QuantumCircuit]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]:
                The quantum circuit of experiment.
        """
        raise NotImplementedError

    def build(
        self,
        *args,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonablize: bool = False,
        workers_num: Optional[int] = None,
        skip_export: bool = False,
        _export_mute: bool = True,
        _pbar: Optional[tqdm.tqdm] = None,
        **other_kwargs: Any,
    ) -> str:
        """Construct the quantum circuit of experiment.
        ## The first finishing point.

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
            _export_mute (bool, optional):
                Whether to mute the export hint. Defaults to True.

            other_kwargs:
                all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            Hashable: The ID of the experiment.
        """

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments."
            )

        pool = ProcessManager(workers_num)

        # preparing
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Parameter loading...")

        id_now = self._params_control_core(**other_kwargs, _pbar=_pbar)
        assert id_now in self.exps, f"ID {id_now} not found."
        assert self.exps[id_now].commons.exp_id == id_now
        current_exp = self.exps[id_now]

        if len(current_exp.beforewards.circuit) > 0:
            return id_now

        # circuit
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Circuit creating...")

        how_the_method_get_args = inspect.signature(self.method).parameters
        if "_pbar" in how_the_method_get_args:
            if how_the_method_get_args["_pbar"].annotation == Optional[tqdm.tqdm]:
                cirqs = self.method(id_now, _pbar=_pbar)
            else:
                cirqs = self.method(id_now)
        else:
            cirqs = self.method(id_now)

        # draw original
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(f"Circuit drawing by {workers_num} workers...")
        fig_originals: list[str] = pool.starmap(
            decomposer_and_drawer, [(_w, 0) for _w in cirqs]
        )
        for wd in fig_originals:
            current_exp.beforewards.fig_original.append(wd)

        # transpile
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Circuit transpiling...")
        transpiled_circs: list[QuantumCircuit] = transpile(
            cirqs,
            backend=current_exp.commons.backend,
            **current_exp.commons.transpile_args,
        )
        for _w in transpiled_circs:
            current_exp.beforewards.circuit.append(_w)
        # commons
        date = current_time()
        current_exp.commons.datetimes["build"] = date

        if not skip_export:
            if isinstance(_pbar, tqdm.tqdm):
                _pbar.set_description_str("Setup data exporting...")
            # export may be slow, consider export at finish or something
            if isinstance(save_location, (Path, str)):
                current_exp.write(
                    save_location=save_location,
                    mode=mode,
                    indent=indent,
                    encoding=encoding,
                    jsonable=jsonablize,
                    mute=_export_mute,
                )

        return id_now

    def run(
        self,
        *args,
        save_location: Optional[Union[Path, str]] = None,
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
            _export_mute (bool, optional):
                Whether to mute the export hint. Defaults to True.

            allArgs:
                all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            Hashable: The ID of the experiment.
        """

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments."
            )

        # preparing
        id_now = self.build(save_location=save_location, **other_kwargs)
        assert id_now in self.exps, f"ID {id_now} not found."
        assert self.exps[id_now].commons.exp_id == id_now
        current_exp = self.exps[id_now]

        execution: Job = execute(
            current_exp.beforewards.circuit,
            **current_exp.commons.run_args,
            backend=current_exp.commons.backend,
            shots=current_exp.commons.shots,
        )
        # commons
        date = current_time()
        current_exp.commons.datetimes["run"] = date
        # beforewards
        current_exp["job_id"] = execution.job_id()
        # afterwards
        result = execution.result()
        current_exp.unlock_afterward(mute_auto_lock=True)
        current_exp["result"].append(result)

        return id_now

    def result(
        self,
        *args,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonablize: bool = False,
        _export_mute: bool = False,
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
            _export_mute (bool, optional):
                Whether to mute the export hint. Defaults to True.

            allArgs:
                all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            Hashable: The ID of the experiment.
        """

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments."
            )

        # preparing
        id_now = self.run(
            save_location=save_location,
            mode=mode,
            indent=indent,
            encoding=encoding,
            jsonablize=jsonablize,
            _export_mute=_export_mute,
            _pbar=_pbar,
            **other_kwargs,
        )
        assert id_now in self.exps, f"ID {id_now} not found."
        assert self.exps[id_now].commons.exp_id == id_now
        current_exp = self.exps[id_now]
        assert len(current_exp.afterwards.result) == 1, "Result should be only one."

        # afterwards
        num = len(current_exp.beforewards.circuit)
        counts = get_counts(
            result=current_exp.afterwards.result[0],
            num=num,
        )
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
                mute=_export_mute,
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
        _export_mute: bool = False,
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
            _export_mute (bool, optional):
                Whether to mute the export hint. Defaults to True.

            otherArgs (Any):
                Other arguments.

        Returns:
            dict: The output.
        """

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments."
            )

        id_now = self.result(
            save_location=save_location,
            mode=mode,
            indent=indent,
            encoding=encoding,
            jsonablize=jsonablize,
            _export_mute=_export_mute,
            _pbar=_pbar,
            **other_kwargs,
        )
        assert id_now in self.exps, f"ID {id_now} not found."
        assert self.exps[id_now].commons.exp_id == id_now
        current_exp = self.exps[id_now]

        if len(current_exp.afterwards.result) > 0:
            return id_now

        return id_now

    _rjustLen: int = 3
    """The length of the serial number of the experiment."""

    def _params_control_multi(
        self,
        config_list: list[dict[str, Any]],
        summoner_name: str = "exps",
        summoner_id: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralAerSimulator(),
        tags: Optional[list[str]] = None,
        save_location: Union[Path, str] = Path("./"),
        jobstype: BackendChoiceLiteral = "local",
        manager_run_args: Optional[dict[str, Any]] = None,
        filetype: TagList._availableFileType = "json",
        is_retrieve: bool = False,
        is_read: bool = False,
        read_version: Literal["v4", "v5"] = "v5",
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
                'local', 'IBMQ', 'AWS_Bracket', '''Azure_Q'
            ], optional):
                What types of the backend will run on. Defaults to "local".
            is_retrieve (bool, optional):
                Whether this jobs will retrieve the pending experiment after initializing.
                Defaults to `False`.
            is_read (bool, optional):
                Whether this jobs will read the existed experiment data during initializing.
                Defaults to False.
            read_version (Literal['v4', 'v5'], optional):
                The version of the data to be read.
                Defaults to 'v5'.

        Returns:
            tuple[list[dict[str, Any]], str]:
                The list of formated configuration of
                each experimemt and summoner_id (ID of multimanager).
        """

        if tags is None:
            tags = []
        if manager_run_args is None:
            manager_run_args = {
                "max_experiments_per_job": 200,
            }

        if summoner_id in self.multimanagers:
            current_multimanager = self.multimanagers[summoner_id]
            return (
                list(current_multimanager.beforewards.expsConfig.values()),
                current_multimanager.summoner_id,
            )

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
                version=read_version,
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
                managerRunArgs=manager_run_args,
                filetype=filetype,
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
        backend: Backend = GeneralAerSimulator(),
        tags: Optional[list[str]] = None,
        manager_run_args: Optional[dict[str, Any]] = None,
        save_location: Union[Path, str] = Path("./"),
        jobstype: Union[Literal["local"], BackendChoiceLiteral] = "local",
        filetype: TagList._availableFileType = "json",
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
            filetype (TagList._availableFileType, optional):
                The file type of export data. Defaults to 'json' (recommend).

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
            # provider=provider,
            tags=tags,
            manager_run_args=manager_run_args,
            summoner_name=summoner_name,
            summoner_id=summoner_id,
            save_location=save_location,
            jobstype=jobstype,
            is_retrieve=False,
            is_read=False,
            filetype=filetype,
        )
        current_multimanager = self.multimanagers[besummonned]
        assert current_multimanager.summoner_id == besummonned
        initial_config_list_progress = qurry_progressbar(initial_config_list)

        initial_config_list_progress.set_description_str("MultiManager building...")
        for config in initial_config_list_progress:
            current_id = self.build(
                **config,
                skip_export=True,  # export later for it's not efficient for one by one
                _pbar=initial_config_list_progress,
            )
            current_multimanager.beforewards.expsConfig[current_id] = config
            current_multimanager.beforewards.circuitsNum[current_id] = len(
                self.exps[current_id].beforewards.circuit
            )
            files = self.exps[current_id].write(
                save_location=current_multimanager.multicommons.save_location, mute=True
            )

            current_multimanager.beforewards.jobTagList[
                self.exps[current_id].commons.tags
            ].append(current_id)
            current_multimanager.beforewards.filesTagList[
                self.exps[current_id].commons.tags
            ].append(files)
            current_multimanager.beforewards.indexTagList[
                self.exps[current_id].commons.tags
            ].append(self.exps[current_id].commons.serial)

        current_multimanager.write()

        assert len(current_multimanager.beforewards.pendingPools) == 0
        assert len(current_multimanager.beforewards.circuitsMap) == 0
        assert len(current_multimanager.beforewards.job_id) == 0

        return current_multimanager.multicommons.summoner_id

    def multiOutput(
        self,
        config_list: list[dict[str, Any]],
        summoner_name: str = "exps",
        summoner_id: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralAerSimulator(),
        tags: Optional[list[str]] = None,
        save_location: Union[Path, str] = Path("./"),
        filetype: TagList._availableFileType = "json",
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
            # provider (Optional[AccountProvider], optional):
            #     :cls:`AccountProvider` of current backend for running :cls:`IBMQJobManager`.
            #     Defaults to `None`.
            save_location (Union[Path, str], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            filetype (TagList._availableFileType, optional):
                The file type of export data. Defaults to 'json' (recommend).
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
            filetype=filetype,
        )
        current_multimanager = self.multimanagers[besummonned]
        assert current_multimanager.summoner_id == besummonned
        circ_serial: list[int] = []

        experiment_progress = qurry_progressbar(
            current_multimanager.beforewards.expsConfig
        )

        for id_exec in experiment_progress:
            experiment_progress.set_description_str("Experiments running...")
            current_id = self.output(
                exp_id=id_exec,
                save_location=current_multimanager.multicommons.save_location,
                _export_mute=True,
            )

            circ_serial_len = len(circ_serial)
            tmp_circ_serial = [
                idx + circ_serial_len
                for idx in range(len(self.exps[current_id].beforewards.circuit))
            ]

            circ_serial += tmp_circ_serial
            current_multimanager.beforewards.pendingPools[current_id] = tmp_circ_serial
            current_multimanager.beforewards.circuitsMap[current_id] = tmp_circ_serial
            current_multimanager.beforewards.job_id.append((current_id, "local"))

            current_multimanager.afterwards.allCounts[current_id] = self.exps[
                current_id
            ].afterwards.counts
        current_multimanager.multicommons.datetimes.add_serial("output")
        # For output include writting, no need to write again
        # bewritten = self.multiWrite(besummonned)
        # assert bewritten == besummonned

        return current_multimanager.multicommons.summoner_id

    def multiPending(
        self,
        config_list: list[dict[str, Any]],
        summoner_name: str = "exps",
        summoner_id: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralAerSimulator(),
        tags: Optional[list[str]] = None,
        manager_run_args: Optional[dict[str, Any]] = None,
        save_location: Union[Path, str] = Path("./"),
        jobstype: BackendChoiceLiteral = "IBM",
        filetype: TagList._availableFileType = "json",
        pending_strategy: Literal["onetime", "each", "tags"] = "onetime",
    ) -> Hashable:
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
            filetype (TagList._availableFileType, optional):
                The file type of export data. Defaults to 'json' (recommend).
            pendingStrategy (Literal['default', 'onetime', 'each', 'tags'], optional):
                The strategy of pending for distributing experiments on jobs.

        Returns:
            Hashable: SummonerID (ID of multimanager).
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
            jobstype=f"{jobstype}.{pending_strategy}",
            filetype=filetype,
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
        specific_analysis_args: Optional[
            dict[Hashable, Union[dict[str, Any], bool]]
        ] = None,
        _write: bool = True,
        **analysis_args: Any,
    ) -> Hashable:
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
            Hashable: SummonerID (ID of multimanager).
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

        if _write:
            current_multimanager.write(_only_quantity=True)

        return current_multimanager.multicommons.summoner_id

    def multiWrite(
        self,
        summoner_id: Hashable,
        save_location: Optional[Union[Path, str]] = None,
        compress: bool = True,
        compress_overwrite: bool = False,
        remain_only_compressed: bool = False,
    ) -> Hashable:
        """Write the multimanager to the file.

        Args:
            summoner_id (Hashable): Name for multimanager.
            save_location (Union[Path, str], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').

        Raises:
            ValueError: summoner_id not in multimanagers.

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """

        if not summoner_id in self.multimanagers:
            raise ValueError("No such summoner_id in multimanagers.", summoner_id)

        current_multimanager = self.multimanagers[summoner_id]
        assert current_multimanager.summoner_id == summoner_id

        current_multimanager.write(
            save_location=save_location if save_location is not None else None,
            wave_container=self.exps,
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
        summoner_name: str = "exps",
        summoner_id: Optional[str] = None,
        save_location: Union[Path, str] = Path("./"),
        read_from_tarfile: bool = False,
        # defaultMultiAnalysis: list[dict[str, Any]] = []
        # analysisName: str = 'report',
    ) -> Hashable:
        """Read the multimanager from the file.

        Args:
            summoner_name (str, optional):
                Name for multimanager. Defaults to 'exps'.
            summoner_id (Optional[str], optional):
                Name for multimanager. Defaults to None.
            save_location (Union[Path, str], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """

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
            name_or_id=summoner_name,
        )
        for exp in quene:
            self.exps[exp.exp_id] = exp

        return besummonned

    def multiRetrieve(
        self,
        summoner_name: str = "exps",
        summoner_id: Optional[str] = None,
        backend: Backend = None,
        save_location: Union[Path, str] = Path("./"),
        refresh: bool = False,
        overwrite: bool = False,
        read_from_tarfile: bool = False,
        skip_compress: bool = False,
    ) -> Hashable:
        """Retrieve the multimanager from the remote backend.

        Args:
            summoner_name (str, optional):
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

        besummonned = self.multiRead(
            summoner_name=summoner_name,
            summoner_id=summoner_id,
            save_location=save_location,
            read_from_tarfile=read_from_tarfile,
        )
        current_multimanager = self.multimanagers[besummonned]
        assert current_multimanager.summoner_id == besummonned

        print("| MultiRetrieve running...")
        jobs_type, _pending_strategy = current_multimanager.multicommons.jobstype.split(
            "."
        )

        self.accessor = ExtraBackendAccessor(
            multimanager=current_multimanager,
            experiment_container=self.exps,
            backend=backend,
            backend_type=jobs_type,
        )

        if jobs_type == "IBMQ":
            self.accessor.retrieve(
                provider=backend.provider(),
                refresh=refresh,
                overwrite=overwrite,
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

        print(f"| Retrieve {current_multimanager.summoner_name} completed.")
        bewritten = self.multiWrite(besummonned, compress=not skip_compress)
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


class QurryV5(QurryV5Prototype):
    """A QurryV5 instance is a container of experiments."""

    @classmethod
    @property
    def experiment(cls) -> Type[QurryExperiment]:
        """The container class responding to this QurryV5 class."""
        return QurryExperiment

    def params_control(
        self,
        wave_key: Hashable = None,
        exp_name: str = "exps",
        sampling: int = 1,
        **otherArgs: Any,
    ) -> tuple[QurryExperiment.Arguments, QurryExperiment.Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            wave_key (Union[QuantumCircuit, int, None], optional):
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
            otherArgs (Any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """

        if isinstance(sampling, int):
            ...
        else:
            sampling = 1
            warnings.warn(f"'{sampling}' is not an integer, use 1 as default")

        return self.experiment.filter(
            exp_name=exp_name,
            wave_key=wave_key,
            sampling=sampling,
            **otherArgs,
        )

    def method(
        self,
        exp_id: Hashable,
        _pbar: Optional[tqdm.tqdm] = None,
    ) -> list[QuantumCircuit]:
        assert exp_id in self.exps
        assert self.exps[exp_id].commons.exp_id == exp_id
        current_exp = self.exps[exp_id]
        args: QurryExperiment.Arguments = self.exps[exp_id].args
        commons: QurryExperiment.Commonparams = self.exps[exp_id].commons
        circuit = self.waves[commons.wave_key]

        current_exp[
            "exp_name"
        ] = f"{args.exp_name}-{current_exp.commons.wave_key}-x{args.sampling}"
        print(
            f"| Directly call: {current_exp.commons.wave_key} with sampling {args.sampling} times."
        )

        return [circuit for i in range(args.sampling)]

    def measure(
        self,
        wave: Union[QuantumCircuit, Any, None] = None,
        exp_name: str = "exps",
        sampling: int = 1,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonablize: bool = False,
        **otherArgs: Any,
    ):
        """The main function to measure the wave function,
        which is the :meth:`result` with dedicated arguments.

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
            sampling (int, optional):
                The number of sampling. Defaults to 1.
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

            otherArgs (Any):
                Other arguments in :meth:`result`.

        Returns:
            dict: The output.
        """

        id_now = self.result(
            wave=wave,
            exp_name=exp_name,
            sampling=sampling,
            save_location=None,
            **otherArgs,
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
