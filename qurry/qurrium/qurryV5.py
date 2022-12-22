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

from ..mori.type import TagMapType
from ..tools import Gajima, ResoureWatch

from .declare.default import (
    transpileConfig,
    runConfig,
    containChecker,
)
from .declare.type import waveContainerType
from .experiment import ExperimentPrototype, QurryExperiment
from .container import WaveContainer, ExperimentContainer

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
        return self.waves.add(wave, key, replace)

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

        self.waves: waveContainerType = WaveContainer()
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

        self.exps = ExperimentContainer()
        """The experiments container."""

        self.multiJob = None
        """The last multiJob be called.
        # TODO: This is a temporary useless until `multimanager` completed.
        Replace the property :prop:`multiNow`. in :cls:`QurryV4`"""

    # state checking
    @property
    def lastID(self) -> Hashable:
        """The last experiment be executed."""
        return self.exps.lastID

    @property
    def lastExp(self) -> Optional[ExperimentPrototype]:
        """The last experiment be executed.
        Replace the property :prop:`now`. in :cls:`QurryV4`"""
        return self.exps.lastExp

    @abstractmethod
    def paramsControl(self) -> tuple[ExperimentPrototype.arguments, ExperimentPrototype.commonparams, dict[str, Any]]:
        """Control the experiment's parameters."""

    def _paramsControlMain(
        self,
        wave: Union[QuantumCircuit, Hashable, None],

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
        
        # TODO: If given a existing expID, then just used its existing parameter except `redo` is given.

        # wave
        if isinstance(wave, QuantumCircuit):
            waveKey = self.add(wave)
        elif wave == None:
            waveKey = self.lastWaveKey
            print(f"| Autofill will use '.lastWave' as key")
        elif isinstance(wave, Hashable):
            if not self.has(wave):
                raise KeyError(f"Wave '{wave}' not found in '.waves'")
            waveKey = wave
        else:
            raise TypeError(
                f"'{wave}' is a '{type(wave)}' instead of 'QuantumCircuit' or 'Hashable'")
        wave = self.waves[waveKey]

        ctrlArgs: ExperimentPrototype.arguments
        commons: ExperimentPrototype.commonparams
        outfields: dict[str, Any]
        ctrlArgs, commons, outfields = self.paramsControl(
            wave=wave,
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
            serial=serial,
            summonerID=summonerID,
            summonerName=summonerName,

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
        assert self.exps[self.lastID] == self.lastExp

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
        **allArgs: any,
    ) -> Hashable:
        """Construct the quantum circuit of experiment.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            Hashable: The ID of the experiment.
        """

        # preparing
        IDNow = self._paramsControlMain(**allArgs)
        assert IDNow == self.lastID
        assert self.lastExp is not None

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments.")

        # circuit
        cirqs = self.method()

        # draw original
        for _w in cirqs:
            self.lastExp.beforewards.figOriginal.append(
                decomposer(_w, self.lastExp.commons.decompose))

        # transpile
        transpiledCirqs: list[QuantumCircuit] = transpile(
            cirqs,
            backend=self.lastExp.commons.backend,
            **self.lastExp.commons.transpileArgs
        )
        for _w in transpiledCirqs:
            self.lastExp.beforewards.figTranspiled.append(
                decomposer(_w, self.lastExp.commons.decompose))
            self.lastExp.beforewards.circuit.append(_w)

        if isinstance(saveLocation, (Path, str)):
            self.lastExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonablize=jsonablize,
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
        self.lastExp['result'] = result

        if isinstance(saveLocation, (Path, str)):
            self.lastExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonablize=jsonablize,
            )

        return IDNow

    @classmethod
    def get_counts(
        cls,
        result: Union[Result, ManagedResults, None],
        resultIdxList: Optional[list[int]] = None,
        num: int = 1,
    ) -> list[dict[str, int]]:
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """
        if resultIdxList == None:
            resultIdxList = [i for i in range(num)]
        else:
            ...

        counts = []
        for i in resultIdxList:
            if result is None:
                counts.append({})
                print("| Failed Job result skip, index:", i)
                continue
            try:
                allMeas = result.get_counts(i)
                counts.append(allMeas)
            except IBMQManagedResultDataNotAvailable as err:
                counts.append({})
                print("| Failed Job result skip, index:", i, err)
                continue
            except IBMQJobManagerJobNotFound as err:
                counts.append({})
                print("| Failed Job result skip, index:", i, err)
                continue

        return counts

    def result(
        self,
        *args,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
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

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments.")

        # afterwards
        counts = self.get_counts(
            result=self.lastExp.afterwards.result,
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

            expsName (str, optional):
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
            )

        return IDNow


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
        wave: Optional[QuantumCircuit] = None,
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

            expsName (str, optional):
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
            wave=wave,
            sampling=sampling,
            **otherArgs,
        )

    def method(self) -> list[QuantumCircuit]:

        assert self.lastExp is not None
        args: QurryExperiment.arguments = self.lastExp.args
        circuit = args.wave
        numQubits = circuit.num_qubits

        self.lastExp['expName'] = f"{args.expName}-{self.lastExp.commons.waveKey}-x{args.sampling}"
        print(
            f"| Directly call: {self.lastExp.commons.waveKey} with sampling {args.sampling} times.")

        return [circuit for i in range(args.sampling)]

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        expsName: str = 'exps',
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

            expsName (str, optional):
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
            expsName=expsName,
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
