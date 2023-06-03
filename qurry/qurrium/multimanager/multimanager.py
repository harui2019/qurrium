from qiskit.result import Result
from qiskit.providers import Backend

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, Any, Iterable
from uuid import uuid4
from multiprocessing import Pool, cpu_count
from tqdm.contrib.concurrent import process_map
import os
import gc
import shutil
import json
import tqdm
import tarfile
import warnings

from ..container import ExperimentContainer, QuantityContainer
from ..experiment import ExperimentPrototype
from ..utils.iocontrol import naming
from ..utils.datetime import currentTime, datetimeDict
from ...mori import TagList, syncControl, defaultConfig
from ...mori.quick import quickJSON, quickRead
from ...exceptions import (
    QurryProtectContent,
    QurryResetAccomplished,
    QurryResetSecurityActivated
)

multicommonConfig = defaultConfig(
    name='multicommon',
    default={
        'summonerID': None,
        'summonerName': None,
        'tags': [],
        'shots': 0,
        'backend': None,
        'saveLocation': None,
        'exportLocation': None,
        'files': {},
        'jobsType': None,
        'managerRunArgs': None,
        'filetype': 'json',
        'datetimes': datetimeDict(),
    }
)


def write_caller(
    iterable: tuple[ExperimentPrototype, Union[Path, str], Hashable]
) -> tuple[Hashable, dict[str, str]]:
    experiment, saveLocation, summonerID = iterable

    return experiment.write(
        saveLocation=saveLocation,
        mute=True,
        _qurryinfo_hold_access=summonerID,
    )


