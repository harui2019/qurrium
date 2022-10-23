from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.providers import Backend
from qiskit.providers.aer import AerProvider
from qiskit.providers.ibmq import AccountProvider

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, overload


class argsCore(NamedTuple):
    expsName: str = 'exps'
    wave: Union[QuantumCircuit, any, None] = None
    sampling: int = 1


class argsMain(NamedTuple):
    # ID of experiment.
    expID: Optional[str] = None

    # Qiskit argument of experiment.
    # Multiple jobs shared
    shots: int = 1024
    backend: Backend = AerProvider().get_backend('aer_simulator')
    provider: Optional[AccountProvider] = None
    runArgs: dict[str, any] = {}

    # Single job dedicated
    runBy: str = "gate"
    decompose: Optional[int] = 2
    transpileArgs: dict[str, any] = {}

    # Other arguments of experiment
    drawMethod: str = 'text'
    resultKeep: bool = False
    tags: tuple[str] = ()
    resoureControl: dict[str, any] = {}

    saveLocation: Union[Path, str] = Path('./')
    exportLocation: Path = Path('./')

    expIndex: Optional[int] = None


class expsCore(NamedTuple):
    ...


class expsMain(NamedTuple):
    # Measurement result
    circuit: list[QuantumCircuit] = []
    figRaw: list[str] = []
    figTranspile: list[str] = []
    result: list[Result] = []
    counts: list[dict[str, int]] = []

    # Export data
    jobID: str = ''
    expsName: str = 'exps'

    # side product
    sideProduct: dict = {}
