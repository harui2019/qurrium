################################################
# This is a backup for deprecated MultiManager 
# which is planned to backward-compatible for qurry v4.
# Due to the data structure and process of experiment is redesigned,
# unlike v3 to v4 which is only a change to optimize the data structure,
# So v5 would no longer be backward-compatible with v4 currently.
# But it's possible there is a solution for partial backward-compatibility in future.
#################################################



from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.providers import Backend
from qiskit.providers.ibmq import AccountProvider
from qiskit_aer import AerSimulator

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, overload, Any
from abc import abstractmethod, abstractstaticmethod, abstractclassmethod
from collections import namedtuple
from uuid import uuid4
from datetime import datetime
import os
import gc
import json
import warnings

from ...mori import jsonablize, TagList, syncControl
from ...mori.quick import quickJSON
from ...exceptions import QurryInvalidInherition, QurryProtectContent
from ..declare.type import Quantity, Counts, waveGetter, waveReturn
from ..utils.naming import namingComplex, naming


class MultiManagerPrototype:

    class multicommonparams(NamedTuple):
        """Multiple jobs shared. `argsMultiMain` in V4 format.
        """

        summonerID: str
        """ID of experiment of the multiManager."""
        summonerName: str
        """Name of experiment of the multiManager."""

        shots: int = 1024
        """Number of shots to run the program (default: 1024), which multiple experiments shared."""
        backend: Backend = AerSimulator()
        """Backend to execute the circuits on, which multiple experiments shared."""
        provider: Optional[AccountProvider] = None
        """Provider to execute the backend on, which multiple experiments shared."""

        saveLocation: Union[Path, str] = Path('./')
        """Location of saving experiment."""
        exportLocation: Path = Path('./')
        """Location of exporting experiment, exportLocation is the final result decided by experiment."""

        jobsType: Literal["local", "IBMQ", "AWS_Bracket", "Azure_Q"] = None
        """Type of jobs to run multiple experiments."""
        
        managerRunArgs: dict[str, any] = None
        """Other arguments will be passed to `IBMQJobManager()`"""

        filetype: TagList._availableFileType = None
        
        # header
        datetimes: dict[str, str] = {}
        
    @abstractmethod
    class extendstate(NamedTuple):
        """Multiple jobs shared. `expsMultiMain` in V4 format.
        """

    class before(NamedTuple):
        """`dataNeccessary` and `expsMultiMain` in V4 format."""
        
        configDict: dict[str, dict[str, any]]
        """The dict of config of each experiments."""
        circuitsNum: dict[str, int]
        """The map with tags of index of experiments, which multiple experiments shared."""
        circuitsMap: TagList[str]
        """The map of circuits of each experiments, which multiple experiments shared."""
        pendingPools: TagList[str]
        """The pool of pending jobs, which multiple experiments shared, it works only when executing experiments is remote."""
        jobID: list[tuple[str, str]]
        
        tagMapExpsID: TagList[str]
        tagMapFiles: TagList[str]
        tagMapIndex: TagList[Union[str, int]]
        
    class after(NamedTuple):
        """`dataStateDepending` and `dataNeccessary` in V4 format."""
        tagMapCounts: TagList[Counts]
        tagMapResult: TagList[Result]
        
    class multiAnalysis(NamedTuple):
        analysisOption: dict[str, any]
        tagMapQuantiity: TagList[Quantity]

    _unexports = ['tagMapResult']
    """The content would not be exported."""
    after_lock = False
    """Protect the :cls:`afterward` content to be overwritten. When setitem is called and completed, it will be setted as `False` automatically."""
    mute_auto_lock = False
    """Whether mute the auto-lock message."""

    def unlock_afterward(self, mute_auto_lock: bool = False):
        """Unlock the :cls:`afterward` content to be overwritten.

        Args:
            mute_auto_lock (bool, optional): 
                Mute anto-locked message for the unlock of this time. Defaults to False.
        """
        self.after_lock = True
        self.mute_auto_lock = mute_auto_lock

    def __setitem__(self, key, value) -> None:
        if key in self.before._fields:
            self.beforewards = self.beforewards._replace(**{key: value})

        elif key in self.extendstate._fields:
            self.extends =self.extends._replace(**{key: value})
        
        elif key in self.after._fields:
            if self.after_lock and isinstance(self.after_lock, bool):
                self.afterwards = self.afterwards._replace(**{key: value})
            else:
                raise QurryProtectContent(
                    f"Can't set value to :cls:`afterward` field {key} because it's locked, use `.unlock_afterward()` to unlock before setting item .")

        else:
            raise ValueError(
                f"{key} is not a valid field of '{self.before.__name__}' and '{self.after.__name__}'.")

        gc.collect()
        if self.after_lock != False:
            self.after_lock = False
            if not self.mute_auto_lock:
                print(
                    f"after_lock is locked automatically now, you can unlock by using `.unlock_afterward()` to set value to :cls:`afterward`.")
            self.mute_auto_lock = False

    def __getitem__(self, key) -> Any:
        if key in self.before._fields:
            return getattr(self.beforewards, key)
        elif key in self.extendstate._fields:
            return getattr(self.extends, key)
        elif key in self.after._fields:
            return getattr(self.afterwards, key)
        else:
            raise ValueError(
                f"{key} is not a valid field of '{self.before.__name__}' and '{self.after.__name__}'.")

    def __init__(
        self,
        *args,
        summonerID: Hashable,
        summonerName: str,
        saveLocation: Union[Path, str],
        initedConfigList: list,
        
        state: Literal["init", "pending", "completed"],
        isRead: bool = False,
        overwrite: bool = False,
        **kwargs
    ) -> None:
        """Initialize the multi-experiment.
        (The replacement of `QurryV4._multiDataGenOrRead` in V4 format.)

        Args:
            summonerID (Hashable): _description_
            summonerName (str): _description_
            saveLocation (Union[Path, str]): _description_
            initedConfigList (list): _description_
            state (Literal[&quot;init&quot;, &quot;pending&quot;, &quot;completed&quot;]): _description_
            isRead (bool, optional): _description_. Defaults to False.
            overwrite (bool, optional): _description_. Defaults to False.

        Raises:
            ValueError: _description_
            ValueError: _description_
        """        
        
        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments.")
        try:
            hash(summonerID)
        except TypeError as e:
            summonerID = None
            warnings.warn(
                "'expID' is not hashable, it will be set to generate automatically.")
        finally:
            if summonerID is None:
                summonerID = str(uuid4())
            else:
                ...
        
        self.gitignore = syncControl()
        self.namingCpx = naming(
            isRead=isRead,
            expsName=summonerName,
            saveLocation=saveLocation,
        )
        
        # migrate from V4 to V5
        version = 5
        if isRead:
            dataDummyJobs: dict[any] = {}
            dataPowerJobsName = self.namingCpx.exportLocation / \
                f"{self.namingCpx.expsName}.powerJobs.json"
            dataMultiJobsName = self.namingCpx.exportLocation / \
                f"{self.namingCpx.expsName}.multiJobs.json"
                
            multiConfigName = self.namingCpx.exportLocation / \
                f"{self.namingCpx.expsName}.multiConfig.json"
            
            legacyLoc = self.namingCpx.exportLocation / 'legacy'

            if not os.path.exists(legacyLoc):
                version = 3
            elif os.path.exists(dataPowerJobsName) or os.path.exists(dataMultiJobsName):
                version = 4
            elif os.path.exists(multiConfigName):
                version = 5
            else:
                raise ValueError(
                    f"Can't find any valid data file for {self.namingCpx.expsName} to detect version.")

            # read
            if os.path.exists(dataPowerJobsName):
                with open(dataPowerJobsName, 'r', encoding='utf-8') as theData:
                    dataDummyJobs = json.load(theData)
                jobsType = "powerJobs"

            else:
                with open(dataMultiJobsName, 'r', encoding='utf-8') as theData:
                    dataDummyJobs = json.load(theData)
                jobsType = "multiJobs"
            dataDummyJobs['jobsType'] = jobsType
            
            if 'state' in dataDummyJobs:
                state = dataDummyJobs['state']
            else:
                warnings.warn(f"'state' no found, use '{state}'.")
                
            rawJobID = []
            if 'powerJobID' in dataDummyJobs:
                rawJobID = dataDummyJobs['powerJobID']
            # powerJobID and handle v3
            if isinstance(rawJobID, str):
                rawJobID = [[rawJobID, "power"]]
            elif rawJobID is None:
                rawJobID = []
            elif isinstance(rawJobID, list):
                ...
            else:
                raise TypeError(
                    f"Invalid type '{type(rawJobID)}' for 'powerJobID', only 'str', 'list[tuple[str, list]]', or 'None' are available.")
            jobID = []
            for pendingID, pendingTag in rawJobID:
                if isinstance(pendingTag, list):
                    pendingTag = tuple(pendingTag)
                jobID.append((pendingID, pendingTag))
        
            if state == 'completed' and not overwrite:
                rawAfterward = self.after(

                    tagMapCounts=TagList.read(
                        saveLocation=namingComplex.exportLocation,
                        tagmapName='tagMapCounts',
                    )
                )
                rawMultiAnalysis = self.multiAnalysis(
                    analysisOption={},
                    tagMapQuantity=TagList.read(
                        saveLocation=namingComplex.exportLocation,
                        tagmapName='tagMapQuantity',
                    ),
                )
            else:
                trawAfterward = self._tagMapStateDepending(**{
                    k: TagList({}, k)
                    for k in self._tagMapStateDepending._fields})
        
        else:
            # data gen
            ...
        
        multicommons = {}
        outfields = {}
        for k in kwargs:
            if k in self.multicommonparams._fields:
                multicommons[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]
        if 'datetimes' not in multicommons:
            multicommons['datetimes']['bulid'] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")
        
        self.multicommons = self.multicommonparams(
            summonerID=summonerID,
            summonerName=self.namingCpx.expsName,
            saveLocation=self.namingCpx.exportLocation,
            exportLocation=self.namingCpx.exportLocation,
            **multicommons
        )
        self.outfields: dict[str, Any] = outfields
        
        self.extends = self.extendstate()
        self.beforewards = self.before()
        self.afterwards = self.after()

    @property
    def summonerID(self) -> str:
        return self.multicommons.summonerID
    
    @property
    def summonerName(self) -> str:
        return self.multicommons.summonerName
    
    def write(
        self,
        saveLocation: Union[Path, str] = Path('./'),

        indent: int = 2,
        encoding: str = 'utf-8',
        # zip: bool = False,
    ) -> dict:
        
        print(f"| Export...")
        self.gitignore.ignore('*.json')
        if not os.path.exists(saveLocation):
            os.makedirs(saveLocation)
        if not os.path.exists(self.multicommons.exportLocation):
            os.makedirs(self.multicommons.exportLocation)
        self.gitignore.export(self.multicommon.exportLocation)
        
        files = {}
        for k in self.before._fields + self.after._fields:
            if k  in self._unexports:
                ...
            elif isinstance(self[k], TagList):
                tmp: TagList = self[k]
                filename = tmp.export(
                    saveLocation=self.multicommons.exportLocation,
                    tagmapName=f"{k}",
                    name=self.multicommons.summonerName,
                    filetype=self.multicommons.filetype,
                    openArgs={
                        'mode': 'w+',
                        'encoding': encoding,
                    },
                    jsonDumpArgs={
                        'indent': indent,
                    }
                )
                files[k] = str(filename)
                self.gitignore.sync(files[k])
                
            elif isinstance(self[k], (dict, list)):
                filename = self.multicommons.exportLocation / \
                    f"{self.multicommons.summonerName}.{k}.json"
                files[k] = str(filename)
                self.gitignore.sync(files[k])
                quickJSON(
                    content=self[k],
                    filename=filename,
                    mode='w+',
                    jsonablize=True,
                    indent=indent,
                    encoding=encoding,
                )
                
            else:
                warnings.warn(
                    f"'{k}' is type '{type(self[k])}' which is not supported to export.")
                
        multiConfigName = self.multicommons.exportLocation / \
            f"{self.multicommons.summonerName}.multiConfig.json"
        files['multiConfig'] = str(multiConfigName)
        self.gitignore.sync(files['multiConfig'])
        multiConfig = {
            **self.multicommons._asdict(), 
            **self.extends._asdict(), 
            'outfields': self.outfields,
            'files': files,
        }
        
        quickJSON(
            content=multiConfig,
            filename=multiConfigName,
            mode='w+',
            jsonablize=True,
            encoding=encoding,
        )
        
        self.gitignore.export(self.multicommon.exportLocation)
        
        return multiConfig
        