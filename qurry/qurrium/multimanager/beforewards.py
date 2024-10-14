"""
================================================================
Beforewards
(:mod:`qurry.qurry.qurrium.multimanager.beforewards`)
================================================================

"""

from pathlib import Path
from collections.abc import Hashable
from typing import Literal, Union, Optional, NamedTuple, Any

from ...capsule import quickRead
from ...capsule.mori import TagList


TagListKeyable = Union[str, tuple[str, ...], Literal["_onetime"], Hashable]
"""Type of keyable in :cls:`TagList`."""

EXPORTING_NAME = {
    "exps_config": "exps.config",
    "circuits_num": "circuitsNum",
    "pending_pool": "pendingPools",
    "circuits_map": "circuitsMap",
    "job_id": "jobID",
    "job_taglist": "job.tagList",
    "files_taglist": "files.tagList",
    "index_taglist": "index.tagList",
}


class Before(NamedTuple):
    """`dataNeccessary` and `expsMultiMain` in V4 format."""

    exps_config: dict[str, dict[str, Any]]
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
    def _exporting_name():
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
    def read(
        cls,
        export_location: Path,
        file_location: Optional[dict[str, Union[str, dict[str, str]]]] = None,
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
            assert isinstance(file_location["exps_config"], str), "ExpsConfig must be Path"
            assert isinstance(file_location["circuits_num"], str), "circuitsNum must be Path"
            assert isinstance(file_location["job_id"], str), "job_id must be Path"
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
