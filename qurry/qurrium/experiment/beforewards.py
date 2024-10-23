"""
================================================================
The experiment container - beforewards
(:mod:`qurry.qurrium.experiment.beforewards`)
================================================================

"""

import json
from typing import Optional, NamedTuple, Any, Union
from collections.abc import Hashable
from pathlib import Path

from qiskit import QuantumCircuit

from ..utils.qasm import qasm_loads

V5_TO_V7_FIELD = {
    "jobID": "job_id",
    "expName": "exp_name",
    "figOriginal": "fig_original",
    "sideProduct": "side_product",
}


def v5_to_v7_field_transpose(advent: dict[str, Any]) -> dict[str, Any]:
    """Transpose the v5 field to v7 field."""
    for k, nk in V5_TO_V7_FIELD.items():
        if k in advent:
            advent[nk] = advent.pop(k)
    return advent


class Before(NamedTuple):
    """The data of experiment will be independently exported in the folder 'advent',
    which generated before the experiment.
    """

    # Experiment Preparation
    target: list[tuple[Hashable, Union[QuantumCircuit, str]]]
    """The target circuits of experiment."""
    target_qasm: list[tuple[str, str]]
    """The OpenQASM of target circuits."""
    circuit: list[QuantumCircuit]
    """The transpiled circuits of experiment."""
    circuit_qasm: list[str]
    """The OpenQASM of transpiled circuits."""
    fig_original: list[str]
    """Raw circuit figures which is the circuit before transpile."""

    # Export data
    job_id: str
    """ID of job for pending on real machine (IBMQBackend)."""
    exp_name: str
    """Name of experiment which is also showed on IBM Quantum Computing quene."""

    # side product
    side_product: dict[str, Any]
    """The data of experiment will be independently exported in the folder 'tales'."""

    @staticmethod
    def default_value():
        """These default value are used for autofill the missing value."""
        return {
            "target": [],
            "target_qasm": [],
            "circuit": [],
            "circuit_qasm": [],
            "job_id": None,
            "exp_name": None,
            "fig_original": [],
            "side_product": {},
        }

    @classmethod
    def read(
        cls,
        file_index: dict[str, str],
        save_location: Path,
        encoding: str = "utf-8",
    ) -> "Before":
        """Read the exported experiment file.

        Args:
            file_index (dict[str, str]): The index of exported experiment file.
            save_location (Path): The location of exported experiment file.
            encoding (str, optional): The encoding of exported experiment file. Defaults to "utf-8".

        Returns:
            tuple[dict[str, Any], "Before", dict[str, Any]]:
                The experiment's arguments,
                the experiment's common parameters,
                and the experiment's side product.
        """
        raw_data = {}
        with open(save_location / file_index["advent"], "r", encoding=encoding) as f:
            raw_data = json.load(f)

        advent: dict[str, Any] = raw_data["adventures"]
        advent = v5_to_v7_field_transpose(advent)
        for k, dv in cls.default_value().items():
            if k not in advent:
                advent[k] = dv

        assert "side_product" in advent, "The side product is not found."

        for filekey, filename in file_index.items():
            filekeydiv = filekey.split(".")
            if filekeydiv[0] == "tales":
                with open(save_location / filename, "r", encoding=encoding) as f:
                    advent["side_product"][filekeydiv[1]] = json.load(f)

        return cls(**advent)

    def export(
        self,
        unexports: Optional[list[str]] = None,
        export_transpiled_circuit: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Export the experiment's data before executing.

        Args:
            unexports (Optional[list[str]], optional): The list of unexported key. Defaults to None.
            export_circuit (bool, optional):
                Whether to export the transpiled circuit as txt. Defaults to False.
                When set to True, the transpiled circuit will be exported as txt.
                Otherwise, the circuit will be not exported but circuit qasm remains.

        Returns:
            tuple[dict[str, Any], dict[str, Any]]:
                The experiment's arguments,
                and the experiment's side product.
        """

        if unexports is None:
            unexports = []

        tales: dict[str, str] = {}
        adventures = {}
        # pylint: disable=no-member
        for k, v in self._asdict().items():
            # pylint: enable=no-member
            if k == "side_product":
                tales = {**tales, **v}
            elif k == "circuit":
                adventures[k] = v if export_transpiled_circuit else []
            elif k in unexports:
                ...
            else:
                adventures[k] = v

        return adventures, tales

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
            print(f"The circuits {is_none_circuits} are not revived.")
        return revived_circuits

    def revive_target(self, replace_target: bool = False) -> dict[Hashable, QuantumCircuit]:
        """Revive the target circuits from the qasm, return the revived target.

        Args:
            replace_target (bool, optional):
                Whether to replace the target circuits. Defaults to False.

        Raises:
            ValueError: If the .target is not empty.

        Returns:
            dict[Hashable, QuantumCircuit]: The revived target circuits.
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
