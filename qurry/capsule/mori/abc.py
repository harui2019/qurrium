"""The abstract base classes for JSON I/O. (:mod:`qurry.capsule.mori.abc`)"""

from typing import Any, TypeVar
from abc import abstractmethod, ABC
from pathlib import Path
from dataclasses import is_dataclass


class DataExportable(ABC):
    """The abstract base class for exporting content."""

    @abstractmethod
    def export(self) -> dict[Any, Any]:
        """Export the serializable data.

        Returns:
            dict[Any, Any]: The serializable data.
        """


_MappingLike = TypeVar("_MappingLike", bound=dict)
WrittenContentType = dict[str, _MappingLike]
"""The type for writing content dictionary."""


class FileWritableObj(DataExportable, ABC):
    """The abstract base class for exporting experiment data."""

    @classmethod
    @abstractmethod
    def folder_and_filename(cls, identifier: str) -> tuple[str, str]:
        """Get the folder name and filename with given identifier.

        Args:
            identifier (str): Identifier for the experiments.

        Returns:
            tuple[str, str]: The folder name and filename
        """

    @abstractmethod
    def content_dumping(self) -> WrittenContentType:
        """Get the content to be written to files.

        Returns:
            WrittenContentType: The content to be written to files.
        """


class DataIngestible(ABC):
    """The abstract base class for importing content."""

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]) -> Any:
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw serialized dictionary.
        """

        if is_dataclass(cls):
            return cls(**raw_dict)

        raise NotImplementedError(f"The ingest method is not implemented for {cls.__name__}.")


class FileReadableObj(DataIngestible, ABC):
    """The abstract base class for importing experiment data."""

    @classmethod
    @abstractmethod
    def content_loading(cls, raw_read: dict[str, Any]) -> Any:
        """Process the serialized content from the method :meth:`content_writing`
        Handle the raw read dictionary with specific structure,
        which is same with the one used in :meth:`FileWritableObj.content_dumping`.

        Args:
            raw_read (dict[str, Any]): The raw read dictionary.
        """

    @classmethod
    @abstractmethod
    def read(cls, file_index: dict[str, str], save_location: Path) -> Any:
        """Read the exported experiment file.

        Args:
            file_index (dict[str, str]): The index of exported experiment file.
            save_location (Path): The location of exported experiment file.
        """
        # TODO: replace return type with typing.Self when Python 3.11 is lowerest version


class DataExportableIngestible(DataExportable, DataIngestible, ABC):
    """The abstract base class for exporting content."""


class FileReadableWritableObj(FileWritableObj, FileReadableObj, ABC):
    """The abstract base class for importing and exporting experiment data."""
