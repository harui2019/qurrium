"""
================================================================
The experiment container
(:mod:`qurry.qurrium.experiment`)
================================================================

"""
from typing import Literal, Union, Optional, NamedTuple, Hashable, Any
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.providers import Backend

from ...tools.datetime import DatetimeDict


class Arguments(NamedTuple):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class."""

    expName: str
    """Name of experiment."""


class Commonparams(NamedTuple):
    """Construct the experiment's parameters for system running."""

    expID: str
    """ID of experiment."""
    waveKey: Hashable
    """Key of the chosen wave."""

    # Qiskit argument of experiment.
    # Multiple jobs shared
    shots: int
    """Number of shots to run the program (default: 1024)."""
    backend: Union[Backend, str]
    """Backend to execute the circuits on, or the backend used."""
    runArgs: dict
    """Arguments of `execute`."""

    # Single job dedicated
    runBy: Literal["gate", "operator"]
    """Run circuits by gate or operator."""
    transpileArgs: dict
    """Arguments of `qiskit.compiler.transpile`."""
    decompose: Optional[int]
    """Decompose the circuit in given times 
    to show the circuit figures in :property:`.before.figOriginal`."""

    tags: tuple
    """Tags of experiment."""

    # Auto-analysis when counts are ready
    defaultAnalysis: list[dict[str, Any]]
    """When counts are ready, 
    the experiment will automatically analyze the counts with the given analysis."""

    # Arguments for exportation
    saveLocation: Union[Path, str]
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
        
        'args': './blabla_experiment/args/blabla_experiment.id={expID}.args.json',
        'advent': './blabla_experiment/advent/blabla_experiment.id={expID}.advent.json',
        'legacy': './blabla_experiment/legacy/blabla_experiment.id={expID}.legacy.json',
        'tales.dummyx1': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyx1.json',
        'tales.dummyx2': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyx2.json',
        ...
        'tales.dummyxn': './blabla_experiment/tales/blabla_experiment.id={expID}.dummyxn.json',
        'reports': './blabla_experiment/reports/blabla_experiment.id={expID}.reports.json',
        'reports.tales.dummyz1': 
            './blabla_experiment/tales/blabla_experiment.id={expID}.dummyz1.reports.json',
        'reports.tales.dummyz2': 
            './blabla_experiment/tales/blabla_experiment.id={expID}.dummyz2.reports.json',
        ...
        'reports.tales.dummyzm': 
            './blabla_experiment/tales/blabla_experiment.id={expID}.dummyzm.reports.json',
    }
    ```
    which `blabla_experiment` is the example filename.
    If this experiment is called by :cls:`multimanager`, 
    then the it will be named after `summonerName` as known as the name of :cls:`multimanager`.
    
    ```python
    files = {
        'folder': './BLABLA_project/',
        
        'args': './BLABLA_project/args/index={serial}.id={expID}.args.json',
        'advent': './BLABLA_project/advent/index={serial}.id={expID}.advent.json',
        'legacy': './BLABLA_project/legacy/index={serial}.id={expID}.legacy.json',
        'tales.dummyx1': './BLABLA_project/tales/index={serial}.id={expID}.dummyx1.json',
        'tales.dummyx2': './BLABLA_project/tales/index={serial}.id={expID}.dummyx2.json',
        ...
        'tales.dummyxn': './BLABLA_project/tales/index={serial}.id={expID}.dummyxn.json',
        'reports': './BLABLA_project/reports/index={serial}.id={expID}.reports.json',
        'reports.tales.dummyz1': 
            './BLABLA_project/tales/index={serial}.id={expID}.dummyz1.reports.json',
        'reports.tales.dummyz2': 
            './BLABLA_project/tales/index={serial}.id={expID}.dummyz2.reports.json',
        ...
        'reports.tales.dummyzm': 
            './BLABLA_project/tales/index={serial}.id={expID}.dummyzm.reports.json',
    }
    ```
    which `BLBLA_project` is the example :cls:`multimanager` name 
    stored at :prop:`commonparams.summonerName`.
    At this senerio, the `expName` will never apply as filename.
    
    """

    # Arguments for multi-experiment
    serial: Optional[int]
    """Index of experiment in a multiOutput."""
    summonerID: Optional[str]
    """ID of experiment of the multiManager."""
    summonerName: Optional[str]
    """Name of experiment of the multiManager."""

    # header
    datetimes: DatetimeDict


class Before(NamedTuple):
    """The data of experiment will be independently exported in the folder 'advent',
    which generated before the experiment.
    """

    # Experiment Preparation
    circuit: list[QuantumCircuit]
    """Circuits of experiment."""
    figOriginal: list[str]
    """Raw circuit figures which is the circuit before transpile."""

    # Export data
    jobID: str
    """ID of job for pending on real machine (IBMQBackend)."""
    expName: str
    """Name of experiment which is also showed on IBM Quantum Computing quene."""

    # side product
    sideProduct: dict
    """The data of experiment will be independently exported in the folder 'tales'."""


class After(NamedTuple):
    """The data of experiment will be independently exported in the folder 'legacy',
    which generated after the experiment."""

    # Measurement Result
    result: list[Result]
    """Results of experiment."""
    counts: list[dict[str, int]]
    """Counts of experiment."""
