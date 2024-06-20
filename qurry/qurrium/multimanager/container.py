"""
================================================================
Container (qurry.qurry.qurrium.multimanager.container)
================================================================

"""

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, Any
import json

from qiskit.result import Result
from qiskit.providers import Backend

from ...tools.datetime import DatetimeDict
from ...capsule import quickRead
from ...capsule.mori import TagList

PendingStrategyLiteral = Literal["onetime", "each", "tags"]
"""Type of pending strategy."""
PENDING_STRATEGY: list[PendingStrategyLiteral] = ["onetime", "each", "tags"]
"""List of pending strategy."""
PendingTargetProviderLiteral = Literal["local", "IBMQ", "IBM", "Qulacs", "AWS_Bracket", "Azure_Q"]
"""Type of backend provider."""
PENDING_TARGET_PROVIDER: list[PendingTargetProviderLiteral] = [
    "IBMQ",
    "IBM",
    # "Qulacs",
    # "AWS_Bracket",
    # "Azure_Q"
]
"""List of backend provider."""


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

    jobstype: PendingTargetProviderLiteral
    """Type of jobs to run multiple experiments.
    - jobstype: "local", "IBMQ", "IBM", "AWS_Bracket", "Azure_Q"
    """
    pending_strategy: PendingStrategyLiteral
    """Type of pending strategy.
    - pendingStrategy: "default", "onetime", "each", "tags"
    """

    manager_run_args: dict[str, any]
    """Other arguments will be passed to `IBMQJobManager()`"""

    filetype: Literal["json"]

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
            "managerRunArgs": "manager_run_args",
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
            "pending_strategy": "tags",
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
        for k, nk in cls.v5_to_v7_field().items():
            if k in rawread_multiconfig:
                rawread_multiconfig[nk] = rawread_multiconfig.pop(k)
        for k, dv in cls.default_value().items():
            if k not in rawread_multiconfig:
                rawread_multiconfig[k] = dv
        rawread_multiconfig["save_location"] = save_location
        rawread_multiconfig["export_location"] = export_location

        # v6 jobstype data
        if "jobstype" in rawread_multiconfig:
            v6jobstype = rawread_multiconfig["jobstype"].split(".")
            if len(v6jobstype) == 2:
                rawread_multiconfig["jobstype"] = v6jobstype[0]
                rawread_multiconfig["pending_strategy"] = v6jobstype[1]

        return rawread_multiconfig


TagListKeyable = Union[str, tuple[str, ...], Literal["_onetime"], Hashable]
"""Type of keyable in :cls:`TagList`."""


class Before(NamedTuple):
    """`dataNeccessary` and `expsMultiMain` in V4 format."""

    exps_config: dict[str, dict[str, any]]
    """The dict of config of each experiments."""
    circuits_num: dict[str, int]
    """The map with tags of index of experiments, which multiple experiments shared."""

    pending_pool: TagList[TagListKeyable, int]
    """The pool of pending jobs, which multiple experiments shared, 
    it works only when executing experiments is remote.
    """
    circuits_map: TagList[str, int]
    """The map of circuits of each experiments in the index of pending, 
    which multiple experiments shared.
    """
    job_id: list[tuple[Optional[str], TagListKeyable]]
    """The list of job_id in pending, which multiple experiments shared, 
    it works only when executing experiments is remote.
    """

    job_taglist: TagList[TagListKeyable, str]
    files_taglist: TagList[TagListKeyable, str]
    index_taglist: TagList[TagListKeyable, Union[str, int]]

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

        if version == "v7":
            real_file_location = {
                "exps_config": "exps.config.json",
                "circuits_num": "circuitsNum.json",
                "jobID": "jobID.json",
            }
        else:
            assert isinstance(file_location["exps_config"], Path), "ExpsConfig must be Path"
            assert isinstance(file_location["circuits_num"], Path), "circuitsNum must be Path"
            assert isinstance(file_location["job_id"], Path), "job_id must be Path"
            real_file_location = {
                "exps_config": Path(file_location["exps_config"]).name,
                "circuits_num": Path(file_location["circuits_num"]).name,
                "jobID": Path(file_location["job_id"]).name,
            }

        return cls(
            exps_config=quickRead(
                filename=(real_file_location["exps_config"]),
                save_location=export_location,
            ),
            circuits_num=quickRead(
                filename=(real_file_location["circuits_num"]),
                save_location=export_location,
            ),
            circuits_map=TagList.read(save_location=export_location, taglist_name="circuitsMap"),
            pending_pool=TagList.read(save_location=export_location, taglist_name="pendingPools"),
            job_id=quickRead(
                filename=(real_file_location["jobID"]),
                save_location=export_location,
            ),
            job_taglist=TagList.read(
                save_location=export_location,
                taglist_name="job.tagList" if version == "v7" else "tagMapExpsID",
            ),
            files_taglist=TagList.read(
                save_location=export_location,
                taglist_name="files.tagList" if version == "v7" else "tagMapFiles",
            ),
            index_taglist=TagList.read(
                save_location=export_location,
                taglist_name="index.tagList" if version == "v7" else "tagMapIndex",
            ),
        )


class After(NamedTuple):
    """`dataStateDepending` and `dataNeccessary` in V4 format."""

    retrievedResult: TagList[Hashable, Result]
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
        if version == "v7":
            real_file_location = "allCounts.json"
        else:
            raw = file_location["allCounts"]
            assert isinstance(raw, Path), "allCounts must be Path"
            real_file_location = Path(raw).name
        tmp: dict[Hashable, list[dict[str, int]]] = quickRead(
            filename=(real_file_location),
            save_location=export_location,
        )
        return cls(
            retrievedResult=TagList(),
            allCounts=tmp,
        )
