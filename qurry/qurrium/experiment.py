from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.providers import Backend
from qiskit_aer import AerSimulator

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, Type, Any
from abc import abstractmethod, abstractclassmethod, abstractproperty
from uuid import uuid4
import gc
import warnings
import os
import glob
import json
import tqdm

from ..hoshi import Hoshi
from ..mori import jsonablize, quickJSON, quickRead, defaultConfig
from ..tools.backend import backendName
from ..exceptions import (
    QurryInvalidInherition,
    QurryExperimentCountsNotCompleted,
    QurryResetSecurityActivated, QurryResetAccomplished,
    QurryProtectContent, QurrySummonerInfoIncompletion)
from .analysis import AnalysisPrototype, QurryAnalysis
from .utils.datetime import currentTime, datetimeDict

commonparamsConfig = defaultConfig(
    name='commonparams',
    default={
        'expID': None,
        'waveKey': None,
        'shots': 1024,
        'backend': AerSimulator(),
        'provider': None,
        'runArgs': {},
        'runBy': 'gate',
        'transpileArgs': {},
        'decompose': None,
        'tags': (),
        'defaultAnalysis': [],
        'saveLocation': Path('./'),
        'filetype': 'json',
        'datetimes': datetimeDict(),
        'serial': None,
        'summonerID': None,
        'summonerName': None,
    })

beforeConfig = defaultConfig(
    name='before',
    default={
        'circuit': [],
        'figOriginal': [],
        'jobID': '',
        'expName': '',
        'sideProduct': {},
    })

afterConfig = defaultConfig(
    name='after',
    default={
        'result': [],
        'counts': [],
    })


