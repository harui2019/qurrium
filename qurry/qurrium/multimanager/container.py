"""
================================================================
Container (qurry.qurry.qurrium.multimanager.container)
================================================================

"""
from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, Any, Iterable
import json

from qiskit.result import Result
from qiskit.providers import Backend

from ...tools.datetime import DatetimeDict
from ...capsule import quickRead
from ...capsule.mori import TagList


class MultiCommonparams(NamedTuple):
    """Multiple jobs shared. `argsMultiMain` in V4 format."""

    summoner_id: str
    """ID of experiment of the multiManager."""
    summoner_name: str
    """Name of experiment of the multiManager."""
    tags: list[str]
    """Tags of experiment of the multiManager."""

    shots: int
    """Number of shots to run the program (default: 1024), which multiple experiments shared."""
    backend: Backend
    """Backend to execute the circuits on, which multiple experiments shared."""

    save_location: Union[Path, str]
    """Location of saving experiment."""
    export_location: Path
    """Location of exporting experiment, 
    export_location is the final result decided by experiment."""
    files: dict[str, Union[str, dict[str, str]]]

    jobstype: str
    """Type of jobs to run multiple experiments and its pending strategy.
    
    - jobstype: "local", "IBMQ", "IBM", "AWS_Bracket", "Azure_Q"
    - pendingStrategy: "default", "onetime", "each", "tags"
    """

    manager_run_args: dict[str, any]
    """Other arguments will be passed to `IBMQJobManager()`"""

    filetype: TagList._availableFileType

    # header
    datetimes: DatetimeDict

    @staticmethod
    def v5_to_v7_field():
        """The field name of :cls:`MultiCommonparams` in V5 format."""
        return {
            "summonerID": "summoner_id",
            "summonerName": "summoner_name",
            "saveLocation": "save_location",
            "exportLocation": "export_location",
            "jobsType": "jobstype",
            "manager_run_args": "manager_run_args",
        }

    @staticmethod
    def default_value():
        """These default value are used for autofill the missing value."""
        return {
            "summoner_id": "",
            "summoner_name": "",
            "tags": [],
            "shots": None,
            "backend": None,
            "save_location": "",
            "export_location": "",
            "files": {},
            "jobstype": "local",
            "manager_run_args": {},
            "filetype": "json",
            "datetimes": {},
        }

    @classmethod
    def _read_as_dict(
        cls,
        mutlticonfig_name: Union[Path, str],
        save_location: Union[Path, str],
        export_location: Union[Path, str],
        encoding: Optional[str] = None,
    ) -> dict[str, Any]:
        rawread_multiconfig = {}
        with open(mutlticonfig_name, "r", encoding=encoding) as f:
            rawread_multiconfig: dict[str, Any] = json.load(f)
        rawread_multiconfig["save_location"] = save_location
        rawread_multiconfig["export_location"] = export_location

        return rawread_multiconfig


class Before(NamedTuple):
    """`dataNeccessary` and `expsMultiMain` in V4 format."""

    exps_config: dict[str, dict[str, any]]
    """The dict of config of each experiments."""
    circuits_num: dict[str, int]
    """The map with tags of index of experiments, which multiple experiments shared."""

    pending_pool: TagList[int]
    """The pool of pending jobs, which multiple experiments shared, 
    it works only when executing experiments is remote.
    """
    circuits_map: TagList[str]
    """The map of circuits of each experiments in the index of pending, 
    which multiple experiments shared.
    """
    job_id: list[Iterable[Union[str, tuple, Hashable, None]]]
    """The list of job_id in pending, which multiple experiments shared, 
    it works only when executing experiments is remote.
    """

    job_taglist: TagList[str]
    files_taglist: TagList[str]
    index_taglist: TagList[Union[str, int]]

    @staticmethod
    def exporting_name():
        """The exporting name of :cls:`Before`."""
        return {
            "exps_config": "exps.config",
            "circuits_num": "circuitsNum",
            "pending_pool": "pendingPools",
            "circuits_map": "circuitsMap",
            "job_id": "jobID",
            "job_taglist": "job.tagList",
            "files_taglist": "files.tagList",
            "index_taglist": "index.tagList",
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
            exps_config=quickRead(
                filename=(
                    "exps.config.json"
                    if version == "v7"
                    else Path(file_location["configDict"]).name
                ),
                save_location=export_location,
            ),
            circuits_num=quickRead(
                filename=(
                    "circuitsNum.json"
                    if version == "v7"
                    else Path(file_location["circuits_num"]).name
                ),
                save_location=export_location,
            ),
            circuits_map=TagList.read(
                save_location=export_location, tagListName="circuitsMap"
            ),
            pending_pool=TagList.read(
                save_location=export_location, tagListName="pendingPools"
            ),
            job_id=quickRead(
                filename=(
                    "jobID.json"
                    if version == "v7"
                    else Path(file_location["job_id"]).name
                ),
                save_location=export_location,
            ),
            job_taglist=TagList.read(
                save_location=export_location,
                tagListName="job.tagList" if version == "v7" else "tagMapExpsID",
            ),
            files_taglist=TagList.read(
                save_location=export_location,
                tagListName="files.tagList" if version == "v7" else "tagMapFiles",
            ),
            index_taglist=TagList.read(
                save_location=export_location,
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
                save_location=export_location,
            ),
        )
