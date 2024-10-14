"""
================================================================
Afterwards
(:mod:`qurry.qurrium.multimanager.afterwards`)
================================================================

"""

from pathlib import Path
from collections.abc import Hashable
from typing import Literal, Union, Optional, NamedTuple

from qiskit.result import Result

from ...capsule import quickRead
from ...capsule.mori import TagList


class After(NamedTuple):
    """`dataStateDepending` and `dataNeccessary` in V4 format."""

    retrievedResult: TagList[Hashable, Result]
    """The list of retrieved results, which multiple experiments shared."""
    allCounts: dict[str, list[dict[str, int]]]
    """The dict of all counts of each experiments."""

    @staticmethod
    def _exporting_name() -> dict[str, str]:
        """The exporting name of :cls:`After`."""
        return {
            "retrievedResult": "retrievedResult",
            "allCounts": "allCounts",
        }

    @classmethod
    def read(
        cls,
        export_location: Path,
        file_location: Optional[dict[str, Union[str, dict[str, str]]]] = None,
        version: Literal["v5", "v7"] = "v5",
    ):
        """Reads the data of :cls:`After` from the file.

        Args:
            export_location (Path): The location of exporting.
            file_location (Optional[dict[str, Union[str, dict[str, str]]]): The location of file.
            version (Literal["v5", "v7"], optional): The version of file. Defaults to "v5".

        Returns:
            After: The data of :cls:`After`.
        """

        if file_location is None:
            file_location = {}
        if version == "v7":
            real_file_location = "allCounts.json"
        else:
            assert isinstance(file_location["allCounts"], str), "allCounts must be Path"
            real_file_location = Path(file_location["allCounts"]).name
        tmp: dict[str, list[dict[str, int]]] = quickRead(
            filename=(real_file_location),
            save_location=export_location,
        )
        return cls(
            retrievedResult=TagList(),
            allCounts=tmp,
        )
