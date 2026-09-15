"""The Common Parameters (:mod:`qurry.qurrium.arguments.commonparams`)"""

from typing import TypedDict, Any
from pathlib import Path
from dataclasses import dataclass

from qiskit.providers import Backend

from .utils import DataClassEssential, raw_commons_process, filter_deprecated_args, isvalid_exp_id
from ..container import BaseRunArgs, TranspileArgs, WCKeyable
from ...tools import DatetimeDict, backend_name_getter
from ...capsule import jsonablize
from ...capsule.mori import DataExportable


class CommonparamsDict(TypedDict):
    """The export dictionary of :class:`Commonparams`."""

    exp_id: str
    """ID of experiment."""
    target_keys: list[WCKeyable]
    """The target keys of experiment, 
    which is the list of key of the used waves in this experiment."""

    shots: int
    """Number of shots to run the program."""
    backend: Backend | str
    """Backend to execute the circuits on, or the backend used."""
    run_args: BaseRunArgs | dict[str, Any]
    """Arguments for :meth:`~qiskit.providers.backend.BackendV2.run`"""
    transpile_args: TranspileArgs
    """Arguments of :func:`~qiskit.compiler.transpile`."""

    tags: tuple[str, ...]
    """Tags of experiment."""

    save_location: Path | str
    """Location of saving experiment."""

    serial: int | None
    """Index of experiment in :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`."""
    summoner_id: str | None
    """ID of experiment of :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`."""
    summoner_name: str | None
    """Name of experiment of :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`."""

    datetimes: DatetimeDict
    """The datetime of experiment."""


@dataclass(frozen=True)
class Commonparams(DataExportable, DataClassEssential):
    """Construct the experiment's parameters for running."""

    exp_id: str
    """ID of experiment."""
    target_keys: list[WCKeyable]
    """The target keys of experiment, 
    which is the list of key of the used waves in this experiment."""

    # Qiskit argument of experiment.
    # Multiple jobs shared
    shots: int
    """Number of shots to run the program."""
    backend: Backend | str
    """Backend to execute the circuits on, or the backend used."""
    run_args: BaseRunArgs | dict[str, Any]
    """Arguments for :meth:`~qiskit.providers.backend.BackendV2.run`"""

    # Single job dedicated
    transpile_args: TranspileArgs
    """Arguments of :func:`~qiskit.compiler.transpile`."""

    tags: tuple[str, ...]
    """Tags of experiment."""

    # Arguments for exportation
    save_location: Path | str
    """Location of saving experiment. 
    If this experiment is called by
    :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`,
    then `adventure`, `legacy`, `tales`, and `reports` will be exported 
    to their dedicated folders in this location respectively.
    This location is the default location for it's not specific 
    where to save when call 
    :meth:`~qurry.qurrium.experiment.experiment.ExperimentPrototype.write`, 
    if does, then will be overwriten and update."""

    # Arguments for multi-experiment
    serial: int | None
    """Index of experiment in :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`."""
    summoner_id: str | None
    """ID of experiment of :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`."""
    summoner_name: str | None
    """Name of experiment of :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`."""

    # header
    datetimes: DatetimeDict
    """The datetime of experiment."""

    folder: str | None = None
    """The folder of experiment, which is set when reading the experiment from file.
    If this is None, then the experiment is newly created. Only used for internal processing.
    """

    def __post_init__(self):
        error_msg = {}
        if not isvalid_exp_id(self.exp_id):
            error_msg["exp_id"] = f"exp_id should be a UUID4 string, got {self.exp_id}"
        if not isinstance(self.target_keys, list):
            error_msg["target_keys"] = f"target_keys should be a list, got {type(self.target_keys)}"

        invalid_tartget_keys = []
        for k1 in self.target_keys:
            if isinstance(k1, (str, int)):
                continue
            if isinstance(k1, tuple) and all(isinstance(k2, (str, int)) for k2 in k1):
                continue
            invalid_tartget_keys.append(k1)
        if len(invalid_tartget_keys) > 0:
            error_msg["target_keys"] = (
                "target_keys should be a list of str, int, or tuple of str and int, "
                + f"got '{invalid_tartget_keys}' in target_keys"
            )

        if not isinstance(self.shots, int):
            error_msg["shots"] = f"shots should be an int, got {type(self.shots)}"
        if not isinstance(self.backend, (Backend, str)):
            error_msg["backend"] = f"backend should be a Backend or str, got {type(self.backend)}"
        if not isinstance(self.run_args, dict):
            error_msg["run_args"] = f"run_args should be a dict, got {type(self.run_args)}"
        if not isinstance(self.transpile_args, dict):
            error_msg["transpile_args"] = (
                f"transpile_args should be a dict, got {type(self.transpile_args)}"
            )

        if not isinstance(self.tags, tuple) or not all(
            isinstance(tag, (str, int)) for tag in self.tags
        ):
            error_msg["tags"] = f"tags should be a tuple of str or int, got {type(self.tags)}"

        if not isinstance(self.save_location, (str, Path)):
            error_msg["save_location"] = (
                f"save_location should be a str or Path, got {type(self.save_location)}"
            )
        if self.serial is not None and not isinstance(self.serial, int):
            error_msg["serial"] = f"serial should be an int or None, got {type(self.serial)}"
        if self.summoner_id is not None and not isinstance(self.summoner_id, str):
            error_msg["summoner_id"] = (
                f"summoner_id should be a str or None, got {type(self.summoner_id)}"
            )
        if self.summoner_name is not None and not isinstance(self.summoner_name, str):
            error_msg["summoner_name"] = (
                f"summoner_name should be a str or None, got {type(self.summoner_name)}"
            )
        if not isinstance(self.datetimes, DatetimeDict):
            error_msg["datetimes"] = (
                f"datetimes should be a DatetimeDict, got {type(self.datetimes)}"
            )

        if error_msg:
            error_details = "; ".join(f"{field}: {msg}" for field, msg in error_msg.items())
            raise ValueError(f"Invalid Commonparams: {error_details}")

    @staticmethod
    def default_value() -> CommonparamsDict:
        """The default value of each field."""
        return {
            "exp_id": "",
            "target_keys": [],
            "shots": -1,
            "backend": "",
            "run_args": {},
            "transpile_args": {},
            "tags": (),
            "save_location": Path("."),
            "serial": None,
            "summoner_id": None,
            "summoner_name": None,
            "datetimes": DatetimeDict(),
        }

    def export(self) -> dict[str, Any]:
        """Export the experiment's common parameters.

        Returns:
            dict[str, Any]: The exported common parameters.
        """

        commons_export = jsonablize(self.asdict())
        commons_export["backend"] = backend_name_getter(self.backend)
        commons_export.pop("folder", None)
        return commons_export

    @classmethod
    def create(
        cls, commons: "Commonparams | dict[str, Any]"
    ) -> tuple["Commonparams", dict[str, Any]]:
        """Create experiment commons from the given commons.

        Args:
            commons (Commonparams | dict[str, Any]): The commons to be parsed.

        Raises:
            TypeError: If the commons is not an instance of the commons class or a dictionary.

        Returns:
            A tuple containing the parsed commons instance and a dictionary of deprecated fields.
        """

        if isinstance(commons, cls):
            return commons, {}
        if isinstance(commons, dict):
            commons_parsed, commons_deprecated = filter_deprecated_args(
                commons, cls.dataclass_fields()
            )
            return cls(**raw_commons_process(commons_parsed)), commons_deprecated

        raise TypeError(f"commons should be {cls} or dict, not {type(commons)}")

    def _repr_short(self) -> str:
        return f"<{self.__class__.__name__}(...)>"
