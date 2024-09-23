"""
================================================================
Arguments for MultiManager 
(:mod:`qurry.qurrium.multimanager.arguments`)
================================================================

"""

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Any, TypedDict
import json

from qiskit.providers import Backend

from ...tools.datetime import DatetimeDict
from ...declare import BaseRunArgs

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
            The field name of :cls:`MultiCommonparams` in V5 format.

    Returns:
        dict[str, Any]: The field name of :cls:`MultiCommonparams` in V7 format.
    """
    for k, nk in V5_TO_V7_FIELD.items():
        if k in rawread_multiconfig:
            rawread_multiconfig[nk] = rawread_multiconfig.pop(k)
    return rawread_multiconfig


class MultiCommonparamsRawdDict(TypedDict):
    """Default values for `MultiCommonparamsRawread`."""

    summoner_id: str
    summoner_name: str
    tags: list[str]
    shots: int
    backend: Union[Backend, str]
    save_location: Union[Path, str]
    export_location: Union[Path, str]
    files: dict[str, Union[str, dict[str, str]]]
    jobstype: PendingTargetProviderLiteral
    pending_strategy: PendingStrategyLiteral
    manager_run_args: Union[BaseRunArgs, dict[str, Any]]
    filetype: Literal["json"]
    datetimes: Union[DatetimeDict, dict[str, str]]
    outfields: dict[str, Any]


class MultiCommonparamsDict(TypedDict):
    """Default values for `MultiCommonparams`."""

    summoner_id: str
    summoner_name: str
    tags: list[str]
    shots: int
    backend: Union[Backend, str]
    save_location: Union[Path, str]
    export_location: Union[Path, str]
    files: dict[str, Union[str, dict[str, str]]]
    jobstype: PendingTargetProviderLiteral
    pending_strategy: PendingStrategyLiteral
    manager_run_args: Union[BaseRunArgs, dict[str, Any]]
    filetype: Literal["json"]
    datetimes: DatetimeDict


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
    backend: Union[Backend, str]
    """Backend to execute the circuits on, which multiple experiments shared."""

    save_location: Path
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

    manager_run_args: Union[BaseRunArgs, dict[str, Any]]
    """Other arguments will be passed to `IBMQJobManager()`"""

    filetype: Literal["json"]

    # header
    datetimes: DatetimeDict

    @staticmethod
    def default_value() -> MultiCommonparamsDict:
        """These default value are used for autofill the missing value."""
        return {
            "summoner_id": "",
            "summoner_name": "",
            "tags": [],
            "shots": -1,
            "backend": "",
            "save_location": "",
            "export_location": "",
            "files": {},
            "jobstype": "local",
            "pending_strategy": "tags",
            "manager_run_args": {},
            "filetype": "json",
            "datetimes": DatetimeDict(),
        }

    @classmethod
    def rawread(
        cls,
        mutlticonfig_name: Union[Path, str],
        save_location: Union[Path, str],
        export_location: Union[Path, str],
        encoding: Optional[str] = None,
    ) -> Union[MultiCommonparamsRawdDict, dict[str, Any]]:
        """Build `MultiCommonparams` from rawread file.

        Args:
            mutlticonfig_name (Union[Path, str]):
                The path of the rawread file.
            save_location (Union[Path, str]):
                The location of saving experiment.
            export_location (Union[Path, str]):
                The location of exporting experiment.
            encoding (Optional[str], optional):
                The encoding of the file. Defaults to None.

        Returns:
            Union[
                MultiCommonparamsRawreadDict,
                dict[str, Any]
            ]: The `MultiCommonparams` in dictionary format.
        """

        rawread_multiconfig = {}
        with open(mutlticonfig_name, "r", encoding=encoding) as f:
            rawread_multiconfig: dict[str, Any] = json.load(f)

        rawread_multiconfig = v5_to_v7_field_transpose(rawread_multiconfig)
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

    @classmethod
    def build(
        cls,
        raw_multiconfig: Union[MultiCommonparamsRawdDict, dict[str, Any]],
    ) -> tuple["MultiCommonparams", dict[str, Any]]:
        """Build `MultiCommonparams` from rawread file.

        Args:
            rawread_multiconfig (Union[MultiCommonparamsRawreadDict, dict[str, Any]]):
                The `MultiCommonparams` in dictionary format.

        Returns:
            tuple["MultiCommonparams", dict[str, Any]]: The `MultiCommonparams` and outfields.
        """

        multicommons: MultiCommonparamsDict = cls.default_value()
        outfields = {}
        for k in raw_multiconfig:
            if k in cls._fields:
                if k == "datetimes":
                    multicommons[k].loads(raw_multiconfig[k])
                else:
                    multicommons[k] = raw_multiconfig[k]
            elif k == "outfields":
                outfields = {**raw_multiconfig[k]}
            else:
                outfields[k] = raw_multiconfig[k]

        if isinstance(multicommons["save_location"], str):
            multicommons["save_location"] = Path(multicommons["save_location"])
        if isinstance(multicommons["export_location"], str):
            multicommons["export_location"] = Path(multicommons["export_location"])

        assert isinstance(
            multicommons["datetimes"], DatetimeDict
        ), "datetimes should be DatetimeDict."

        return (
            cls(
                summoner_id=multicommons["summoner_id"],
                summoner_name=multicommons["summoner_name"],
                tags=multicommons["tags"],
                shots=multicommons["shots"],
                backend=multicommons["backend"],
                save_location=multicommons["save_location"],
                export_location=multicommons["export_location"],
                files=multicommons["files"],
                jobstype=multicommons["jobstype"],
                pending_strategy=multicommons["pending_strategy"],
                manager_run_args=multicommons["manager_run_args"],
                filetype=multicommons["filetype"],
                datetimes=multicommons["datetimes"],
            ),
            outfields,
        )
