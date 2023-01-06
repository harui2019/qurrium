from qiskit.result import Result
from qiskit.providers import Backend
from qiskit.providers.ibmq import AccountProvider
from qiskit_aer import AerSimulator

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, overload, Any
from uuid import uuid4
from datetime import datetime
import os
import gc
import json
import warnings

from ...mori import jsonablize, TagList, syncControl, defaultConfig
from ...mori.quick import quickJSON, quickRead
from ...exceptions import QurryProtectContent
from ..declare.type import Quantity, Counts
from ..utils.naming import namingComplex, naming

multicommonConfig = defaultConfig(
    name='multicommon',
    default={
        'summonerID': None,
        'summonerName': None,
        'shots': 1024,
        'backend': AerSimulator(),
        'provider': None,
        'saveLocation': Path('./'),
        'exportLocation': Path('./'),
        'files': {},
        'jobsType': None,
        'managerRunArgs': None,
        'filetype': 'json',
        'datetimes': {}
    }
)

class MultiManager:

    class multicommonparams(NamedTuple):
        """Multiple jobs shared. `argsMultiMain` in V4 format.
        """

        summonerID: str
        """ID of experiment of the multiManager."""
        summonerName: str
        """Name of experiment of the multiManager."""

        shots: int
        """Number of shots to run the program (default: 1024), which multiple experiments shared."""
        backend: Backend
        """Backend to execute the circuits on, which multiple experiments shared."""
        provider: Optional[AccountProvider]
        """Provider to execute the backend on, which multiple experiments shared."""

        saveLocation: Union[Path, str]
        """Location of saving experiment."""
        exportLocation: Path
        """Location of exporting experiment, exportLocation is the final result decided by experiment."""
        files: dict[str, Union[str, dict[str, str]]]

        jobsType: Literal["local", "IBMQ", "AWS_Bracket", "Azure_Q"]
        """Type of jobs to run multiple experiments."""
        
        managerRunArgs: dict[str, any]
        """Other arguments will be passed to `IBMQJobManager()`"""

        filetype: TagList._availableFileType
        
        # header
        datetimes: dict[str, str]

    class before(NamedTuple):
        """`dataNeccessary` and `expsMultiMain` in V4 format."""
        
        configDict: dict[str, dict[str, any]]
        """The dict of config of each experiments."""
        circuitsNum: dict[str, int]
        """The map with tags of index of experiments, which multiple experiments shared."""
        
        pendingPools: TagList[str]
        """The pool of pending jobs, which multiple experiments shared, it works only when executing experiments is remote."""
        circuitsMap: TagList[str]
        """The map of circuits of each experiments in the index of pending, which multiple experiments shared."""
        jobID: list[tuple[str, str]]
        """The list of jobID in pending, which multiple experiments shared, it works only when executing experiments is remote."""
        
        tagMapExpsID: TagList[str]
        tagMapFiles: TagList[str]
        tagMapIndex: TagList[Union[str, int]] 
        
    class after(NamedTuple):
        """`dataStateDepending` and `dataNeccessary` in V4 format."""
        retrievedResult: TagList[Result]
        allCounts: dict[Hashable, list[dict[str, int]]]

    _unexports = ['retrievedResult']
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
        elif key in self.after._fields:
            return getattr(self.afterwards, key)
        else:
            raise ValueError(
                f"{key} is not a valid field of '{self.before.__name__}' and '{self.after.__name__}'.")

    @property
    def summonerID(self) -> str:
        return self.multicommons.summonerID
    
    @property
    def summonerName(self) -> str:
        return self.multicommons.summonerName

    def __init__(
        self,
        *args,
        summonerID: Hashable,
        summonerName: str,
        saveLocation: Union[Path, str] = Path('./'),
        
        isRead: bool = False,
        encoding: str = 'utf-8',
        
        filetype: TagList._availableFileType = 'json',
        version: Literal['v4', 'v5'] = 'v5',
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
                if isRead:
                    if version == 'v5':
                        summonerID = ''
                    else:
                        summonerID = str(uuid4())
                else:
                    summonerID = str(uuid4())
            else:
                ...
        
        self.gitignore = syncControl()
        self.namingCpx = naming(
            isRead=isRead,
            expsName=summonerName,
            saveLocation=saveLocation,
        )
        
        if isRead and version == 'v5':     
            multiConfigName = self.namingCpx.exportLocation / \
                f"{self.namingCpx.expsName}.multiConfig.json"
            if not multiConfigName.exists():
                raise FileNotFoundError(
                    f"Can't find the multiConfig file in {multiConfigName}.")
            with open(multiConfigName, 'r', encoding=encoding) as f:
                rawReadMultiConfig: dict[str, Any] = json.load(f)
            rawReadMultiConfig['saveLocation'] = self.namingCpx.saveLocation
            rawReadMultiConfig['exportLocation'] = self.namingCpx.exportLocation
            files: dict[str, Union[str, dict[str, str]]] = rawReadMultiConfig['files']
                    
            self.beforewards = self.before(
                configDict=quickRead(
                    filename=Path(files['configDict']).name,
                    saveLocation=self.namingCpx.exportLocation,
                ),
                circuitsNum=quickRead(
                    filename=Path(files['circuitsNum']).name,
                    saveLocation=self.namingCpx.exportLocation,
                ),
                circuitsMap=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName='circuitsMap'
                ),
                pendingPools=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName='pendingPools'
                ),
                jobID=quickRead(
                    filename=Path(files['jobID']).name,
                    saveLocation=self.namingCpx.exportLocation,
                ),
                
                tagMapExpsID=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName='tagMapExpsID'
                ),
                tagMapFiles=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName='tagMapFiles'
                ),
                tagMapIndex=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName='tagMapIndex'
                ),
            )
            self.afterwards = self.after(
                retrievedResult={},
                allCounts=quickRead(
                    filename=Path(files['allCounts']).name,
                    saveLocation=self.namingCpx.exportLocation,
                ),
            )
            self.tagMapQuantity: dict[str, TagList[Quantity]] = {}
            for qk in files['tagMapQuantity'].keys():
                self.tagMapQuantity[qk] = TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName=f'tagMapQuantity',
                    name=f'{self.namingCpx.expsName}.{qk}',
                )

        elif isRead and version == 'v4':
            dataDummyJobs: dict[any] = {}
            dataPowerJobsName = self.namingCpx.exportLocation / \
                f"{self.namingCpx.expsName}.powerJobs.json"
            dataMultiJobsName = self.namingCpx.exportLocation / \
                f"{self.namingCpx.expsName}.multiJobs.json"
            
            if os.path.exists(dataPowerJobsName):
                with open(dataPowerJobsName, 'r', encoding='utf-8') as theData:
                    dataDummyJobs = json.load(theData)
                jobsType = "powerJobs"

            else:
                with open(dataMultiJobsName, 'r', encoding='utf-8') as theData:
                    dataDummyJobs = json.load(theData)
                jobsType = "multiJobs"
            
            rawReadMultiConfig = {
                **kwargs,
                'summonerID': summonerID,
                'summonerName': self.namingCpx.expsName,
                'saveLocation': self.namingCpx.saveLocation,
                'exportLocation': self.namingCpx.exportLocation,
                'filetype': filetype,
                'jobsType': jobsType,
                'files': {
                    'v4': {
                        jobsType: f'{self.namingCpx.expsName}.{jobsType}.json',
                        'configDict': f'{self.namingCpx.expsName}.configDict.json',
                        'circuitsMap': f'{self.namingCpx.expsName}.circuitsMap.json',
                        'pendingPools': f'{self.namingCpx.expsName}.pendingPools.json',
                        'tagMapExpsID': f'{self.namingCpx.expsName}.tagMapExpsID.json',
                        'tagMapFiles': f'{self.namingCpx.expsName}.tagMapFiles.json',
                        'tagMapIndex': f'{self.namingCpx.expsName}.tagMapIndex.json',
                        'tagMapQuantity': f'{self.namingCpx.expsName}.tagMapQuantity.json',
                    }
                }
            }
            for k in dataDummyJobs.keys():
                if k in self.multicommonparams._fields:
                    rawReadMultiConfig[k] = dataDummyJobs[k]
            self.beforewards = self.before(
                configDict=quickRead(
                    filename=f"{self.namingCpx.expsName}.configDict.json",
                    saveLocation=self.namingCpx.exportLocation,
                ),
                circuitsNum=dataDummyJobs['circuitsNum'],
                circuitsMap=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName='circuitsMap'
                ),
                pendingPools=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName='pendingPools'
                ),
                jobID=[],
                
                tagMapExpsID=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName='tagMapExpsID'
                ),
                tagMapFiles=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName='tagMapFiles'
                ),
                tagMapIndex=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName='tagMapIndex'
                ),
            )
            self.afterwards = self.after(
                retrievedResult={},
                allCounts={},
            )
            self.tagMapQuantity: dict[str, TagList[Quantity]] = {
                'oldreport': TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagmapName='tagMapQuantity',
                ),
            }

        else:
            rawReadMultiConfig = {
                **kwargs,
                'summonerID': summonerID,
                'summonerName': self.namingCpx.expsName,
                'saveLocation': self.namingCpx.saveLocation,
                'exportLocation': self.namingCpx.exportLocation,
                'filetype': filetype,
            }
            self.beforewards = self.before(
                configDict={},
                circuitsNum={},
                circuitsMap=TagList(),
                pendingPools=TagList(),
                jobID=[],
                
                tagMapExpsID=TagList(),
                tagMapFiles=TagList(),
                tagMapIndex=TagList(),
            )
            self.afterwards = self.after(
                retrievedResult={},
                allCounts={},
            )
            self.tagMapQuantity: dict[str, TagList[Quantity]] = {}
        
        multicommons = {}
        outfields = {}
        for k in rawReadMultiConfig:
            if k in self.multicommonparams._fields:
                multicommons[k] = rawReadMultiConfig[k]
            else:
                outfields[k] = rawReadMultiConfig[k]
        
        if 'datetimes' not in multicommons:
            multicommons['datetimes'] = {}
            if version == 'v4':
                multicommons['datetimes']['v4Read'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            multicommons['datetimes']['bulid'] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")
        
        self.multicommons = self.multicommonparams(**multicommons)
        self.outfields: dict[str, Any] = outfields
        
    @property
    def summonerID(self) -> str:
        return self.multicommons.summonerID
    
    @property
    def summonerName(self) -> str:
        return self.multicommons.summonerName
    
    def write(
        self,
        saveLocation: Optional[Union[Path, str]] = None,

        indent: int = 2,
        encoding: str = 'utf-8',
        # zip: bool = False,
        _onlyQuantity: bool = False,
    ) -> dict:
        
        self.gitignore.read(self.multicommons.exportLocation)
        print(f"| Export multimanager...")
        if saveLocation is None:
            saveLocation = self.multicommons.saveLocation
            if saveLocation is None:
                raise ValueError(
                    "Can't find the saveLocation, please specify it.")
        
        self.gitignore.ignore('*.json')
        if not os.path.exists(saveLocation):
            os.makedirs(saveLocation)
        if not os.path.exists(self.multicommons.exportLocation):
            os.makedirs(self.multicommons.exportLocation)
        self.gitignore.export(self.multicommons.exportLocation)
        
        # beforewards amd afterwards
        for k in self.before._fields + self.after._fields:
            if _onlyQuantity or (k in self._unexports):
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
                self.multicommons.files[k] = str(filename)
                self.gitignore.sync(f"*.{k}.{self.multicommons.filetype}")
                
            elif isinstance(self[k], (dict, list)):
                filename = Path(self.multicommons.exportLocation) / \
                    f"{self.multicommons.summonerName}.{k}.json"
                self.multicommons.files[k] = str(filename)
                self.gitignore.sync(f"*.{k}.json")
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
        # tagMapQuantity
        self.multicommons.files['tagMapQuantity'] = {}
        for k, v in self.tagMapQuantity.items():
            filename = v.export(
                saveLocation=self.multicommons.exportLocation,
                tagmapName='tagMapQuantity',
                name=f'{self.multicommons.summonerName}.{k}',
                filetype=self.multicommons.filetype,
                openArgs={
                    'mode': 'w+',
                    'encoding': encoding,
                },
                jsonDumpArgs={
                    'indent': indent,
                }
            )
            self.multicommons.files['tagMapQuantity'][k] = str(filename)
        self.gitignore.sync(f"*.tagMapQuantity.{self.multicommons.filetype}")
        # multiConfig
        multiConfigName = Path(self.multicommons.exportLocation) / \
            f"{self.multicommons.summonerName}.multiConfig.json"
        self.multicommons.files['multiConfig'] = str(multiConfigName)
        self.gitignore.sync('*.multiConfig.json')
        multiConfig = {
            **self.multicommons._asdict(), 
            'outfields': self.outfields,
            'files': self.multicommons.files,
        }
        quickJSON(
            content=multiConfig,
            filename=multiConfigName,
            mode='w+',
            jsonablize=True,
            encoding=encoding,
        )
        
        self.gitignore.export(self.multicommons.exportLocation)
        
        return multiConfig
        