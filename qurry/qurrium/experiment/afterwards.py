"""Experiment - Afterwards (:mod:`qurry.qurrium.experiment.afterwards`)"""

from typing import Any
from pathlib import Path
import warnings
from dataclasses import dataclass, fields
import gc
import json

from qiskit.result import Result
from qiskit.primitives import PrimitiveResult

from ..utils.file_structure import FOLDER_NAME_AFTERWARDS as FOLDER_NAME
from ..exceptions import ResetSecurityActivated, ResetAccomplished
from ...capsule import DEFAULT_ENCODING
from ...capsule.mori import FileReadableWritableObj, WrittenContentType


FILENAME_TEMPLATE = "{}.legacy.json"
"""Filename template for afterwards export."""


@dataclass(frozen=True)
class After(FileReadableWritableObj):
    """The data of experiment will be independently exported in the folder 'legacy',
    which generated after the experiment."""

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

    # Measurement Result
    result: list[Result]
    """Results of experiment from :class:`qiskit.result.Result`"""
    counts: list[dict[str, int]]
    """Counts of experiment from :class:`qiskit.result.Result`"""
    primitive_result: list[PrimitiveResult]
    """Primitive results of experiment from :class:`qiskit.primitives.PrimitiveResult`"""
    primitive_counts: list[dict[str, int]]
    """Primitive counts of experiment from :class:`qiskit.primitives.PrimitiveResult`"""

    @staticmethod
    def default_value():
        """The default value of each field."""
        return {"result": [], "primitive_result": [], "counts": [], "primitive_counts": []}

    @classmethod
    def folder_and_filename(cls, identifier: str) -> tuple[str, str]:
        """Get the folder name and filename for the given analysis ID.

        Args:
            identifier (str): Identifier for the experiments.

        Returns:
            tuple[str, str]: The folder name and filename for the experiments.
        """
        return FOLDER_NAME, FILENAME_TEMPLATE.format(identifier)

    def export(self) -> dict[str, list[dict[str, int]]]:
        """Export the experiment's data after executing.

        Returns:
            dict[str, list[dict[str, int]]]: The experiment's data after executing.
        """
        return {"counts": self.counts, "primitive_counts": self.primitive_counts}

    def content_dumping(self) -> WrittenContentType[dict[str, list[dict[str, int]]]]:
        """Get the content to be written to files.

        Returns:
            WrittenContentType: The content to be written to files.
        """
        return {"legacy": self.export()}

    @classmethod
    def content_loading(cls, raw_read: dict[str, Any]) -> "After":
        """Process the serialized content from the method :meth:`content_writing`
        Handle the raw read dictionary with specific structure,
        which is same with the one used in :meth:`FileWritableObj.content_writing`.

        Args:
            raw_read (dict[str, Any]): The raw read dictionary.

        Returns:
            After: The experiment's afterwards data.
        """
        if "legacy" not in raw_read:
            raise KeyError("The 'legacy' field is missing in the raw read data.")

        legacy_dict: dict[str, Any] = raw_read["legacy"]
        for k, dv in cls.default_value().items():
            if k not in legacy_dict:
                legacy_dict[k] = dv
        return cls.ingest(legacy_dict)

    @classmethod
    def read(cls, file_index: dict[str, str], save_location: Path) -> "After":
        """Read the exported experiment file.

        Args:
            file_index (dict[str, str]): The index of exported experiment file.
            save_location (Path): The location of exported experiment file.

        Returns:
            tuple[dict[str, Any], "After", dict[str, Any]]:
                The experiment's arguments,
                the experiment's common parameters,
                and the experiment's side product.
        """
        if "legacy" not in file_index:
            raise KeyError("The 'legacy' field is missing in the file index.")

        with open(save_location / file_index["legacy"], encoding=DEFAULT_ENCODING) as f:
            afterwards = cls.content_loading(json.load(f))

        return afterwards

    def clear_result(self, *, security: bool = False, mute_warning: bool = True):
        """Clear the result of experiment.

        Args:
            security (bool, optional): Security for clearing. Defaults to `False`.
            mute_warning (bool, optional): Mute the warning when clearing. Defaults to `False`.
        """

        if security and isinstance(security, bool):
            self.result.clear()
            if not mute_warning:
                warnings.warn(
                    "The result of experiment is cleared.",
                    ResetAccomplished,
                )
            gc.collect()
        else:
            warnings.warn(
                "'clear_result' is called, but does not execute to prevent executing accidentally."
                + "If you are sure to clear the result, please set .(security=True).",
                ResetSecurityActivated,
            )

    @classmethod
    def create(cls, afterwards: "After | None") -> "After":
        """Create an :class:`After` object.

        Args:
            afterwards (After | None, optional):
                The After object to create. Defaults to None.

        Raises:
            TypeError: If the 'afterwards' is not an instance of 'After' or None.

        Returns:
            After: The After object.
        """
        if afterwards is None:
            return cls(**cls.default_value())
        if isinstance(afterwards, cls):
            return afterwards

        raise TypeError("The 'afterwards' must be an instance of 'After' or None.")
