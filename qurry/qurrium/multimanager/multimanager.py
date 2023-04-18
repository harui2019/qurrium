from qiskit.result import Result
from qiskit.providers import Backend
from qiskit_aer import AerSimulator

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, Any
from uuid import uuid4
import os
import gc
import shutil
import json
import tarfile
import warnings

from ...mori import TagList, syncControl, defaultConfig
from ...mori.quick import quickJSON, quickRead
from ...exceptions import (
    QurryProtectContent,
    QurryResetAccomplished,
    QurryResetSecurityActivated
)
from ..declare.type import Quantity
from ..utils.iocontrol import naming
from ..utils.datetime import currentTime, datetimeDict

multicommonConfig = defaultConfig(
    name='multicommon',
    default={
        'summonerID': None,
        'summonerName': None,
        'shots': 1024,
        'backend': AerSimulator(),
        'saveLocation': Path('./'),
        'exportLocation': Path('./'),
        'files': {},
        'jobsType': None,
        'managerRunArgs': None,
        'filetype': 'json',
        'datetimes': datetimeDict(),
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

        saveLocation: Union[Path, str]
        """Location of saving experiment."""
        exportLocation: Path
        """Location of exporting experiment, exportLocation is the final result decided by experiment."""
        files: dict[str, Union[str, dict[str, str]]]

        jobsType: str
        """Type of jobs to run multiple experiments and its pending strategy.
        
        - jobsType: "local", "IBMQ", "IBM", "AWS_Bracket", "Azure_Q"
        - pendingStrategy: "default", "onetime", "each", "tags"
        """

        managerRunArgs: dict[str, any]
        """Other arguments will be passed to `IBMQJobManager()`"""

        filetype: TagList._availableFileType

        # header
        datetimes: datetimeDict

    class before(NamedTuple):
        """`dataNeccessary` and `expsMultiMain` in V4 format."""

        configDict: dict[str, dict[str, any]]
        """The dict of config of each experiments."""
        circuitsNum: dict[str, int]
        """The map with tags of index of experiments, which multiple experiments shared."""

        pendingPools: TagList[int]
        """The pool of pending jobs, which multiple experiments shared, it works only when executing experiments is remote."""
        circuitsMap: TagList[str]
        """The map of circuits of each experiments in the index of pending, which multiple experiments shared."""
        jobID: list[Union[
            tuple[Union[str, None], Union[str, tuple, Hashable, None]],
            list[Union[str, None], Union[str, tuple, Hashable, None]]
        ]]
        """The list of jobID in pending, which multiple experiments shared, it works only when executing experiments is remote."""

        tagMapExpsID: TagList[str]
        tagMapFiles: TagList[str]
        tagMapIndex: TagList[Union[str, int]]

    class after(NamedTuple):
        """`dataStateDepending` and `dataNeccessary` in V4 format."""
        retrievedResult: TagList[Result]
        """The list of retrieved results, which multiple experiments shared."""
        allCounts: dict[Hashable, list[dict[str, int]]]
        """The dict of all counts of each experiments."""

        def reset(
            self,
            *args,
            security: bool = False,
            muteWarning: bool = False,
        ) -> None:
            """Reset the measurement and release memory for overwrite.

            Args:
                security (bool, optional): Security for reset. Defaults to `False`.
                muteWarning (bool, optional): Mute the warning message. Defaults to `False`.
            """

            if security and isinstance(security, bool):
                self.__init__(
                    retrievedResult=TagList(),
                    allCounts={}
                )
                gc.collect()
                if not muteWarning:
                    warnings.warn(
                        "Afterwards reset accomplished.",
                        QurryResetAccomplished)
            else:
                warnings.warn(
                    "Reset does not execute to prevent executing accidentally, " +
                    "if you are sure to do this, then use '.reset(security=True)'.",
                    QurryResetSecurityActivated)

    _unexports: list[str] = ['retrievedResult']
    """The content would not be exported."""
    _syncPrevent = ['allCounts', 'retrievedResult']
    
    after_lock: bool = False
    """Protect the :cls:`afterward` content to be overwritten. When setitem is called and completed, it will be setted as `False` automatically."""
    mute_auto_lock: bool = False
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
        readFromTarfile: bool = False,

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

        isTarfileExisted = os.path.exists(self.namingCpx.tarLocation)
        multiConfigName = self.namingCpx.exportLocation / \
            f"{self.namingCpx.expsName}.multiConfig.json"

        if isTarfileExisted:
            print(
                f"| Found the tarfile '{self.namingCpx.tarName}' in '{self.namingCpx.saveLocation}', decompressing is available.")
            if not multiConfigName.exists():
                print(
                    f"| No multiConfig file found, decompressing all files in the tarfile '{self.namingCpx.tarName}'.")
                self.easydecompress()
            elif readFromTarfile:
                print(
                    f"| Decompressing all files in the tarfile '{self.namingCpx.tarName}', replace all files in '{self.namingCpx.exportLocation}'.")
                self.easydecompress()

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
            files: dict[str, Union[str, dict[str, str]]
                        ] = rawReadMultiConfig['files']

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
            elif k == 'outfields':
                outfields = {**rawReadMultiConfig[k]}
            else:
                outfields[k] = rawReadMultiConfig[k]

        # datetimes
        if 'datetimes' not in multicommons:
            multicommons['datetimes'] = datetimeDict()
        else:
            multicommons['datetimes'] = datetimeDict(
                **multicommons['datetimes'])
        if version == 'v4':
            multicommons['datetimes']['v4Read'] = currentTime()

        if 'build' not in multicommons['datetimes'] and not isRead:
            multicommons['datetimes']['bulid'] = currentTime()

        if isTarfileExisted:
            if not multiConfigName.exists():
                multicommons['datetimes'].addSerial('decompress')
            elif readFromTarfile:
                multicommons['datetimes'].addSerial('decompressOverwrite')

        self.multicommons = self.multicommonparams(**multicommons)
        self.outfields: dict[str, Any] = outfields

        assert self.namingCpx.saveLocation == self.multicommons.saveLocation, "| saveLocation is not consistent with namingCpx.saveLocation."

    @property
    def summonerID(self) -> str:
        return self.multicommons.summonerID

    @property
    def summonerName(self) -> str:
        return self.multicommons.summonerName

    def updateSaveLocation(
        self,
        saveLocation: Union[Path, str],
        withoutSerial: bool = True,
    ) -> dict:
        saveLocation = Path(saveLocation)
        self.namingCpx = naming(
            withoutSerial=withoutSerial,
            expsName=self.multicommons.summonerName,
            saveLocation=saveLocation,
        )
        self.multicommons = self.multicommons._replace(
            saveLocation=self.namingCpx.saveLocation,
            exportLocation=self.namingCpx.exportLocation,
        )

        return self.namingCpx._asdict()

    def _writeMultiConfig(
        self,
        encoding: str = 'utf-8',
    ) -> dict[str, Any]:
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

        return multiConfig

    def write(
        self,
        saveLocation: Optional[Union[Path, str]] = None,

        indent: int = 2,
        encoding: str = 'utf-8',
        _onlyQuantity: bool = False,
    ) -> dict[str, Any]:

        self.gitignore.read(self.multicommons.exportLocation)
        print(f"| Export multimanager...")
        if saveLocation is None:
            saveLocation = self.multicommons.saveLocation
        else:
            self.updateSaveLocation(
                saveLocation=saveLocation, withoutSerial=True)

        self.gitignore.ignore('*.json')
        self.gitignore.sync('qurryinfo.json')
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
                if not k in self._syncPrevent:
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
        multiConfig = self._writeMultiConfig(encoding=encoding)

        self.gitignore.export(self.multicommons.exportLocation)

        return multiConfig

    def compress(
        self,
        compressOverwrite: bool = False,
        remainOnlyCompressed: bool = False,
    ) -> Path:

        if remainOnlyCompressed:
            self.multicommons.datetimes.addSerial('uncompressedRemove')
        multiConfig = self._writeMultiConfig()

        print(
            f"| Compress multimanager of '{self.namingCpx.expsName}'...", end='/r')
        loc = self.easycompress(overwrite=compressOverwrite)
        print(f"| Compress multimanager of '{self.namingCpx.expsName}'...done")

        if remainOnlyCompressed:
            print(
                f"| Remove uncompressed files in '{self.namingCpx.exportLocation}' ...", end='/r')
            shutil.rmtree(self.multicommons.exportLocation)
            print(
                f"| Remove uncompressed files in '{self.namingCpx.exportLocation}' ...done")

        return loc

    def easycompress(
        self,
        overwrite: bool = False,
    ) -> Path:
        """Compress the exportLocation to tar.xz.

        Args:
            overwrite (bool, optional): Reproduce all the compressed files. Defaults to False.

        Returns:
            Path: Path of the compressed file.
        """

        self.multicommons.datetimes.addSerial('compressed')
        multiConfig = self._writeMultiConfig()

        isExists = os.path.exists(self.namingCpx.tarLocation)
        if isExists and overwrite:
            os.remove(self.namingCpx.tarLocation)
            with tarfile.open(self.namingCpx.tarLocation, 'x:xz') as tar:
                tar.add(
                    self.namingCpx.exportLocation,
                    arcname=os.path.basename(self.namingCpx.exportLocation)
                )

        else:
            with tarfile.open(self.namingCpx.tarLocation, 'w:xz') as tar:
                tar.add(self.namingCpx.exportLocation, arcname=os.path.basename(
                    self.namingCpx.exportLocation))

        return self.namingCpx.tarLocation

    def easydecompress(self) -> Path:
        """Decompress the tar.xz file of experiment.

        Returns:
            Path: Path of the decompressed file.
        """

        with tarfile.open(self.namingCpx.tarLocation, 'r:xz') as tar:
            tar.extractall(self.namingCpx.saveLocation)

        return self.namingCpx.tarLocation

    @property
    def name(self) -> Hashable:
        return self.multicommons.summonerName
