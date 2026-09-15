"""Declaration of the input fields of QurriumPrototype (:mod:`qurry.qurrium.utils.declare`)"""

from typing import TypedDict, Any, Literal, TypeVar
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend

from .waves import WCKeyable
from .transpiler import PassManagerType, TranspileArgs


class BaseRunArgs(TypedDict):
    """Arguments for :meth:`~qiskit.providers.backend.BackendV2.run`."""


RunArgsType = BaseRunArgs | dict[str, Any] | None
"""The type hint for :meth:`~qiskit.providers.backend.BackendV2.run`."""


class BasicArgs(TypedDict, total=False):
    """Basic input fields for
    :meth:`~qurry.qurrium.qurrium.QurriumPrototype.measure`
    and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`."""

    shots: int
    """Shots of the job."""
    backend: Backend | None
    """The quantum backend."""
    exp_name: str
    """ The name of the experiment."""
    run_args: RunArgsType
    """Arguments for :meth:`Backend.run`."""
    transpile_args: TranspileArgs | None
    """Arguments of :func:`~qiskit.compiler.transpile`."""
    passmanager: PassManagerType
    """The passmanager."""
    tags: tuple[str, ...] | None
    """Given tags for the experiment to describe it."""
    # process tool
    qasm_version: Literal["qasm2", "qasm3"]
    """The export version of OpenQASM."""
    export: bool
    """Whether to export the experiment."""
    save_location: Path | str | None
    """The location to save the experiment."""
    pbar: tqdm.tqdm | None
    """The progress bar for showing the progress of the experiment."""


_MA = TypeVar("_MA", bound=BasicArgs)
"""The type var of :class:`BasicArgs` for
:meth:`~qurry.qurrium.qurrium.QurriumPrototype.measure`
and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput"""

ConfigListType = list[dict[str, Any]] | list[_MA] | list[_MA | dict[str, Any]]
"""The generic type hint for the input of
:meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiBulid`
and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`.
"""


class OutputArgs(BasicArgs):
    """Basic output arguments for
    :meth:`~qurry.qurrium.qurrium.QurriumPrototype.output`."""

    circuits: list[QuantumCircuit | WCKeyable]


_OA = TypeVar("_OA", bound=OutputArgs)
"""The type var of :class:`OutputArgs` 
for :meth:`~qurry.qurrium.qurrium.QurriumPrototype.output` 

:class:`OutputArgs` is also used for passing arguments in an standard format to
:meth:`~qurry.qurrium.qurrium.QurriumPrototype.output` 
and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`.
"""
