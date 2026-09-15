"""MultiManager - Arguments (:mod:`qurry.qurrium.multimanager.arguments`)"""

from pathlib import Path
from typing import Literal, Any, TypedDict
from dataclasses import dataclass
import json

from qiskit.providers import Backend

from .beforewards import V7_FILE_INDEX
from ..container import BaseRunArgs
from ..arguments.utils import DataClassEssential, isvalid_exp_id, check_tags
from ...tools import DatetimeDict, backend_name_getter
from ...capsule import DEFAULT_ENCODING, jsonablize, quick_json_write, DEFAULT_MODE
from ...capsule.mori import FileReadableObj, DataExportable, WrittenContentType

PendingStrategyLiteral = Literal["onetime", "each", "tags"]
"""Type of pending strategy."""
PENDING_STRATEGY: list[PendingStrategyLiteral] = ["onetime", "each", "tags"]
"""List of pending strategy."""
PendingTargetProviderLiteral = Literal[
    "local", "IBMQ", "IBM", "IBMRuntime", "Qulacs", "AWS_Bracket", "Azure_Q"
]
"""Type of backend provider."""
PENDING_TARGET_PROVIDER: list[PendingTargetProviderLiteral] = [
    "IBMQ",
    "IBM",
    "IBMRuntime",
    # "Qulacs",
    # "AWS_Bracket",
    # "Azure_Q"
]
"""List of backend provider."""


V5_TO_V7_FIELD = {
    "summonerID": "summoner_id",
    "summonerName": "summoner_name",
    "saveLocation": "save_location",
    "exportLocation": "export_location",
    "jobsType": "jobstype",
    "managerRunArgs": "manager_run_args",
}


def v5_to_v7_field_transpose(rawread_multiconfig: dict[str, Any]) -> dict[str, Any]:
    """Transpose the field name of V5 format to V7 format.

    Args:
        rawread_multiconfig (dict[str, Any]):
            The field name of :class:`MultiCommonparams` in V5 format.

    Returns:
        dict[str, Any]: The field name of :class:`MultiCommonparams` in V7 format.
    """
    for k, nk in V5_TO_V7_FIELD.items():
        if k in rawread_multiconfig:
            rawread_multiconfig[nk] = rawread_multiconfig.pop(k)
    return rawread_multiconfig


class MultiCommonparamsDict(TypedDict):
    """Dictionary format of :class:`MultiCommonparams`."""

    summoner_id: str
    summoner_name: str
    tags: tuple | tuple[str, ...]
    shots: int
    backend: Backend | str
    save_location: Path | str
    export_location: Path | str
    files: dict[str, str | dict[str, str]]
    jobstype: PendingTargetProviderLiteral
    pending_strategy: PendingStrategyLiteral
    manager_run_args: BaseRunArgs | dict[str, Any]
    datetimes: DatetimeDict


class MultiCommonparamsRawdDict(TypedDict):
    """Rawread dictionary of :class:`MultiCommonparams`."""

    summoner_id: str
    summoner_name: str
    tags: list[str]
    shots: int
    backend: Backend | str
    save_location: Path | str
    export_location: Path | str
    files: dict[str, str | dict[str, str]]
    jobstype: PendingTargetProviderLiteral
    pending_strategy: PendingStrategyLiteral
    manager_run_args: BaseRunArgs | dict[str, Any]
    datetimes: DatetimeDict | dict[str, str]
    outfields: dict[str, Any]


