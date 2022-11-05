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
import json

from ...hoshi import Hoshi
from ...mori import jsonablize, TagMap, syncControl
from ...mori.type import TagMapType
from ...exceptions import QurryInvalidInherition, QurryExperimentCountsNotCompleted
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

        # Arguments for exportation
        tags: tuple[str] = ()
        """Tags of experiment."""
        saveLocation: Union[Path, str] = Path('./')
        """Location of saving experiment. 
        If this experiment is called by :cls:`QurryMultiManager`,
        then `adventure`, `legacy`, `tales`, and `reports` will be exported to their dedicated folders in this location respectively."""

        # Arguments for multi-experiment
        serial: Optional[int] = None
        """Index of experiment in a multiOutput."""
        summoner: Optional[Hashable] = None
        """ID of experiment of the multiManager."""

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
        sideProduct: dict = {}
        """The data of experiment will be independently exported in the folder 'tales'."""

    class after(NamedTuple):
        # Measurement Result
        result: list[Result] = []
        """Results of experiment."""
        counts: list[dict[str, int]] = []
        """Counts of experiment."""

        # side product
        sideProduct: dict = {}
        """The data of experiment will be independently exported in the folder 'tales'."""

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
        summoner: Optional[str] = None
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

        def __repr__(self):
            return f'<analysis(serial={self.header.serial} ,sampling={self.sampling})>'

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
            elif k in self._v3ArgsMapping:
                commons[self._v3ArgsMapping[k]] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        if 'datetime' not in commons:
            commons['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.args = self.arguments(**params)
        self.commons = self.commonparams(expID=expID, **commons)
        self.outfields: dict[str, any] = outfields
        self.beforewards = self.before()
        self.afterwards = self.after()
        self.reports: list[QurryExperiment.analysis] = []

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
            summoner=self.commons.summoner,
            log={'blabla': 'nothing'}
        )
        report = report._replace(
            sideProduct={**report.sideProduct, 'bla': 'nothing'},
            header=header
        )
        self.reports.append(report)
        return report

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
            info.newline(('itemize', str(k), str(v), 'test', 2))
        info.newline(('itemize', 'outfields', len(self.outfields),
                     'Number of unused arguments.', 1))
        for k, v in self.outfields.items():
            info.newline(('itemize', str(k), str(v), '', 2))
        info.newline(('itemize', 'beforewards', len(
            self.before._fields), 'Number of preparing dates.', 1))
        info.newline(('itemize', 'afterwards', len(
            self.after._fields), 'Number of experiment result datasets.', 1))
        info.newline(('itemize', 'reports', len(
            self.reports), 'Number of analysis.', 1))
        if reportExpanded:
            for item in self.reports:
                info.newline(
                    ('itemize', 'serial', None, item.header.serial, 2))
                info.newline(('txt', item, 3))

        return info

    class Export(NamedTuple):
        expID: str = ''
        expName: str = 'exps'
        serial: Optional[int] = None
        filename: str = ''
        """The name of file to be exported, Warning, this is not the actual name of files
        for the `.write` function actually exports 4 different files
        respecting to `adventure`, `legacy`, `tales`, and `reports` like:
        
        ```txt
        blabla_experiment.adventure.json
        blabla_experiment.legacy.json
        blabla_experiment.{tales_fields}.tales.json
        blabla_experiment.report.json
        ```
        
        which `blabla_experiment` is the example filename.
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
        """Recording the data of 'sideProduct' in 'afterward' and 'befosrewards' for API. ~Tales of braves circulate~"""

        reports: list[dict[str, any]] = []
        """Recording the data of 'reports'. ~The guild concludes the results.~"""

    def export(self) -> Export:
        """Export the data of experiment.

        Returns:
            Export: A namedtuple containing the data of experiment.
        """

        # independent values
        expID = self.commons.expID
        serial = self.commons.serial
        expName = self.beforewards.expName
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
        legacy_wunex.__doc__ = "Legacy with unexported data."
        
        legacy = {}
        for k, v in legacy_wunex.items():
            if k == 'sideProduct':
                tales = {**tales, **v}
            elif k in self._unexports:
                ...
            else:
                adventures[k] = jsonablize(v)
        tales: dict[str, any] = jsonablize(tales)
        # filename
        filename = f"{expName}.id={expID}"
        if serial is not None:
            filename += f".index={serial}"
        # reports
        reports: list[dict[str, any]] = [
            jsonablize(al._asdict()) for al in self.reports]

        return self.Export(
            expID=expID,
            expName=expName,
            serial=serial,
            filename=filename,

            args=args,
            commons=commons,
            outfields=outfields,
            adventures=adventures,
            legacy=legacy,
            tales=tales,

            reports=reports
        )
        
    def write(
        self,
        saveLocation: Optional[Union[Path, str]] = None,
        excepts: list = [],
        _isMulti: bool = False,
        _clear: bool = False,
    ) -> dict[str, any]:
        """Export the experiment data, if there is a previous export, then will overwrite.
        Replacement of :func:`QurryV4().writeLegacy`

        - example of file.name:

            >>> {name}.{self.exps[expID]['expsName']}.expId={expID}.json

            In `self.exps`,
            >>> filename = ((
                Path(f"{self.exps[legacyId]['expsName']}.expId={legacyId}.json")
            )
            >>> self.exps[legacyId]['filename'] = filename

        Args:
            expID (Optional[str], optional):
                The id of the experiment will be exported.
                If `expID == None`, then export the experiment which id is`.IDNow`.
                Defaults to `None`.

            saveLocation (Optional[Union[Path, str]], optional):
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to `None`.

            name (str, optional):
                The first name of the file.
                Export as showing in example.

        Returns:
            dict[any]: the export content.
        """
