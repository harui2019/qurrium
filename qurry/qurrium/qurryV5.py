from qiskit import execute, transpile, QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Operator
from qiskit.circuit import Gate
from qiskit.result import Result
from qiskit.providers import Backend
from qiskit.providers.ibmq import IBMQJobManager, AccountProvider
from qiskit.providers.ibmq.managed import (
    ManagedJobSet,
    # ManagedJob,
    ManagedResults,
    IBMQManagedResultDataNotAvailable,
    # IBMQJobManagerInvalidStateError,
    # IBMQJobManagerUnknownJobSet
    IBMQJobManagerJobNotFound
)

import warnings
import datetime
from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, Iterable, Type, overload, Any
from abc import abstractmethod, abstractclassmethod, abstractproperty

from ..mori import TagMap
from ..mori.type import TagMapType
from ..tools import Gajima, ResoureWatch

from .declare.default import (
    transpileConfig,
    runConfig,
    managerRunConfig,
    containChecker,
)
from .experiment import ExperimentPrototype, QurryExperiment, DummyExperiment
from .container import WaveContainer, ExperimentContainer
from .multimanager import MultiManager

from .utils import decomposer
from ..exceptions import QurryInheritionNoEffect

# Qurry V0.5.0 - a Qiskit Macro


def defaultCircuit(numQubit: int) -> QuantumCircuit:
    return QuantumCircuit(
        numQubit, numQubit, name=f'qurry_default_{numQubit}')


DefaultResourceWatch = ResoureWatch()


