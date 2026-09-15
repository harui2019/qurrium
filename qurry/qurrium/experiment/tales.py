"""The Side Product Container (:mod:`qurry.qurrium.experiment.tales`)"""

from typing import Any
import warnings
from pathlib import Path
import json

from ..utils.file_structure import (
    FOLDER_NAME_SIDE_PRODUCTS as FOLDER_NAME,
    is_old_v7_file_structure,
)
from ..exceptions import OldFormatedIncompatibleWarning, MSG_V7_FILE_FORMAT_INCOMPATIBLE
from ...capsule import jsonablize, DEFAULT_ENCODING, CustomDict
from ...capsule.mori import FileReadableWritableObj, WrittenContentType


FILENAME_TEMPLATE = "{}.tales.json"
"""Filename template for side products export."""


class Tales(CustomDict, FileReadableWritableObj):
    """A customized dictionary for storing side products.

    If you want to have some typed access,
    you can do something in the inherited class like this:

    .. code-block:: python

        class EntropyMeasureTales(Tales):
            @overload
            def __getitem__(
                self, key: Literal["unitary_operator"]
            ) -> dict[int, dict[int, list[list[complex]]]]: ...
            @overload
            def __getitem__(
                self, key: Literal["bloch_vector"]
            ) -> dict[int, dict[int, tuple[float, float, float]]]: ...
            def __getitem__(self, key: Any) -> Any:
                return super().__getitem__(key)

    """

    @classmethod
    def remain_keys(cls) -> tuple[str, ...]:
        """The keys that will be remained in the side product container,
        which denotes with the typed dictionary.
        """
        return ()

    def export(self) -> dict[str, Any]:
        """Export the side products for file writing.

        Returns:
            dict[str, Any]: The side products as a dictionary.
        """

        return jsonablize(self)

    @classmethod
    def folder_and_filename(cls, identifier: str) -> tuple[str, str]:
        """Get the folder name and filename for the given analysis ID.

        Args:
            identifier (str): Identifier for the experiments.

        Returns:
            tuple[str, str]: The folder name and filename for the experiments.
        """
        return FOLDER_NAME, FILENAME_TEMPLATE.format(identifier)

    def content_dumping(self) -> WrittenContentType[dict[str, Any]]:
        """Get the content to be written to files.

        Returns:
            WritingContentType: The content to be written to files.
        """
        return {"side_products": self.export()}

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw read dictionary.
        """
        return cls(raw_dict.items())

    @classmethod
    def content_loading(cls, raw_read: dict[str, Any]):
        """Process the serialized content from the method :meth:`content_writing`
        Handle the raw read dictionary with specific structure,
        which is same with the one used in :meth:`FileWritableObj.content_writing`.

        Args:
            raw_read (dict[str, Any]): The raw read dictionary.

        Returns:
            Tales: The side product container.
        """
        if "side_products" not in raw_read:
            raise KeyError("The 'side_products' field is missing in the raw read data.")

        side_products_dict: dict[str, Any] = raw_read["side_products"]
        return cls.ingest(side_products_dict)

    @classmethod
    def read(cls, file_index: dict[str, str], save_location: Path) -> "Tales":
        """Read the exported experiment file.

        Args:
            file_index (dict[str, str]): The index of exported experiment file.
            save_location (Path): The location of exported experiment file.

        Returns:
            Tales: The side product container.
        """
        if FOLDER_NAME not in file_index:
            if is_old_v7_file_structure(file_index):
                warnings.warn(MSG_V7_FILE_FORMAT_INCOMPATIBLE, OldFormatedIncompatibleWarning)
                return cls()
            raise KeyError(f"The '{FOLDER_NAME}' field is missing in the file index.")

        with open(save_location / file_index[FOLDER_NAME], "r", encoding=DEFAULT_ENCODING) as f:
            side_products = cls.content_loading(json.load(f))

        return cls(side_products)