class ExperimentPrototype():

    __name__ = 'ExperimentPrototype'
    """Name of the QurryExperiment which could be overwritten."""

    # Experiment Property
    @abstractmethod
    class arguments(NamedTuple):
        """Construct the experiment's parameters for specific options, which is overwritable by the inherition class."""

    class commonparams(NamedTuple):
        """Construct the experiment's parameters for system running."""

        expID: str
        """ID of experiment."""
        waveKey: Hashable
        """Key of the chosen wave."""

        # Qiskit argument of experiment.
        # Multiple jobs shared
        shots: int
        """Number of shots to run the program (default: 1024)."""
        backend: Union[Backend, str]
        """Backend to execute the circuits on, or the backend used."""
        runArgs: dict
        """Arguments of `execute`."""

        # Single job dedicated
        runBy: Literal['gate', 'operator']
        """Run circuits by gate or operator."""
        transpileArgs: dict
        """Arguments of `qiskit.compiler.transpile`."""
        decompose: Optional[int]
        """Decompose the circuit in given times to show the circuit figures in :property:`.before.figOriginal`."""

        tags: tuple
        """Tags of experiment."""

        # Auto-analysis when counts are ready
        defaultAnalysis: list[dict[str, Any]]
        """When counts are ready, the experiment will automatically analyze the counts with the given analysis."""

        # Arguments for exportation
        saveLocation: Union[Path, str]
        """Location of saving experiment. 
        If this experiment is called by :cls:`QurryMultiManager`,
        then `adventure`, `legacy`, `tales`, and `reports` will be exported to their dedicated folders in this location respectively.
        This location is the default location for it's not specific where to save when call :meth:`.write()`, if does, then will be overwriten and update."""
        filename: str
        """The name of file to be exported, it will be decided by the :meth:`.export` when it's called.
        More info in the pydoc of :prop:`files` or :meth:`.export`.
        """
        files: dict[str, Path]
        """The list of file to be exported.
        For the `.write` function actually exports 4 different files
        respecting to `adventure`, `legacy`, `tales`, and `reports` like:
        
        ```python
        files = {
            'folder': './blabla_experiment/',
            
            'args': './blabla_experiment/args/blabla_experiment.id={expID}.args.json',
            'advent': './blabla_experiment/advent/blabla_experiment.id={expID}.advent.json',
            'legacy': './blabla_experiment/legacy/blabla_experiment.id={expID}.legacy.json',
            'tales.dummyx1': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyx1.json',
            'tales.dummyx2': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyx2.json',
            ...
            'tales.dummyxn': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyxn.json',
            'reports': './blabla_experiment/reports/blabla_experiment.id={expID}.reports.json',
            'reports.tales.dummyz1': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyz1.reports.json',
            'reports.tales.dummyz2': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyz2.reports.json',
            ...
            'reports.tales.dummyzm': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyzm.reports.json',
        }
        ```
        which `blabla_experiment` is the example filename.
        If this experiment is called by :cls:`multimanager`, then the it will be named after `summonerName` as known as the name of :cls:`multimanager`.
        
        ```python
        files = {
            'folder': './BLABLA_project/',
            
            'args': './BLABLA_project/args/index={serial}.id={expID}.args.json',
            'advent': './BLABLA_project/advent/index={serial}.id={expID}.advent.json',
            'legacy': './BLABLA_project/legacy/index={serial}.id={expID}.legacy.json',
            'tales.dummyx1': './BLABLA_project/tales/index={serial}.id={expID}.dummyx1.json',
            'tales.dummyx2': './BLABLA_project/tales/index={serial}.id={expID}.dummyx2.json',
            ...
            'tales.dummyxn': './BLABLA_project/tales/index={serial}.id={expID}.dummyxn.json',
            'reports': './BLABLA_project/reports/index={serial}.id={expID}.reports.json',
            'reports.tales.dummyz1': './BLABLA_project/tales/index={serial}.id={expID}.dummyz1.reports.json',
            'reports.tales.dummyz2': './BLABLA_project/tales/index={serial}.id={expID}.dummyz2.reports.json',
            ...
            'reports.tales.dummyzm': './BLABLA_project/tales/index={serial}.id={expID}.dummyzm.reports.json',
        }
        ```
        which `BLBLA_project` is the example :cls:`multimanager` name stored at :prop:`commonparams.summonerName`.
        At this senerio, the `expName` will never apply as filename.
        
        """

        # Arguments for multi-experiment
        serial: Optional[int]
        """Index of experiment in a multiOutput."""
        summonerID: Optional[Hashable]
        """ID of experiment of the multiManager."""
        summonerName: Optional[str]
        """Name of experiment of the multiManager."""

        # header
        datetimes: datetimeDict

    class before(NamedTuple):
        # Experiment Preparation
        circuit: list[QuantumCircuit]
        """Circuits of experiment."""
        figOriginal: list[str]
        """Raw circuit figures which is the circuit before transpile."""

        # Export data
        jobID: str
        """ID of job for pending on real machine (IBMQBackend)."""
        expName: str
        """Name of experiment which is also showed on IBM Quantum Computing quene."""

        # side product
        sideProduct: dict
        """The data of experiment will be independently exported in the folder 'tales'."""

    class after(NamedTuple):
        # Measurement Result
        result: list[Result]
        """Results of experiment."""
        counts: list[dict[str, int]]
        """Counts of experiment."""

    _unexports = ['sideProduct', 'result']
    """Unexports properties.
    """
    
    _deprecated = ['figTranspiled']
    """Deprecated properties.
        - `figTranspiled` is deprecated since v0.6.0.
    """
        
    tqdm_handleable = False
    """Whether the method :meth:`
    e` can handle the processing bar from :module:`tqdm`."""

    # Analysis Property
    @classmethod
    def filter(cls, *args,
               **kwargs) -> tuple[arguments, commonparams, dict[str, Any]]:
        """Filter the arguments of experiment.

        Raises:
            ValueError: When input arguments are not positional arguments.

        Returns:
            tuple[argsCore, dict[str, Any]]: argsCore, outfields for other unused arguments.
        """
        if len(args) > 0:
            raise ValueError(
                "args filter can't be initialized with positional arguments.")
        infields = {}
        commonsinput = {}
        outfields = {}
        for k in kwargs:
            if k in cls.arguments._fields:
                infields[k] = kwargs[k]
            elif k in cls.commonparams._fields:
                commonsinput[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        return cls.arguments(**infields), cls.commonparams(
            **commonsinput), outfields

    # analysis
    @classmethod
    @abstractproperty
    def analysis_container(cls) -> Type[AnalysisPrototype]:
        """The container of analysis, it should be overwritten by each construction of new measurement.
        """

    def __init__(self,
                 expID: Hashable,
                 waveKey: Hashable,
                 *args,
                 serial: Optional[int] = None,
                 summonerID: Optional[Hashable] = None,
                 summonerName: Optional[str] = None,
                 **kwargs) -> None:
        """Initialize the experiment."""

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments."
            )
        try:
            hash(expID)
        except TypeError as e:
            expID = None
            warnings.warn(
                "'expID' is not hashable, it will be set to generate automatically."
            )
        finally:
            if expID is None:
                expID = str(uuid4())
            else:
                ...

        for i in ['analysisInput', 'analysisContent']:
            if not hasattr(self.analysis_container, i):
                raise QurryInvalidInherition(
                    f"{self.__name__}._analysis_container() should be inherited from {AnalysisPrototype.__name__}."
                )
        if not 'expName' in self.arguments._fields:
            raise QurryInvalidInherition(
                f"{self.__name__}.arguments should have 'expName'.")
        duplicate_fields = set(self.arguments._fields) & set(
            self.commonparams._fields)
        if len(duplicate_fields) > 0:
            raise QurryInvalidInherition(
                f"{self.__name__}.arguments and {self.__name__}.commonparams should not have same fields: {duplicate_fields}."
            )

        params = {}
        commons = {}
        outfields = {}
        for k in kwargs:
            if k in self.arguments._fields:
                params[k] = kwargs[k]
            elif k in self.commonparams._fields:
                commons[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        # Dealing special arguments
        if 'datetimes' not in commons:
            commons['datetimes'] = datetimeDict({'bulid': currentTime()})
        if 'defaultAnalysis' in commons:
            filted_analysis = []
            for raw_input_analysis in commons['defaultAnalysis']:
                if isinstance(raw_input_analysis, dict):
                    filted_analysis.append(
                        self.analysis_container.input_filter(
                            **raw_input_analysis)[0]._asdict())
                elif isinstance(raw_input_analysis,
                                self.analysis_container.analysisInput):
                    filted_analysis.append(raw_input_analysis._asdict())
                else:
                    warnings.warn(
                        f"Analysis input {raw_input_analysis} is not a 'dict' or '.analysis_container.analysisInput', it will be ignored."
                    )
            commons['defaultAnalysis'] = filted_analysis
        else:
            commons['defaultAnalysis'] = []
        if 'tags' in commons:
            if isinstance(commons['tags'], list):
                commons['tags'] = tuple(commons['tags'])

        self.args: self.arguments = self.arguments(**params)
        self.commons = self.commonparams(expID=expID,
                                         serial=serial,
                                         waveKey=waveKey,
                                         summonerID=summonerID,
                                         summonerName=summonerName,
                                         **commons)
        self.outfields: dict[str, Any] = outfields
        self.beforewards = self.before(
            circuit=[],
            figOriginal=[],
            jobID='',
            expName=self.args.expName,
            sideProduct={},
        )
        self.afterwards = self.after(
            result=[],
            counts=[],
        )
        self.reports: dict[str, ExperimentPrototype.analysis_container] = {}

        _summon_check = {
            'serial': self.commons.serial,
            'summonerID': self.commons.summonerID,
            'summonerName': self.commons.summonerName
        }
        _summon_detect = any((not v is None) for v in _summon_check.values())
        _summon_fulfill = all((not v is None) for v in _summon_check.values())
        if _summon_detect:
            if _summon_fulfill:
                ...
            else:
                summon_msg = Hoshi(ljust_description_len=20)
                summon_msg.newline(('divider', ))
                summon_msg.newline(('h3', 'Summoner Info Incompletion'))
                summon_msg.newline(
                    ('itemize', 'Summoner info detect.', _summon_detect))
                summon_msg.newline(
                    ('itemize', 'Summoner info fulfilled.', _summon_fulfill))
                for k, v in _summon_check.items():
                    summon_msg.newline(('itemize', k, str(v),
                                        f'fulfilled: {not v is None}', 2))
                warnings.warn(
                    "Summoner data is not completed, it will export in single experiment mode.",
                    category=QurrySummonerInfoIncompletion)
                summon_msg.print()

        self.after_lock = False
        """Protect the :cls:`afterward` content to be overwritten. When setitem is called and completed, it will be setted as `False` automatically."""
        self.mute_auto_lock = False
        """Whether mute the auto-lock message."""

    def reset_counts(self, summonerID: Hashable) -> None:
        """Reset the counts of the experiment."""
        if summonerID == self.commons.summonerID:
            self.afterwards = self.afterwards._replace(counts=[])
            gc.collect()
        else:
            warnings.warn(
                "The summonerID is not matched, the counts will not be reset, it can only be activated by multimanager.",
                category=QurryResetSecurityActivated)

    def unlock_afterward(self, mute_auto_lock: bool = False):
        """Unlock the :cls:`afterward` content to be overwritten.

        Args:
            mute_auto_lock (bool, optional): 
                Mute anto-locked message for the unlock of this time. Defaults to False.
        """
        self.after_lock = True
        self.mute_auto_lock = mute_auto_lock

    def __setitem__(self, key, value) -> None:
        if key in self.beforewards._fields:
            self.beforewards = self.beforewards._replace(**{key: value})

        elif key in self.afterwards._fields:
            if self.after_lock and isinstance(self.after_lock, bool):
                self.afterwards = self.afterwards._replace(**{key: value})
            else:
                raise QurryProtectContent(
                    f"Can't set value to :cls:`afterward` field {key} because it's locked, use `.unlock_afterward()` to unlock before setting item ."
                )

        elif key in self._deprecated:
            ...
            # print(f"| Warning: {key} is deprecated.")

        else:
            raise ValueError(
                f"{key} is not a valid field of '{self.before.__name__}' and '{self.after.__name__}'."
            )

        gc.collect()
        if self.after_lock != False:
            self.after_lock = False
            if not self.mute_auto_lock:
                print(
                    f"after_lock is locked automatically now, you can unlock by using `.unlock_afterward()` to set value to :cls:`afterward`."
                )
            self.mute_auto_lock = False

    def __getitem__(self, key) -> Any:
        if key in self.beforewards._fields:
            return getattr(self.beforewards, key)
        elif key in self.afterwards._fields:
            return getattr(self.afterwards, key)
        elif key in self._deprecated:
            ...
            # print(
            #     f"| Warning: {key} is deprecated, it will be removed in the future.")
        else:
            raise ValueError(
                f"{key} is not a valid field of '{self.before.__name__}' and '{self.after.__name__}'."
            )

    # analysis
    @abstractclassmethod
    def quantities(cls, *args, **kwargs) -> dict[str, Any]:
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.
        """

    @abstractmethod
    def analyze(self, *args, **kwargs) -> AnalysisPrototype:
        """Analyzing the example circuit results in specific method.

        Args:
            allArgs: all arguments will pass to `.quantities`.

        Returns:
            analysis: Analysis of the counts from measurement.
        """

    @abstractmethod
    def analyze(self, pbar: Optional[tqdm.tqdm], *args, **kwargs) -> dict[str, Any]:
        """Analyzing the example circuit results in specific method.

        Args:
            allArgs: all arguments will pass to `.quantities`.

        Returns:
            analysis: Analysis of the counts from measurement.
        """

    def clear_analysis(self,
                       *args,
                       security: bool = False,
                       mute: bool = False) -> None:
        """Reset the measurement and release memory.

        Args:
            args (any): Positional arguments handler to protect other keyword arguments. It's useless, umm...😐 
            security (bool, optional): Security for reset. Defaults to `False`.
            mute (bool, optional): Mute the warning when reset activated. Defaults to `False`.
        """

        if security and isinstance(security, bool):
            self.reports = {}
            gc.collect()
            if not mute:
                warnings.warn(
                    "The measurement has reset and release memory allocating.",
                    category=QurryResetAccomplished)
        else:
            warnings.warn(
                "Reset does not execute to prevent executing accidentally, " +
                "if you are sure to do this, then use '.reset(security=True)'."
                +
                ("Attention: any position arguments are not available on this method."
                 if len(args) > 0 else ""),
                category=QurryResetSecurityActivated)

    # show info
    def __hash__(self) -> int:
        return hash(self.commons.expID)

    @property
    def expID(self) -> property:
        return self.commons.expID

    def __repr__(self) -> str:
        return (f"<{self.__name__} with expID={self.commons.expID}, " +
                f"{self.args.__repr__()}, " + f"{self.commons.__repr__()}, " +
                f"{len(self.outfields)} unused arguments, " +
                f"{len(self.before._fields)} preparing dates, " +
                f"{len(self.after._fields)} experiment result datasets, " +
                f"and {len(self.reports)} analysis>")

    def statesheet(
        self,
        reportExpanded: bool = False,
        hoshi: bool = False,
    ) -> Hoshi:
        info = Hoshi(
            [
                ('h1', f"{self.__name__} with expID={self.commons.expID}"),
            ],
            name='Hoshi' if hoshi else 'QurryExperimentSheet',
        )
        info.newline(('itemize', 'arguments'))
        for k, v in self.args._asdict().items():
            info.newline(('itemize', str(k), str(v), '', 2))

        info.newline(('itemize', 'commonparams'))
        for k, v in self.commons._asdict().items():
            info.newline(('itemize', str(k), str(v), (
                '' if k != 'expID' else
                "This is ID is generated by Qurry which is different from 'jobID' for pending."
            ), 2))

        info.newline(('itemize', 'outfields', len(self.outfields),
                      'Number of unused arguments.', 1))
        for k, v in self.outfields.items():

            info.newline(('itemize', str(k), v, '', 2))

        info.newline(('itemize', 'beforewards'))
        for k, v in self.beforewards._asdict().items():
            if isinstance(v, str):
                info.newline(('itemize', str(k), str(v), '', 2))
            else:
                info.newline(('itemize', str(k), len(v), f'Number of {k}', 2))

        info.newline(('itemize', 'afterwards'))
        for k, v in self.afterwards._asdict().items():
            if k == 'jobID':
                info.newline(('itemize', str(k), str(
                    v
                ), "If it's null meaning this experiment doesn't use online backend like IBMQ.",
                    2))
            elif isinstance(v, str):
                info.newline(('itemize', str(k), str(v), '', 2))
            else:
                info.newline(('itemize', str(k), len(v), f'Number of {k}', 2))

        info.newline(('itemize', 'reports', len(self.reports),
                      'Number of analysis.', 1))
        if reportExpanded:
            for ser, item in self.reports.items():
                info.newline(
                    ('itemize', 'serial',
                     f"k={ser}, serial={item.header.serial}", None, 2))
                info.newline(('txt', item, 3))

        return info

    # Export
    class Export(NamedTuple):
        """Data-stored namedtuple with all experiments data which is jsonable."""

        expID: str = ''
        """ID of experiment, which will be packed into `.args.json`."""
        expName: str = 'exps'
        """Name of the experiment, which will be packed into `.args.json`. 
        If this experiment is called by multimanager, then this name will never apply as filename."""
        # Arguments for multi-experiment
        serial: Optional[int] = None
        """Index of experiment in a multiOutput, which will be packed into `.args.json`."""
        summonerID: Optional[Hashable] = None
        """ID of experiment of the multiManager, which will be packed into `.args.json`."""
        summonerName: Optional[str] = None
        """Name of experiment of the multiManager, which will be packed into `.args.json`."""

        filename: str = ''
        """The name of file to be exported, it will be decided by the :meth:`.export` when it's called.
        More info in the pydoc of :prop:`files` or :meth:`.export`, which will be packed into `.args.json`.
        """
        files: dict[str, str] = {}
        """The list of file to be exported.
        For the `.write` function actually exports 4 different files
        respecting to `adventure`, `legacy`, `tales`, and `reports` like:
        
        ```python
        files = {
            'folder': './blabla_experiment/',
            'qurryinfo': './blabla_experiment/qurryinfo.json',
            
            'args': './blabla_experiment/args/blabla_experiment.id={expID}.args.json',
            'advent': './blabla_experiment/advent/blabla_experiment.id={expID}.advent.json',
            'legacy': './blabla_experiment/legacy/blabla_experiment.id={expID}.legacy.json',
            'tales.dummyx1': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyx1.json',
            'tales.dummyx2': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyx2.json',
            ...
            'tales.dummyxn': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyxn.json',
            'reports': './blabla_experiment/reports/blabla_experiment.id={expID}.reports.json',
            'reports.tales.dummyz1': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyz1.reports.json',
            'reports.tales.dummyz2': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyz2.reports.json',
            ...
            'reports.tales.dummyzm': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyzm.reports.json',
        }
        ```
        which `blabla_experiment` is the example filename.
        If this experiment is called by :cls:`multimanager`, then the it will be named after `summonerName` as known as the name of :cls:`multimanager`.
        
        ```python
        files = {
            'folder': './BLABLA_project/',
            'qurryinfo': './BLABLA_project/qurryinfo.json',
            
            'args': './BLABLA_project/args/index={serial}.id={expID}.args.json',
            'advent': './BLABLA_project/advent/index={serial}.id={expID}.advent.json',
            'legacy': './BLABLA_project/legacy/index={serial}.id={expID}.legacy.json',
            'tales.dummyx1': './BLABLA_project/tales/index={serial}.id={expID}.dummyx1.json',
            'tales.dummyx2': './BLABLA_project/tales/index={serial}.id={expID}.dummyx2.json',
            ...
            'tales.dummyxn': './BLABLA_project/tales/index={serial}.id={expID}.dummyxn.json',
            'reports': './BLABLA_project/reports/index={serial}.id={expID}.reports.json',
            'reports.tales.dummyz1': './BLABLA_project/tales/index={serial}.id={expID}.dummyz1.reports.json',
            'reports.tales.dummyz2': './BLABLA_project/tales/index={serial}.id={expID}.dummyz2.reports.json',
            ...
            'reports.tales.dummyzm': './BLABLA_project/tales/index={serial}.id={expID}.dummyzm.reports.json',
        }
        ```
        which `BLBLA_project` is the example :cls:`multimanager` name stored at :prop:`commonparams.summonerName`.
        At this senerio, the `expName` will never apply as filename.
        
        """

        args: dict[str, Any] = {}
        """Construct the experiment's parameters, which will be packed into `.args.json`."""
        commons: dict[str, Any] = {}
        """Construct the experiment's common parameters, which will be packed into `.args.json`."""
        outfields: dict[str, Any] = {}
        """Recording the data of other unused arguments, which will be packed into `.args.json`."""

        adventures: dict[str, Any] = {}
        """Recording the data of 'beforeward', which will be packed into `.advent.json`. 
        ~A Great Adventure begins~"""
        legacy: dict[str, Any] = {}
        """Recording the data of 'afterward', which will be packed into `.legacy.json`. 
        ~The Legacy remains from the achievement of ancestors~"""
        tales: dict[str, Any] = {}
        """Recording the data of 'sideProduct' in 'afterward' and 'beforewards' for API, which will be packed into `.*.tales.json`. 
        ~Tales of braves circulate~"""

        reports: dict[str, dict[str, Any]] = {}
        """Recording the data of 'reports', which will be packed into `.reports.json`. 
        ~The guild concludes the results.~"""
        tales_reports: dict[str, dict[str, Any]] = {}
        """Recording the data of 'sideProduct' in 'reports' for API, which will be packed into `.*.reprts.json`. 
        ~Tales of braves circulate~"""

    _rjustLen = 3
    """The length of the string to be right-justified for serial number when :prop:`expName` is duplicated."""
    _required_folder = ['args', 'advent', 'legacy', 'tales', 'reports']
    """Folder for saving exported files."""

    def export(self) -> Export:
        """Export the data of experiment.

        For the `.write` function actually exports 4 different files
        respecting to `adventure`, `legacy`, `tales`, and `reports` like:

        ```python
        files = {
            'folder': './blabla_experiment/',
            'qurryinfo': './blabla_experiment/qurryinfo.json',

            'args': './blabla_experiment/args/blabla_experiment.id={expID}.args.json',
            'advent': './blabla_experiment/advent/blabla_experiment.id={expID}.advent.json',
            'legacy': './blabla_experiment/legacy/blabla_experiment.id={expID}.legacy.json',
            'tales.dummyx1': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyx1.json',
            'tales.dummyx2': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyx2.json',
            ...
            'tales.dummyxn': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyxn.json',
            'reports': ./blabla_experiment/reports/blabla_experiment.id={expID}.reports.json,
            'reports.tales.dummyz1': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyz1.reports.json',
            'reports.tales.dummyz2': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyz2.reports.json',
            ...
            'reports.tales.dummyzm': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyzm.reports.json',
        }
        ```
        which `blabla_experiment` is the example filename.
        If this experiment is called by :cls:`multimanager`, then the it will be named after `summonerName` as known as the name of :cls:`multimanager`.

        ```python
        files = {
            'folder': './BLABLA_project/',
            'qurryinfo': './BLABLA_project/qurryinfo.json',

            'args': './BLABLA_project/args/index={serial}.id={expID}.args.json',
            'advent': './BLABLA_project/advent/index={serial}.id={expID}.advent.json',
            'legacy': './BLABLA_project/legacy/index={serial}.id={expID}.legacy.json',
            'tales.dummyx1': './BLABLA_project/tales/index={serial}.id={expID}.dummyx1.json',
            'tales.dummyx2': './BLABLA_project/tales/index={serial}.id={expID}.dummyx2.json',
            ...
            'tales.dummyxn': './BLABLA_project/tales/index={serial}.id={expID}.dummyxn.json',
            'reports': ./BLABLA_project/reports/index={serial}.id={expID}.reports.json,
            'reports.tales.dummyz1': './BLABLA_project/tales/index={serial}.id={expID}.dummyz1.reports.json',
            'reports.tales.dummyz2': './BLABLA_project/tales/index={serial}.id={expID}.dummyz2.reports.json',
            ...
            'reports.tales.dummyzm': './BLABLA_project/tales/index={serial}.id={expID}.dummyzm.reports.json',
        }
        ```
        which `BLBLA_project` is the example :cls:`multimanager` name stored at :prop:`commonparams.summonerName`.
        At this senerio, the `expName` will never apply as filename.

        Returns:
            Export: A namedtuple containing the data of experiment which can be more easily to export as json file.
        """

        # independent values
        expID = self.commons.expID
        expName = self.beforewards.expName
        # multimanager values
        serial = self.commons.serial
        summonerID = self.commons.summonerID
        summonerName = self.commons.summonerName
        _summon = all(
            (not v is None) for v in [serial, summonerID, summonerID])
        # args, commons, outfields

        args: dict[str, Any] = jsonablize(self.args._asdict())
        commons: dict[str, Any] = jsonablize(self.commons._asdict())
        commons['backend'] = (
            self.commons.backend if isinstance(self.commons.backend, str) 
            else backendName(self.commons.backend))
        
        outfields = jsonablize(self.outfields)
        # adventures, legacy, tales
        tales = {}
        adventures_wunex = self.beforewards._asdict()  # With UNEXported data
        adventures = {}
        for k, v in adventures_wunex.items():
            if k == 'sideProduct':
                tales = {**tales, **v}
            elif k in self._unexports:
                ...
            else:
                adventures[k] = jsonablize(v)

        legacy_wunex = self.afterwards._asdict()
        """Legacy with unexported data."""

        legacy = {}
        for k, v in legacy_wunex.items():
            if k == 'sideProduct':
                tales = {**tales, **v}
            elif k in self._unexports:
                ...
            else:
                legacy[k] = jsonablize(v)

        tales = jsonablize(tales)

        # reports
        reports: dict[str, dict[str, Any]] = {}
        """reports formats.
        ```
        reports = {
            1: { ...quantities, 'input': { ... }, 'header': { ... }, },
            2: { ...quantities, 'input': { ... }, 'header': { ... }, },
            ...
            {serial}: { ...quantities, 'input': { ... }, 'header': { ... }, },
        }
        ```
        """
        tales_reports: dict[str, dict[str, dict[str, Any]]] = {}
        """tales_reports formats.
        ```
        tales_reports = {
            'dummyz1': { 
                1: { ... },
                2: { ... },
                ...
                {serial}: { ... },
            }, 
            'dummyz2': { 
                1: { ... },
                2: { ... },
                ...
                {serial}: { ... },
            }, 
            ...
            'dummyz': { 
                1: { ... },
                2: { ... },
                ...
                {serial}: { ... },
            }, 
        }
        ```
        """
        for k, al in self.reports.items():
            report_main, report_tales = al.export()
            reports[k] = report_main
            for tk, tv in report_tales.items():
                if tk not in tales_reports:
                    tales_reports[tk] = {}
                tales_reports[tk][k] = tv

        # filename
        filename = ''
        folder = ''
        files = {}
        if _summon:
            folder += f'./{summonerName}/'
            filename += f"index={serial}.id={expID}"
        else:
            repeat_times = 1
            tmp = folder + \
                f"./{expName}.{str(repeat_times).rjust(self._rjustLen, '0')}/"
            while os.path.exists(tmp):
                repeat_times += 1
                tmp = folder + \
                    f"./{expName}.{str(repeat_times).rjust(self._rjustLen, '0')}/"
            folder = tmp
            filename += f"{expName}.{str(repeat_times).rjust(self._rjustLen, '0')}.id={expID}"

        self.commons = self.commons._replace(filename=filename)
        files['folder'] = folder
        files['qurryinfo'] = folder + 'qurryinfo.json'
        files['args'] = folder + f'args/{filename}.args.json'
        files['advent'] = folder + f'advent/{filename}.advent.json'
        files['legacy'] = folder + f'legacy/{filename}.legacy.json'
        for k in tales.keys():
            files[f'tales.{k}'] = folder + f'tales/{filename}.{k}.json'
        files['reports'] = folder + f'reports/{filename}.reports.json'
        for k in tales_reports.keys():
            files[f'reports.tales.{k}'] = folder + \
                f'tales/{filename}.{k}.reports.json'

        files = {k: str(Path(v)) for k, v in files.items()}

        return self.Export(expID=expID,
                           expName=expName,
                           serial=serial,
                           summonerID=summonerID,
                           summonerName=summonerName,
                           filename=filename,
                           files=files,
                           args=args,
                           commons=commons,
                           outfields=outfields,
                           adventures=adventures,
                           legacy=legacy,
                           tales=tales,
                           reports=reports,
                           tales_reports=tales_reports)

    def write(
        self,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
        # zip: bool = False,
        mute: bool = False,
    ) -> dict[str, str]:
        """Export the experiment data, if there is a previous export, then will overwrite.
        Replacement of :func:`QurryV4().writeLegacy`

        - example of filename:

        ```python
        files = {
            'folder': './blabla_experiment/',
            'qurrtinfo': './blabla_experiment/qurrtinfo',

            'args': './blabla_experiment/args/blabla_experiment.id={expID}.args.json',
            'advent': './blabla_experiment/advent/blabla_experiment.id={expID}.advent.json',
            'legacy': './blabla_experiment/legacy/blabla_experiment.id={expID}.legacy.json',
            'tales.dummyx1': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyx1.json',
            'tales.dummyx2': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyx2.json',
            ...
            'tales.dummyxn': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyxn.json',
            'reports': ./blabla_experiment/reports/blabla_experiment.id={expID}.reports.json,
            'reports.tales.dummyz1': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyz1.reports.json',
            'reports.tales.dummyz2': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyz2.reports.json',
            ...
            'reports.tales.dummyzm': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyzm.reports.json',
        }
        ```

        Args:
            saveLocation (Optional[Union[Path, str]], optional):
                Where to save the export content as `json` file.
                If `saveLocation == None`, then use the value in `self.commons` to be exported, if it's None too, then raise error.
                Defaults to `None`.

            mode (str): 
                Mode for :func:`open` function, for :func:`mori.quickJSON`. Defaults to 'w+'.
            indent (int, optional): 
                Indent length for json, for :func:`mori.quickJSON`. Defaults to 2.
            encoding (str, optional): 
                Encoding method, for :func:`mori.quickJSON`. Defaults to 'utf-8'.
            jsonablize (bool, optional): 
                Whether to transpile all object to jsonable via :func:`mori.jsonablize`, for :func:`mori.quickJSON`. Defaults to False.

        Returns:
            dict[any]: the export content.
        """

        if isinstance(saveLocation, Path):
            ...
        elif isinstance(saveLocation, str):
            saveLocation = Path(saveLocation)
        elif saveLocation is None:
            saveLocation = Path(self.commons.saveLocation)
            if self.commons.saveLocation is None:
                raise ValueError(
                    "saveLocation is None, please provide a valid saveLocation"
                )
        else:
            raise TypeError(
                f"saveLocation must be Path or str, not {type(saveLocation)}")

        if self.commons.saveLocation != saveLocation:
            self.commons = self.commons._replace(saveLocation=saveLocation)

        export_material = self.export()
        export_set = {}
        # qurryinfo ..........  # file location, dedicated hash
        qurryinfo = {
            export_material.expID: export_material.files,
        }
        # args ...............  # arguments, commonparams, outfields, files
        export_set['args'] = {
            # 'expID': export_material.expID,
            # 'expName': export_material.expName,
            # 'serial': export_material.serial,
            # 'summonerID': export_material.summonerID,
            # 'summonerName': export_material.summonerName,
            # 'filename': export_material.filename,
            'arguments': export_material.args,
            'commonparams': export_material.commons,
            'outfields': export_material.outfields,
            'files': export_material.files,
        }
        # advent .............  # adventures
        export_set['advent'] = {
            'files': export_material.files,
            'adventures': export_material.adventures
        }
        # legacy .............  # legacy
        export_set['legacy'] = {
            'files': export_material.files,
            'legacy': export_material.legacy
        }
        # tales ..............  # tales
        for tk, tv in export_material.tales.items():
            if isinstance(tv, (dict, list, tuple)):
                export_set[f'tales.{tk}'] = tv
            else:
                export_set[f'tales.{tk}'] = [tv]
            if f'tales.{tk}' not in export_material.files:
                warnings.warn(
                    f"tales.{tk} is not in export_names, it's not exported.")
        # reports ............  # reports
        export_set['reports'] = {
            'files': export_material.files,
            'reports': export_material.reports
        }
        # reports.tales ......  # tales_reports
        for tk, tv in export_material.tales_reports.items():
            if isinstance(tv, (dict, list, tuple)):
                export_set[f'reports.tales.{tk}'] = tv
            else:
                export_set[f'reports.tales.{tk}'] = [tv]
            if f'reports.tales.{tk}' not in export_material.files:
                warnings.warn(
                    f"reports.tales.{tk} is not in export_names, it's not exported."
                )
        # Exportation
        folder = saveLocation / Path(export_material.files['folder'])
        if not os.path.exists(folder):
            os.mkdir(folder)
        for k in self._required_folder:
            if not os.path.exists(folder / k):
                os.mkdir(folder / k)

        for k, v in export_material.files.items():
            self.commons.files[k] = v

        for filekey, content in list(
                export_set.items()) + [('qurryinfo', qurryinfo)]:
            # Exportation of qurryinfo
            if filekey == 'qurryinfo':
                if os.path.exists(saveLocation /
                                  export_material.files['qurryinfo']):
                    with open(saveLocation /
                              export_material.files['qurryinfo'],
                              'r',
                              encoding='utf-8') as f:
                        qurryinfoFound: dict[str, dict[str,
                                                       str]] = json.load(f)
                        content = {**qurryinfoFound, **content}

            quickJSON(
                content=content,
                filename=str(saveLocation / export_material.files[filekey]),
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonablize=jsonablize,
                mute=mute,
            )

        return export_material.files

    @classmethod
    def _read_core(
        cls,
        expID: str,
        fileIndex: dict[str, str],
        saveLocation: Union[Path, str] = Path('./'),
        encoding: str = 'utf-8',
    ) -> 'ExperimentPrototype':
        """Core of read function.

        Args:
            expID (str): The id of the experiment to be read.
            fileIndex (dict[str, str]): The index of the experiment to be read.
            saveLocation (Union[Path, str]): The location of the experiment to be read.
            encoding (str): Encoding method, for :func:`mori.quickJSON`.

        Raises:
            ValueError: 'saveLocation' needs to be the type of 'str' or 'Path'.
            FileNotFoundError: When `saveLocation` is not available.

        Returns:
            QurryExperiment: The experiment to be read.
        """

        if isinstance(saveLocation, (Path, str)):
            saveLocation = Path(saveLocation)
        else:
            raise ValueError(
                "'saveLocation' needs to be the type of 'str' or 'Path'.")
        if not os.path.exists(saveLocation):
            raise FileNotFoundError(
                f"'saveLocation' does not exist, '{saveLocation}'.")

        export_material_set = {}
        export_set = {}
        for filekey, filename in fileIndex.items():
            filekeydiv = filekey.split('.')

            if filekey == 'args':
                with open(saveLocation / filename, 'r',
                          encoding=encoding) as f:
                    export_set['args'] = json.load(f)
                for ak in ['arguments', 'commonparams', 'outfields']:
                    export_material_set[ak]: dict[str,
                                                  Any] = export_set['args'][ak]

            elif filekey == 'advent':
                with open(saveLocation / filename, 'r',
                          encoding=encoding) as f:
                    export_set['advent'] = json.load(f)
                export_material_set['adventures']: dict[
                    str, Any] = export_set['advent']['adventures']

            elif filekey == 'legacy':
                with open(saveLocation / filename, 'r',
                          encoding=encoding) as f:
                    export_set['legacy'] = json.load(f)
                export_material_set['legacy']: dict[
                    str, Any] = export_set['legacy']['legacy']

            elif filekey == 'reports':
                with open(saveLocation / filename, 'r',
                          encoding=encoding) as f:
                    export_set['reports'] = json.load(f)
                export_material_set['reports']: dict[
                    str, Any] = export_set['reports']['reports']

            elif filekeydiv[0] == 'tales':
                with open(saveLocation / filename, 'r',
                          encoding=encoding) as f:
                    export_set[filekey] = json.load(f)
                if not 'tales' in export_material_set:
                    export_material_set['tales'] = {}
                export_material_set['tales'][
                    filekeydiv[1]] = export_set[filekey]

            elif filekeydiv[0] == 'reports' and filekeydiv[1] == 'tales':
                with open(saveLocation / filename, 'r',
                          encoding=encoding) as f:
                    export_set[filekey] = json.load(f)
                if not 'tales_report' in export_material_set:
                    export_material_set['tales_report']: dict[str,
                                                              dict[str,
                                                                   Any]] = {}
                export_material_set['tales_report'][
                    filekeydiv[2]] = export_set[filekey]
            elif filekey == 'qurryinfo' or filekey == 'folder':
                pass
            else:
                warnings.warn(
                    f"Unknown filekey '{filekey}' found in the index of '{expID}'."
                )

        # Construct the experiment
        ## arguments, commonparams, outfields
        instance = cls(**export_material_set['commonparams'],
                       **export_material_set['arguments'],
                       **export_material_set['outfields'])
        # beforewards
        # Hint: It should avoid to use ._replace
        for k, v in export_material_set['adventures'].items():
            if isinstance(instance[k], list):
                for vv in v:
                    instance[k].append(vv)
            else:
                instance[k] = v
        if 'tales' in export_material_set:
            for k, v in export_material_set['tales'].items():
                instance['sideProduct'][k] = v
        # afterwards
        for k, v in export_material_set['legacy'].items():
            # instance.unlock_afterward(mute_auto_lock=True)
            for vv in v:
                instance[k].append(vv)
        # reports
        if 'reports' in export_material_set:
            mains = {k: v for k, v in export_material_set['reports'].items()}
            sides = {k: {} for k in export_material_set['reports']}
        else:
            mains = {}
            sides = {}
        if 'tales_report' in export_material_set:
            for tk, tv in export_material_set['tales_report'].items():
                for k, v in tv.items():
                    if k not in sides:
                        sides[k] = {}
                        mains[k] = {}
                    sides[k][tk] = v

        # print(mains, sides, 'mains, sides')
        for k, v in mains.items():
            instance.reports[k] = cls.analysis_container.read(v, sides[k])

        return instance

    @classmethod
    def read(
        cls,
        name: Union[Path, str],
        saveLocation: Union[Path, str] = Path('./'),
        encoding: str = 'utf-8',
    ) -> list['ExperimentPrototype']:
        """Read the experiment from file.
        Replacement of :func:`QurryV4().readLegacy`

        Args:
            name_or_id (Union[Path, str]): 
                The name or id of the experiment to be read.
            saveLocation (Union[Path, str], optional):
                The location of the experiment to be read.
                Defaults to Path('./').
            indent (int, optional): 
                Indent length for json, for :func:`mori.quickJSON`. Defaults to 2.
            encoding (str, optional): 
                Encoding method, for :func:`mori.quickJSON`. Defaults to 'utf-8'.

        Raises:
            ValueError: 'saveLocation' needs to be the type of 'str' or 'Path'.
            FileNotFoundError: When `saveLocation` is not available.

        """

        if isinstance(saveLocation, (Path, str)):
            saveLocation = Path(saveLocation)
        else:
            raise ValueError(
                "'saveLocation' needs to be the type of 'str' or 'Path'.")
        if not os.path.exists(saveLocation):
            raise FileNotFoundError(
                f"'saveLocation' does not exist, '{saveLocation}'.")

        exportLocation = saveLocation / name
        if not os.path.exists(exportLocation):
            raise FileNotFoundError(
                f"'ExportLoaction' does not exist, '{exportLocation}'.")

        qurryinfo = {}
        qurryinfoLocation = exportLocation / 'qurryinfo.json'
        if not os.path.exists(qurryinfoLocation):
            raise FileNotFoundError(
                f"'qurryinfo.json' does not exist at '{saveLocation}'. It's required for loading all experiment data."
            )

        with open(qurryinfoLocation, 'r', encoding=encoding) as f:
            qurryinfoFound: dict[str, dict[str, str]] = json.load(f)
            qurryinfo = {**qurryinfoFound, **qurryinfo}

        queue = []
        for expID, fileIndex in qurryinfo.items():
            queue.append(
                cls._read_core(expID, fileIndex, saveLocation, encoding))

        return queue

    @classmethod
    def readV4(
        cls,
        name: Union[Path, str],
        summonerID: Optional[Hashable] = None,
        saveLocation: Union[Path, str] = Path('./'),
        encoding: str = 'utf-8',
    ) -> list['ExperimentPrototype']:
        """Read the experiment from file made by QurryV4, it's only available for the export of multiOutput.
        Replacement of :func:`QurryV4().readLegacy`

        Args:
            name_or_id (Union[Path, str]): 
                The name or id of the experiment to be read.
            saveLocation (Union[Path, str], optional):
                The location of the experiment to be read.
                Defaults to Path('./').
            indent (int, optional): 
                Indent length for json, for :func:`mori.quickJSON`. Defaults to 2.
            encoding (str, optional): 
                Encoding method, for :func:`mori.quickJSON`. Defaults to 'utf-8'.

        Raises:
            ValueError: 'saveLocation' needs to be the type of 'str' or 'Path'.
            FileNotFoundError: When `saveLocation` is not available.

        """

        if isinstance(saveLocation, (Path, str)):
            saveLocation = Path(saveLocation)
        else:
            raise ValueError(
                "'saveLocation' needs to be the type of 'str' or 'Path'.")
        if not os.path.exists(saveLocation):
            raise FileNotFoundError(
                f"'saveLocation' does not exist, '{saveLocation}'.")

        exportLocation = saveLocation / name
        if not os.path.exists(exportLocation):
            raise FileNotFoundError(
                f"'exportLoaction' does not exist, '{exportLocation}'.")

        configDict = quickRead(
            filename=f'{name}.configDict.json',
            saveLocation=exportLocation,
        )
        qurryinfoV4: dict[str, dict[str, str]] = {}
        for k, v in configDict.items():
            exportLocTmp = Path(v["exportLocation"]).name
            qurryinfoV4[k] = {
                'folder': exportLocTmp,
                'legacy':
                str(Path(exportLocTmp) / 'legacy' / f"*expId={k}*.json"),
                'tales':
                str(Path(exportLocTmp) / 'tales' / f"*expId={k}*.json"),
            }

        queue = []
        for expID, fileIndex in qurryinfoV4.items():
            queue.append(
                cls._readV4_core(expID, fileIndex, name, summonerID,
                                 saveLocation, encoding))

        return queue

    @classmethod
    def _readV4_core(
        cls,
        expID: str,
        fileIndex: dict[str, str],
        summonerName: str,
        summonerID: Optional[Hashable] = None,
        saveLocation: Union[Path, str] = Path('./'),
        encoding: str = 'utf-8',
    ) -> 'ExperimentPrototype':
        ...

        if isinstance(saveLocation, (Path, str)):
            saveLocation = Path(saveLocation)
        else:
            raise ValueError(
                "'saveLocation' needs to be the type of 'str' or 'Path'.")
        if not os.path.exists(saveLocation):
            raise FileNotFoundError(
                f"'saveLocation' does not exist, '{saveLocation}'.")

        legacyRead = {}
        lsfolder = glob.glob(str(saveLocation / fileIndex['legacy']))
        if len(lsfolder) == 0:
            raise FileNotFoundError(
                f"The file 'expID={expID}' not found at the legacy folder of '{fileIndex['legacy']}'."
            )
        for p in lsfolder:
            with open(p, 'r', encoding=encoding) as Legacy:
                legacyRead = json.load(Legacy)

        talesRead = {}
        lsfoldertales = glob.glob(str(saveLocation / fileIndex['tales']))
        for p in lsfoldertales:
            tmp = Path(p)
            with open(p, 'r', encoding='utf-8') as Tales:
                talesRead[tmp.suffixes[-2][1:]] = json.load(Tales)

        infields = {}
        commonsinput = {
            "files": {
                'v4': fileIndex
            },
            'summonerName': summonerName,
            'summonerID': summonerID,
        }
        beforewards = {}
        afterwards = {}
        outfields = {'oldTales': talesRead}

        for k in legacyRead:
            if k in cls.arguments._fields:
                infields[k] = legacyRead[k]
            elif k in cls.commonparams._fields:
                commonsinput[k] = legacyRead[k]
            elif k in cls.before._fields:
                beforewards[k] = legacyRead[k]
            elif k in cls.after._fields:
                afterwards[k] = legacyRead[k]

            elif k == 'figRaw':
                beforewards['figOriginal'] = legacyRead[k]
            elif k == 'dateCreate':
                commonsinput['datetimes'] = datetimeDict({
                    'build':
                    legacyRead[k],
                    'transformToV5':
                    currentTime(),
                })
            elif k == 'expIndex':
                commonsinput['serial'] = legacyRead[k]
            elif k == 'tags':
                commonsinput['serial'] = legacyRead[k]

            else:
                outfields[k] = legacyRead[k]

        if "wave" in legacyRead:
            infields['waveKey'] = legacyRead['wave']

        instance = cls(
            **infields,
            **commonsinput,
            **outfields,
        )

        for k, v in beforewards.items():
            instance[k] = v
        for k, v in afterwards.items():
            for vv in v:
                instance[k].append(vv)

        return instance


class DummyExperiment(ExperimentPrototype):
    """The dummy experiment for testing and before first experiment runs."""


class QurryExperiment(ExperimentPrototype):

    __name__ = 'QurryExperiment'

    class arguments(NamedTuple):
        """Construct the experiment's parameters for specific options, which is overwritable by the inherition class."""
        expName: str = 'exps'
        sampling: int = 1

    @classmethod
    @property
    def analysis_container(cls) -> Type[QurryAnalysis]:
        return QurryAnalysis

    @classmethod
    def quantities(cls,
                   shots: int,
                   counts: list[dict[str, int]],
                   ultimate_question: str = '',
                   **otherArgs) -> dict[str, float]:
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            dict[str, float]: Counts, purity, entropy of experiment.
        """

        dummy = -100
        utlmatic_answer = 42,
        return {
            'dummy': dummy,
            'utlmatic_answer': utlmatic_answer,
        }

    def analyze(self,
                ultimate_question: str = '',
                shots: Optional[int] = None,
                **otherArgs):
        """Analysis of the experiment.
        Where should be overwritten by each construction of new measurement.
        """

        if shots is None:
            shots = self.commons.shots
        if len(self.afterwards.counts) < 1:
            raise QurryExperimentCountsNotCompleted(
                "The counts of the experiment is not completed. So there is no data to analyze."
            )

        qs = self.quantities(
            shots=shots,
            counts=self.afterwards.counts,
            ultimate_question=ultimate_question,
        )

        serial = len(self.reports)
        analysis = self.analysis_container(
            ultimate_question=ultimate_question,
            serial=serial,
            **qs,
        )

        self.reports[serial] = analysis
        return analysis
