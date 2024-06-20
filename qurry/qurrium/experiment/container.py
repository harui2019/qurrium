"""
================================================================
The experiment container
(:mod:`qurry.qurrium.experiment`)
================================================================

"""

import json
from typing import Union, Optional, NamedTuple, Hashable, TypedDict, Any
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.providers import Backend

from ...tools import backendName
from ...tools.datetime import DatetimeDict
from ...capsule import jsonablize

REQUIRED_FOLDER = ["args", "advent", "legacy", "tales", "reports"]
"""The required folder for exporting experiment."""


class ArgumentsPrototype(NamedTuple):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class."""

    exp_name: str
    """Name of experiment."""


class CommonparamsDict(TypedDict):
    """The export dictionary of :cls:`Commonparams`."""

    exp_name: str
    exp_id: str
    wave_key: Hashable
    shots: int
    backend: Union[Backend, str]
    run_args: dict[str, Any]
    transpile_args: dict[str, Any]
    tags: tuple[str, ...]
    default_analysis: list[dict[str, Any]]
    save_location: Union[Path, str]
    filename: str
    files: dict[str, Path]
    serial: Optional[int]
    summoner_id: Optional[str]
    summoner_name: Optional[str]
    datetimes: DatetimeDict


class Commonparams(NamedTuple):
    """Construct the experiment's parameters for system running."""

    exp_id: str
    """ID of experiment."""
    wave_key: Hashable
    """Key of the chosen wave."""

    # Qiskit argument of experiment.
    # Multiple jobs shared
    shots: int
    """Number of shots to run the program (default: 1024)."""
    backend: Union[Backend, str]
    """Backend to execute the circuits on, or the backend used."""
    run_args: dict[str, Any]
    """Arguments of `execute`."""

    # Single job dedicated
    transpile_args: dict
    """Arguments of `qiskit.compiler.transpile`."""

    tags: tuple[str, ...]
    """Tags of experiment."""

    # Auto-analysis when counts are ready
    default_analysis: list[dict[str, Any]]
    """When counts are ready, 
    the experiment will automatically analyze the counts with the given analysis."""

    # Arguments for exportation
    save_location: Union[Path, str]
    """Location of saving experiment. 
    If this experiment is called by :cls:`QurryMultiManager`,
    then `adventure`, `legacy`, `tales`, and `reports` will be exported 
    to their dedicated folders in this location respectively.
    This location is the default location for it's not specific 
    where to save when call :meth:`.write()`, if does, then will be overwriten and update."""
    filename: str
    """The name of file to be exported, 
    it will be decided by the :meth:`.export` when it's called.
    More info in the pydoc of :prop:`files` or :meth:`.export`.
    """
    files: dict[str, Path]
    """The list of file to be exported.
    For the `.write` function actually exports 4 different files
    respecting to `adventure`, `legacy`, `tales`, and `reports` like:

    ```python
    files = {
        'folder': './blabla_experiment/',

        'args': './blabla_experiment/args/blabla_experiment.id={exp_id}.args.json',
        'advent': './blabla_experiment/advent/blabla_experiment.id={exp_id}.advent.json',
        'legacy': './blabla_experiment/legacy/blabla_experiment.id={exp_id}.legacy.json',
        'tales.dummyx1': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyx1.json',
        'tales.dummyx2': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyx2.json',
        ...
        'tales.dummyxn': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyxn.json',
        'reports': './blabla_experiment/reports/blabla_experiment.id={exp_id}.reports.json',
        'reports.tales.dummyz1': 
            './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyz1.reports.json',
        'reports.tales.dummyz2': 
            './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyz2.reports.json',
        ...
        'reports.tales.dummyzm': 
            './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyzm.reports.json',
    }
    ```
    which `blabla_experiment` is the example filename.
    If this experiment is called by :cls:`multimanager`, 
    then the it will be named after `summoner_name` as known as the name of :cls:`multimanager`.

    ```python
    files = {
        'folder': './BLABLA_project/',

        'args': './BLABLA_project/args/index={serial}.id={exp_id}.args.json',
        'advent': './BLABLA_project/advent/index={serial}.id={exp_id}.advent.json',
        'legacy': './BLABLA_project/legacy/index={serial}.id={exp_id}.legacy.json',
        'tales.dummyx1': './BLABLA_project/tales/index={serial}.id={exp_id}.dummyx1.json',
        'tales.dummyx2': './BLABLA_project/tales/index={serial}.id={exp_id}.dummyx2.json',
        ...
        'tales.dummyxn': './BLABLA_project/tales/index={serial}.id={exp_id}.dummyxn.json',
        'reports': './BLABLA_project/reports/index={serial}.id={exp_id}.reports.json',
        'reports.tales.dummyz1': 
            './BLABLA_project/tales/index={serial}.id={exp_id}.dummyz1.reports.json',
        'reports.tales.dummyz2': 
            './BLABLA_project/tales/index={serial}.id={exp_id}.dummyz2.reports.json',
        ...
        'reports.tales.dummyzm': 
            './BLABLA_project/tales/index={serial}.id={exp_id}.dummyzm.reports.json',
    }
    ```
    which `BLBLA_project` is the example :cls:`multimanager` name 
    stored at :prop:`commonparams.summoner_name`.
    At this senerio, the `exp_name` will never apply as filename.

    """

    # Arguments for multi-experiment
    serial: Optional[int]
    """Index of experiment in a multiOutput."""
    summoner_id: Optional[str]
    """ID of experiment of the multiManager."""
    summoner_name: Optional[str]
    """Name of experiment of the multiManager."""

    # header
    datetimes: DatetimeDict

    @staticmethod
    def v5_to_v7_field():
        """The field name of v5 to v7."""
        return {
            "expName": "exp_name",
            "expID": "exp_id",
            "waveKey": "wave_key",
            "runArgs": "run_args",
            "transpileArgs": "transpile_args",
            "defaultAnalysis": "default_analysis",
            "saveLocation": "save_location",
            "summonerID": "summoner_id",
            "summonerName": "summoner_name",
        }

    @staticmethod
    def default_value() -> CommonparamsDict:
        """The default value of each field."""
        return {
            "exp_name": "exps",
            "exp_id": "",
            "wave_key": None,
            "shots": -1,
            "backend": "",
            "run_args": {},
            "transpile_args": {},
            "tags": (),
            "default_analysis": [],
            "save_location": Path("."),
            "filename": "unknown",
            "files": {},
            "serial": None,
            "summoner_id": None,
            "summoner_name": None,
            "datetimes": DatetimeDict(),
        }

    @classmethod
    def read_with_arguments(
        cls,
        exp_id: str,
        file_index: dict[str, str],
        save_location: Path,
        encoding: str = "utf-8",
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Read the exported experiment file.

        Args:
            exp_id (str): The ID of experiment.
            file_index (dict[str, str]): The index of exported experiment file.
            save_location (Path): The location of exported experiment file.
            encoding (str, optional): The encoding of exported experiment file. Defaults to "utf-8".

        Returns:
            tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
                The experiment's arguments,
                the experiment's common parameters,
                and the experiment's side product.
        """
        raw_data = {}
        with open(save_location / file_index["args"], "r", encoding=encoding) as f:
            raw_data = json.load(f)
        data_args: dict[str, dict[str, Any]] = {
            "arguments": raw_data["arguments"],
            "commonparams": raw_data["commonparams"],
            "outfields": raw_data["outfields"],
        }
        for k, nk in cls.v5_to_v7_field().items():
            if k in data_args["commonparams"]:
                data_args["commonparams"][nk] = data_args["commonparams"].pop(k)
            if k in data_args["arguments"]:
                data_args["arguments"][nk] = data_args["arguments"].pop(k)

        assert data_args["commonparams"]["exp_id"] == exp_id, "The exp_id is not match."

        return (
            data_args["arguments"],
            data_args["commonparams"],
            data_args["outfields"],
        )

    def export(self) -> CommonparamsDict:
        """Export the experiment's common parameters.

        Returns:
            dict[str, Any]: The experiment's common parameters.
        """
        # pylint: disable=no-member
        commons: CommonparamsDict = jsonablize(self._asdict())
        # pylint: enable=no-member
        commons["backend"] = (
            self.backend if isinstance(self.backend, str) else backendName(self.backend)
        )
        return commons


class Before(NamedTuple):
    """The data of experiment will be independently exported in the folder 'advent',
    which generated before the experiment.
    """

    # Experiment Preparation
    circuit: list[QuantumCircuit]
    """Circuits of experiment."""
    circuit_qasm: list[str]
    """OpenQASM of circuits."""
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
    def v5_to_v7_field():
        """The field name of v5 to v7."""
        return {
            "jobID": "job_id",
            "expName": "exp_name",
            "figOriginal": "fig_original",
            "sideProduct": "side_product",
        }

    @staticmethod
    def default_value():
        """These default value are used for autofill the missing value."""
        return {
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
        for k, nk in cls.v5_to_v7_field().items():
            if k in advent:
                advent[nk] = advent.pop(k)
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
        """
        revived_circuits = []
        if len(self.circuit) != 0:
            if replace_circuits:
                self.circuit.clear()
            else:
                raise ValueError("The circuits is not empty.")
        for qasm in self.circuit_qasm:
            revived_circuits.append(QuantumCircuit.from_qasm_str(qasm))
        return revived_circuits


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