@dataclass(frozen=True)
class MultiCommonparams(FileReadableObj, DataExportable, DataClassEssential):
    """Multiple jobs shared. `argsMultiMain` in V4 format."""

    summoner_id: str
    """ID of experiment of the multiManager."""
    summoner_name: str
    """Name of experiment of the multiManager."""
    tags: tuple[str, ...]
    """Tags of experiment of the multiManager."""

    shots: int
    """Number of shots to run the program (default: 1024), which multiple experiments shared."""
    backend: Backend | str
    """Backend to execute the circuits on, which multiple experiments shared."""

    save_location: Path
    """Location of saving experiment."""
    export_location: Path
    """Location of exporting experiment, 
    export_location is the final result decided by experiment."""
    files: dict[str, str | dict[str, str]]

    jobstype: PendingTargetProviderLiteral
    """Type of jobs to run multiple experiments.
    - jobstype: "local", "IBMQ", "IBM", "AWS_Bracket", "Azure_Q"
    """
    pending_strategy: PendingStrategyLiteral
    """Type of pending strategy.
    - pendingStrategy: "default", "onetime", "each", "tags"
    """

    manager_run_args: BaseRunArgs | dict[str, Any]
    """Run arguments for all experiments, which multiple experiments shared."""

    # header
    datetimes: DatetimeDict
    """The datetime of experiment."""

    def __post_init__(self):
        """Post-initialization processing for MultiCommonparams."""
        error_msg = {}
        if not isvalid_exp_id(self.summoner_id):
            error_msg["summoner_id"] = (
                f"summoner_id should be a valid experiment ID, got {self.summoner_id}."
            )
        if not isinstance(self.summoner_name, str):
            error_msg["summoner_name"] = (
                f"summoner_name should be a string, got {type(self.summoner_name)}."
            )
        if not isinstance(self.tags, tuple) or not all(
            isinstance(tag, (str, int)) for tag in self.tags
        ):
            error_msg["tags"] = f"tags should be a tuple of str or int, got {type(self.tags)}"
        if not isinstance(self.shots, int) or self.shots < 0:
            error_msg["shots"] = f"shots should be a non-negative integer, got {self.shots}."
        if not isinstance(self.backend, (str, Backend)):
            error_msg["backend"] = (
                f"backend should be a string or a Backend instance, got {type(self.backend)}."
            )
        if not isinstance(self.save_location, (str, Path)):
            error_msg["save_location"] = (
                "save_location should be a string or a Path instance,"
                + f" got {type(self.save_location)}."
            )
        if not isinstance(self.export_location, (str, Path)):
            error_msg["export_location"] = (
                "export_location should be a string or a Path instance,"
                + f" got {type(self.export_location)}."
            )
        if not isinstance(self.files, dict) or not all(
            isinstance(k, str) and isinstance(v, (str, dict)) for k, v in self.files.items()
        ):
            error_msg["files"] = (
                "files should be a dictionary with"
                + f" string keys and string or dictionary values, got {self.files}."
            )
        if not isinstance(self.datetimes, DatetimeDict):
            error_msg["datetimes"] = (
                f"datetimes should be a DatetimeDict instance, got {type(self.datetimes)}."
            )

        if error_msg:
            error_details = "; ".join(f"{field}: {msg}" for field, msg in error_msg.items())
            raise ValueError(f"Invalid MultiCommonparams initialization: {error_details}")

    @staticmethod
    def default_value() -> MultiCommonparamsDict:
        """These default value are used for autofill the missing value."""
        return {
            "summoner_id": "",
            "summoner_name": "",
            "tags": (),
            "shots": -1,
            "backend": "",
            "save_location": "",
            "export_location": "",
            "files": {},
            "jobstype": "local",
            "pending_strategy": "tags",
            "manager_run_args": {},
            "datetimes": DatetimeDict(),
        }

    @classmethod
    def content_loading(
        cls,
        raw_read: dict[str, Any],
        save_location: Path | str | None = None,
        export_location: Path | str | None = None,
    ):
        """Process the serialized content from the method :meth:`content_writing`

        Args:
            raw_read (dict[str, Any]): The raw read dictionary.
            save_location (Path | str | None):
                The location of saving experiment.
            export_location (Path | str | None):
                The location of exporting experiment.

        Returns:
            MultiCommonparams: The experiment's common parameters.
        """
        if save_location is None or export_location is None:
            raise ValueError(
                "save_location and export_location must be provided to load the common parameters."
            )

        raw_read = v5_to_v7_field_transpose(raw_read)
        missing_fields = (set(cls.default_value().keys()) | {"outfields"}) - set(raw_read.keys())
        if missing_fields:
            raise ValueError(
                "Invalid raw_read for MultiCommonparams loading. "
                + f"Missing fields: {', '.join(missing_fields)}"
            )
        outfields_raw = raw_read.pop("outfields", {})
        outfields = outfields_raw if isinstance(outfields_raw, dict) else {}

        tags = check_tags(raw_read.get("tags", ()))
        data_args = raw_read.copy()
        data_args["tags"] = tags
        for k, dv in cls.default_value().items():
            if k not in data_args:
                data_args[k] = dv

        data_args["save_location"] = Path(data_args["save_location"])
        data_args["export_location"] = Path(data_args["export_location"])

        # v6 jobstype data
        if "jobstype" in data_args:
            v6jobstype = data_args["jobstype"].split(".")
            if len(v6jobstype) == 2:
                data_args["jobstype"] = v6jobstype[0]
                data_args["pending_strategy"] = v6jobstype[1]

        data_args["datetimes"] = DatetimeDict(data_args["datetimes"])
        data_args["files"] = {
            k: v if isinstance(v, str) else {sk: Path(sv) for sk, sv in v.items()}
            for k, v in data_args["files"].items()
        }
        if set(V7_FILE_INDEX) & set(data_args["files"]):
            data_args["datetimes"].add_only("migrate_to_v15")

        return cls.ingest(data_args), outfields

    @classmethod
    def read(
        cls, file_index: dict[str, str], save_location: Path, export_location: Path | None = None
    ):
        """Read the exported experiment file.

        Args:
            file_index (dict[str, str]): The index of exported experiment file.
            save_location (Path): The location of exported experiment file.
            export_location (Path | None): The location of exported experiment file.
        """
        if "multi.config" not in file_index:
            raise KeyError("The file index does not contain 'multi.config' key.")
        if file_index["multi.config"] != "multi.config.json":
            raise ValueError("The file index 'multi.config' key must be 'multi.config.json'.")
        if export_location is None:
            raise ValueError(
                "export_location must be provided to read the multi common parameters."
            )

        # Different with other read method for using export_location
        with open(
            export_location / file_index["multi.config"], "r", encoding=DEFAULT_ENCODING
        ) as f:
            multicommons, outfields = cls.content_loading(
                json.load(f), save_location=save_location, export_location=export_location
            )

        assert isinstance(multicommons, cls), (
            f"Expected multicommons to be of type {cls}, got {type(multicommons)}"
        )
        assert isinstance(outfields, dict), (
            f"Expected outfields to be of type dict, got {type(outfields)}"
        )

        return multicommons, outfields

    @classmethod
    def create(
        cls,
        raw_multiconfig: "MultiCommonparamsRawdDict | dict[str, Any] | MultiCommonparams",
    ) -> tuple["MultiCommonparams", dict[str, Any]]:
        """Build `MultiCommonparams` from rawread file.

        Args:
            raw_multiconfig (MultiCommonparamsRawdDict | dict[str, Any] | MultiCommonparams):
                The `MultiCommonparams` in dictionary format.

        Returns:
            tuple["MultiCommonparams", dict[str, Any]]: The `MultiCommonparams` and outfields.
        """

        if isinstance(raw_multiconfig, MultiCommonparams):
            return raw_multiconfig, {}

        multicommons = cls.default_value()

        outfields_raw = raw_multiconfig.pop("outfields", {})
        outfields = outfields_raw if isinstance(outfields_raw, dict) else {}
        datetime_raw = raw_multiconfig.pop("datetimes", {})
        if isinstance(datetime_raw, dict):
            multicommons["datetimes"].loads(datetime_raw)

        for k in set(raw_multiconfig.keys()):
            if k in cls.dataclass_fields():
                multicommons[k] = raw_multiconfig.pop(k)
            else:
                outfields[k] = raw_multiconfig.pop(k)

        if isinstance(multicommons["save_location"], str):
            multicommons["save_location"] = Path(multicommons["save_location"])
        if isinstance(multicommons["export_location"], str):
            multicommons["export_location"] = Path(multicommons["export_location"])

        assert isinstance(multicommons["datetimes"], DatetimeDict), (
            "datetimes should be DatetimeDict."
        )

        return cls(
            summoner_id=multicommons["summoner_id"],
            summoner_name=multicommons["summoner_name"],
            tags=check_tags(multicommons["tags"]),
            shots=multicommons["shots"],
            backend=multicommons["backend"],
            save_location=multicommons["save_location"],
            export_location=multicommons["export_location"],
            files=multicommons["files"],
            jobstype=multicommons["jobstype"],
            pending_strategy=multicommons["pending_strategy"],
            manager_run_args=multicommons["manager_run_args"],
            datetimes=multicommons["datetimes"],
        ), outfields

    def export(self) -> dict[str, Any]:
        """Export the experiment's common parameters.

        Returns:
            dict[str, Any]: The exported common parameters.
        """

        multiconfig_name = Path(self.export_location) / "multi.config.json"
        commons_export = jsonablize(self.asdict())
        commons_export.pop("folder", None)
        commons_export["backend"] = backend_name_getter(self.backend)
        commons_export["files"]["multi.config"] = str(multiconfig_name)
        return commons_export

    def content_dumping(self, outfields: dict[str, Any] | None = None) -> WrittenContentType[Any]:
        """Get the content to be written to files.

        Returns:
            WrittenContentType: The content to be written to files.
        """
        if outfields is None:
            raise ValueError("sideproduct can't be None.")

        return {**self.export(), "outfields": outfields}

    def write(self, outfields: dict[str, Any] | None = None) -> WrittenContentType[Any]:
        """Write the content to files.

        Args:
            outfields (dict[str, Any] | None): The outfields to be written to files.
        """
        if outfields is None:
            raise ValueError("sideproduct can't be None.")

        content = self.content_dumping(outfields)
        assert "files" in content, "Exported content must contain 'files' field."
        assert "multi.config" in content["files"], (
            "Exported content's 'files' field must contain 'multi.config'."
        )
        multiconfig_name = content["files"]["multi.config"]
        quick_json_write(
            content,
            filename=multiconfig_name,
            mode=DEFAULT_MODE,
            jsonable=True,
            encoding=DEFAULT_ENCODING,
            mute=True,
        )

        return content
