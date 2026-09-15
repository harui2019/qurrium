"""AnalysisContainer (:mod:`qurry.qurrium.experiment.analyses`)"""

from typing import Any
from pathlib import Path
import warnings
import json

from .analysis import _R
from ..utils.file_structure import FOLDER_NAME_ANALYSES as FOLDER_NAME, is_old_v7_file_structure
from ..exceptions import OldFormatedIncompatibleWarning, MSG_V7_FILE_FORMAT_INCOMPATIBLE
from ...capsule import DEFAULT_ENCODING, DEFAULT_INDENT
from ...capsule.mori import FileReadableWritableObj, WrittenContentType


FILENAME_TEMPLATE = "{}.myths.json"
"""Filename template for analyses export."""
WRITING_KEY = "reports"
"""The key in :meth:`AnalysesContainer.content_dumping`."""


class AnalysesContainer(dict[int, _R], FileReadableWritableObj):
    """A customized dictionary for storing
    :class:`~qurry.qurrium.analysis.AnalysisPrototype` objects."""

    __name__ = "AnalysesContainer"

    def __init__(self, *, analysis_instance: type[_R]):
        self.analysis_instance = analysis_instance
        super().__init__()

    def export(self):
        """Export the serializable data.

        Returns:
            dict[str, Any]: The serializable data.
        """

        return {k: v.export() for k, v in self.items()}

    @classmethod
    def folder_and_filename(cls, identifier: str) -> tuple[str, str]:
        """Get the folder name and filename for the given analysis ID.

        Args:
            identifier (str): Identifier for the experiments.

        Returns:
            tuple[str, str]: The folder name and filename for the experiments.
        """
        return FOLDER_NAME, FILENAME_TEMPLATE.format(identifier)

    def content_dumping(self) -> WrittenContentType[dict[int, dict[str, Any]]]:
        """Get the content to be written to files.

        Returns:
            WritingContentType: The content to be written to files.
        """
        return {WRITING_KEY: self.export()}

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any], analysis_instance: type[_R] | None = None):
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, Any]): The dictionary to deserialize.
            analysis_instance (type[_R] | None): The analysis instance type.

        Returns:
            The deserialized analysis instance, or None if not applicable.
        """
        if analysis_instance is None:
            raise ValueError("analysis_instance must be provided to ingest the analyses.")
        nc = cls(analysis_instance=analysis_instance)
        nc.update({int(k): analysis_instance.ingest(v) for k, v in raw_dict.items()})
        return nc

    @classmethod
    def content_loading(cls, raw_read: dict[str, Any], analysis_instance: type[_R] | None = None):
        """Process the serialized content from the method :meth:`content_writing`

        Args:
            raw_read (dict[str, Any]): The raw read dictionary.
            analysis_instance (type[_R] | None): The analysis instance type.

        Returns:
            The deserialized analysis instance, or None if not applicable.
        """
        if WRITING_KEY not in raw_read:
            raise KeyError(f"The '{WRITING_KEY}' field is missing in the raw read data.")
        if analysis_instance is None:
            raise ValueError("analysis_instance must be provided to load the analyses.")

        return cls.ingest(raw_read[WRITING_KEY], analysis_instance=analysis_instance)

    @classmethod
    def read(
        cls,
        file_index: dict[str, str],
        save_location: Path,
        analysis_instance: type[_R] | None = None,
    ):
        """Read the analysis from file index.

        Args:
            file_index (dict[str, str]): The file index.
            save_location (Path): The save location.
            analysis_instance (type[_R] | None): The analysis instance type.

        Returns:
            The analysis instances in dictionary.
        """
        if analysis_instance is None:
            raise ValueError("analysis_instance must be provided to read the analyses.")

        if FOLDER_NAME not in file_index:
            if is_old_v7_file_structure(file_index):
                warnings.warn(MSG_V7_FILE_FORMAT_INCOMPATIBLE, OldFormatedIncompatibleWarning)
                return cls(analysis_instance=analysis_instance)
            raise KeyError(f"The '{FOLDER_NAME}' field is missing in the file index.")
        if analysis_instance is None:
            raise ValueError("analysis_instance must be provided to read the analyses.")

        with open(save_location / file_index[FOLDER_NAME], "r", encoding=DEFAULT_ENCODING) as f:
            analyses_data = json.load(f)

        return cls.content_loading(analyses_data, analysis_instance=analysis_instance)

    def __repr__(self):
        inner_lines = ", ".join(f"{k}" + "{...}" for k in self.keys())
        return f"{self.__name__}(length={len(self)}, " + "{" + f"{inner_lines}" + "})"

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(f"{self.__name__}(length={len(self)}, ...)")
        else:
            with p.group(DEFAULT_INDENT, f"{self.__name__}(length={len(self)}" + ", {"):
                p.breakable()
                for i, (k, v) in enumerate(self.items()):
                    if i:
                        p.text(",")
                        p.breakable()
                    p.text(f"{k}: {v}")
                p.text("})")

    @classmethod
    def create(
        cls, reports: "AnalysesContainer[_R] | None", *, analysis_instance: type[_R]
    ) -> "AnalysesContainer[_R]":
        """Create an :class:`AnalysesContainer` from the given reports.

        Args:
            reports (AnalysesContainer[_R] | None): The reports to be parsed.
            analysis_instance (type[_R]): The analysis instance type.

        Returns:
            AnalysesContainer[_R]: The created AnalysesContainer.
        """
        if reports is None:
            return cls(analysis_instance=analysis_instance)

        if reports.analysis_instance is not analysis_instance:
            raise ValueError("The analysis instance type does not match.")

        return reports
