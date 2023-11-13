"""
================================================================
MultiManager for Qurry (:mod:`qurry.qurrium.multimanager`)
================================================================

"""
import os
import gc
import shutil
import json
import tarfile
import warnings

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, Any, Iterable
from uuid import uuid4
from tqdm.contrib.concurrent import process_map

from qiskit.result import Result
from qiskit.providers import Backend

from .container import ExperimentContainer, QuantityContainer
from .experiment import ExperimentPrototype
from .utils.iocontrol import naming
from ..tools.datetime import current_time, DatetimeDict
from ..declare.multimanager import multicommonConfig
from ..tools import qurry_progressbar, DEFAULT_POOL_SIZE
from ..capsule import quickJSON, quickRead
from ..capsule.mori import TagList, GitSyncControl
from ..exceptions import (
    QurryInvalidArgument,
    QurryProtectContent,
    QurryResetAccomplished,
    QurryResetSecurityActivated,
)


def write_caller(
    iterable: tuple[ExperimentPrototype, Union[Path, str], Hashable]
) -> tuple[Hashable, dict[str, str]]:
    """The caller of :func:`ExperimentPrototype.write` for multiprocessing.

    Args:
        iterable (tuple[ExperimentPrototype, Union[Path, str], Hashable]):
            The iterable of :func:`ExperimentPrototype.write` for multiprocessing.

            - iterable[0]: ExperimentPrototype
            - iterable[1]: saveLocation
            - iterable[2]: _qurryinfo_hold_access

    Returns:
        tuple[Hashable, dict[str, str]]: The tuple of experimentID and the dict of files.
    """
    experiment, save_location, summoner_id = iterable

    return experiment.write(
        save_location=save_location,
        mute=True,
        _qurryinfo_hold_access=summoner_id,
    )


