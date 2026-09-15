"""The Arguments of Experiment (:mod:`qurry.qurrium.arguments.arguments`)"""

from typing import Any, TypeVar
from pathlib import Path
from dataclasses import dataclass
import json

from .utils import (
    DataClassEssential,
    filter_deprecated_args,
    v7_to_v9_field_transpose,
    create_exp_outfields,
    raw_commons_process,
)
from .commonparams import Commonparams
from ..utils.file_structure import FOLDER_NAME_ARGS as FOLDER_NAME
from ...capsule import jsonablize, DEFAULT_ENCODING
from ...capsule.mori import FileReadableWritableObj, WrittenContentType


FILENAME_TEMPLATE = "{}.args.json"
"""Filename template for arguments and common parameters export."""


@dataclass(frozen=True)
class ArgumentsPrototype(FileReadableWritableObj, DataClassEssential):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class."""

    exp_name: str
    """Name of experiment."""

    def __post_init__(self):
        error_msg = {}
        if not isinstance(self.exp_name, str):
            error_msg["exp_name"] = f"exp_name should be a string, got {type(self.exp_name)}"

        if error_msg:
            error_details = "; ".join(f"'{field}': '{msg}'" for field, msg in error_msg.items())
            raise ValueError(f"Invalid ArgumentsPrototype: {error_details}")

    @classmethod
    def filter(cls, *args, **kwargs):
        """Filter the arguments of the experiment.

        Returns:
            tuple["ArgumentsPrototype", "Commonparams", dict[str, Any]]:
                The experiment's arguments,
                the experiment's common parameters,
                and the experiment's side product.
        """
        if len(args) > 0:
            raise ValueError("args filter can't be initialized with positional arguments.")
        infields = {}
        commonsinput = {}
        outfields = {}
        for k, v in kwargs.items():
            if k in cls.dataclass_fields():
                infields[k] = v
            elif k in Commonparams.dataclass_fields():
                commonsinput[k] = v
            else:
                outfields[k] = v

        return (cls(**infields), Commonparams(**commonsinput), outfields)

    def export(self) -> dict[str, Any]:
        """Export the experiment's arguments after serializing.

        Returns:
            dict[str, Any]: The experiment's arguments.
        """
        return jsonablize(self.asdict())

    @classmethod
    def folder_and_filename(cls, identifier: str) -> tuple[str, str]:
        """Get the folder name and filename for the given analysis ID.

        Args:
            identifier (str): Identifier for the experiments.

        Returns:
            tuple[str, str]: The folder name and filename for the experiments.
        """
        return FOLDER_NAME, FILENAME_TEMPLATE.format(identifier)

    @classmethod
    def export_outfields(cls, outfields: dict[str, Any]) -> dict[str, Any]:
        """Export the outfields of the experiment.

        Args:
            outfields (dict[str, Any]): The outfields to be exported.
        """
        return jsonablize(outfields)

    def content_dumping(
        self,
        commonparams: Commonparams | None = None,
        outfields: dict[str, Any] | None = None,
    ) -> WrittenContentType[dict[str, Any]]:
        """Get the content to be written to files.

        Returns:
            WritingContentType: The content to be written to files.
        """
        if commonparams is None:
            raise ValueError("commonparams can't be None.")
        if outfields is None:
            raise ValueError("sideproduct can't be None.")

        return {
            "arguments": self.export(),
            "commonparams": commonparams.export(),
            "outfields": self.export_outfields(outfields),
        }

    @classmethod
    def content_loading(cls, raw_read: dict[str, Any], folder_name: str | None = None):
        """Process the serialized content from the method :meth:`content_writing`

        Args:
            raw_read (dict[str, Any]): The raw read dictionary.
            folder_name (str | None): The folder name of this experiment. Defaults to None.

        Returns:
            tuple["ArgumentsPrototype", "Commonparams", dict[str, Any]]:
                The experiment's arguments,
                the experiment's common parameters,
                and the outfields of the experiment.
        """
        missing_fields = {"arguments", "commonparams", "outfields"} - set(raw_read.keys())
        if missing_fields:
            raise ValueError(
                "Invalid raw_read for ArgumentsPrototype loading. "
                + f"Missing fields: {', '.join(missing_fields)}"
            )
        data_args: dict[str, dict[str, Any]] = {
            "arguments": raw_read["arguments"],
            "commonparams": raw_read["commonparams"],
            "outfields": raw_read["outfields"],
        }

        data_args = v7_to_v9_field_transpose(data_args)
        data_args["commonparams"] = raw_commons_process(data_args["commonparams"])
        data_args["commonparams"]["folder"] = folder_name

        return (
            cls.ingest(data_args["arguments"]),
            Commonparams(**data_args["commonparams"]),
            data_args["outfields"],
        )

    @classmethod
    def read(cls, file_index: dict[str, str], save_location: Path, exp_id: str | None = None):
        """Read the exported experiment file.

        Args:
            file_index (dict[str, str]): The index of exported experiment file.
            save_location (Path): The location of exported experiment file.
            exp_id (str | None, optional): The experiment ID. Defaults to None.
        """
        if "args" not in file_index and "folder" not in file_index:
            raise KeyError("The file index does not contain 'args' or 'folder' key.")
        if exp_id is None:
            raise ValueError("exp_id must be provided to read the arguments.")

        with open(save_location / file_index["args"], "r", encoding=DEFAULT_ENCODING) as f:
            arguments, commonparams, outfields = cls.content_loading(
                json.load(f), folder_name=file_index["folder"]
            )

        assert isinstance(arguments, cls), (
            f"Expected arguments to be of type {cls}, got {type(arguments)}"
        )
        assert isinstance(commonparams, Commonparams), (
            f"Expected commonparams to be of type Commonparams, got {type(commonparams)}"
        )
        assert isinstance(outfields, dict), (
            f"Expected outfields to be of type dict, got {type(outfields)}"
        )

        if commonparams.exp_id != exp_id:
            raise ValueError(
                f"The exp_id from commonparams '{commonparams.exp_id}'"
                + f" does not match the provided exp_id '{exp_id}'."
            )

        return arguments, commonparams, outfields

    @classmethod
    def create(cls: "type[_A]", arguments: "_A | dict[str, Any]") -> "tuple[_A, dict[str, Any]]":
        """Create experiment arguments from the given arguments.

        Args:
            arguments (_A | dict[str, Any]): The arguments to be parsed.
            arguments_instance (type[_A]): The instance of the arguments class.

        Raises:
            TypeError: If the arguments is not an instance of the arguments class or a dictionary.

        Returns:
            A tuple containing the parsed arguments instance and a dictionary of deprecated fields.
        """

        if isinstance(arguments, cls):
            return arguments, {}
        if isinstance(arguments, dict):
            # pylint: disable=protected-access
            arg_parsed, arguments_deprecated = filter_deprecated_args(
                arguments, cls.dataclass_fields()
            )
            # pylint: enable=protected-access
            return cls(**arg_parsed), arguments_deprecated

        raise TypeError(f"arguments should be {cls} or dict, not {type(arguments)}")

    def _repr_short(self) -> str:
        return f"<{self.__class__.__name__}(...)>"


_A = TypeVar("_A", bound=ArgumentsPrototype)
"""Type variable for :class:`ArgumentsPrototype`."""


def create_all_arguments(
    arguments: _A | dict[str, Any],
    commonparams: Commonparams | dict[str, Any],
    outfields: dict[str, Any] | None,
    arguments_instance: type[_A],
) -> tuple[_A, Commonparams, dict[str, Any]]:
    """Create experiment arguments from the given arguments.

    Args:
        arguments (_A | dict[str, Any]):
            The arguments of the experiment.
        commonparams (Commonparams | dict[str, Any]):
            The common parameters of the experiment.
        outfields (dict[str, Any] | None):
            The outfields of the experiment.
        arguments_instance (type[_A]):
            The instance of the arguments class.

    Returns:
        The arguments of the experiment,
        the common parameters of the experiment,
        and the side product of the experiment.
    """

    the_arguments, arguments_deprecated = arguments_instance.create(arguments)
    commons, commonparams_deprecated = Commonparams.create(commonparams)
    outfields = create_exp_outfields(outfields)

    if len(arguments_deprecated):
        outfields["arguments_deprecated"] = arguments_deprecated
    if len(commonparams_deprecated):
        outfields["commonparams_deprecated"] = commonparams_deprecated

    return the_arguments, commons, outfields