class QurryV5Prototype:
    """QurryV5
    A qiskit Macro.
    ~Create countless adventure, legacy and tales.~
    """
    __version__ = (0, 5, 0)
    __name__ = 'QurryV5Prototype'
    shortName = 'qurry'

    # container
    @classmethod
    @abstractproperty
    def experiment(cls) -> Type[ExperimentPrototype]:
        """The container class responding to this QurryV5 class.
        """

    # @abstractproperty
    # def multimanager(self) -> property:
    #     return property()

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
            key (Optional[Hashable], optional): Given a specific key to add to the wave function or circuit,
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
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
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
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
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
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
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
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
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
        *waves: Union[QuantumCircuit, tuple[Hashable, QuantumCircuit]],
        resourceWatch: ResoureWatch = DefaultResourceWatch,
    ) -> None:

        if isinstance(resourceWatch, ResoureWatch):
            self.resourceWatch = resourceWatch
        else:
            raise TypeError(
                f"resourceWatch must be a ResoureWatch instance, not {type(resourceWatch)}")

        self.waves: WaveContainer = WaveContainer()
        """The wave functions container."""
        for w in waves:
            if isinstance(w, QuantumCircuit):
                self.add(w)
            elif isinstance(w, tuple):
                self.add(w[0], w[1])
            else:
                warnings.warn(
                    f"'{w}' is a '{type(w)}' instead of 'QuantumCircuit' or 'tuple' " +
                    "contained hashable key and 'QuantumCircuit', skipped to be adding.",
                    category=TypeError)

        self.exps: ExperimentContainer = ExperimentContainer()
        """The experiments container."""

        self.multimanagers: dict[str, MultiManager] = {}
        """The last multiJob be called.
        Replace the property :prop:`multiNow`. in :cls:`QurryV4`"""

    # state checking
    @property
    def lastID(self) -> Hashable:
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
    def paramsControl(self) -> tuple[ExperimentPrototype.arguments, ExperimentPrototype.commonparams, dict[str, Any]]:
        """Control the experiment's parameters."""

    def _paramsControlMain(
        self,
        wave: Union[QuantumCircuit, Hashable, None] = None,

        expID: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = AerSimulator(),
        provider: Optional[AccountProvider] = None,
        runArgs: dict = {},

        runBy: Literal['gate', 'operator'] = "gate",
        transpileArgs: dict = {},
        decompose: Optional[int] = 2,

        tags: tuple = (),

        defaultAnalysis: list[dict[str, Any]] = [],

        serial: Optional[int] = None,
        summonerID: Optional[Hashable] = None,
        summonerName: Optional[str] = None,

        muteOutfieldsWarning: bool = False,
        **otherArgs: any
    ) -> Hashable:

        if expID in self.exps:
            self.exps.call(expID)
            assert self.exps.lastID == expID
            assert self.exps.lastExp is not None
            assert self.exps.lastID == self.lastID
            return self.lastID

        # wave
        if isinstance(wave, QuantumCircuit):
            waveKey = self.add(wave)
        elif isinstance(wave, Hashable):
            if not self.has(wave):
                raise KeyError(f"Wave '{wave}' not found in '.waves'")
            waveKey = wave
        else:
            raise TypeError(
                f"'{wave}' is a '{type(wave)}' instead of 'QuantumCircuit' or 'Hashable'")

        ctrlArgs: ExperimentPrototype.arguments
        commons: ExperimentPrototype.commonparams
        outfields: dict[str, Any]
        # Given parameters and default parameters
        ctrlArgs, commons, outfields = self.paramsControl(
            waveKey=waveKey,
            expID=expID,
            shots=shots,
            backend=backend,
            provider=provider,
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
            datetimes={},
            **otherArgs)

        # TODO: levenshtein_distance check for outfields
        if len(outfields) > 0:
            if not muteOutfieldsWarning:
                warnings.warn(
                    f"The following keys are not recognized as arguments for main process of experiment: " +
                    f"{list(outfields.keys())}'" +
                    ', but are still kept in experiment record.',
                    QurryInheritionNoEffect
                )

        if len(commons.defaultAnalysis) > 0:
            for index, analyze_input in enumerate(commons.defaultAnalysis):
                if not isinstance(analyze_input, dict):
                    raise TypeError(
                        f"Each element of 'defaultAnalysis' must be a dict, not {type(analyze_input)}, for index {index} in 'defaultAnalysis'")
                try:
                    self.experiment.analysis_container.input_filter(
                        **analyze_input)
                except TypeError as e:
                    raise ValueError(
                        f'analysis input filter found index {index} in "defaultAnalysis" failed: {e}')

        # config check
        containChecker(commons.transpileArgs, transpileConfig)
        containChecker(commons.runArgs, runConfig)

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
        assert len(self.lastExp.beforewards.figTranspiled) == 0
        assert len(self.lastExp.afterwards.result) == 0
        assert len(self.lastExp.afterwards.counts) == 0

        return self.lastID

    # Circuit
    @abstractmethod
    def method(self) -> list[QuantumCircuit]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]:
                The quantum circuit of experiment.
        """

    def build(
        self,
        *args,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
        _exportMute: bool = True,
        **allArgs: any,
    ) -> Hashable:
        """Construct the quantum circuit of experiment.
        The first finishing point.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            Hashable: The ID of the experiment.
        """

        # preparing
        IDNow = self._paramsControlMain(**allArgs)
        assert IDNow == self.lastID
        assert self.lastExp is not None
        currentExp = self.lastExp
        if len(currentExp.beforewards.circuit) > 0:
            return IDNow

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments.")

        # circuit
        cirqs = self.method()

        # draw original
        for _w in cirqs:
            currentExp.beforewards.figOriginal.append(
                decomposer(_w, currentExp.commons.decompose).draw(output='text'))

        # transpile
        transpiledCirqs: list[QuantumCircuit] = transpile(
            cirqs,
            backend=self.lastExp.commons.backend,
            **currentExp.commons.transpileArgs
        )
        for _w in transpiledCirqs:
            currentExp.beforewards.figTranspiled.append(
                decomposer(_w, currentExp.commons.decompose).draw(output='text'))
            currentExp.beforewards.circuit.append(_w)

        if isinstance(saveLocation, (Path, str)):
            currentExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonablize=jsonablize,
                mute=_exportMute,
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
        _exportMute: bool = True,
        **allArgs: any,
    ) -> Hashable:
        """Export the result after running the job.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            Hashable: The ID of the experiment.
        """

        # preparing
        IDNow = self.build(
            saveLocation=None,
            **allArgs
        )
        assert IDNow == self.lastID
        assert self.lastExp is not None

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments.")

        execution = execute(
            self.lastExp.beforewards.circuit,
            **self.lastExp.commons.runArgs,
            backend=self.lastExp.commons.backend,
            shots=self.lastExp.commons.shots,
        )
        # commons
        date = datetime.datetime.today().strftime("%Y-%m-%d_%H-%M-%S")
        self.lastExp.commons.datetimes['run'] = date
        # beforewards
        jobID = execution.job_id()
        self.lastExp['jobID'] = jobID
        # afterwards
        result = execution.result()
        self.lastExp.unlock_afterward(mute_auto_lock=True)
        self.lastExp['result'].append(result)

        if isinstance(saveLocation, (Path, str)):
            self.lastExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonablize=jsonablize,
                mute=_exportMute,
            )

        return IDNow

    @classmethod
    def get_counts(
        cls,
        result: Union[Result, ManagedResults, None],
        num: Optional[int] = None,
        resultIdxList: Optional[list[int]] = None,
    ) -> list[dict[str, int]]:
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """
        counts: list[dict[str, int]] = []
        if result is None:
            counts.append({})
            print("| Failed Job result skip, Job ID:", result.job_id)
            return counts

        try:
            if num is None:
                get: Union[list[dict[str, int]],
                           dict[str, int]] = result.get_counts()
                if isinstance(get, list):
                    counts: list[dict[str, int]] = get
                else:
                    counts.append(get)
            else:
                if resultIdxList is None:
                    resultIdxList = [i for i in range(num)]
                for i in resultIdxList:
                    allMeas = result.get_counts(i)
                    counts.append(allMeas)

        except IBMQManagedResultDataNotAvailable as err:
            counts.append({})
            print("| Failed Job result skip, Job ID:", result.job_id, err)
        except IBMQJobManagerJobNotFound as err:
            counts.append({})
            print("| Failed Job result skip, Job ID:", result.job_id, err)

        return counts

    def result(
        self,
        *args,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
        _exportMute: bool = False,
        **allArgs: any,
    ) -> Hashable:
        """Export the result after running the job.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            Hashable: The ID of the experiment.
        """

        # preparing
        IDNow = self.run(
            saveLocation=None,
            **allArgs
        )
        assert IDNow == self.lastID
        assert self.lastExp is not None
        assert len(
            self.lastExp.afterwards.result) == 1, "Result should be only one."

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments.")

        # afterwards
        num = len(self.lastExp.beforewards.circuit)
        counts = self.get_counts(
            result=self.lastExp.afterwards.result[0],
            num=num,
        )
        for _c in counts:
            self.lastExp.afterwards.counts.append(_c)

        # default analysis
        if len(self.lastExp.commons.defaultAnalysis) > 0:
            for _analysis in self.lastExp.commons.defaultAnalysis:
                self.lastExp.analyze(**_analysis)

        if isinstance(saveLocation, (Path, str)):
            self.lastExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonablize=jsonablize,
                mute=_exportMute,
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
        _exportMute: bool = False,
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
                mute=_exportMute,
            )

        return IDNow

    _rjustLen = 3

    def _paramsControlMulti(
        self,
        # configList
        configList: list = [],
        # defaultConfig of `IBMQJobManager().run`
        # Multiple jobs shared
        summonerName: str = 'exps',
        summonerID: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = AerSimulator(),
        provider: AccountProvider = None,
        # Other arguments of experiment
        # Multiple jobs shared
        saveLocation: Union[Path, str] = Path('./'),
        jobsType: Literal["local", "IBMQ", "AWS_Bracket", "Azure_Q"] = "local",
        # IBMQJobManager() dedicated
        managerRunArgs: dict[str, any] = {
            'max_experiments_per_job': 200,
        },
        filetype: TagMap._availableFileType = 'json',

        isRetrieve: bool = False,
        isRead: bool = False,
    ) -> tuple[list[dict[str, Any]], str]:
        """_summary_

        Args:
            configList (list, optional): _description_. Defaults to [].
            shots (int, optional): _description_. Defaults to 1024.
            backend (Backend, optional): _description_. Defaults to AerSimulator().
            provider (AccountProvider, optional): _description_. Defaults to None.
            managerRunArgs (_type_, optional): _description_. Defaults to { 'max_experiments_per_job': 200, }.
            summonerName (str, optional): _description_. Defaults to 'exps'.
            summonerID (Optional[str], optional): _description_. Defaults to None.
            saveLocation (Union[Path, str], optional): _description_. Defaults to Path('./').
            jobsType (Literal[&quot;local&quot;, &quot;IBMQ&quot;, &quot;AWS_Bracket&quot;, &quot;Azure_Q&quot;], optional): _description_. Defaults to "local".
            isRetrieve (bool, optional): _description_. Defaults to False.
            isRead (bool, optional): _description_. Defaults to False.
            filetype (TagMap._availableFileType, optional): _description_. Defaults to 'json'.

        Returns:
            tuple[list[dict[str, any]], str]: _description_
        """

        if summonerID in self.multimanagers:
            multiJob = self.multimanagers[summonerID]
            return list(multiJob.beforewards.configDict.values()), multiJob.summonerID

        isRead = isRetrieve | isRead

        for config, checker in [
            (managerRunArgs, managerRunConfig),
        ]:
            containChecker(config, checker)

        if isRead:
            multiJob = MultiManager(
                summonerID=None,
                summonerName=summonerName,
                isRead=isRead,

                saveLocation=saveLocation,
            )
        else:
            multiJob = MultiManager(
                summonerID=summonerID,
                summonerName=summonerName,
                shots=shots,
                backend=backend,
                provider=provider,

                saveLocation=saveLocation,
                files={},

                jobsType=jobsType,
                managerRunArgs=managerRunArgs,
                filetype=filetype,
                datetimes={},
            )

        self.multimanagers[multiJob.summonerID] = multiJob

        initedConfigList: list[dict[str, Any]] = []
        for serial, config in enumerate(configList):
            initedConfigList.append({
                **config,
                'shots': shots,
                'backend': backend,
                'provider': provider,

                'expName': multiJob.multicommons.summonerName,
                'saveLocation': multiJob.multicommons.saveLocation,

                'serial': serial,
                'summonerID': multiJob.multicommons.summonerID,
                'summonerName': multiJob.multicommons.summonerName,
            })

        return initedConfigList, multiJob.summonerID

    def multiOutput(
        self,
        # configList
        configList: list = [],

        # defaultConfig of `IBMQJobManager().run`
        # Multiple jobs shared
        summonerName: str = 'exps',
        summonerID: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = AerSimulator(),
        provider: AccountProvider = None,
        # IBMQJobManager() dedicated
        # Other arguments of experiment
        # Multiple jobs shared
        saveLocation: Union[Path, str] = Path('./'),

        filetype: TagMap._availableFileType = 'json',

        defaultMultiAnalysis: list[dict[str, Any]] = [],
        analysisName: str = 'report',
    ) -> Hashable:
        """_summary_

        Args:
            configList (list, optional): _description_. Defaults to [].
            shots (int, optional): _description_. Defaults to 1024.
            backend (Backend, optional): _description_. Defaults to AerSimulator().
            provider (AccountProvider, optional): _description_. Defaults to None.
            summonerName (str, optional): _description_. Defaults to 'exps'.
            summonerID (Optional[str], optional): _description_. Defaults to None.
            saveLocation (Union[Path, str], optional): _description_. Defaults to Path('./').
            filetype (TagMap._availableFileType, optional): _description_. Defaults to 'json'.
            overwrite (bool, optional): _description_. Defaults to False.

        Returns:
            Hashable: _description_
        """

        print(f"| MultiOutput building...")
        initedConfigList, besummonned = self._paramsControlMulti(
            configList=configList,
            shots=shots,
            backend=backend,
            provider=provider,
            managerRunArgs={},
            summonerName=summonerName,
            summonerID=summonerID,
            saveLocation=saveLocation,
            jobsType="local",
            isRetrieve=False,
            isRead=False,
            filetype=filetype,
        )
        currentMultiJob = self.multimanagers[besummonned]
        assert currentMultiJob.summonerID == besummonned

        for config in initedConfigList:
            currentID = self.build(**config)
            currentMultiJob.beforewards.configDict[currentID] = config
            currentMultiJob.beforewards.circuitsNum[currentID] = len(
                self.exps[currentID].beforewards.circuit)
            files = self.exps[currentID].write(mute=True)

            tmpCircSerial = [
                idx for idx in range(len(self.exps[currentID].beforewards.circuit))]
            currentMultiJob.beforewards.pendingPools[currentID] = tmpCircSerial
            currentMultiJob.beforewards.circuitsMap[currentID] = tmpCircSerial
            currentMultiJob.beforewards.jobID.append((currentID, 'local'))

            currentMultiJob.beforewards.tagMapExpsID[
                self.exps[currentID].commons.tags].append(currentID)
            currentMultiJob.beforewards.tagMapFiles[
                self.exps[currentID].commons.tags].append(files)
            currentMultiJob.beforewards.tagMapIndex[
                self.exps[currentID].commons.tags
            ].append(self.exps[currentID].commons.serial)

        filesMulti = currentMultiJob.write()

        print(f"| MultiOutput running...")
        for id_exec, jobtype in currentMultiJob.beforewards.jobID:
            self.output(
                expID=id_exec,
                saveLocation=currentMultiJob.multicommons.saveLocation,
                _exportMute=True,
            )
            currentMultiJob.afterwards.allCounts[id_exec] = self.exps[id_exec].afterwards.counts

        if len(defaultMultiAnalysis) > 0:
            print(f"| MultiOutput analyzing...")
            for analysis in defaultMultiAnalysis:
                self.multiAnalysis(
                    summonerID=currentMultiJob.multicommons.summonerID,
                    analysisName=analysisName,
                    _write=False,
                    **analysis,
                )

        filesMulti = currentMultiJob.write()

        return currentMultiJob.multicommons.summonerID

    def multiAnalysis(
        self,
        summonerID: str,
        analysisName: str = 'report',
        *args,
        specificAnalysisArgs: dict[Hashable, dict[str, Any]] = {},
        _write: bool = True,
        **analysisArgs: Any,
    ) -> str:
        """_summary_

        Args:
            summonerID (str): _description_
            analysisName (str, optional): _description_. Defaults to 'report'.
            specificAnalysisArgs (dict[Hashable, dict[str, Any]], optional): _description_. Defaults to {}.

        Raises:
            ValueError: _description_
            ValueError: _description_
            ValueError: _description_

        Returns:
            str: _description_
        """

        if len(args) > 0:
            raise ValueError(
                "No positional arguments allowed except `summonerID`.")

        if summonerID in self.multimanagers:
            multiJob = self.multimanagers[summonerID]
        else:
            raise ValueError("No such summonerID in multimanagers.")

        if len(multiJob.afterwards.allCounts) == 0:
            raise ValueError("No counts in multimanagers.")

        idx_tagMapQ = len(multiJob.tagMapQuantity)
        name = f"{analysisName}."+f'{idx_tagMapQ+1}'.rjust(self._rjustLen, '0')
        multiJob.tagMapQuantity[name] = TagMap()

        for k in multiJob.afterwards.allCounts.keys():
            if k in specificAnalysisArgs:
                report = self.exps[k].analyze(**specificAnalysisArgs[k])
            else:
                report = self.exps[k].analyze(**analysisArgs)

            self.exps[k].write(mute=True)
            main, tales = report.export()
            multiJob.tagMapQuantity[name][
                self.exps[k].commons.tags].append(main)

        if _write:
            filesMulti = multiJob.write(_onlyQuantity=True)
        else:
            filesMulti = {}

        return multiJob.multicommons.summonerID

    def multiRead(
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
        """_summary_

        Args:
            configList (list, optional): _description_. Defaults to [].
            shots (int, optional): _description_. Defaults to 1024.
            backend (Backend, optional): _description_. Defaults to AerSimulator().
            provider (AccountProvider, optional): _description_. Defaults to None.
            summonerName (str, optional): _description_. Defaults to 'exps'.
            summonerID (Optional[str], optional): _description_. Defaults to None.
            saveLocation (Union[Path, str], optional): _description_. Defaults to Path('./').
            filetype (TagMap._availableFileType, optional): _description_. Defaults to 'json'.
            overwrite (bool, optional): _description_. Defaults to False.

        Returns:
            Hashable: _description_
        """

        initedConfigList, besummonned = self._paramsControlMulti(
            summonerName=summonerName,
            summonerID=summonerID,
            saveLocation=saveLocation,
            isRead=True,
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
        #     currentMultiJob = self.multimanagers[besummonned]
        #     for analysis in defaultMultiAnalysis:
        #         self.multiAnalysis(
        #             summonerID=currentMultiJob.multicommons.summonerID,
        #             analysisName=analysisName,
        #             _write=False,
        #             **analysis,
        #         )

        return besummonned


class QurryV5(QurryV5Prototype):

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
        **otherArgs: any
    ) -> tuple[QurryExperiment.arguments, QurryExperiment.commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

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

    def method(self) -> list[QuantumCircuit]:

        assert self.lastExp is not None
        args: QurryExperiment.arguments = self.lastExp.args
        commons: QurryExperiment.commonparams = self.lastExp.commons
        circuit = self.waves[commons.waveKey]
        numQubits = circuit.num_qubits

        self.lastExp['expName'] = f"{args.expName}-{self.lastExp.commons.waveKey}-x{args.sampling}"
        print(
            f"| Directly call: {self.lastExp.commons.waveKey} with sampling {args.sampling} times.")

        return [circuit for i in range(args.sampling)]

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        expName: str = 'exps',
        sampling: int = 1,
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
            sampling=sampling,
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
