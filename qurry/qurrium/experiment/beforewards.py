"""Experiment - Beforewards (:mod:`qurry.qurrium.experiment.beforewards`)"""

from typing import Any
from pathlib import Path
import warnings
import json
from dataclasses import dataclass, fields

from qiskit import QuantumCircuit

from ..container import WCKeyable
from ..utils.qasm import qasm_loads
from ..utils.file_structure import FOLDER_NAME_BEFOREWARDS as FOLDER_NAME
from ..exceptions import OldFormatedIncompatibleWarning
from ...capsule import DEFAULT_ENCODING
from ...capsule.mori import FileReadableWritableObj, WrittenContentType

V5_TO_V7_FIELD = {
    "jobID": "job_id",
    "expName": "exp_name",
    "sideProduct": "side_product",
}
DEPRECATED_PROPERTIES = ["figTranspiled", "fig_original", "exp_name"]

FILENAME_TEMPLATE = "{}.advent.json"
"""Filename template for beforewards export."""


def v5_to_v7_field_transpose(advent: dict[str, Any]) -> dict[str, Any]:
    """Transpose the v5 field to v7 field."""
    for k, nk in V5_TO_V7_FIELD.items():
        if k in advent:
            advent[nk] = advent.pop(k)
    return advent


def v7_to_v11_field_transpose(advent: dict[str, Any]) -> dict[str, Any]:
    """Transpose the v7 field to v11 field."""

    if "job_id" in advent:
        if isinstance(advent["job_id"], str):
            advent["job_id"] = [advent["job_id"]]
        elif isinstance(advent["job_id"], list):
            advent["job_id"] = advent["job_id"]
        else:
            raise TypeError("job_id must be str or list[str].")

    return advent


