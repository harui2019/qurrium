"""The writers of JSON I/O (:mod:`qurry.capsule.mori.writers`)"""

from typing import Any, TypedDict, TypeVar
from collections.abc import Callable
from abc import abstractmethod, ABC
from pathlib import Path
from dataclasses import dataclass

from .abc import FileWritableObj, WrittenContentType


class WritableQueueUnit(TypedDict, total=False):
    """The typed dictionary for writable quene unit."""

    file_writable_obj: FileWritableObj
    """The :class:`FileWritableObj` object to be written."""
    content_dumping_kwargs: dict[str, Any]
    """The extra arguments for :meth:`FileWritableObj.content_dumping` method."""
    folder_and_filename_kwargs: dict[str, Any]
    """The extra arguments for :meth:`FileWritableObj.folder_and_filename` method."""


class WrittenQueueUnit(TypedDict):
    """The typed dictionary for writable quene unit."""

    folder: str
    """The folder name where the file is written."""
    filename: str
    """The filename where the file is written."""
    written: WrittenContentType
    """The content written to the file."""


def check_writable(writable_objects_params: list[WritableQueueUnit]):
    """Check the inputs for making export writer.

    Args:
        writable_objects_params (list[WritableQueueUnit]):
            The list of writable quene units, which contains
            the :class:`FileWritableObj` objects and their extra arguments,
            stored as :class:`WritableQueneUnit`.
    """
    invalids_writings_inputs = [
        unit for unit in writable_objects_params if "file_writable_obj" not in unit
    ]
    if invalids_writings_inputs:
        raise ValueError(
            "The writable_objects_params must be a list of WritableQueueUnit, "
            + "which is a dictionary containing necessarily 'file_writable_obj', "
            + "'content_dumping_kwargs', and 'folder_and_filename_kwargs'. "
            + f"Invalid inputs: {invalids_writings_inputs}"
        )
    invalid_writings_objs = [
        unit["file_writable_obj"]  # type: ignore
        for unit in writable_objects_params
        if not isinstance(unit["file_writable_obj"], FileWritableObj)  # type: ignore
    ]
    if invalid_writings_objs:
        raise ValueError(
            "The 'file_writable_obj' in writable_objects_params must be an instance of "
            + ":class:`FileWritableObj`. "
            + f"Invalid objects: {invalid_writings_objs}"
        )


_UW = TypeVar("_UW", bound="UniversalWriterABC")
"""Type variable for :class:`UniversalWriterABC`."""


def check_export(func: Callable[[type[_UW], str, Path | str, list[WritableQueueUnit]], _UW]):
    """The decorator for :meth:`UniversalWriterABC.make` to check inputs.

    Args:
        func (Callable): The original load function.
    """

    def wrapper(
        cls: type[_UW],
        identifier: str,
        save_location: Path | str,
        writable_objects_params: list[WritableQueueUnit],
        *args: Any,
        **kwargs: Any,
    ) -> _UW:
        """The wrapped load function including input check."""

        check_writable(writable_objects_params)
        result = func(cls, identifier, save_location, writable_objects_params, *args, **kwargs)

        return result

    # pylint: disable=protected-access
    wrapper._check_export_decorated = True  # type: ignore[attr-defined]
    # pylint: enable=protected-access

    return wrapper


@dataclass(frozen=True)
class UniversalWriterABC(ABC):
    """The writes that handle multiple file writings
    from :class:`FileWritableObj` objects.
    """

    identifier: str
    """The identifier among multiple :class:`FileWritableObj` objects used in filenames."""
    save_location: Path | str
    """The save location of multiple :class:`FileWritableObj` objects."""

    folder_filenames_writtens: list[WrittenQueueUnit]
    """The written contents of experiment used in exporting."""

    def __init_subclass__(cls, **kwargs):
        """Automatically apply decorator to make method."""
        super().__init_subclass__(**kwargs)

        if "make" in cls.__dict__:
            original_make = cls.__dict__.get("make")
            if not isinstance(original_make, classmethod):
                raise TypeError("The 'make' method must be a classmethod.")

            original_func = original_make.__func__
            if not hasattr(original_func, "_check_export_decorated"):
                decorated_func = check_export(original_func)
                setattr(cls, "make", classmethod(decorated_func))

    def __post_init__(self):
        invalids_writtens_inputs = [
            unit
            for unit in self.folder_filenames_writtens
            if (set(unit.keys()) != {"folder", "filename", "written"})
        ]
        if invalids_writtens_inputs:
            raise ValueError(
                "The folder_filenames_writtens must be a list of WrittenQueneUnit, "
                + "which is a dictionary containing 'folder', 'filename', and 'written'. "
                + f"Invalid inputs: {invalids_writtens_inputs}"
            )
        invalid_filenames = [
            unit["filename"]
            for unit in self.folder_filenames_writtens
            if self.identifier not in unit["filename"]
        ]
        if invalid_filenames:
            raise ValueError(
                "The identifier be included in all filenames. "
                + f"Invalid filenames: {invalid_filenames}"
            )

    @abstractmethod
    def write(self) -> Any:
        """Export the experiment data, if there is a previous export, then will overwrite.

        Returns:
            Any: The result of writing process.
        """

    @classmethod
    @abstractmethod
    def make(
        cls,
        identifier: str,
        save_location: Path | str,
        writable_objects_params: list[WritableQueueUnit],
    ) -> "UniversalWriterABC":
        """Make a universal writer object.

        Args:
            identifier (str): The identifier among multiple
                :class:`FileWritableObj` objects used in filenames.
            save_location (Path | str): The save location of multiple
                :class:`FileWritableObj` objects.
            writable_objects_params (list[WritableQueueUnit]):
                The list of writable quene units, which contains
                the :class:`FileWritableObj` objects and their extra arguments,
                stored as :class:`WritableQueneUnit`.

        Returns:
            UniversalWriterABC: The universal writer object.
        """
