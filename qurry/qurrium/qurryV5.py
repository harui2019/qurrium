"""
===========================================================
Qurry - A Qiskit Macro
===========================================================
"""
import gc
import inspect
import warnings
from abc import abstractmethod, abstractproperty
from typing import Literal, Union, Optional, Hashable, Type, Any, overload
from pathlib import Path
import tqdm

from qiskit import execute, transpile, QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.providers import Backend
from qiskit.circuit import Gate

from ..tools import ResoureWatch, qurryProgressBar, ProcessManager
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
from .runner import backendChoiceLiteral, ExtraBackendAccessor

from .utils import get_counts, decomposer_and_drawer
from .utils.inputfixer import outfields_check, outfields_hint
from ..exceptions import (
    QurryResetAccomplished,
    QurryResetSecurityActivated
)

# Qurry V0.5.0 - a Qiskit Macro


def defaultCircuit(num_qubit: int) -> QuantumCircuit:
    """Default circuit for QurryV5.

    Args:
        num_qubit (int): Number of qubits.

    Returns:
        QuantumCircuit: The default circuit.
    """
    return QuantumCircuit(
        num_qubit, num_qubit, name=f'qurry_default_{num_qubit}')


DefaultResourceWatch = ResoureWatch()


class QurryV5Prototype:
    """QurryV5
    A qiskit Macro.
    ~Create countless adventure, legacy and tales.~
    """
    __name__ = 'QurryV5Prototype'
    shortName = 'qurry'

    # container
    @classmethod
    @abstractproperty
    def experiment(cls) -> Type[ExperimentPrototype]:
        """The container class responding to this QurryV5 class.
        """
        raise NotImplementedError

    # Wave
    def add(
        self,
        wave: QuantumCircuit,
        key: Optional[Hashable] = None,
        replace: Literal[True, False, 'duplicate'] = False,
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
        return self.waves.add(
            wave=wave,
            key=key,
            replace=replace
        )

    def remove(self, key: Hashable) -> None:
        """Remove wave function from `.waves`.

        Args:
            wave (Hashable): The key of wave in `.waves`.
        """
        self.waves.remove(key)

    def operator(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Operator], Operator]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, 
                then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.waves.operator(wave)

    def gate(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, 
                then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.waves.gate(wave)

    def copy_circuit(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, 
                then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.waves.copy_circuit(wave)

    def instruction(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, 
                then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.waves.instruction(wave)

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
        resource_watch: ResoureWatch = DefaultResourceWatch,
    ) -> None:

        if isinstance(resource_watch, ResoureWatch):
            self.resource_watch = resource_watch
        else:
            raise TypeError(
                f"resourceWatch must be a ResoureWatch instance, not {type(resource_watch)}")

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

    # state checking
    @property
    def lastID(self) -> str:
        """The last experiment be executed."""
        return self.exps.lastID

    @property
    def lastExp(self) -> ExperimentPrototype:
        """The last experiment be executed.
        Replace the property :prop:`now`. in :cls:`QurryV4`"""
        return self.exps.lastExp

    @property
    def lastWave(self) -> QuantumCircuit:
        """The last wave be added."""
        return self.waves.lastWave

    @property
    def lastWaveKey(self) -> Hashable:
        """The key of the last wave be added."""
        return self.waves.lastWaveKey

    @abstractmethod
    def paramsControl(
        self, *arg, **kwargs
    ) -> tuple[ExperimentPrototype.arguments, ExperimentPrototype.commonparams, dict[str, Any]]:
        """Control the experiment's parameters."""
        raise NotImplementedError

    def _paramsControlMain(
        self,
        wave: Union[QuantumCircuit, Hashable, None] = None,

        expID: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralAerSimulator(),
        # provider: Optional[AccountProvider] = None,
        runArgs: Optional[dict[str, Any]] = None,

        runBy: Literal['gate', 'operator'] = "gate",
        transpileArgs: Optional[dict[str, Any]] = None,
        decompose: Optional[int] = 2,

        tags: tuple = (),

        defaultAnalysis: Optional[list[dict[str, Any]]] = None,

        serial: Optional[int] = None,
        summonerID: Optional[Hashable] = None,
        summonerName: Optional[str] = None,

        mute_outfields_warning: bool = False,
        _pbar: Optional[tqdm.tqdm] = None,
        **otherArgs: Any
    ) -> Hashable:
        """Control the experiment's general parameters.

        Args:
            wave (Union[QuantumCircuit, Hashable, None], optional): 
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.
            expID (Optional[str], optional): 
                If input is `None`, then create an new experiment.
                If input is a existed experiment ID, then use it.
                Otherwise, use the experiment with given specific ID.
                Defaults to None.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend, optional): 
                The quantum backend. Defaults to AerSimulator().
            runArgs (dict, optional): 
                defaultConfig of :func:`qiskit.execute`. Defaults to `{}`.
            runBy (Literal[&#39;gate&#39;, &#39;operator&#39;], optional): 
                Construct wave function via :cls:`Operater` 
                for "operator" or :cls:`Gate` for "gate".
                When use 'IBMQBackend' only allowed to use wave function 
                as `Gate` instead of `Operator`.
                Defaults to "gate".
            transpileArgs (dict, optional):
                defaultConfig of :func:`qiskit.transpile`. Defaults to `{}`.
            decompose (Optional[int], optional): 
                Running `QuantumCircuit` which be decomposed given times. Defaults to 2.
            tags (tuple, optional): 
                Given the experiment multiple tags to make a dictionary for recongnizing it.
                Defaults to ().
            defaultAnalysis (list[dict[str, Any]], optional): 
                The analysis methods will be excuted after counts has been computed.
                Defaults to [].
            serial (Optional[int], optional): 
                Index of experiment in a multiOutput.
                **!!ATTENTION, this should only be used by `Multimanager`!!**
                Defaults to None.
            summonerID (Optional[Hashable], optional): 
                ID of experiment of the multiManager. 
                **!!ATTENTION, this should only be used by `Multimanager`!!**
                Defaults to None.
            summonerName (Optional[str], optional): 
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
            TypeError: One of defaultAnalysis is not a dict.
            ValueError: One of defaultAnalysis is invalid.

        Returns:
            Hashable: The ID of the experiment.
        """

        if runArgs is None:
            runArgs = {}
        if transpileArgs is None:
            transpileArgs = {}
        if defaultAnalysis is None:
            defaultAnalysis = []

        if expID in self.exps:
            self.exps.call(expID)
            assert self.exps.lastID == expID
            assert self.exps.lastExp is not None
            assert self.exps.lastID == self.lastID
            return self.lastID
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Generating experiment... ")

        # wave
        if isinstance(wave, QuantumCircuit):
            waveKey = self.add(wave)
        elif isinstance(wave, Hashable):
            if wave is None:
                ...
            elif not self.has(wave):
                raise KeyError(f"Wave '{wave}' not found in '.waves'")
            waveKey = wave
        else:
            raise TypeError(
                f"'{wave}' is a '{type(wave)}' instead of 'QuantumCircuit' or 'Hashable'")

        ctrlArgs: ExperimentPrototype.arguments
        commons: ExperimentPrototype.commonparams
        outfields: dict[str, Any]
        # Given parameters and default parameters
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Prepaing parameters...")
        ctrlArgs, commons, outfields = self.paramsControl(
            waveKey=waveKey,
            expID=expID,
            shots=shots,
            backend=backend,
            # provider=provider,
            runArgs=runArgs,

            runBy=runBy,
            transpileArgs=transpileArgs,
            decompose=decompose,

            tags=tags,

            defaultAnalysis=defaultAnalysis,
            saveLocation=Path('./'),
            filename='',
            files={},
            serial=serial,
            summonerID=summonerID,
            summonerName=summonerName,
            datetimes=DatetimeDict(),
            **otherArgs)

        outfield_maybe, outfields_unknown = outfields_check(
            outfields, ctrlArgs._fields+commons._fields)
        outfields_hint(outfield_maybe, outfields_unknown,
                       mute_outfields_warning)

        if len(commons.defaultAnalysis) > 0:
            for index, analyze_input in enumerate(commons.defaultAnalysis):
                if not isinstance(analyze_input, dict):
                    raise TypeError(
                        "Each element of 'defaultAnalysis' must be a dict, " +
                        f"not {type(analyze_input)}, for index {index} in 'defaultAnalysis'")
                try:
                    self.experiment.analysis_container.input_filter(
                        **analyze_input)
                except TypeError as e:
                    raise ValueError(
                        f'analysis input filter found index {index} in "defaultAnalysis"') from e

        # config check
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Checking parameters... ")
        contain_checker(commons.transpileArgs, transpileConfig)
        contain_checker(commons.runArgs, runConfig)

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Create experiment instance... ")
        newExps = self.experiment(
            **ctrlArgs._asdict(),
            **commons._asdict(),
            **outfields,
        )

        self.exps[newExps.commons.expID] = newExps
        # The last wave only refresh here.
        self.exps.lastID = newExps.commons.expID

        assert self.exps.lastID == self.lastID
        assert self.exps[self.lastID].expID == self.lastExp.expID
        assert len(self.lastExp.beforewards.circuit) == 0
        assert len(self.lastExp.beforewards.figOriginal) == 0
        assert len(self.lastExp.afterwards.result) == 0
        assert len(self.lastExp.afterwards.counts) == 0

        return self.lastID

    # Circuit
    @overload
    @abstractmethod
    def method(
        self,
        expID: Hashable,
        _pbar: Optional[tqdm.tqdm] = None,
    ) -> list[QuantumCircuit]:
        ...

    @abstractmethod
    def method(
        self,
        expID: Hashable,
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
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,

        workers_num: Optional[int] = None,
        _export_mute: bool = True,
        _pbar: Optional[tqdm.tqdm] = None,
        **allArgs: Any,
    ) -> Hashable:
        """Construct the quantum circuit of experiment.
        ## The first finishing point.

        Args:
            saveLocation (Optional[Union[Path, str]], optional):
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
                f"{self.__name__} can't be initialized with positional arguments.")

        pool = ProcessManager(workers_num)

        # preparing
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Parameter loading...")

        IDNow = self._paramsControlMain(**allArgs, _pbar=_pbar)
        assert IDNow in self.exps, f"ID {IDNow} not found."
        assert self.exps[IDNow].commons.expID == IDNow
        currentExp = self.exps[IDNow]

        if len(currentExp.beforewards.circuit) > 0:
            return IDNow

        # circuit
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Circuit creating...")

        howTheMethodGetArgs = inspect.signature(self.method).parameters
        if '_pbar' in howTheMethodGetArgs:
            if howTheMethodGetArgs['_pbar'].annotation == Optional[tqdm.tqdm]:
                cirqs = self.method(IDNow, _pbar=_pbar)
            else:
                cirqs = self.method(IDNow)
        else:
            cirqs = self.method(IDNow)

        # draw original
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Circuit drawing by {workers_num} workers...")
        figOriginals: list[str] = pool.starmap(
            decomposer_and_drawer,
            [(_w, currentExp.commons.decompose) for _w in cirqs]
        )
        for wd in figOriginals:
            currentExp.beforewards.figOriginal.append(wd)

        # transpile
        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Circuit transpiling...")
        transpiledCirqs: list[QuantumCircuit] = transpile(
            cirqs,
            backend=currentExp.commons.backend,
            **currentExp.commons.transpileArgs
        )
        for _w in transpiledCirqs:
            currentExp.beforewards.circuit.append(_w)
        # commons
        date = current_time()
        currentExp.commons.datetimes['build'] = date

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str("Setup data exporting...")
        # export may be slow, consider export at finish or something
        if isinstance(saveLocation, (Path, str)):
            currentExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonablize,
                mute=_export_mute,
            )

        return IDNow

    def run(
        self,
        *args,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
        _export_mute: bool = True,
        **allArgs: Any,
    ) -> Hashable:
        """Export the result after running the job.

        Args:
            saveLocation (Optional[Union[Path, str]], optional):
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
                f"{self.__name__} can't be initialized with positional arguments.")

        # preparing
        IDNow = self.build(
            saveLocation=None,
            **allArgs
        )
        assert IDNow in self.exps, f"ID {IDNow} not found."
        assert self.exps[IDNow].commons.expID == IDNow
        currentExp = self.exps[IDNow]

        execution = execute(
            currentExp.beforewards.circuit,
            **currentExp.commons.runArgs,
            backend=currentExp.commons.backend,
            shots=currentExp.commons.shots,
        )
        # commons
        date = current_time()
        currentExp.commons.datetimes['run'] = date
        # beforewards
        jobID = execution.job_id()
        currentExp['jobID'] = jobID
        # afterwards
        result = execution.result()
        currentExp.unlock_afterward(mute_auto_lock=True)
        currentExp['result'].append(result)

        if isinstance(saveLocation, (Path, str)):
            currentExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonablize,
                mute=_export_mute,
            )

        return IDNow

    def result(
        self,
        *args,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
        _export_mute: bool = False,
        **allArgs: Any,
    ) -> Hashable:
        """Export the result after running the job.

        Args:
            saveLocation (Optional[Union[Path, str]], optional):
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
                f"{self.__name__} can't be initialized with positional arguments.")

        # preparing
        IDNow = self.run(
            saveLocation=None,
            **allArgs
        )
        assert IDNow in self.exps, f"ID {IDNow} not found."
        assert self.exps[IDNow].commons.expID == IDNow
        currentExp = self.exps[IDNow]
        assert len(
            currentExp.afterwards.result) == 1, "Result should be only one."

        # afterwards
        num = len(currentExp.beforewards.circuit)
        counts = get_counts(
            result=currentExp.afterwards.result[0],
            num=num,
        )
        for _c in counts:
            currentExp.afterwards.counts.append(_c)

        # default analysis
        if len(currentExp.commons.defaultAnalysis) > 0:
            for _analysis in currentExp.commons.defaultAnalysis:
                currentExp.analyze(**_analysis)

        if isinstance(saveLocation, (Path, str)):
            currentExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonablize,
                mute=_export_mute,
            )

        return IDNow

    def output(
        self,
        *args,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
        _export_mute: bool = False,

        **otherArgs: Any
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
            expName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            saveLocation (Optional[Union[Path, str]], optional):
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
                f"{self.__name__} can't be initialized with positional arguments.")

        IDNow = self.result(
            saveLocation=None,
            **otherArgs,
        )
        assert IDNow in self.exps, f"ID {IDNow} not found."
        assert self.exps[IDNow].commons.expID == IDNow
        currentExp = self.exps[IDNow]

        if len(currentExp.afterwards.result) > 0:
            return IDNow

        if isinstance(saveLocation, (Path, str)):
            currentExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonablize,
                mute=_export_mute,
            )

        return IDNow

    _rjustLen: int = 3
    """The length of the serial number of the experiment."""

    def _paramsControlMulti(
        self,
        # configList
        configList: list[dict[str, Any]],
        # defaultConfig of `IBMQJobManager().run`
        # Multiple jobs shared
        summonerName: str = 'exps',
        summonerID: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralAerSimulator(),
        # provider: AccountProvider = None,
        # Other arguments of experiment
        # Multiple jobs shared
        tags: Optional[list[str]] = None,
        saveLocation: Union[Path, str] = Path('./'),
        jobsType: backendChoiceLiteral = "local",
        # IBMQJobManager() dedicated
        managerRunArgs: Optional[dict[str, Any]] = None,
        filetype: TagList._availableFileType = 'json',

        is_retrieve: bool = False,
        is_read: bool = False,
        read_version: Literal['v4', 'v5'] = 'v5',
        read_from_tarfile: bool = False,
    ) -> tuple[list[dict[str, Any]], str]:
        """Control the experiment's parameters for running multiple jobs.

        Args:
            configList (list, optional): 
                The list of default configurations of multiple experiment. 
            summonerName (str, optional): 
                Name for multimanager. Defaults to 'exps'.
            summonerID (Optional[str], optional):
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

            saveLocation (Union[Path, str], optional): 
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            filetype (TagList._availableFileType, optional): 
                The file type of export data. Defaults to 'json' (recommended).
            managerRunArgs (dict, optional):
                defaultConfig of :func:`IBMQJobManager().run`.
                Defaults to `{
                    'max_experiments_per_job': 200,
                }`.
            jobsType (Literal[
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
                each experimemt and summonerID (ID of multimanager).
        """

        if tags is None:
            tags = []
        if managerRunArgs is None:
            managerRunArgs = {
                'max_experiments_per_job': 200,
            }

        if summonerID in self.multimanagers:
            currentMultimanager = self.multimanagers[summonerID]
            return list(
                currentMultimanager.beforewards.expsConfig.values()
            ), currentMultimanager.summonerID

        is_read = is_retrieve | is_read

        for config, checker in [
            (managerRunArgs, managerRunConfig),
        ]:
            contain_checker(config, checker)

        if is_read:
            currentMultimanager = MultiManager(
                summonerID=None,
                summonerName=summonerName,
                is_read=is_read,
                read_from_tarfile=read_from_tarfile,

                saveLocation=saveLocation,
                version=read_version,
            )
        else:
            currentMultimanager = MultiManager(
                summonerID=summonerID,
                summonerName=summonerName,
                shots=shots,
                backend=backend,
                # provider=provider,

                tags=tags,
                saveLocation=saveLocation,
                files={},

                jobsType=jobsType,
                managerRunArgs=managerRunArgs,
                filetype=filetype,
                datetimes=DatetimeDict(),
            )

        self.multimanagers[currentMultimanager.summonerID] = currentMultimanager

        initedConfigList: list[dict[str, Any]] = []
        for serial, config in enumerate(configList):
            initedConfigList.append({
                **config,
                'shots': shots,
                'backend': backend,
                # 'provider': provider,

                'expName': currentMultimanager.multicommons.summonerName,
                'saveLocation': currentMultimanager.multicommons.saveLocation,

                'serial': serial,
                'summonerID': currentMultimanager.multicommons.summonerID,
                'summonerName': currentMultimanager.multicommons.summonerName,
            })

        return initedConfigList, currentMultimanager.summonerID

    def multiBuild(
        self,
        # configList
        configList: list[dict[str, Any]],
        # defaultConfig of `IBMQJobManager().run`
        # Multiple jobs shared
        summonerName: str = 'exps',
        summonerID: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralAerSimulator(),
        # IBMQJobManager() dedicated
        tags: Optional[list[str]] = None,
        managerRunArgs: Optional[dict[str, Any]] = None,
        # Other arguments of experiment
        # Multiple jobs shared
        saveLocation: Union[Path, str] = Path('./'),
        jobsType: Union[Literal["local"], backendChoiceLiteral] = 'local',
        filetype: TagList._availableFileType = 'json',
    ) -> str:
        """Buling the experiment's parameters for running multiple jobs.

        Args:
            configList (list, optional): 
                The list of default configurations of multiple experiment. 
                Defaults to [].
            summonerName (str, optional): 
                Name for multimanager. Defaults to 'exps'.
            summonerID (Optional[str], optional):
                Name for multimanager. Defaults to None.
            shots (int, optional):
                Shots of the job.
                Defaults to `1024`.
            backend (Backend, optional):
                The quantum backend.
                Defaults to AerSimulator().
            managerRunArgs (dict, optional):
                defaultConfig of :func:`IBMQJobManager().run`.
                Defaults to `{}`.
            saveLocation (Union[Path, str], optional): 
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            jobsType (Literal[
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
        if managerRunArgs is None:
            managerRunArgs = {}

        print("| MultiManager building...")
        initedConfigList, besummonned = self._paramsControlMulti(
            configList=configList,
            shots=shots,
            backend=backend,
            # provider=provider,
            tags=tags,
            managerRunArgs=managerRunArgs,
            summonerName=summonerName,
            summonerID=summonerID,
            saveLocation=saveLocation,
            jobsType=jobsType,
            is_retrieve=False,
            is_read=False,
            filetype=filetype,
        )
        currentMultimanager = self.multimanagers[besummonned]
        assert currentMultimanager.summonerID == besummonned
        initedConfigListProgress = qurryProgressBar(initedConfigList)

        initedConfigListProgress.set_description_str(
            "MultiManager building...")
        for config in initedConfigListProgress:
            currentID = self.build(
                **config,
                _pbar=initedConfigListProgress,
            )
            currentMultimanager.beforewards.expsConfig[currentID] = config
            currentMultimanager.beforewards.circuitsNum[currentID] = len(
                self.exps[currentID].beforewards.circuit)
            files = self.exps[currentID].write(mute=True)

            currentMultimanager.beforewards.jobTagList[
                self.exps[currentID].commons.tags].append(currentID)
            currentMultimanager.beforewards.filesTagList[
                self.exps[currentID].commons.tags].append(files)
            currentMultimanager.beforewards.indexTagList[
                self.exps[currentID].commons.tags
            ].append(self.exps[currentID].commons.serial)

        filesMulti = currentMultimanager.write()

        assert len(currentMultimanager.beforewards.pendingPools) == 0
        assert len(currentMultimanager.beforewards.circuitsMap) == 0
        assert len(currentMultimanager.beforewards.jobID) == 0

        return currentMultimanager.multicommons.summonerID

    def multiOutput(
        self,
        # configList
        configList: list[dict[str, Any]],

        # defaultConfig of `IBMQJobManager().run`
        # Multiple jobs shared
        summonerName: str = 'exps',
        summonerID: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralAerSimulator(),
        tags: Optional[list[str]] = None,
        # provider: AccountProvider = None,
        # IBMQJobManager() dedicated
        # Other arguments of experiment
        # Multiple jobs shared
        saveLocation: Union[Path, str] = Path('./'),
        filetype: TagList._availableFileType = 'json',
        # analysis preparation
        defaultMultiAnalysis: Optional[list[dict[str, Any]]] = None,
        analysisName: str = 'report',
    ) -> Hashable:
        """Running multiple jobs on local backend and output the analysis.

        Args:
            configList (list, optional): 
                The list of default configurations of multiple experiment. 
                Defaults to [].
            summonerName (str, optional): 
                Name for multimanager. Defaults to 'exps'.
            summonerID (Optional[str], optional):
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
            saveLocation (Union[Path, str], optional): 
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
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
        if defaultMultiAnalysis is None:
            defaultMultiAnalysis = []

        print("| MultiOutput running...")
        besummonned = self.multiBuild(
            configList=configList,
            shots=shots,
            backend=backend,
            # provider=provider,
            tags=tags,
            managerRunArgs={},
            summonerName=summonerName,
            summonerID=summonerID,
            saveLocation=saveLocation,
            jobsType="local",
            filetype=filetype,
        )
        currentMultimanager = self.multimanagers[besummonned]
        assert currentMultimanager.summonerID == besummonned
        circSerial = []

        experimentProgress = qurryProgressBar(
            currentMultimanager.beforewards.expsConfig)

        for id_exec in experimentProgress:
            experimentProgress.set_description_str("Experiments running...")
            currentID = self.output(
                expID=id_exec,
                saveLocation=currentMultimanager.multicommons.saveLocation,
                _export_mute=True,
            )

            circSerialLen = len(circSerial)
            tmpCircSerial = [
                idx+circSerialLen
                for idx in range(len(self.exps[currentID].beforewards.circuit))]

            circSerial += tmpCircSerial
            currentMultimanager.beforewards.pendingPools[currentID] = tmpCircSerial
            currentMultimanager.beforewards.circuitsMap[currentID] = tmpCircSerial
            currentMultimanager.beforewards.jobID.append((currentID, 'local'))

            currentMultimanager.afterwards.allCounts[
                currentID] = self.exps[currentID].afterwards.counts

        currentMultimanager.multicommons.datetimes.add_serial('output')
        if len(defaultMultiAnalysis) > 0:
            print("| MultiOutput analyzing...")
            for analysis in defaultMultiAnalysis:
                self.multiAnalysis(
                    summonerID=currentMultimanager.multicommons.summonerID,
                    analysisName=analysisName,
                    _write=False,
                    **analysis,
                )

        bewritten = self.multiWrite(besummonned)
        assert bewritten == besummonned

        return currentMultimanager.multicommons.summonerID

    def multiPending(
        self,
        # configList
        configList: list[dict[str, Any]],
        # Multiple jobs shared
        summonerName: str = 'exps',
        summonerID: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralAerSimulator(),
        tags: Optional[list[str]] = None,
        managerRunArgs: Optional[dict[str, Any]] = None,
        # Other arguments of experiment
        # Multiple jobs shared
        saveLocation: Union[Path, str] = Path('./'),
        jobsType: backendChoiceLiteral = "IBM",

        filetype: TagList._availableFileType = 'json',

        pendingStrategy: Literal[
            'default', 'onetime', 'each', 'tags'] = 'default',

    ) -> Hashable:
        """Pending the multiple jobs on IBMQ backend or other remote backend.

        Args:
            configList (list, optional): 
                The list of default configurations of multiple experiment. 
                Defaults to [].
            summonerName (str, optional): 
                Name for multimanager. Defaults to 'exps'.
            summonerID (Optional[str], optional):
                Name for multimanager. Defaults to None.
            shots (int, optional):
                Shots of the job.
                Defaults to `1024`.
            backend (Backend, optional):
                The quantum backend.
                Defaults to AerSimulator().
            managerRunArgs (dict, optional):
                defaultConfig of :func:`IBMQJobManager().run`.
                Defaults to `{}`.
            saveLocation (Union[Path, str], optional): 
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            filetype (TagList._availableFileType, optional): 
                The file type of export data. Defaults to 'json' (recommend).
            pendingStrategy (Literal['default', 'onetime', 'each', 'tags'], optional):
                The strategy of pending for distributing experiments on jobs.

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """
        besummonned = self.multiBuild(
            configList=configList,
            shots=shots,
            backend=backend,
            tags=tags,
            managerRunArgs=managerRunArgs,
            summonerName=summonerName,
            summonerID=summonerID,
            saveLocation=saveLocation,
            jobsType=f"{jobsType}.{pendingStrategy}",
            filetype=filetype,
        )
        currentMultimanager = self.multimanagers[besummonned]
        assert currentMultimanager.summonerID == besummonned

        print("| MultiPending running...")
        self.accessor = ExtraBackendAccessor(
            multimanager=currentMultimanager,
            experimentContainer=self.exps,
            backend=backend,
            backendType=jobsType,
        )
        bependings = self.accessor.pending(
            pendingStrategy=pendingStrategy,
        )
        bewritten = self.multiWrite(besummonned)
        assert bewritten == besummonned

        return currentMultimanager.multicommons.summonerID

    def multiAnalysis(
        self,
        summonerID: str,
        analysisName: str = 'report',
        noSerialize: bool = False,
        specificAnalysisArgs: Optional[
            dict[Hashable, Union[dict[str, Any], bool]]
        ] = None,
        _write: bool = True,
        **analysisArgs: Any,
    ) -> Hashable:
        """Run the analysis for multiple experiments.

        Args:
            summonerID (str): Name for multimanager.
            analysisName (str, optional):
                The name of the analysis.
                Defaults to 'report'.
            specificAnalysisArgs (Optional[dict[Hashable, dict[str, Any]]], optional): 
                Specific some experiment to run the analysis arguments for each experiment.
                Defaults to {}.

        Raises:
            ValueError: No positional arguments allowed except `summonerID`.
            ValueError: summonerID not in multimanagers.
            ValueError: No counts in multimanagers, which experiments are not ready.

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """
        if specificAnalysisArgs is None:
            specificAnalysisArgs = {}

        if summonerID in self.multimanagers:
            currentMultimanager = self.multimanagers[summonerID]
        else:
            raise ValueError("No such summonerID in multimanagers.")

        reportName = currentMultimanager.analyze(
            self.exps,
            analysisName=analysisName,
            noSerialize=noSerialize,
            specificAnalysisArgs=specificAnalysisArgs,
            **analysisArgs,
        )
        print(f'| "{reportName}" has been completed.')

        if _write:
            filesMulti = currentMultimanager.write(_onlyQuantity=True)
        else:
            filesMulti = {}

        return currentMultimanager.multicommons.summonerID

    def multiWrite(
        self,
        summonerID: Hashable,
        saveLocation: Optional[Union[Path, str]] = None,
        compress: bool = True,
        compressOverwrite: bool = False,
        remainOnlyCompressed: bool = False,
    ) -> Hashable:
        """Write the multimanager to the file.

        Args:
            summonerID (Hashable): Name for multimanager.
            saveLocation (Union[Path, str], optional): 
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to Path('./').

        Raises:
            ValueError: summonerID not in multimanagers.

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """

        if not summonerID in self.multimanagers:
            raise ValueError(
                "No such summonerID in multimanagers.", summonerID)

        currentMultimanager = self.multimanagers[summonerID]
        assert currentMultimanager.summonerID == summonerID

        filesMulti = currentMultimanager.write(
            saveLocation=saveLocation if saveLocation is not None else None,
            wave_container=self.exps,
        )

        if compress:
            currentMultimanager.compress(
                compressOverwrite=compressOverwrite,
                remainOnlyCompressed=remainOnlyCompressed,
            )
        else:
            if compressOverwrite or remainOnlyCompressed:
                warnings.warn(
                    "'compressOverwrite' or 'remainOnlyCompressed' is set to True, " +
                    "but 'compress' is False.")

        return currentMultimanager.multicommons.summonerID

    def multiRead(
        self,
        # configList
        summonerName: str = 'exps',
        summonerID: Optional[str] = None,
        # IBMQJobManager() dedicated
        # Other arguments of experiment
        # Multiple jobs shared
        saveLocation: Union[Path, str] = Path('./'),

        read_from_tarfile: bool = False,
        # defaultMultiAnalysis: list[dict[str, Any]] = []
        # analysisName: str = 'report',
    ) -> Hashable:
        """Read the multimanager from the file.

        Args:
            summonerName (str, optional): 
                Name for multimanager. Defaults to 'exps'.
            summonerID (Optional[str], optional):
                Name for multimanager. Defaults to None.
            saveLocation (Union[Path, str], optional): 
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to Path('./').

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """

        print("| MultiRead running...")
        initedConfigList, besummonned = self._paramsControlMulti(
            configList=[],
            summonerName=summonerName,
            summonerID=summonerID,
            saveLocation=saveLocation,
            is_read=True,

            read_from_tarfile=read_from_tarfile,
        )

        assert besummonned in self.multimanagers
        assert self.multimanagers[besummonned].multicommons.summonerID == besummonned

        quene: list[ExperimentPrototype] = self.experiment.read(
            saveLocation=self.multimanagers[besummonned].multicommons.saveLocation,
            name=summonerName,
        )
        for exp in quene:
            self.exps[exp.expID] = exp

        # if len(defaultMultiAnalysis) > 0:
        #     currentMultimanager = self.multimanagers[besummonned]
        #     for analysis in defaultMultiAnalysis:
        #         self.multiAnalysis(
        #             summonerID=currentMultimanager.multicommons.summonerID,
        #             analysisName=analysisName,
        #             _write=False,
        #             **analysis,
        #         )

        return besummonned

    def multiRetrieve(
        self,
        # configList
        summonerName: str = 'exps',
        summonerID: Optional[str] = None,
        # IBMQJobManager() dedicated
        # Other arguments of experiment
        # Multiple jobs shared
        backend: Backend = None,
        # provider: AccountProvider = None,
        saveLocation: Union[Path, str] = Path('./'),
        refresh: bool = False,
        overwrite: bool = False,
        read_from_tarfile: bool = False,

        defaultMultiAnalysis: Optional[list[dict[str, Any]]] = None,
        analysisName: str = 'report',
        skipCompress: bool = False
    ) -> Hashable:
        """Retrieve the multimanager from the remote backend.

        Args:
            summonerName (str, optional): 
                Name for multimanager. Defaults to 'exps'.
            summonerID (Optional[str], optional):
                Name for multimanager. Defaults to None.
            backend (IBMBackend, optional):
                The quantum backend.
                Defaults to IBMBackend().
            provider (Optional[AccountProvider], optional):
                :cls:`AccountProvider` of current backend for running :cls:`IBMQJobManager`.
                Defaults to `None`.
            saveLocation (Union[Path, str], optional): 
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
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
        if defaultMultiAnalysis is None:
            defaultMultiAnalysis = []

        besummonned = self.multiRead(
            summonerName=summonerName,
            summonerID=summonerID,
            saveLocation=saveLocation,
            read_from_tarfile=read_from_tarfile,
        )
        currentMultimanager = self.multimanagers[besummonned]
        assert currentMultimanager.summonerID == besummonned

        print("| MultiRetrieve running...")
        jobsType, pendingStrategy = currentMultimanager.multicommons.jobsType.split(
            '.')

        self.accessor = ExtraBackendAccessor(
            multimanager=currentMultimanager,
            experimentContainer=self.exps,
            backend=backend,
            backendType=jobsType,
        )

        if jobsType == 'IBMQ':
            beretrieveds = self.accessor.retrieve(
                provider=backend.provider(),
                refresh=refresh,
                overwrite=overwrite,
            )
        elif jobsType == 'IBM':
            beretrieveds = self.accessor.retrieve(
                overwrite=overwrite,
            )

        else:
            warnings.warn(
                f"Jobstype of '{besummonned}' is " +
                f"{currentMultimanager.multicommons.jobsType} which is not supported.")
            return besummonned

        print(f"| Retrieve {currentMultimanager.summonerName} completed.")
        bewritten = self.multiWrite(besummonned, compress=not skipCompress)
        assert bewritten == besummonned

        if len(defaultMultiAnalysis) > 0:
            for analysis in defaultMultiAnalysis:
                self.multiAnalysis(
                    summonerID=currentMultimanager.multicommons.summonerID,
                    analysisName=analysisName,
                    _write=False,
                    **analysis,
                )

        return currentMultimanager.multicommons.summonerID

    def multiReadV4(
        self,
        # configList
        summonerName: str = 'exps',
        summonerID: Optional[str] = None,
        # IBMQJobManager() dedicated
        # Other arguments of experiment
        # Multiple jobs shared
        saveLocation: Union[Path, str] = Path('./'),

        # defaultMultiAnalysis: list[dict[str, Any]] = []
        # analysisName: str = 'report',
    ) -> Hashable:
        """Read the multimanager from the local file exported by QurryV4.

        Args:
            summonerName (str, optional): 
                Name for multimanager. Defaults to 'exps'.
            summonerID (Optional[str], optional):
                Name for multimanager. Defaults to None.
            saveLocation (Union[Path, str], optional): 
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to Path('./').

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """

        initedConfigList, besummonned = self._paramsControlMulti(
            configList=[],
            summonerName=summonerName,
            summonerID=summonerID,
            saveLocation=saveLocation,
            is_read=True,
            read_version='v4',
        )

        assert besummonned in self.multimanagers
        assert self.multimanagers[besummonned].multicommons.summonerID == besummonned
        currentMultimanager = self.multimanagers[besummonned]

        quene: list[ExperimentPrototype] = self.experiment.readV4(
            saveLocation=saveLocation,
            name=summonerName,
            summonerID=besummonned,
        )
        for exp in quene:
            self.exps[exp.expID] = exp
            currentMultimanager.beforewards.jobID.append([
                exp.expID, currentMultimanager.multicommons.jobsType])
            currentMultimanager.afterwards.allCounts[exp.expID] = exp.afterwards.counts

        # if len(defaultMultiAnalysis) > 0:
        #     currentMultimanager = self.multimanagers[besummonned]
        #     for analysis in defaultMultiAnalysis:
        #         self.multiAnalysis(
        #             summonerID=currentMultimanager.multicommons.summonerID,
        #             analysisName=analysisName,
        #             _write=False,
        #             **analysis,
        #         )

        return besummonned

    def reset(
        self,
        *args,
        keepWave: bool = True,
        security: bool = False,
    ) -> None:
        """Reset the measurement and release memory.

        Args:
            security (bool, optional): Security for reset. Defaults to `False`.
        """

        tmpWaveContainer = {
            k: v for k, v in self.waves.items()
        } if keepWave else {}

        if security and isinstance(security, bool):
            self.__init__()
            gc.collect()
            for k, v in tmpWaveContainer.items():
                self.add(v, k)
            warnings.warn(
                "The measurement has reset and release memory allocating.",
                QurryResetAccomplished)
        else:
            warnings.warn(
                "Reset does not execute to prevent executing accidentally, " +
                "if you are sure to do this, then use '.reset(security=True)'.",
                QurryResetSecurityActivated)


class QurryV5(QurryV5Prototype):
    """A QurryV5 instance is a container of experiments."""

    @classmethod
    @property
    def experiment(cls) -> Type[QurryExperiment]:
        """The container class responding to this QurryV5 class.
        """
        return QurryExperiment

    def paramsControl(
        self,
        expName: str = 'exps',
        waveKey: Hashable = None,
        sampling: int = 1,
        **otherArgs: Any
    ) -> tuple[QurryExperiment.arguments, QurryExperiment.commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            waveKey (Union[QuantumCircuit, int, None], optional):
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
            expName=expName,
            waveKey=waveKey,
            sampling=sampling,
            **otherArgs,
        )

    def method(
        self,
        expID: Hashable,
    ) -> list[QuantumCircuit]:

        assert expID in self.exps
        assert self.exps[expID].commons.expID == expID
        currentExp = self.exps[expID]
        args: QurryExperiment.arguments = self.exps[expID].args
        commons: QurryExperiment.commonparams = self.exps[expID].commons
        circuit = self.waves[commons.waveKey]
        numQubits = circuit.num_qubits

        currentExp['expName'] = f"{args.expName}-{currentExp.commons.waveKey}-x{args.sampling}"
        print(
            f"| Directly call: {currentExp.commons.waveKey} with sampling {args.sampling} times.")

        return [circuit for i in range(args.sampling)]

    def measure(
        self,
        wave: Union[QuantumCircuit, Any, None] = None,
        expName: str = 'exps',
        sampling: int = 1,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
        **otherArgs: Any
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
            expName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            sampling (int, optional):
                The number of sampling. Defaults to 1.
            saveLocation (Optional[Union[Path, str]], optional):
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

        IDNow = self.result(
            wave=wave,
            expName=expName,
            sampling=sampling,
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
