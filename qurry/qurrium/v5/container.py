from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.providers import Backend
from qiskit.providers.ibmq import AccountProvider
from qiskit_aer import AerSimulator

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, overload
from abc import abstractmethod, abstractstaticmethod, abstractclassmethod
from collections import namedtuple
from uuid import uuid4
from datetime import datetime
import gc
import warnings
import os

from ...hoshi import Hoshi
from ...mori import jsonablize, quickJSON
from ...exceptions import (
    QurryInvalidInherition,
    QurryExperimentCountsNotCompleted,
    QurryResetSecurityActivate,
    QurryResetAccomplished
)
from ..declare.type import Quantity, Counts, waveGetter, waveReturn

# argument


class QurryExperiment:

    __name__ = 'QurryExperiment'
    """Name of the QurryExperiment which could be overwritten."""

    # Experiment Property
    @abstractmethod
    class arguments(NamedTuple):
        """Construct the experiment's parameters for specific options."""

    class arguments(NamedTuple):
        expName: str = 'exps'
        wave: Union[QuantumCircuit, any, None] = None
        sampling: int = 1

    class commonparams(NamedTuple):
        """Construct the experiment's parameters for system running."""

        expID: str
        """ID of experiment."""

        # Qiskit argument of experiment.
        # Multiple jobs shared
        shots: int = 1024
        """Number of shots to run the program (default: 1024)."""
        backend: Backend = AerSimulator()
        """Backend to execute the circuits on."""
        provider: Optional[AccountProvider] = None
        """Provider to execute the backend on."""
        runArgs: dict[str, any] = {}
        """Arguments of `IBMQJobManager().run`."""

        # Single job dedicated
        runBy: Literal['gate', 'operator'] = "gate"
        """Run circuits by gate or operator."""
        transpileArgs: dict[str, any] = {}
        """Arguments of `qiskit.compiler.transpile`."""
        decompose: Optional[int] = 2
        """Decompose the circuit in given times to show the circuit figures in :property:`.before.figOriginal`."""

        tags: tuple[str] = ()
        """Tags of experiment."""

        # Arguments for exportation
        saveLocation: Union[Path, str] = Path('./')
        """Location of saving experiment. 
        If this experiment is called by :cls:`QurryMultiManager`,
        then `adventure`, `legacy`, `tales`, and `reports` will be exported to their dedicated folders in this location respectively.
        This location is the default location for it's not specific where to save when call :meth:`.write()`, if does, then will be overwriten and update."""
        filename: str = ''
        """The name of file to be exported, it will be decided by the :meth:`.export` when it's called.
        More info in the pydoc of :prop:`files` or :meth:`.export`.
        """
        files: dict[str, Path] = {}
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
        serial: Optional[int] = None
        """Index of experiment in a multiOutput."""
        summonerID: Optional[Hashable] = None
        """ID of experiment of the multiManager."""
        summonerName: Optional[str] = None
        """Name of experiment of the multiManager."""

        # header
        datetime: str = ''

    class before(NamedTuple):
        # Experiment Preparation
        circuit: list[QuantumCircuit] = []
        """Circuits of experiment."""
        figOriginal: list[str] = []
        """Raw circuit figures which is the circuit before transpile."""
        figTranspiled: list[str] = []
        """Transpile circuit figures which is the circuit after transpile and the actual one would be executed."""

        # Export data
        jobID: str = ''
        """ID of job for pending on real machine (IBMQBackend)."""
        expName: str = 'exps'
        """Name of experiment which is also showed on IBM Quantum Computing quene."""

        # side product
        sideProduct: dict = {
            'number_between_3_and_4': ['bleem', '(it\'s a joke)']
        }
        """The data of experiment will be independently exported in the folder 'tales'."""

    class after(NamedTuple):
        # Measurement Result
        result: list[Result] = []
        """Results of experiment."""
        counts: list[dict[str, int]] = []
        """Counts of experiment."""

    _unexports = ['sideProduct', 'result']

    # Analysis Property
    class analysisheader(NamedTuple):
        """Construct the experiment's output. 
        A standard `analysis` namedtuple will contain ['serial', 'time', 'summoner', 'run_log', 'sideProduct']
        for more information storing. If it does not contain will raise `QurryInvalidInherition`.
        """

        serial: str
        """Serial Number of analysis."""
        datetime: str
        """Written time of analysis."""
        summoner: Optional[tuple[any, str]] = None
        """Which multiManager makes this analysis. If it's an independent one, then usr the default 'None'."""
        log: dict[str] = {}
        """Other info will be recorded."""

    @abstractmethod
    class analysisinput(NamedTuple):
        """To set the analysis."""

    class analysisinput(NamedTuple):
        utlmatic_answer: int
        """~answer to the ultimate question of life the universe and everything.~"""

    @abstractmethod
    class analysis(NamedTuple):
        ...

    class analysis(NamedTuple):
        sampling: int
        """Number of circuit been repeated."""

        input: NamedTuple = None
        """Input of analyze."""
        header: NamedTuple = None
        """Header of analysis."""
        sideProduct: dict[str, any] = {}
        """The data of experiment will be independently exported in the folder 'tales'."""

        def __repr__(self) -> str:
            return f'<analysis(serial={self.header.serial}, sampling={self.sampling})>'

        def _jsonable(self) -> dict[str, any]:
            """Return a jsonable dict.

            Returns:
                dict[str, any]: jsonable dict of analysis.
            """
            jsonized = jsonablize(self._asdict())
            jsonized['header'] = jsonablize(self.header._asdict())
            jsonized['input'] = jsonablize(self.input._asdict())
            return jsonized

        def _export(self) -> tuple[dict[str, any], dict[str, any]]:
            """Export the analysis as main and side product dict.

            ```python
            main = { ...quantities, 'input': { ... }, 'header': { ... }, }
            side = { 'dummyz1': ..., 'dummyz2': ..., ..., 'dummyzm': ... }

            ```

            Returns:
                tuple[dict[str, any], dict[str, any]]: `main` and `side` product dict.

            """

            jsonized = self._jsonable()
            main = {k: v for k, v in jsonized.items() if k != 'sideProduct'}
            tales = jsonized['sideProduct']
            return main, tales

    _analysisrequried = ['header', 'input', 'sideProduct']

    @classmethod
    def argsFilter(cls, *args, **kwargs) -> tuple[arguments, dict[str, any]]:
        """Filter the arguments of experiment.

        Raises:
            ValueError: When input arguments are not positional arguments.

        Returns:
            tuple[argsCore, dict[str, any]]: argsCore, outfields for other unused arguments.
        """
        if len(args) > 0:
            raise ValueError(
                "args filter can't be initialized with positional arguments.")
        infields = {}
        outfields = {}
        for k in kwargs:
            if k in cls.arguments._fields:
                infields[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        return cls.arguments(**infields), outfields

    @classmethod
    def analysisFilter(cls, *args, **kwargs) -> tuple[analysis, dict[str, any]]:
        if len(args) > 0:
            raise ValueError(
                "analysis filter can't be initialized with positional arguments.")
        infields = {}
        outfields = {}
        for k in kwargs:
            if k in cls.analysis._fields:
                infields[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        return cls.analysis(**infields), outfields

    def __init__(self, expID: Hashable, *args, **kwargs) -> None:

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments.")
        try:
            hash(expID)
        except TypeError as e:
            expID = None
            warnings.warn(
                "'expID' is not hashable, it will be set to generate automatically.")
        finally:
            if expID is None:
                expID = str(uuid4())
            else:
                ...

        for k in self._analysisrequried:
            if k not in self.analysis._fields:
                raise QurryInvalidInherition(
                    f"Overwrittable namedtuple class 'analysis' lost the required key: {k}." +
                    f" The standard analysis namedtuple requires {self._analysisrequried}."
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

        if 'datetime' not in commons:
            commons['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.args = self.arguments(**params)
        self.commons = self.commonparams(expID=expID, **commons)
        self.outfields: dict[str, any] = outfields
        self.beforewards = self.before()
        self.afterwards = self.after()
        self.reports: dict[str, QurryExperiment.analysis] = {}
        
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
                summon_msg.newline(('itemize', 'Summoner info detect.', _summon_detect))
                summon_msg.newline(('itemize', 'Summoner info fulfilled.', _summon_fulfill))
                for k, v in _summon_check.items():
                    summon_msg.newline(('itemize', k, str(v), f'fulfulled: {not v is None}', 2))
                warnings.warn(
                    "Summoner data is not completed, it will export in single experiment mode.")
                summon_msg.print()
        

    def __setitem__(self, key, value) -> None:
        if key in self.before._fields:
            self.beforewards = self.beforewards._replace(**{key: value})
            gc.collect()
        elif key in self.after._fields:
            self.afterwards = self.afterwards._replace(**{key: value})
        else:
            raise ValueError(
                f"{key} is not a valid field of '{self.before.__name__}' and '{self.after.__name__}'.")

    def __getitem__(self, key) -> any:
        if key in self.before._fields:
            return getattr(self.beforewards, key)
        elif key in self.after._fields:
            return getattr(self.afterwards, key)
        else:
            raise ValueError(
                f"{key} is not a valid field of '{self.before.__name__}' and '{self.after.__name__}'.")

    # analysis
    @abstractclassmethod
    def quantities(cls, *args, **kwargs) -> analysis:
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            dict[str, float]: Counts, purity, entropy of experiment.
        """

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[Counts],
        num: int = 1,

        utlmatic_answer: int = 42,

        **otherArgs
    ):

        dummy = -100
        return cls.analysis(
            sampling=num,

            input=cls.analysisinput(
                utlmatic_answer=utlmatic_answer,
            ),
            sideProduct={
                'dummy': dummy,
                **otherArgs,
            },
        )

    def analyze(
        self,
        **allArgs: any,
    ) -> analysis:
        """Analyzing the example circuit results in specific method.

        Args:
            allArgs: all arguments will pass to `.quantities`.

        Returns:
            analysis: Analysis of the counts from measurement.
        """

        if len(self.afterwards.counts) == 0:
            raise QurryExperimentCountsNotCompleted(
                f"No counts in experiment '{self.commons.expID}'.")

        report = self.quantities(
            shots=self.commons.shots,
            counts=self.afterwards.counts,
            num=self.args.sampling,
            **allArgs,
        )

        header = self.analysisheader(
            serial=len(self.reports),
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summoner=(self.commons.summonerID, self.commons.summonerName),
            log={'blabla': 'nothing'}
        )
        report = report._replace(
            sideProduct={**report.sideProduct, 'bla': 'nothing'},
            header=header
        )
        self.reports[header.serial] = report
        return report

    def clear_analysis(self, *args, security: bool = False, mute: bool = False) -> None:
        """Reset the measurement and release memory.

        Args:
            security (bool, optional): Security for reset. Defaults to `False`.
            mute (bool, optional): Mute the warning when reset activated. Defaults to `False`.
        """

        if security and isinstance(security, bool):
            self.reports = []
            gc.collect()
            if not mute:
                warnings.warn(
                    "The measurement has reset and release memory allocating.",
                    category=QurryResetAccomplished)
        else:
            warnings.warn(
                "Reset does not execute to prevent executing accidentally, " +
                "if you are sure to do this, then use '.reset(security=True)'.",
                category=QurryResetSecurityActivate)

    # show info
    def __hash__(self) -> int:
        return hash(self.commons.expID)

    @property
    def expID(self) -> property:
        return self.commons.expID

    def __repr__(self) -> str:
        return (
            f"<{self.__name__} with expID={self.commons.expID}, " +
            f"{self.args.__repr__()}, " +
            f"{self.commons.__repr__()}, " +
            f"{len(self.outfields)} unused arguments, " +
            f"{len(self.before._fields)} preparing dates, " +
            f"{len(self.after._fields)} experiment result datasets, " +
            f"and {len(self.reports)} analysis>")

    def sheet(
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
                '' if k != 'expID' else "This is ID is generated by Qurry which is different from 'jobID' for pending."
            ), 2))

        info.newline(('itemize', 'outfields', len(self.outfields),
                      'Number of unused arguments.', 1))
        for k, v in self.outfields.items():
            info.newline(('itemize', str(k), str(v), '', 2))

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
                    v), "If it's null meaning this experiment doesn't use online backend like IBMQ.", 2))
            elif isinstance(v, str):
                info.newline(('itemize', str(k), str(v), '', 2))
            else:
                info.newline(('itemize', str(k), len(v), f'Number of {k}', 2))

        info.newline(('itemize', 'reports', len(
            self.reports), 'Number of analysis.', 1))
        if reportExpanded:
            for ser, item in self.reports.items():
                info.newline(
                    ('itemize', 'serial', f"k={ser}, serial={item.header.serial}", None, 2))
                info.newline(('txt', item, 3))

        return info

    # Export
    class Export(NamedTuple):
        """Data-stored namedtuple with all experiments data which is jsonable."""

        expID: str = ''
        """ID of experiment."""
        expName: str = 'exps'
        """Name of the experiment. If this experiment is called by multimanager, then this name will never apply as filename."""
        # Arguments for multi-experiment
        serial: Optional[int] = None
        """Index of experiment in a multiOutput."""
        summonerID: Optional[Hashable] = None
        """ID of experiment of the multiManager."""
        summonerName: Optional[str] = None
        """Name of experiment of the multiManager."""

        filename: str = ''
        """The name of file to be exported, it will be decided by the :meth:`.export` when it's called.
        More info in the pydoc of :prop:`files` or :meth:`.export`.
        """
        files: dict[str, Path] = {}
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

        args: dict[str, any] = {}
        """Construct the experiment's parameters."""
        commons: dict[str, any] = {}
        """Construct the experiment's common parameters."""
        outfields: dict[str, any] = {}
        """Recording the data of other unused arguments."""

        adventures: dict[str, any] = {}
        """Recording the data of 'beforeward'. ~A Great Adventure begins~"""
        legacy: dict[str, any] = {}
        """Recording the data of 'afterward'. ~The Legacy remains from the achievement of ancestors~"""
        tales: dict[str, any] = {}
        """Recording the data of 'sideProduct' in 'afterward' and 'beforewards' for API. ~Tales of braves circulate~"""

        reports: dict[str, dict[str, any]] = {}
        """Recording the data of 'reports'. ~The guild concludes the results.~"""
        tales_reports: dict[str, dict[str, any]] = {}
        """Recording the data of 'sideProduct' in 'reports' for API. ~Tales of braves circulate~"""

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
        _summon = all((not v is None) for v in [serial, summonerID, summonerID])
        # args, commons, outfields

        args: dict[str, any] = jsonablize(self.args._asdict())
        commons: dict[str, any] = jsonablize(self.commons._asdict())
        outfields = jsonablize(self.outfields)
        # adventures, legacy, tales
        tales = {}
        adventures_wunex = self.beforewards._asdict()
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

        tales: dict[str, any] = jsonablize(tales)

        # reports
        reports: dict[str, dict[str, any]] = {}
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
        tales_reports: dict[str, dict[str, dict[str, any]]] = {}
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
            report_main, report_tales = al._export()
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
            tmp = folder + f"./{expName}.{str(repeat_times).rjust(self._rjustLen, '0')}/"
            while os.path.exists(tmp):
                repeat_times += 1
                tmp = folder + f"./{expName}.{str(repeat_times).rjust(self._rjustLen, '0')}/"
            folder = tmp
            filename += f"{expName}.{str(repeat_times).rjust(self._rjustLen, '0')}.id={expID}"
            
        self.commons = self.commons._replace(filename=filename)
        files['folder'] = folder
        files['args'] = folder + f'args/{filename}.args.json'
        files['advent'] = folder + f'advent/{filename}.advent.json'
        files['legacy'] = folder + f'legacy/{filename}.legacy.json'
        for k in tales.keys():
            files[f'tales.{k}'] = folder + f'tales/{filename}.{k}.json'
        files['reports'] = folder + f'reports/{filename}.reports.json'
        for k in tales_reports.keys():
            files[f'reports.tales.{k}'] = folder + \
                f'tales/{filename}.{k}.reports.json'
        
        files = {
            k: str(Path(v)) for k, v in files.items()
        }

        return self.Export(
            expID=expID,
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
            tales_reports=tales_reports
        )

    def write(
        self,
        saveLocation: Union[Path, str] = Path('./'),
        
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
    ) -> Export:
        """Export the experiment data, if there is a previous export, then will overwrite.
        Replacement of :func:`QurryV4().writeLegacy`

        - example of filename:

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
                If `saveLocation == None`, then cancelled the file to be exported.
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
        else:
            raise TypeError(f"saveLocation must be Path or str, not {type(saveLocation)}")
        
        export_material = self.export()
        export_set = {}
        # args ...............  # arguments, commonparams, outfields, files
        export_set['args'] = {
            'expID': export_material.expID,
            'expName': export_material.expName,
            'serial': export_material.serial,
            'summonerID': export_material.summonerID,
            'summonerName': export_material.summonerName,
            'filename': export_material.filename,
            
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
            if f'reports.tales.{tk}' not in export_material.files:
                warnings.warn(f"tales.{tk} is not in export_names, it's not exported.")
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
                warnings.warn(f"reports.tales.{tk} is not in export_names, it's not exported.")
                
        folder = saveLocation / Path(export_material.files['folder']) 
        if not os.path.exists(folder):
            os.mkdir(folder)
        for k in self._required_folder:
            if not os.path.exists(folder / k):
                os.mkdir(folder / k)
                
        for filekey, content in export_set.items():
            quickJSON(
                content=content, 
                filename=saveLocation / export_material.files[filekey],
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonablize=jsonablize,
            )
                
