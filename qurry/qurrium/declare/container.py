from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.providers import Backend
from qiskit.providers.ibmq import AccountProvider
from qiskit_aer import AerSimulator

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, overload
from abc import abstractmethod, abstractstaticmethod
from collections import namedtuple
import gc

from ...mori import jsonablize, TagMap, syncControl
from ...mori.type import TagMapType
from .type import Quantity, Counts, waveGetter, waveReturn

# argument
class QurryExperiment:

    __name__ = 'QurryExperiment'

    @abstractstaticmethod
    class arguments(NamedTuple):
        """Construct the experiment's parameters."""
        
    class arguments(NamedTuple):
        expsName: str = 'exps'
        wave: Union[QuantumCircuit, any, None] = None
        sampling: int = 1

    class commonparams(NamedTuple):
        expID: Optional[str] = None
        expID.__doc__ = "ID of e                  xperiment."

        # Qiskit argument of experiment.
        # Multiple jobs shared
        shots: int = 1024
        backend: Backend = AerSimulator()
        provider: Optional[AccountProvider] = None
        runArgs: dict[str, any] = {}
        shots.__doc__ = "Number of shots to run the program (default: 1024)."
        backend.__doc__ = "Backend to execute the circuits on."
        provider.__doc__ = "Provider to execute the backend on."
        runArgs.__doc__ = "Arguments of `IBMQJobManager().run`."

        # Single job dedicated
        runBy: Literal['gate', 'operator'] = "gate"
        decompose: Optional[int] = 2
        transpileArgs: dict[str, any] = {}
        runBy.__doc__ = "Run circuits by gate or operator."
        decompose.__doc__ = "Decompose the circuit in given times."
        transpileArgs.__doc__ = "Arguments of `qiskit.compiler.transpile`."

        # Other arguments of experiment
        drawMethod: str = 'text'
        tags: tuple[str] = ()
        resoureControl: dict[str, any] = {}
        drawMethod.__doc__ = "Method of drawing circuit."
        tags.__doc__ = "Tags of experiment."
        resoureControl.__doc__ = "Arguments of `ResoureWatch`."

        saveLocation: Union[Path, str] = Path('./')
        exportLocation: Path = Path('./')
        saveLocation.__doc__ = "Location of saving experiment."
        exportLocation.__doc__ = "Location of exporting experiment, exportLocation is the final result decided by experiment."

        expIndex: Optional[int] = None
        expIndex.__doc__ = "Index of experiment in a multiOutput."

    _v3ArgsMapping = {
        'runConfig': 'runArgs',
    }
    
    @abstractmethod
    class analysis(NamedTuple):
        """Construct the experiment's output."""
        
    class analysis(NamedTuple):
        lucky: int = 0

    class before(NamedTuple):
        # Experiment Preparation
        circuit: list[QuantumCircuit] = []
        figRaw: list[str] = []
        figTranspile: list[str] = []
        circuit.__doc__ = "Circuits of experiment."
        figRaw.__doc__ = "Raw circuit figures which is the circuit before transpile."
        figTranspile.__doc__ = "Transpile circuit figures which is the circuit after transpile and the actual one would be executed."
        
        # Export data
        jobID: str = ''
        expsName: str = 'exps'
        jobID.__doc__ = "ID of job for pending on real machine (IBMQBackend)."
        expsName.__doc__ = "Name of experiment which is also showed on IBM Quantum Computing quene."
        
        # side product
        sideProduct: dict = {}
        sideProduct.__doc__ = "The data of experiment will be independently exported in the folder 'tales'."

    class after(NamedTuple):
        # Measurement Result
        result: list[Result] = []
        counts: list[dict[str, int]] = []
        result.__doc__ = "Results of experiment."
        counts.__doc__ = "Counts of experiment."

        # side product
        sideProduct: dict = {}
        sideProduct.__doc__ = "The data of experiment will be independently exported in the folder 'tales'."

    _unexports = ['sideProduct', 'result']

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
                "argsCore filter can't be initialized with positional arguments.")
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
                "expsCore filter can't be initialized with positional arguments.")
        infields = {}
        outfields = {}
        for k in kwargs:
            if k in cls.analysis._fields:
                infields[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        return cls.analysis(**infields), outfields

    def __init__(self, *args, **kwargs) -> None:

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments.")
            
        self.args = self.arguments(**kwargs)

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

        self.args = self.arguments(**params)
        self.commons = self.commonparams(**commons)
        self.outfields: dict[str, any] = outfields
        self.beforewards = self.before()
        self.afterwards = self.after()
        self.reports: list[QurryExperiment.analysis] = []
        
    class Export(NamedTuple):
        expID: str = ''
        expsName: str = 'exps'
        expIndex: Optional[int] = None
        filename: str = ''
        
        args: dict[str, any] = {}
        args.__doc__ = "Construct the experiment's parameters."
        commons: dict[str, any] = {}
        commons.__doc__ = "Construct the experiment's common parameters."
        outfields: dict[str, any] = {}
        outfields.__doc__ = "Recording the data of other unused arguments."
        
        adventures: dict[str, any] = {}
        adventures.__doc__ = "Recording the data of 'beforeward'. ~A Great Adventure begins~"
        legacy: dict[str, any] = {}
        legacy.__doc__ = "Recording the data of 'afterward'. ~The Legacy remains from the achievement of ancestors~"
        tales: dict[str, any] = {}
        tales.__doc__ = "Recording the data of 'sideProduct' in 'afterward' and 'befosrewards' for API. ~Tales of braves circulate~"
        
        reports: list[dict[str, any]] = []
        reports.__doc__ = "Recording the data of 'reports'. ~The guild concludes the results.~"

    def export(self) -> Export:
        """Export the data of experiment.

        Returns:
            Export: A namedtuple containing the data of experiment.
        """
        
        # independent values
        expID = self.args.expID
        expIndex = self.args.expIndex
        expsName = self.beforewards.expsName
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
                tales = { **tales, **v }
            elif k in self._unexports:
                ...
            else:
                adventures[k] = jsonablize(v)
                
        legacy_wunex = self.afterwards._asdict()
        legacy = {}
        for k, v in legacy_wunex.items():
            if k == 'sideProduct':
                tales = { **tales, **v }
            elif k in self._unexports:
                ...
            else:
                adventures[k] = jsonablize(v)
        tales: dict[str, any]= jsonablize(tales)
        # filename
        filename = f"{expsName}.id={expID}"
        if expIndex is not None:
            filename += f".index={expIndex}"
        # reports
        reports: list[dict[str, any]] = [jsonablize(al._asdict()) for al in self.reports]

        return self.Export(
            expID=expID,
            expsName=expsName,
            expIndex=expIndex,
            filename=filename,
            
            args=args,
            commons=commons,
            outfields=outfields,
            adventures=adventures,
            legacy=legacy, 
            tales=tales,
            
            reports=reports
        )

    def __setitem__(self, key, value) -> None:
        if key in self.before._fields:
            self.beforewards = self.beforewards._replace(**{key: value})
            gc.collect()
        elif key in self.after._fields:
            self.afterwards = self.afterwards._replace(**{key: value})
        else:
            raise ValueError(
                f"{key} is not a valid field of '{self.before.__name__}' and '{self.after.__name__}'.")

    def __repr__(self) -> str:
        return (
            f"<{self.__name__} with "+
            f"{self.args.__repr__()}, "+
            f"{self.commons.__repr__()}, "+
            f"{len(self.outfields)} unused arguments, "+
            f"{len(self.before._fields)} preparing dates, "+
            f"{len(self.after._fields)} experiment result datasets, "+
            f"and {len(self.reports)} analysis>")


"""
exps structure:

```py
exps['someID'] = {
    args: QurryArgs(),
    data: QurryExpsData(),
}
```

"""


class QurryMultiExps:
    
    class argsMultiMain(NamedTuple):
        # defaultConfig of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = None
        backend: Backend = None
        provider: AccountProvider = None

        # IBMQJobManager() dedicated
        managerRunArgs: dict[str, any] = None

        # Other arguments of experiment
        # Multiple jobs shared
        expsName: str = None
        saveLocation: Union[Path, str] = None
        exportLocation: Path = None

        pendingStrategy: Literal['power', 'tags', 'each'] = None
        jobsType: Literal["multiJobs", "powerJobs"] = None
        isRetrieve: bool = None
        isRead: bool = None
        clear: bool = None
        independentExports: list[str] = None
        filetype: TagMap._availableFileType = None
        
    class expsMultiMain(NamedTuple):
        # configList
        configList: list = []
        configDict: dict = {}

        powerJobID: Union[str, list[str]] = []
        gitignore: syncControl = syncControl()

        circuitsNum: dict[str, int] = {}
        state: Literal["init", "pending", "completed"] = 'init'
        
    class dataStateDepending(NamedTuple):
        tagMapQuantity: TagMapType[Quantity]
        tagMapCounts: TagMapType[Counts]

    class dataUnexported(NamedTuple):
        tagMapResult: TagMapType[Result]

    class dataNeccessary(NamedTuple):
        # with Job.json file
        tagMapExpsID: TagMapType[str]
        tagMapFiles: TagMapType[str]
        tagMapIndex: TagMapType[Union[str, int]]
        # circuitsMap
        circuitsMap: TagMapType[str]
        pendingPools: TagMapType[str]
        
    _v3ArgsMapping = {
        'circuitsMap': 'circuitsMap',
    }
    _exportsExceptKeys = ['configList']+[i for i in dataUnexported._fields]
    _powerJobKeyRequired = ['powerJobID', 'state']
    _multiJobKeyRequired = ['state']
    _independentExport = ['configDict']
    
    def __init__(self, *args, **kwargs) -> None:
        
        self.args = self.argsMultiMain(*args, **kwargs)
        self.exps = self.expsMultiMain()
        self.stateDepending = self.dataStateDepending()
        self.unexported = self.dataUnexported()
        self.neccessary = self.dataNeccessary()