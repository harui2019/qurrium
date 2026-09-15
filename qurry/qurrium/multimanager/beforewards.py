"""MultiManager - Beforewards (:mod:`qurry.qurrium.multimanager.beforewards`)"""

from typing import Literal, Any
from pathlib import Path
from dataclasses import dataclass, fields
import json

from ...capsule import (
    jsonablize,
    key_tuple_loads,
    DEFAULT_ENCODING,
    DEFAULT_INDENT,
    DEFAULT_MODE,
    quick_json_write,
)

PendingTagsType = str | tuple[str, ...] | Literal["_onetime"]
"""Type for tags in :class:`Before`."""

STANDARD_FILE_INDEX = {
    "exps.config": "exps.config.json",
    "circuits_map": "circuits_map.json",
    "pending_pool": "pending_pool.json",
    "job_group": "job_group.json",
}
"""Standard file index for beforewards export."""
V7_FILE_INDEX = {
    "exps.config": "exps.config.json",
    "circuitsNum": "circuitsNum.json",
    "pendingPools": "pendingPools.json",
    "circuitsMap": "circuitsMap.json",
    "jobID": "jobID.json",
    "job.tagList": "job.tagList.json",
    "index.tagList": "index.tagList.json",
}
"""v7 file index for beforewards export."""


@dataclass(frozen=True)
class Before:
    """The data structure stores everything before executing."""

    @property
    def fields(self) -> tuple[str, ...]:
        """The fields of arguments."""
        return tuple(self.__dict__.keys())

    @classmethod
    def dataclass_fields(cls) -> tuple[str, ...]:
        """The fields of arguments."""
        return tuple(f.name for f in fields(cls))

    def asdict(self) -> dict[str, Any]:
        """The arguments as dictionary."""
        return dict(self.__dict__)

    exps_config: dict[str, dict[str, Any]]
    """The dict of config of each experiments."""
    circuits_map: dict[str, int]
    """The map of circuits of each experiments in the index of pending, 
    which multiple experiments shared."""
    pending_pool: dict[PendingTagsType, int]
    """The pool of pending circuits, which multiple experiments shared.
    Denotes the index of circuit in the pending pool."""
    job_group: dict[PendingTagsType, list[str]]
    """The group of job ids for each experiment id."""

    def content_dumping(self) -> dict[str, Any]:
        """Get the content to be written to files.

        Returns:
            dict[str, Any]: The content to be written to files.
        """
        return {
            "exps.config": jsonablize(self.exps_config),
            "circuits_map": jsonablize(self.circuits_map),
            "pending_pool": jsonablize(self.pending_pool),
            "job_group": jsonablize(self.job_group),
        }

    def write(self, save_location: Path) -> dict[str, str]:
        """Write the beforewards data to files.

        Args:
            save_location (Path): The location of MultiManager.

        Returns:
            dict[str, str]: The index of saved files.
        """
        exported_content = self.content_dumping()
        file_index: dict[str, str] = {}

        for key, filename in STANDARD_FILE_INDEX.items():
            quick_json_write(
                exported_content[key],
                filename,
                DEFAULT_MODE,
                indent=DEFAULT_INDENT,
                encoding=DEFAULT_ENCODING,
                save_location=save_location,
                mute=True,
            )
            file_index[key] = str(Path(save_location) / filename)

        return file_index

    @classmethod
    def content_loading(cls, raw_dict: dict[str, Any]) -> dict[str, Any]:
        """Process the serialized content from the method :meth:`content_writing`
        Handle the raw read dictionary with specific structure,
        which is same with the one used in :meth:`content_dumping`.

        Args:
            raw_dict (dict[str, Any]): The raw dictionary.

        Returns:
            dict[str, Any]: The loaded content.
        """
        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise KeyError(f"The fields {missing_fields} are missing in the raw dictionary.")

        return {
            "exps_config": raw_dict["exps_config"],
            "circuits_map": raw_dict["circuits_map"],
            "pending_pool": key_tuple_loads(raw_dict["pending_pool"]),
            "job_group": key_tuple_loads(raw_dict["job_group"]),
        }

    @classmethod
    def read(cls, file_index: dict[str, str]):
        """Read the exported experiment file.

        Args:
            file_index (dict[str, str]): The index of exported experiment file.
        """

        missing_files_1 = (set(STANDARD_FILE_INDEX) & set(V7_FILE_INDEX)) - set(file_index)
        if missing_files_1:
            raise KeyError(f"The {missing_files_1} file is missing in the file index.")
        missing_files_v7 = set(V7_FILE_INDEX) - set(file_index)
        missing_files_standard = set(STANDARD_FILE_INDEX) - set(file_index)
        if len(missing_files_standard) > 0 and len(missing_files_v7) > 0:
            raise KeyError(
                "The file index is neither standard nor v7 format. "
                + f"Missing files in standard: {missing_files_standard}, "
                + f"missing files in v7: {missing_files_v7}"
            )

        raw_reads = {}
        with open(Path(file_index["exps.config"]), "r", encoding=DEFAULT_ENCODING) as f:
            raw_reads["exps_config"] = json.load(f)

        if len(missing_files_standard) > 0:
            # v7 format
            with open(Path(file_index["circuitsMap"]), "r", encoding=DEFAULT_ENCODING) as f:
                raw_reads["circuits_map"] = json.load(f)
            with open(Path(file_index["pendingPools"]), "r", encoding=DEFAULT_ENCODING) as f:
                raw_reads["pending_pool"] = json.load(f)
            with open(Path(file_index["job.tagList"]), "r", encoding=DEFAULT_ENCODING) as f:
                raw_reads["job_group"] = json.load(f)

            return cls(**cls.content_loading(raw_reads))

        with open(Path(file_index["circuits_map"]), "r", encoding=DEFAULT_ENCODING) as f:
            raw_reads["circuits_map"] = json.load(f)
        with open(Path(file_index["pending_pool"]), "r", encoding=DEFAULT_ENCODING) as f:
            raw_reads["pending_pool"] = json.load(f)
        with open(Path(file_index["job_group"]), "r", encoding=DEFAULT_ENCODING) as f:
            raw_reads["job_group"] = json.load(f)

        return cls(**cls.content_loading(raw_reads))
