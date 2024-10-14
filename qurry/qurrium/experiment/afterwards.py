"""
================================================================
The experiment container - afterwards
(:mod:`qurry.qurrium.experimental.afterwards`)
================================================================

"""

import json
from typing import NamedTuple, Any
from pathlib import Path

from qiskit.result import Result


class After(NamedTuple):
    """The data of experiment will be independently exported in the folder 'legacy',
    which generated after the experiment."""

    # Measurement Result
    result: list[Result]
    """Results of experiment."""
    counts: list[dict[str, int]]
    """Counts of experiment."""

    @staticmethod
    def default_value():
        """The default value of each field."""
        return {
            "result": [],
            "counts": [],
        }

    @classmethod
    def read(
        cls,
        file_index: dict[str, str],
        save_location: Path,
        encoding: str = "utf-8",
    ) -> "After":
        """Read the exported experiment file.

        Args:
            file_index (dict[str, str]): The index of exported experiment file.
            save_location (Path): The location of exported experiment file.
            encoding (str, optional): The encoding of exported experiment file. Defaults to "utf-8".

        Returns:
            tuple[dict[str, Any], "After", dict[str, Any]]:
                The experiment's arguments,
                the experiment's common parameters,
                and the experiment's side product.
        """
        raw_data = {}
        with open(save_location / file_index["legacy"], encoding=encoding) as f:
            raw_data = json.load(f)
        legacy: dict[str, Any] = raw_data["legacy"]
        for k, dv in cls.default_value().items():
            if k not in legacy:
                legacy[k] = dv

        return cls(**legacy)

    def export(
        self,
        unexports: list[str],
    ) -> dict[str, Any]:
        """Export the experiment's data after executing.

        Args:
            unexports (Optional[list[str]], optional): The list of unexported key. Defaults to None.

        Returns:
            dict[str, Any]: The experiment's data after executing.
        """
        legacy = {}
        # pylint: disable=no-member
        for k, v in self._asdict().items():
            # pylint: enable=no-member
            if k not in unexports:
                legacy[k] = v

        return legacy