@dataclass(frozen=True)
class Before(FileReadableWritableObj):
    """The data of experiment will be independently exported in the folder 'advent',
    which generated before the experiment.
    """

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

    # Experiment Preparation
    target: list[tuple[WCKeyable, QuantumCircuit | str]]
    """The target circuits of experiment."""
    target_qasm: list[tuple[str, str]]
    """The OpenQASM of target circuits."""
    circuit_qasm: list[str]
    """The OpenQASM of circuits (not yet transpiled)."""
    circuit: list[QuantumCircuit]
    """The transpiled circuits of experiment."""

    # Export data
    job_id: list[str]
    """ID of job for pending on real machine (IBMQBackend)."""

    @staticmethod
    def default_value():
        """These default value are used for autofill the missing value."""
        return {
            "target": [],
            "target_qasm": [],
            "circuit": [],
            "circuit_qasm": [],
            "job_id": [],
        }

    def export(self, export_transpiled_circuit: bool = False) -> dict[str, Any]:
        """Export the experiment's data before executing.

        Args:
            export_transpiled_circuit (bool, optional):
                Whether to export the transpiled circuit as txt. Defaults to False.
                For space-saving purpose and performance improvement,
                when set to True, the transpiled circuit will be draw as txt.
                Otherwise, the circuit will be not exported but circuit qasm remains.

        Returns:
            dict[str, Any]: The exported experiment's data.
        """

        return {
            "target_qasm": self.target_qasm,
            "circuit": (
                [c.draw(output="text") for c in self.circuit] if export_transpiled_circuit else []
            ),
            "circuit_qasm": self.circuit_qasm,
            "job_id": self.job_id,
        }

    def content_dumping(
        self, export_transpiled_circuit: bool = False
    ) -> WrittenContentType[dict[str, Any]]:
        """Get the content to be written to files.

        Args:
            export_transpiled_circuit (bool, optional):
                Whether to export the transpiled circuit as txt. Defaults to False.
                For space-saving purpose and performance improvement,
                when set to True, the transpiled circuit will be draw as txt.
                Otherwise, the circuit will be not exported but circuit qasm remains.

        Returns:
            WrittenContentType: The content to be written to files.
        """
        return {"advent": self.export(export_transpiled_circuit=export_transpiled_circuit)}

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Load the experiment's arguments from a dictionary.

        Args:
            data (dict[str, Any]): The data to load.

        Returns:
            Before: The experiment's beforewards data.
        """

        for k in DEPRECATED_PROPERTIES:
            raw_dict.pop(k, None)
        raw_dict = v5_to_v7_field_transpose(raw_dict)
        raw_dict = v7_to_v11_field_transpose(raw_dict)
        raw_dict = {**cls.default_value(), **raw_dict}
        return cls(**raw_dict)

    @classmethod
    def content_loading(cls, raw_read: dict[str, Any]):
        """Process the serialized content from the method :meth:`content_writing`
        Handle the raw read dictionary with specific structure,
        which is same with the one used in :meth:`FileWritableObj.content_writing`.

        Args:
            raw_read (dict[str, Any]): The raw read dictionary.

        Returns:
            Before: The experiment's beforewards data.
        """
        if "adventures" in raw_read:
            warnings.warn("Reading old format 'adventures' field", OldFormatedIncompatibleWarning)
            raw_read["advent"] = raw_read.pop("adventures")

        if "advent" not in raw_read:
            raise KeyError("The 'advent' field is missing in the raw read data.")
        if not isinstance(raw_read["advent"], dict):
            raise TypeError("The 'advent' field must be a dictionary.")

        advent_dict: dict[str, Any] = raw_read["advent"]
        for k, dv in cls.default_value().items():
            if k not in advent_dict:
                advent_dict[k] = dv
        return cls.ingest(advent_dict)

    @classmethod
    def read(cls, file_index: dict[str, str], save_location: Path) -> "Before":
        """Read the exported experiment file.

        Args:
            file_index (dict[str, str]): The index of exported experiment file.
            save_location (Path): The location of exported experiment file.

        Returns:
            Before: The experiment's beforewards data.
        """

        with open(save_location / file_index["advent"], "r", encoding=DEFAULT_ENCODING) as f:
            advent = cls.content_loading(json.load(f))

        return advent

    @classmethod
    def folder_and_filename(cls, identifier: str) -> tuple[str, str]:
        """Get the folder name and filename for the given analysis ID.

        Args:
            identifier (str): Identifier for the experiments.

        Returns:
            tuple[str, str]: The folder name and filename for the experiments.
        """
        return FOLDER_NAME, FILENAME_TEMPLATE.format(identifier)

    def revive_circuit(self, replace_circuits: bool = False) -> list[QuantumCircuit]:
        """Revive the circuit from the qasm, return the revived circuits.

        Args:
            replace_circuits (bool, optional): Whether to replace the circuits. Defaults to False.

        Raises:
            ValueError: If the .circuit is not empty.

        Returns:
            list[QuantumCircuit]: The revived circuits.
        """
        revived_circuits = []
        if len(self.circuit) != 0:
            if replace_circuits:
                self.circuit.clear()
            else:
                raise ValueError(".circuit is not empty.")
        is_none_circuits = []
        for i, qasm in enumerate(self.circuit_qasm):
            tmp_circ = qasm_loads(qasm)
            revived_circuits.append(tmp_circ)
            if tmp_circ is None:
                is_none_circuits.append(i)
        if len(is_none_circuits) != 0:
            warnings.warn(f"The circuits with indices {is_none_circuits} are not revived.")
        return revived_circuits

    def revive_target(self, replace_target: bool = False) -> dict[WCKeyable, QuantumCircuit]:
        """Revive the target circuits from the qasm, return the revived target.

        Args:
            replace_target (bool, optional):
                Whether to replace the target circuits. Defaults to False.

        Raises:
            ValueError: If the .target is not empty.

        Returns:
            dict[WCKeyable, QuantumCircuit]: The revived target circuits.
        """
        revived_target = {}
        if len(self.target) != 0:
            if replace_target:
                self.target.clear()
            else:
                raise ValueError("The target is not empty.")
        for key, qasm in self.target_qasm:
            revived_target[key] = QuantumCircuit.from_qasm_str(qasm)
        return revived_target

    @classmethod
    def create(cls, beforewards: "Before | None") -> "Before":
        """Create a :class:`Before` object.

        Args:
            beforewards (Before | None):
                The Beforewards object to create. Defaults to None.

        Raises:
            TypeError: If 'beforewards' is not a Before object or None.

        Returns:
            Before: The Beforewards object.
        """

        if beforewards is None:
            return cls(**cls.default_value())
        if isinstance(beforewards, cls):
            return beforewards

        raise TypeError(
            f"beforewards must be a Before object or None, but got {type(beforewards)}."
        )