class MultiManager:

    class multicommonparams(NamedTuple):
        """Multiple jobs shared. `argsMultiMain` in V4 format.
        """

        summonerID: str
        """ID of experiment of the multiManager."""
        summonerName: str
        """Name of experiment of the multiManager."""
        tags: list[str]
        """Tags of experiment of the multiManager."""

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

        expsConfig: dict[str, dict[str, any]]
        """The dict of config of each experiments."""
        circuitsNum: dict[str, int]
        """The map with tags of index of experiments, which multiple experiments shared."""

        pendingPools: TagList[int]
        """The pool of pending jobs, which multiple experiments shared, it works only when executing experiments is remote."""
        circuitsMap: TagList[str]
        """The map of circuits of each experiments in the index of pending, which multiple experiments shared."""
        jobID: list[Iterable[Union[str, tuple, Hashable, None]]]
        """The list of jobID in pending, which multiple experiments shared, it works only when executing experiments is remote."""

        jobTagList: TagList[str]
        filesTagList: TagList[str]
        indexTagList: TagList[Union[str, int]]

        @staticmethod
        def _exportingName():
            return {
                'expsConfig': 'exps.config',
                'circuitsNum': 'circuitsNum',
                'pendingPools': 'pendingPools',
                'circuitsMap': 'circuitsMap',
                'jobID': 'jobID',

                'jobTagList': 'job.tagList',
                'filesTagList': 'files.tagList',
                'indexTagList': 'index.tagList',
            }

        @classmethod
        def _read(
            cls,
            exportLocation: Path,
            fileLocation: dict[str, Union[Path, dict[str, str]]] = {},
            version: Literal['v5', 'v7'] = 'v5',
        ):

            return cls(
                expsConfig=quickRead(
                    filename=(
                        'exps.config.json' if version == 'v7'
                        else Path(fileLocation['configDict']).name
                    ),
                    saveLocation=exportLocation,
                ),

                circuitsNum=quickRead(
                    filename=(
                        'circuitsNum.json' if version == 'v7'
                        else Path(fileLocation['circuitsNum']).name
                    ),
                    saveLocation=exportLocation,
                ),
                circuitsMap=TagList.read(
                    saveLocation=exportLocation,
                    tagListName='circuitsMap'
                ),
                pendingPools=TagList.read(
                    saveLocation=exportLocation,
                    tagListName='pendingPools'
                ),
                jobID=quickRead(
                    filename=(
                        'jobID.json' if version == 'v7'
                        else Path(fileLocation['jobID']).name
                    ),
                    saveLocation=exportLocation,
                ),

                jobTagList=TagList.read(
                    saveLocation=exportLocation,
                    tagListName='job.tagList' if version == 'v7' else 'tagMapExpsID'
                ),
                filesTagList=TagList.read(
                    saveLocation=exportLocation,
                    tagListName='files.tagList' if version == 'v7' else 'tagMapFiles'
                ),
                indexTagList=TagList.read(
                    saveLocation=exportLocation,
                    tagListName='index.tagList' if version == 'v7' else 'tagMapIndex'
                ),
            )

    class after(NamedTuple):
        """`dataStateDepending` and `dataNeccessary` in V4 format."""
        retrievedResult: TagList[Result]
        """The list of retrieved results, which multiple experiments shared."""
        allCounts: dict[Hashable, list[dict[str, int]]]
        """The dict of all counts of each experiments."""

        @staticmethod
        def _exportingName():
            return {
                'retrievedResult': 'retrievedResult',
                'allCounts': 'allCounts',
            }

        @classmethod
        def _read(
            cls,
            exportLocation: Path,
            fileLocation: dict[str, Union[Path, dict[str, str]]] = {},
            version: Literal['v5', 'v7'] = 'v5',
        ):
            return cls(
                retrievedResult={},
                allCounts=quickRead(
                    filename=(
                        'allCounts.json' if version == 'v7'
                        else Path(fileLocation['allCounts']).name
                    ),
                    saveLocation=exportLocation,
                ),
            )

    def reset_afterwards(
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
            self.afterwards = self.afterwards._replace(
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

    _rjustLen = 3
    """The length of the string to be right-justified for serial number when duplicated."""
    _unexports: list[str] = ['retrievedResult']
    """The content would not be exported."""
    _syncPrevent = ['allCounts', 'retrievedResult']
    """The content would not be synchronized."""

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
        multiConfigNameV5 = self.namingCpx.exportLocation / \
            f"{self.namingCpx.expsName}.multiConfig.json"
        multiConfigNameV7 = self.namingCpx.exportLocation / \
            f"multi.config.json"
        oldFiles: dict[str, Union[str, dict[str, str]]] = {}

        if isTarfileExisted:
            print(
                f"| Found the tarfile '{self.namingCpx.tarName}' in '{self.namingCpx.saveLocation}', decompressing is available.")
            if (not multiConfigNameV5.exists()) and (not multiConfigNameV7.exists()):
                print(
                    f"| No multi.config file found, decompressing all files in the tarfile '{self.namingCpx.tarName}'.")
                self.easydecompress()
            elif readFromTarfile:
                print(
                    f"| Decompressing all files in the tarfile '{self.namingCpx.tarName}', replace all files in '{self.namingCpx.exportLocation}'.")
                self.easydecompress()

        if isRead and version == 'v5':

            if multiConfigNameV5.exists():
                print("| Found the multiConfig.json, reading in 'v5' file structure.")
                with open(multiConfigNameV5, 'r', encoding=encoding) as f:
                    rawReadMultiConfig: dict[str, Any] = json.load(f)
                    rawReadMultiConfig['saveLocation'] = self.namingCpx.saveLocation
                    rawReadMultiConfig['exportLocation'] = self.namingCpx.exportLocation
                    files: dict[str, Union[str, dict[str, str]]
                                ] = rawReadMultiConfig['files']
                    oldFiles = rawReadMultiConfig['files'].copy()

                self.beforewards = self.before._read(
                    exportLocation=self.namingCpx.exportLocation,
                    fileLocation=files,
                    version='v5'
                )
                self.afterwards = self.after._read(
                    exportLocation=self.namingCpx.exportLocation,
                    fileLocation=files,
                    version='v5'
                )
                self.quantityContainer = QuantityContainer()
                for qk in files['tagMapQuantity'].keys():
                    self.quantityContainer.read(
                        key=qk,
                        saveLocation=self.namingCpx.exportLocation,
                        tagListName=f'tagMapQuantity',
                        name=f'{self.namingCpx.expsName}.{qk}',
                    )

            elif multiConfigNameV7.exists():
                with open(multiConfigNameV7, 'r', encoding=encoding) as f:
                    rawReadMultiConfig: dict[str, Any] = json.load(f)
                    rawReadMultiConfig['saveLocation'] = self.namingCpx.saveLocation
                    rawReadMultiConfig['exportLocation'] = self.namingCpx.exportLocation
                    files: dict[str, Union[str, dict[str, str]]
                                ] = rawReadMultiConfig['files']

                self.beforewards = self.before._read(
                    exportLocation=self.namingCpx.exportLocation,
                    version='v7'
                )
                self.afterwards = self.after._read(
                    exportLocation=self.namingCpx.exportLocation,
                    version='v7'
                )
                self.quantityContainer = QuantityContainer()
                for qk in files['quantity'].keys():
                    self.quantityContainer.read(
                        key=qk,
                        saveLocation=self.namingCpx.exportLocation,
                        tagListName=f'quantity',
                        name=f'{qk}',
                    )
            else:
                print(f"| v5: {multiConfigNameV5}")
                print(f"| v7: {multiConfigNameV7}")
                raise FileNotFoundError(
                    f"Can't find the multi.config file in '{self.namingCpx.expsName}'.")

        elif isRead and version == 'v4':
            print("| Reading in 'v4' format.")
            files = {}
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
                'tags': [],
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
                expsConfig=quickRead(
                    filename=f"{self.namingCpx.expsName}.configDict.json",
                    saveLocation=self.namingCpx.exportLocation,
                ),
                circuitsNum=dataDummyJobs['circuitsNum'],
                circuitsMap=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagListName='circuitsMap'
                ),
                pendingPools=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagListName='pendingPools'
                ),
                jobID=[],

                jobTagList=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagListName='tagMapExpsID'
                ),
                filesTagList=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagListName='tagMapFiles'
                ),
                indexTagList=TagList.read(
                    saveLocation=self.namingCpx.exportLocation,
                    tagListName='tagMapIndex'
                ),
            )
            self.afterwards = self.after(
                retrievedResult={},
                allCounts={},
            )
            self.quantityContainer = QuantityContainer()
            self.quantityContainer.read(
                key='oldreport',
                saveLocation=self.namingCpx.exportLocation,
                tagListName='tagMapQuantity',
            )

        else:
            files = {}
            rawReadMultiConfig = {
                'tags': [],
                **kwargs,
                'summonerID': summonerID,
                'summonerName': self.namingCpx.expsName,
                'saveLocation': self.namingCpx.saveLocation,
                'exportLocation': self.namingCpx.exportLocation,
                'filetype': filetype,
            }
            self.beforewards = self.before(
                expsConfig={},
                circuitsNum={},
                circuitsMap=TagList(),
                pendingPools=TagList(),
                jobID=[],

                jobTagList=TagList(),
                filesTagList=TagList(),
                indexTagList=TagList(),
            )
            self.afterwards = self.after(
                retrievedResult={},
                allCounts={},
            )
            self.quantityContainer = QuantityContainer()

        # multicommon prepare
        multicommons = multicommonConfig.make()
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
            if not multiConfigNameV5.exists() or not multiConfigNameV7.exists():
                multicommons['datetimes'].addSerial('decompress')
            elif readFromTarfile:
                multicommons['datetimes'].addSerial('decompressOverwrite')

        # readV5 files re-export
        if multiConfigNameV5.exists():
            multicommons['datetimes']['v7Read'] = currentTime()
            for k, pathstr in oldFiles.items():
                multicommons['files'].pop(k, None)

        self.multicommons = self.multicommonparams(**multicommons)
        self.outfields: dict[str, Any] = outfields
        assert self.namingCpx.saveLocation == self.multicommons.saveLocation, "| saveLocation is not consistent with namingCpx.saveLocation."

        # readV5 files re-export
        if multiConfigNameV5.exists():
            print(
                f'| {self.namingCpx.expsName} auto-export in "v7" format and remove "v5" format.')
            self.write()
            removeV5Progress = tqdm.tqdm(
                oldFiles.items(),
                bar_format='| {percentage:3.0f}%[{bar}] - remove v5 - {desc} - {elapsed}',
            )
            for k, pathstr in removeV5Progress:
                if isinstance(pathstr, str):
                    removeV5Progress.set_description(f'{k}')
                    path = Path(pathstr)
                    if path.exists():
                        path.unlink()
                elif isinstance(pathstr, dict):
                    for k2, pathstr2 in pathstr.items():
                        removeV5Progress.set_description(f'{k} - {k2}')
                        path = Path(pathstr2)
                        if path.exists():
                            path.unlink()

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
        mute: bool = True,
    ) -> dict[str, Any]:
        multiConfigName = Path(self.multicommons.exportLocation) / \
            f"multi.config.json"
        self.multicommons.files['multi.config'] = str(multiConfigName)
        self.gitignore.sync('multi.config.json')
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
            mute=mute,
        )

        return multiConfig

    def write(
        self,
        saveLocation: Optional[Union[Path, str]] = None,
        wave_container: Optional[ExperimentContainer] = None,
        indent: int = 2,
        encoding: str = 'utf-8',
        workers_num: Optional[int] = None,
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

        exportingName = {
            **self.after._exportingName(),
            **self.before._exportingName()
        }

        exportProgress = tqdm.tqdm(
            self.before._fields + self.after._fields,
            desc='exporting',
            bar_format='| {n_fmt}/{total_fmt} - {desc} - {elapsed} < {remaining}',
        )

        # beforewards amd afterwards
        for i, k in enumerate(exportProgress):
            if _onlyQuantity or (k in self._unexports):
                exportProgress.set_description(
                    f'{k} as {exportingName[k]} - skip')
            elif isinstance(self[k], TagList):
                exportProgress.set_description(f'{k} as {exportingName[k]}')
                tmp: TagList = self[k]
                filename = tmp.export(
                    saveLocation=self.multicommons.exportLocation,
                    tagListName=f"{exportingName[k]}",
                    filetype=self.multicommons.filetype,
                    openArgs={
                        'mode': 'w+',
                        'encoding': encoding,
                    },
                    jsonDumpArgs={
                        'indent': indent,
                    }
                )
                self.multicommons.files[exportingName[k]] = str(filename)
                self.gitignore.sync(
                    f"{exportingName[k]}.{self.multicommons.filetype}")

            elif isinstance(self[k], (dict, list)):
                exportProgress.set_description(f'{k} as {exportingName[k]}')
                filename = Path(self.multicommons.exportLocation) / \
                    f"{exportingName[k]}.json"
                self.multicommons.files[exportingName[k]] = str(filename)
                if not k in self._syncPrevent:
                    self.gitignore.sync(f"{exportingName[k]}.json")
                quickJSON(
                    content=self[k],
                    filename=filename,
                    mode='w+',
                    jsonablize=True,
                    indent=indent,
                    encoding=encoding,
                    mute=True,
                )

            else:
                warnings.warn(
                    f"'{k}' is type '{type(self[k])}' which is not supported to export.")

            if i == len(exportProgress) - 1:
                exportProgress.set_description(f'exporting done')

        # tagMapQuantity or quantity
        self.multicommons.files['quantity'] = self.quantityContainer.write(
            saveLocation=self.multicommons.exportLocation,
            filetype=self.multicommons.filetype,
            indent=indent,
            encoding=encoding
        )
        self.gitignore.sync(
            f"*.quantity.{self.multicommons.filetype}")
        # multiConfig
        multiConfig = self._writeMultiConfig(encoding=encoding, mute=True)
        print(f"| Export multi.config.json for {self.summonerID}")

        self.gitignore.export(self.multicommons.exportLocation)

        if workers_num is None:
            workers_num = int(cpu_count() - 2)

        if wave_container is not None:
            qurryinfos = {}
            qurryinfosLoc = self.multicommons.exportLocation / 'qurryinfo.json'
            if os.path.exists(saveLocation / qurryinfosLoc):
                with open(saveLocation / qurryinfosLoc, 'r', encoding='utf-8') as f:
                    qurryinfoFound: dict[
                        str, dict[str, str]] = json.load(f)
                    qurryinfos = {**qurryinfoFound, **qurryinfos}
            
            # expConfigsProgress = tqdm.tqdm(
            #     self.beforewards.expsConfig,
            #     bar_format=(
            #         '| {n_fmt}/{total_fmt} - {desc} - {elapsed} < {remaining}'
            #     ),
            # )
            # for i, id_exec in enumerate(expConfigsProgress):
            #     expConfigsProgress.set_description(
            #         f"Multimanger experiment write: {id_exec} in {self.summonerID}.")
            #     exportExpID, exportQurryInfo = wave_container[id_exec].write(
            #         saveLocation=self.multicommons.saveLocation,
            #         mute=True,
            #         _qurryinfo_hold_access=self.summonerID,
            #     )
            #     qurryinfos[exportExpID] = exportQurryInfo
            #     if i == len(expConfigsProgress) - 1:
            #         expConfigsProgress.set_description(
            #             f"Multimanger experiment write in {self.summonerID}...done")
            print(
                f"| Export datas of {len(self.beforewards.expsConfig)} experiments for {self.summonerID}")
            exportQurryInfoItems = process_map(
                write_caller,
                [
                    (
                        wave_container[id_exec],
                        self.multicommons.saveLocation,
                        self.summonerID,
                    )
                    for id_exec in self.beforewards.expsConfig
                ],
                bar_format='| {n_fmt}/{total_fmt} {percentage:3.0f}%|{bar}| - writing... - {elapsed} < {remaining}',
                ascii=" ▖▘▝▗▚▞█"
            )
            qurryinfos = {**qurryinfos, **
                          {k: v for k, v in exportQurryInfoItems}}

            quickJSON(
                content=qurryinfos,
                filename=qurryinfosLoc,
                mode='w+',
                indent=indent,
                encoding=encoding,
                jsonablize=True,
                mute=True,
            )

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

    def analyze(
        self,
        wave_continer: ExperimentContainer,
        analysisName: str = 'report',
        noSerialize: bool = False,
        specificAnalysisArgs: dict[Hashable, Union[dict[str, Any], bool]] = {},
        **analysisArgs: Any,
    ) -> str:
        """Run the analysis for multiple experiments.

        Args:
            analysisName (str, optional):
                The name of the analysis.
                Defaults to 'report'.
            specificAnalysisArgs (dict[Hashable, dict[str, Any]], optional): 
                Specific some experiment to run the analysis arguments for each experiment.
                Defaults to {}.

        Raises:
            ValueError: No positional arguments allowed except `summonerID`.
            ValueError: summonerID not in multimanagers.
            ValueError: No counts in multimanagers, which experiments are not ready.

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """

        if len(self.afterwards.allCounts) == 0:
            raise ValueError("No counts in multimanagers.")

        idx_tagMapQ = len(self.quantityContainer)
        name = (
            analysisName if noSerialize else f"{analysisName}."+f'{idx_tagMapQ+1}'.rjust(self._rjustLen, '0'))
        self.quantityContainer[name] = TagList()

        allCountsProgressBar = tqdm.tqdm(
            self.afterwards.allCounts.keys(),
            bar_format=(
                '| {n_fmt}/{total_fmt} - Analysis: {desc} - {elapsed} < {remaining}'
            ),
        )
        for k in allCountsProgressBar:
            tqdm_handleable = wave_continer[k].tqdm_handleable

            if k in specificAnalysisArgs:
                if isinstance(specificAnalysisArgs[k], bool):
                    if specificAnalysisArgs[k] is False:
                        allCountsProgressBar.set_description(
                            f"Skipped {k} in {self.summonerID}.")
                        continue
                    else:
                        report = wave_continer[k].analyze(
                            **analysisArgs, **({'pbar': allCountsProgressBar} if tqdm_handleable else {}))
                else:
                    report = wave_continer[k].analyze(
                        **specificAnalysisArgs[k], **({'pbar': allCountsProgressBar} if tqdm_handleable else {}))
            else:
                report = wave_continer[k].analyze(
                    **analysisArgs, **({'pbar': allCountsProgressBar} if tqdm_handleable else {}))

            wave_continer[k].write(mute=True)
            main, tales = report.export()
            self.quantityContainer[name][
                wave_continer[k].commons.tags].append(main)

        self.multicommons.datetimes.addOnly(name)

        return name

    def remove_analysis(
        self,
        name: str
    ):
        """Removes the analysis.

        Args:
            name (str): The name of the analysis.
        """
        self.quantityContainer.remove(name)
        print(f"| Removing analysis: {name}")
        self.multicommons.datetimes.addOnly(f"{name}_remove")

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