class MultiManager:
    """The manager of multiple experiments."""

    class MultiCommonparams(NamedTuple):
        """Multiple jobs shared. `argsMultiMain` in V4 format."""

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
        """Location of exporting experiment, 
        exportLocation is the final result decided by experiment."""
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
        datetimes: DatetimeDict

    class Before(NamedTuple):
        """`dataNeccessary` and `expsMultiMain` in V4 format."""

        expsConfig: dict[str, dict[str, any]]
        """The dict of config of each experiments."""
        circuitsNum: dict[str, int]
        """The map with tags of index of experiments, which multiple experiments shared."""

        pendingPools: TagList[int]
        """The pool of pending jobs, which multiple experiments shared, 
        it works only when executing experiments is remote.
        """
        circuitsMap: TagList[str]
        """The map of circuits of each experiments in the index of pending, 
        which multiple experiments shared.
        """
        jobID: list[Iterable[Union[str, tuple, Hashable, None]]]
        """The list of jobID in pending, which multiple experiments shared, 
        it works only when executing experiments is remote.
        """

        jobTagList: TagList[str]
        filesTagList: TagList[str]
        indexTagList: TagList[Union[str, int]]

        @staticmethod
        def exporting_name():
            """The exporting name of :cls:`Before`."""
            return {
                "expsConfig": "exps.config",
                "circuitsNum": "circuitsNum",
                "pendingPools": "pendingPools",
                "circuitsMap": "circuitsMap",
                "jobID": "jobID",
                "jobTagList": "job.tagList",
                "filesTagList": "files.tagList",
                "indexTagList": "index.tagList",
            }

        @classmethod
        def _read(
            cls,
            export_location: Path,
            file_location: Optional[dict[str, Union[Path, dict[str, str]]]] = None,
            version: Literal["v5", "v7"] = "v5",
        ):
            if file_location is None:
                file_location = {}

            return cls(
                expsConfig=quickRead(
                    filename=(
                        "exps.config.json"
                        if version == "v7"
                        else Path(file_location["configDict"]).name
                    ),
                    saveLocation=export_location,
                ),
                circuitsNum=quickRead(
                    filename=(
                        "circuitsNum.json"
                        if version == "v7"
                        else Path(file_location["circuitsNum"]).name
                    ),
                    saveLocation=export_location,
                ),
                circuitsMap=TagList.read(
                    saveLocation=export_location, tagListName="circuitsMap"
                ),
                pendingPools=TagList.read(
                    saveLocation=export_location, tagListName="pendingPools"
                ),
                jobID=quickRead(
                    filename=(
                        "jobID.json"
                        if version == "v7"
                        else Path(file_location["jobID"]).name
                    ),
                    saveLocation=export_location,
                ),
                jobTagList=TagList.read(
                    saveLocation=export_location,
                    tagListName="job.tagList" if version == "v7" else "tagMapExpsID",
                ),
                filesTagList=TagList.read(
                    saveLocation=export_location,
                    tagListName="files.tagList" if version == "v7" else "tagMapFiles",
                ),
                indexTagList=TagList.read(
                    saveLocation=export_location,
                    tagListName="index.tagList" if version == "v7" else "tagMapIndex",
                ),
            )

    class After(NamedTuple):
        """`dataStateDepending` and `dataNeccessary` in V4 format."""

        retrievedResult: TagList[Result]
        """The list of retrieved results, which multiple experiments shared."""
        allCounts: dict[Hashable, list[dict[str, int]]]
        """The dict of all counts of each experiments."""

        @staticmethod
        def exporting_name() -> dict[str, str]:
            """The exporting name of :cls:`After`."""
            return {
                "retrievedResult": "retrievedResult",
                "allCounts": "allCounts",
            }

        @classmethod
        def _read(
            cls,
            export_location: Path,
            file_location: Optional[dict[str, Union[Path, dict[str, str]]]] = None,
            version: Literal["v5", "v7"] = "v5",
        ):
            if file_location is None:
                file_location = {}
            return cls(
                retrievedResult={},
                allCounts=quickRead(
                    filename=(
                        "allCounts.json"
                        if version == "v7"
                        else Path(file_location["allCounts"]).name
                    ),
                    saveLocation=export_location,
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

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be reset with positional arguments."
            )

        if security and isinstance(security, bool):
            self.afterwards = self.afterwards._replace(
                retrievedResult=TagList(), allCounts={}
            )
            gc.collect()
            if not muteWarning:
                warnings.warn("Afterwards reset accomplished.", QurryResetAccomplished)
        else:
            warnings.warn(
                "Reset does not execute to prevent executing accidentally, "
                + "if you are sure to do this, then use '.reset(security=True)'.",
                QurryResetSecurityActivated,
            )

    _rjustLen = 3
    """The length of the string to be right-justified for serial number when duplicated."""
    _unexports: list[str] = ["retrievedResult"]
    """The content would not be exported."""
    _syncPrevent = ["allCounts", "retrievedResult"]
    """The content would not be synchronized."""

    after_lock: bool = False
    """Protect the :cls:`afterward` content to be overwritten. 
    When setitem is called and completed, it will be setted as `False` automatically.
    """
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
        if key in self.Before._fields:
            self.beforewards = self.beforewards._replace(**{key: value})

        elif key in self.After._fields:
            if self.after_lock and isinstance(self.after_lock, bool):
                self.afterwards = self.afterwards._replace(**{key: value})
            else:
                raise QurryProtectContent(
                    f"Can't set value to :cls:`afterward` field {key} "
                    + "because it's locked, use `.unlock_afterward()` "
                    + "to unlock before setting item ."
                )

        else:
            raise ValueError(
                f"{key} is not a valid field of "
                + f"'{self.Before.__name__}' and '{self.After.__name__}'."
            )

        gc.collect()
        if self.after_lock is not False:
            self.after_lock = False
            if not self.mute_auto_lock:
                print(
                    "after_lock is locked automatically now, "
                    + "you can unlock by using `.unlock_afterward()` "
                    + "to set value to :cls:`afterward`."
                )
            self.mute_auto_lock = False

    def __getitem__(self, key) -> Any:
        if key in self.Before._fields:
            return getattr(self.beforewards, key)
        if key in self.After._fields:
            return getattr(self.afterwards, key)
        raise ValueError(
            f"{key} is not a valid field of '{self.Before.__name__}' and '{self.After.__name__}'."
        )

    # pylint: disable=invalid-name

    @property
    def summonerID(self) -> str:
        """ID of experiment of the MultiManager."""
        return self.multicommons.summonerID

    @property
    def summonerName(self) -> str:
        """Name of experiment of the MultiManager."""
        return self.multicommons.summonerName

    # pylint: enable=invalid-name

    quantity_container: QuantityContainer
    """The container of quantity."""

    def __init__(
        self,
        *args,
        summonerID: Hashable,
        summonerName: str,
        save_location: Union[Path, str] = Path("./"),
        is_read: bool = False,
        encoding: str = "utf-8",
        read_from_tarfile: bool = False,
        filetype: TagList._availableFileType = "json",
        version: Literal["v4", "v5"] = "v5",
        **kwargs,
    ) -> None:
        """Initialize the multi-experiment.
        (The replacement of `QurryV4._multiDataGenOrRead` in V4 format.)

        Args:
            summonerID (Hashable): ID of experiment of the MultiManager.
            summonerName (str): Name of experiment of the MultiManager.
            save_location (Union[Path, str]): Location of saving experiment.
            is_read (bool, optional): Whether read the experiment. Defaults to False.
            encoding (str, optional): The encoding of json file. Defaults to "utf-8".
            read_from_tarfile (bool, optional): Whether read from tarfile. Defaults to False.
            filetype (TagList._availableFileType, optional): The filetype of json file. Defaults to "json".
            version (Literal[&quot;v4&quot;, &quot;v5&quot;], optional): The version of json file. Defaults to "v5".
            **kwargs (Any): The other arguments of multi-experiment.

        Raises:
            ValueError: Can't be initialized with positional arguments.
            FileNotFoundError: Can't find the multi.config file.
        """

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments."
            )
        try:
            hash(summonerID)
        except TypeError:
            summonerID = None
            warnings.warn(
                "'expID' is not hashable, it will be set to generate automatically.",
                category=QurryInvalidArgument,
            )
        finally:
            if summonerID is None:
                if is_read and version == "v5":
                    summonerID = ""
                else:
                    summonerID = str(uuid4())
            else:
                ...

        self.gitignore = GitSyncControl()
        self.naming_complex = naming(
            is_read=is_read,
            exps_name=summonerName,
            save_location=save_location,
        )

        is_tarfile_existed = os.path.exists(self.naming_complex.tarLocation)
        multiconfig_name_v5 = (
            self.naming_complex.exportLocation
            / f"{self.naming_complex.expsName}.multiConfig.json"
        )
        multiconfig_name_v7 = self.naming_complex.exportLocation / "multi.config.json"
        old_files: dict[str, Union[str, dict[str, str]]] = {}

        if is_tarfile_existed:
            print(
                f"| Found the tarfile '{self.naming_complex.tarName}' "
                + f"in '{self.naming_complex.saveLocation}', decompressing is available."
            )
            if (not multiconfig_name_v5.exists()) and (
                not multiconfig_name_v7.exists()
            ):
                print(
                    "| No multi.config file found, "
                    + f"decompressing all files in the tarfile '{self.naming_complex.tarName}'."
                )
                self.easydecompress()
            elif read_from_tarfile:
                print(
                    f"| Decompressing all files in the tarfile '{self.naming_complex.tarName}'"
                    + f", replace all files in '{self.naming_complex.exportLocation}'."
                )
                self.easydecompress()

        if is_read and version == "v5":
            if multiconfig_name_v5.exists():
                print("| Found the multiConfig.json, reading in 'v5' file structure.")
                with open(multiconfig_name_v5, "r", encoding=encoding) as f:
                    rawread_multiconfig: dict[str, Any] = json.load(f)
                    rawread_multiconfig[
                        "saveLocation"
                    ] = self.naming_complex.saveLocation
                    rawread_multiconfig[
                        "exportLocation"
                    ] = self.naming_complex.exportLocation
                    files: dict[str, Union[str, dict[str, str]]] = rawread_multiconfig[
                        "files"
                    ]
                    old_files = rawread_multiconfig["files"].copy()

                self.beforewards = self.Before._read(
                    export_location=self.naming_complex.exportLocation,
                    file_location=files,
                    version="v5",
                )
                self.afterwards = self.After._read(
                    export_location=self.naming_complex.exportLocation,
                    file_location=files,
                    version="v5",
                )
                self.quantity_container = QuantityContainer()
                for qk in files["tagMapQuantity"].keys():
                    self.quantity_container.read(
                        key=qk,
                        save_location=self.naming_complex.exportLocation,
                        taglist_name="tagMapQuantity",
                        name=f"{self.naming_complex.expsName}.{qk}",
                    )

            elif multiconfig_name_v7.exists():
                with open(multiconfig_name_v7, "r", encoding=encoding) as f:
                    rawread_multiconfig: dict[str, Any] = json.load(f)
                    rawread_multiconfig[
                        "saveLocation"
                    ] = self.naming_complex.saveLocation
                    rawread_multiconfig[
                        "exportLocation"
                    ] = self.naming_complex.exportLocation
                    files: dict[str, Union[str, dict[str, str]]] = rawread_multiconfig[
                        "files"
                    ]

                self.beforewards = self.Before._read(
                    export_location=self.naming_complex.exportLocation, version="v7"
                )
                self.afterwards = self.After._read(
                    export_location=self.naming_complex.exportLocation, version="v7"
                )
                self.quantity_container = QuantityContainer()
                for qk in files["quantity"].keys():
                    self.quantity_container.read(
                        key=qk,
                        save_location=self.naming_complex.exportLocation,
                        taglist_name="quantity",
                        name=f"{qk}",
                    )
            else:
                print(f"| v5: {multiconfig_name_v5}")
                print(f"| v7: {multiconfig_name_v7}")
                raise FileNotFoundError(
                    f"Can't find the multi.config file in '{self.naming_complex.expsName}'."
                )

        elif is_read and version == "v4":
            print("| Reading in 'v4' format.")
            files = {}
            data_dummy_jobs: dict[any] = {}
            data_power_jobs_name = (
                self.naming_complex.exportLocation
                / f"{self.naming_complex.expsName}.powerJobs.json"
            )
            data_multi_jobs_name = (
                self.naming_complex.exportLocation
                / f"{self.naming_complex.expsName}.multiJobs.json"
            )

            if os.path.exists(data_power_jobs_name):
                with open(data_power_jobs_name, "r", encoding="utf-8") as the_data:
                    data_dummy_jobs = json.load(the_data)
                jobs_type = "powerJobs"

            else:
                with open(data_multi_jobs_name, "r", encoding="utf-8") as the_data:
                    data_dummy_jobs = json.load(the_data)
                jobs_type = "multiJobs"

            rawread_multiconfig = {
                "tags": [],
                **kwargs,
                "summonerID": summonerID,
                "summonerName": self.naming_complex.expsName,
                "saveLocation": self.naming_complex.saveLocation,
                "exportLocation": self.naming_complex.exportLocation,
                "filetype": filetype,
                "jobsType": jobs_type,
                "files": {
                    "v4": {
                        jobs_type: f"{self.naming_complex.expsName}.{jobs_type}.json",
                        "configDict": f"{self.naming_complex.expsName}.configDict.json",
                        "circuitsMap": f"{self.naming_complex.expsName}.circuitsMap.json",
                        "pendingPools": f"{self.naming_complex.expsName}.pendingPools.json",
                        "tagMapExpsID": f"{self.naming_complex.expsName}.tagMapExpsID.json",
                        "tagMapFiles": f"{self.naming_complex.expsName}.tagMapFiles.json",
                        "tagMapIndex": f"{self.naming_complex.expsName}.tagMapIndex.json",
                        "tagMapQuantity": f"{self.naming_complex.expsName}.tagMapQuantity.json",
                    }
                },
            }
            for k in data_dummy_jobs.keys():
                if k in self.MultiCommonparams._fields:
                    rawread_multiconfig[k] = data_dummy_jobs[k]
            self.beforewards = self.Before(
                expsConfig=quickRead(
                    filename=f"{self.naming_complex.expsName}.configDict.json",
                    saveLocation=self.naming_complex.exportLocation,
                ),
                circuitsNum=data_dummy_jobs["circuitsNum"],
                circuitsMap=TagList.read(
                    saveLocation=self.naming_complex.exportLocation,
                    tagListName="circuitsMap",
                ),
                pendingPools=TagList.read(
                    saveLocation=self.naming_complex.exportLocation,
                    tagListName="pendingPools",
                ),
                jobID=[],
                jobTagList=TagList.read(
                    saveLocation=self.naming_complex.exportLocation,
                    tagListName="tagMapExpsID",
                ),
                filesTagList=TagList.read(
                    saveLocation=self.naming_complex.exportLocation,
                    tagListName="tagMapFiles",
                ),
                indexTagList=TagList.read(
                    saveLocation=self.naming_complex.exportLocation,
                    tagListName="tagMapIndex",
                ),
            )
            self.afterwards = self.After(
                retrievedResult={},
                allCounts={},
            )
            self.quantity_container = QuantityContainer()
            self.quantity_container.read(
                key="oldreport",
                save_location=self.naming_complex.exportLocation,
                taglist_name="tagMapQuantity",
            )

        else:
            files = {}
            rawread_multiconfig = {
                "tags": [],
                **kwargs,
                "summonerID": summonerID,
                "summonerName": self.naming_complex.expsName,
                "saveLocation": self.naming_complex.saveLocation,
                "exportLocation": self.naming_complex.exportLocation,
                "filetype": filetype,
            }
            self.beforewards = self.Before(
                expsConfig={},
                circuitsNum={},
                circuitsMap=TagList(),
                pendingPools=TagList(),
                jobID=[],
                jobTagList=TagList(),
                filesTagList=TagList(),
                indexTagList=TagList(),
            )
            self.afterwards = self.After(
                retrievedResult={},
                allCounts={},
            )
            self.quantity_container = QuantityContainer()

        # multicommon prepare
        multicommons = multicommonConfig.make()
        outfields = {}
        for k in rawread_multiconfig:
            if k in self.MultiCommonparams._fields:
                multicommons[k] = rawread_multiconfig[k]
            elif k == "outfields":
                outfields = {**rawread_multiconfig[k]}
            else:
                outfields[k] = rawread_multiconfig[k]

        # datetimes
        if "datetimes" not in multicommons:
            multicommons["datetimes"] = DatetimeDict()
        else:
            multicommons["datetimes"] = DatetimeDict(**multicommons["datetimes"])
        if version == "v4":
            multicommons["datetimes"]["v4Read"] = current_time()

        if "build" not in multicommons["datetimes"] and not is_read:
            multicommons["datetimes"]["bulid"] = current_time()

        if is_tarfile_existed:
            if not multiconfig_name_v5.exists() or not multiconfig_name_v7.exists():
                multicommons["datetimes"].add_serial("decompress")
            elif read_from_tarfile:
                multicommons["datetimes"].add_serial("decompressOverwrite")

        # readV5 files re-export
        if multiconfig_name_v5.exists():
            multicommons["datetimes"]["v7Read"] = current_time()
            for k, pathstr in old_files.items():
                multicommons["files"].pop(k, None)

        self.multicommons = self.MultiCommonparams(**multicommons)
        self.outfields: dict[str, Any] = outfields
        assert (
            self.naming_complex.saveLocation == self.multicommons.saveLocation
        ), "| saveLocation is not consistent with namingCpx.saveLocation."

        # readV5 files re-export
        if multiconfig_name_v5.exists():
            print(
                f"| {self.naming_complex.expsName} auto-export "
                + 'in "v7" format and remove "v5" format.'
            )
            self.write()
            remove_v5_progress = qurry_progressbar(
                old_files.items(),
                bar_format="| {percentage:3.0f}%[{bar}] - remove v5 - {desc} - {elapsed}",
            )
            for k, pathstr in remove_v5_progress:
                if isinstance(pathstr, str):
                    remove_v5_progress.set_description_str(f"{k}")
                    path = Path(pathstr)
                    if path.exists():
                        path.unlink()
                elif isinstance(pathstr, dict):
                    for k2, pathstr2 in pathstr.items():
                        remove_v5_progress.set_description_str(f"{k} - {k2}")
                        path = Path(pathstr2)
                        if path.exists():
                            path.unlink()

    def update_save_location(
        self,
        save_location: Union[Path, str],
        without_serial: bool = True,
    ) -> dict[str, Any]:
        """Update the save location of the multi-experiment.

        Args:
            save_location (Union[Path, str]): Location of saving experiment.
            without_serial (bool, optional): Whether without serial number. Defaults to True.

        Returns:
            dict[str, Any]: The dict of multiConfig.
        """
        save_location = Path(save_location)
        self.naming_complex = naming(
            without_serial=without_serial,
            exps_name=self.multicommons.summonerName,
            save_location=save_location,
        )
        self.multicommons = self.multicommons._replace(
            saveLocation=self.naming_complex.saveLocation,
            exportLocation=self.naming_complex.exportLocation,
        )

        return self.naming_complex._asdict()

    def _write_multiconfig(
        self,
        encoding: str = "utf-8",
        mute: bool = True,
    ) -> dict[str, Any]:
        multiconfig_name = Path(self.multicommons.exportLocation) / "multi.config.json"
        self.multicommons.files["multi.config"] = str(multiconfig_name)
        self.gitignore.sync("multi.config.json")
        multiconfig = {
            **self.multicommons._asdict(),
            "outfields": self.outfields,
            "files": self.multicommons.files,
        }
        quickJSON(
            content=multiconfig,
            filename=multiconfig_name,
            mode="w+",
            jsonable=True,
            encoding=encoding,
            mute=mute,
        )

        return multiconfig

    def write(
        self,
        save_location: Optional[Union[Path, str]] = None,
        wave_container: Optional[ExperimentContainer] = None,
        indent: int = 2,
        encoding: str = "utf-8",
        workers_num: Optional[int] = None,
        _only_quantity: bool = False,
    ) -> dict[str, Any]:
        """Export the multi-experiment.

        Args:
            save_location (Union[Path, str], optional): Location of saving experiment.
                Defaults to None.
            wave_container (Optional[ExperimentContainer], optional): The container of experiments.
                Defaults to None.
            indent (int, optional): The indent of json file. Defaults to 2.
            encoding (str, optional): The encoding of json file. Defaults to "utf-8".
            workers_num (Optional[int], optional): The number of workers for multiprocessing.
                Defaults to None.
            _only_quantity (bool, optional): Whether only export quantity. Defaults to False.

        Returns:
            dict[str, Any]: The dict of multiConfig.
        """
        self.gitignore.read(self.multicommons.exportLocation)
        print("| Export multimanager...")
        if save_location is None:
            save_location = self.multicommons.saveLocation
        else:
            self.update_save_location(save_location=save_location, without_serial=True)

        self.gitignore.ignore("*.json")
        self.gitignore.sync("qurryinfo.json")
        if not os.path.exists(save_location):
            os.makedirs(save_location)
        if not os.path.exists(self.multicommons.exportLocation):
            os.makedirs(self.multicommons.exportLocation)
        self.gitignore.export(self.multicommons.exportLocation)

        exporting_name = {
            **self.After.exporting_name(),
            **self.Before.exporting_name(),
        }

        export_progress = qurry_progressbar(
            self.Before._fields + self.After._fields,
            desc="exporting",
            bar_format="qurry-barless",
        )

        # beforewards amd afterwards
        for i, k in enumerate(export_progress):
            if _only_quantity or (k in self._unexports):
                export_progress.set_description_str(
                    f"{k} as {exporting_name[k]} - skip"
                )
            elif isinstance(self[k], TagList):
                export_progress.set_description_str(f"{k} as {exporting_name[k]}")
                tmp: TagList = self[k]
                filename = tmp.export(
                    saveLocation=self.multicommons.exportLocation,
                    tagListName=f"{exporting_name[k]}",
                    filetype=self.multicommons.filetype,
                    openArgs={
                        "mode": "w+",
                        "encoding": encoding,
                    },
                    jsonDumpArgs={
                        "indent": indent,
                    },
                )
                self.multicommons.files[exporting_name[k]] = str(filename)
                self.gitignore.sync(f"{exporting_name[k]}.{self.multicommons.filetype}")

            elif isinstance(self[k], (dict, list)):
                export_progress.set_description_str(f"{k} as {exporting_name[k]}")
                filename = (
                    Path(self.multicommons.exportLocation) / f"{exporting_name[k]}.json"
                )
                self.multicommons.files[exporting_name[k]] = str(filename)
                if not k in self._syncPrevent:
                    self.gitignore.sync(f"{exporting_name[k]}.json")
                quickJSON(
                    content=self[k],
                    filename=filename,
                    mode="w+",
                    jsonable=True,
                    indent=indent,
                    encoding=encoding,
                    mute=True,
                )

            else:
                warnings.warn(
                    f"'{k}' is type '{type(self[k])}' which is not supported to export."
                )

            if i == len(export_progress) - 1:
                export_progress.set_description_str("exporting done")

        # tagMapQuantity or quantity
        self.multicommons.files["quantity"] = self.quantity_container.write(
            save_location=self.multicommons.exportLocation,
            filetype=self.multicommons.filetype,
            indent=indent,
            encoding=encoding,
        )
        self.gitignore.sync(f"*.quantity.{self.multicommons.filetype}")
        # multiConfig
        multiconfig = self._write_multiconfig(encoding=encoding, mute=True)
        print(f"| Export multi.config.json for {self.summonerID}")

        self.gitignore.export(self.multicommons.exportLocation)

        if workers_num is None:
            workers_num = DEFAULT_POOL_SIZE

        if wave_container is not None:
            qurryinfos = {}
            qurryinfos_loc = self.multicommons.exportLocation / "qurryinfo.json"
            if os.path.exists(save_location / qurryinfos_loc):
                with open(save_location / qurryinfos_loc, "r", encoding="utf-8") as f:
                    qurryinfo_found: dict[str, dict[str, str]] = json.load(f)
                    qurryinfos = {**qurryinfo_found, **qurryinfos}

            print(
                f"| Export datas of {len(self.beforewards.expsConfig)} "
                + f"experiments for {self.summonerID}"
            )
            export_qurryinfo_items = process_map(
                write_caller,
                [
                    (
                        wave_container[id_exec],
                        self.multicommons.saveLocation,
                        self.summonerID,
                    )
                    for id_exec in self.beforewards.expsConfig
                ],
                bar_format="| {n_fmt}/{total_fmt} {percentage:3.0f}%|{bar}| "
                + "- writing... - {elapsed} < {remaining}",
                ascii=" ▖▘▝▗▚▞█",
            )
            qurryinfos = {**qurryinfos, **{k: v for k, v in export_qurryinfo_items}}

            quickJSON(
                content=qurryinfos,
                filename=qurryinfos_loc,
                mode="w+",
                indent=indent,
                encoding=encoding,
                jsonable=True,
                mute=True,
            )

        return multiconfig

    def compress(
        self,
        compress_overwrite: bool = False,
        remain_only_compressed: bool = False,
    ) -> Path:
        """Compress the exportLocation to tar.xz.

        Args:
            compress_overwrite (bool, optional):
                Reproduce all the compressed files. Defaults to False.
            remain_only_compressed (bool, optional):
                Remove uncompressed files. Defaults to False.

        Returns:
            Path: Path of the compressed file.
        """

        if remain_only_compressed:
            self.multicommons.datetimes.add_serial("uncompressedRemove")
        _multiconfig = self._write_multiconfig()

        print(
            f"| Compress multimanager of '{self.naming_complex.expsName}'...", end="\r"
        )
        loc = self.easycompress(overwrite=compress_overwrite)
        print(f"| Compress multimanager of '{self.naming_complex.expsName}'...done")

        if remain_only_compressed:
            print(
                f"| Remove uncompressed files in '{self.naming_complex.exportLocation}' ...",
                end="\r",
            )
            shutil.rmtree(self.multicommons.exportLocation)
            print(
                f"| Remove uncompressed files in '{self.naming_complex.exportLocation}' ...done"
            )

        return loc

    def analyze(
        self,
        wave_continer: ExperimentContainer,
        analysis_name: str = "report",
        no_serialize: bool = False,
        specific_analysis_args: Optional[
            dict[Hashable, Union[dict[str, Any], bool]]
        ] = None,
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
        if specific_analysis_args is None:
            specific_analysis_args = {}

        if len(self.afterwards.allCounts) == 0:
            raise ValueError("No counts in multimanagers.")

        idx_tagmap_quantities = len(self.quantity_container)
        name = (
            analysis_name
            if no_serialize
            else f"{analysis_name}."
            + f"{idx_tagmap_quantities+1}".rjust(self._rjustLen, "0")
        )
        self.quantity_container[name] = TagList()

        all_counts_progress = qurry_progressbar(
            self.afterwards.allCounts.keys(),
            bar_format=(
                "| {n_fmt}/{total_fmt} - Analysis: {desc} - {elapsed} < {remaining}"
            ),
        )
        for k in all_counts_progress:
            tqdm_handleable = wave_continer[k].tqdm_handleable

            if k in specific_analysis_args:
                if isinstance(specific_analysis_args[k], bool):
                    if specific_analysis_args[k] is False:
                        all_counts_progress.set_description_str(
                            f"Skipped {k} in {self.summonerID}."
                        )
                        continue
                    report = wave_continer[k].analyze(
                        **analysisArgs,
                        **({"pbar": all_counts_progress} if tqdm_handleable else {}),
                    )
                else:
                    report = wave_continer[k].analyze(
                        **specific_analysis_args[k],
                        **({"pbar": all_counts_progress} if tqdm_handleable else {}),
                    )
            else:
                report = wave_continer[k].analyze(
                    **analysisArgs,
                    **({"pbar": all_counts_progress} if tqdm_handleable else {}),
                )

            wave_continer[k].write(mute=True)
            main, _tales = report.export()
            self.quantity_container[name][wave_continer[k].commons.tags].append(main)

        self.multicommons.datetimes.add_only(name)

        return name

    def remove_analysis(self, name: str):
        """Removes the analysis.

        Args:
            name (str): The name of the analysis.
        """
        self.quantity_container.remove(name)
        print(f"| Removing analysis: {name}")
        self.multicommons.datetimes.add_only(f"{name}_remove")

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

        self.multicommons.datetimes.add_serial("compressed")
        _multiconfig = self._write_multiconfig()

        is_exists = os.path.exists(self.naming_complex.tarLocation)
        if is_exists and overwrite:
            os.remove(self.naming_complex.tarLocation)
            with tarfile.open(self.naming_complex.tarLocation, "x:xz") as tar:
                tar.add(
                    self.naming_complex.exportLocation,
                    arcname=os.path.basename(self.naming_complex.exportLocation),
                )

        else:
            with tarfile.open(self.naming_complex.tarLocation, "w:xz") as tar:
                tar.add(
                    self.naming_complex.exportLocation,
                    arcname=os.path.basename(self.naming_complex.exportLocation),
                )

        return self.naming_complex.tarLocation

    def easydecompress(self) -> Path:
        """Decompress the tar.xz file of experiment.

        Returns:
            Path: Path of the decompressed file.
        """

        with tarfile.open(self.naming_complex.tarLocation, "r:xz") as tar:
            tar.extractall(self.naming_complex.saveLocation)

        return self.naming_complex.tarLocation

    @property
    def name(self) -> Hashable:
        """Name of experiment of the MultiManager."""
        return self.multicommons.summonerName
