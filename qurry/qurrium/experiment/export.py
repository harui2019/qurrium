"""The instance for exporting data. (:mod:`qurry.qurrium.experiment.export`)"""

import os
from typing import Literal
from dataclasses import dataclass
from pathlib import Path
import json

from ...capsule import (
    quick_json_write,
    DEFAULT_ENCODING,
    DEFAULT_INDENT,
    DEFAULT_MODE,
    jsonablize,
    CustomDict,
)
from ..utils.file_structure import REQUIRED_KEYS
from ...capsule.mori import WrittenQueueUnit, WritableQueueUnit, UniversalWriterABC


class QurryInfo(CustomDict[str, dict[str, str]]):
    """The type for qurryinfo dictionary."""

    def __init__(self, *, qurryinfo_dict: dict[str, dict[str, str]] | None = None):
        if qurryinfo_dict is None:
            super().__init__()
            return

        invalid_types_1, invalid_types_2, invalid_types_3 = [], {}, {}
        for k, v in qurryinfo_dict.items():
            if not isinstance(k, str):
                invalid_types_1.append(k)
            if not isinstance(v, dict):
                invalid_types_2[k] = v
                continue
            invalid_inner_keys = [kk for kk, vv in v.items() if not isinstance(vv, str)]
            if invalid_inner_keys:
                invalid_types_3[k] = invalid_inner_keys
        if invalid_types_1 or invalid_types_2 or invalid_types_3:
            raise TypeError(
                "The qurryinfo_dict has invalid types. "
                + f"Invalid outer keys (not str): {invalid_types_1}. "
                + f"Invalid outer values (not dict): {invalid_types_2}. "
                + f"Invalid inner keys (not str): {invalid_types_3}."
            )

        missing_keys = [
            k for k, v in qurryinfo_dict.items() if not {"folder", "qurryinfo"}.issubset(v.keys())
        ]
        if missing_keys:
            raise KeyError(
                "The raw_dict has missing required keys 'folder' or 'qurryinfo' in inner dict. "
                + f"Missing keys in outer keys: {missing_keys}."
            )
        super().__init__(qurryinfo_dict)

    def export(self) -> dict[str, dict[str, str]]:
        """Export the serializable data.

        Returns:
            dict[str, dict[str, str]]: The serializable data.
        """
        return jsonablize(self)

    def write(self, save_location: Path | str) -> None:
        """Write the qurryinfo to the specified location.

        Args:
            save_location (Path | str):
                The location to save the qurryinfo.
        """
        qurryinfo_location = Path(save_location) / "qurryinfo.json"

        quick_json_write(
            content=self.export(),
            filename=qurryinfo_location,
            mode=DEFAULT_MODE,
            indent=DEFAULT_INDENT,
            encoding=DEFAULT_ENCODING,
        )

    def update_qurryinfo(self, other: "QurryInfo | dict[str, dict[str, str]]") -> None:
        """Update the qurryinfo with another dictionary.

        Args:
            other (QurryInfo | dict[str, dict[str, str]]):
                The other dictionary to update the qurryinfo.
        """

        if not isinstance(other, self.__class__):
            other = self.__class__(qurryinfo_dict=other)

        for k, v in other.items():
            if k not in self:
                self[k] = v
            else:
                self[k].update(v)

    @classmethod
    def ingest(cls, raw_dict: dict[str, dict[str, str]]):
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, dict[str, str]]):
                The raw serialized dictionary.
        """

        return cls(qurryinfo_dict=raw_dict)

    @classmethod
    def read(cls, save_location: Path | str) -> "QurryInfo":
        """Read the qurryinfo from the specified location.

        Args:
            save_location (Path | str):
                The location to read the qurryinfo.

        Returns:
            QurryInfo: The qurryinfo object.
        """
        filepath = Path(save_location) / "qurryinfo.json"
        if not os.path.exists(filepath):
            return cls()

        with open(filepath, "r", encoding=DEFAULT_ENCODING) as f:
            new_instance = json.load(f)
        return cls.ingest(new_instance)


@dataclass(frozen=True)
class Export(UniversalWriterABC):
    """Data-stored namedtuple with all experiments data which is jsonable.

    ### Single experiment:

    For the :meth:`write` function actually exports 5 different files
    respecting to `args`, `advent`, `legacy`, `tales`, and `myths` like:

    .. code-block:: python

        files = {
            'folder': './bla_exp/',
            'qurryinfo': './bla_exp/qurryinfo.json',
            'args': './bla_exp/args/id={exp_id}.args.json',
            'advent': './bla_exp/advent/id={exp_id}.advent.json',
            'legacy': './bla_exp/legacy/id={exp_id}.legacy.json',
            'tales': './bla_exp/tales/id={exp_id}.tales.json',
            'myths': './bla_exp/myths/id={exp_id}.myths.json',
        }

    which `bla_exp` is the example filename.

    ### Multi-experiment:

    If this experiment is called by
    :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`,
    then the it will be named after `summoner_name` as known as the name of
    :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.

    .. code-block:: python

        files = {
            'folder': './BLABLA_project/',
            'qurryinfo': './BLABLA_project/qurryinfo.json',
            'args': './BLABLA_project/args/index={serial}.id={exp_id}.args.json',
            'advent': './BLABLA_project/advent/index={serial}.id={exp_id}.advent.json',
            'legacy': './BLABLA_project/legacy/index={serial}.id={exp_id}.legacy.json',
            'tales': './BLABLA_project/tales/index={serial}.id={exp_id}.tales.json',
            'myths': './BLABLA_project/myths/index={serial}.id={exp_id}.myths.json',
        }

    which `BLBLA_project` is the example
    :class:`~qurry.qurrium.multimanager.multimanager.MultiManager` name
    stored at `summoner_name` in
    :class:`~qurry.qurrium.experiment.arguments.Commonparams.summoner_name`.
    At this senerio, the `exp_name` will never apply as filename.
    """

    exp_id: str
    """The id of experiment used in filenames."""
    folder: str
    """The folder of experiment."""

    def __post_init__(self):
        super().__post_init__()

        invalid_filenames = [
            unit["filename"]
            for unit in self.folder_filenames_writtens
            if self.exp_id not in unit["filename"]
        ]
        if invalid_filenames:
            raise ValueError(
                "The exp_id must be included in all filenames. "
                + f"Invalid filenames: {invalid_filenames}"
            )
        invalid_written_contents = {
            unit["filename"]: unit["written"].keys()
            for unit in self.folder_filenames_writtens
            if "files" in unit["written"]
        }
        if invalid_written_contents:
            raise ValueError(
                "The written_contents must not contain 'files' key, "
                + "which is reserved for internal use. "
                + f"Invalid written_contents: {invalid_written_contents.keys()}"
            )

    def write(self) -> tuple[str, dict[Literal["folder", "qurryinfo"] | str, str]]:
        """Export the experiment data, if there is a previous export, then will overwrite.

        Returns:
            tuple[str, dict[Literal["folder", "qurryinfo"] | str, str]]:
                The first element is the id of experiment,
                the second element is the dictionary of files of experiment.
        """

        exp_folder_path = Path(self.folder)
        abs_exp_folder_path = Path(self.save_location) / exp_folder_path
        if not os.path.exists(abs_exp_folder_path):
            os.makedirs(abs_exp_folder_path)

        files = {
            "save_location": str(self.save_location),
            "folder": exp_folder_path,
            "qurryinfo": exp_folder_path / "qurryinfo.json",
        }
        for unit in self.folder_filenames_writtens:
            unit_path = exp_folder_path / unit["folder"]
            abs_unit_path = Path(self.save_location) / unit_path
            if not os.path.exists(abs_unit_path):
                os.mkdir(abs_unit_path)
            files[unit["folder"]] = unit_path / unit["filename"]
        files_str = {k: str(v) for k, v in files.items()}

        for unit in self.folder_filenames_writtens:
            written = {"files": files_str}
            written.update(unit["written"])
            quick_json_write(
                content=written,
                filename=files[unit["folder"]],
                mode=DEFAULT_MODE,
                indent=DEFAULT_INDENT,
                encoding=DEFAULT_ENCODING,
                save_location=self.save_location,
            )

        missing_keys = REQUIRED_KEYS - set(files_str.keys())
        if missing_keys:
            raise KeyError(
                "The exported files are missing required keys. "
                + f"Required keys: {REQUIRED_KEYS}, exported keys: {files_str.keys()}."
            )

        return self.exp_id, files_str

    @classmethod
    def make(
        cls,
        identifier: str,
        save_location: Path | str,
        writable_objects_params: list[WritableQueueUnit],
        exp_id: str | None = None,
        folder: str | None = None,
    ) -> "Export":
        """Make a export object.

        Args:
            identifier (str): The identifier among multiple
                :class:`FileWritableObj` objects used in filenames.
            save_location (Path | str): The save location of multiple
                :class:`FileWritableObj` objects.
            writable_objects_params (list[WritableQueueUnit]):
                The list of writable quene units, which contains
                the :class:`FileWritableObj` objects and their extra arguments,
                stored as :class:`WritableQueneUnit`.
            exp_id (str | None, optional):
                The experiment id used in filenames. Defaults to None.
            folder (str | None, optional):
                The folder used in filenames. Defaults to None.

        Returns:
            Export: The export object.
        """
        if exp_id is None:
            raise ValueError("The exp_id must be provided for Export.")
        if folder is None:
            raise ValueError("The folder must be provided for Export.")

        folder_filenames_writtens: list[WrittenQueueUnit] = []
        for unit in writable_objects_params:
            writable = unit["file_writable_obj"]  # type: ignore
            folder_of_obj, filenames = writable.folder_and_filename(
                identifier, **unit.get("folder_and_filename_kwargs", {})
            )
            dumpings = writable.content_dumping(**unit.get("content_dumping_kwargs", {}))
            folder_filenames_writtens.append(
                {
                    "folder": folder_of_obj,
                    "filename": filenames,
                    "written": dumpings,
                }
            )

        return cls(
            identifier=identifier,
            save_location=save_location,
            folder_filenames_writtens=folder_filenames_writtens,
            exp_id=exp_id,
            folder=folder,
        )
