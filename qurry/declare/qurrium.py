"""
================================================================
Arguments for :meth:`output` 
from :module:`QurriumPrototype` 
(:mod:`qurry.declare.qurrium`)
================================================================

"""

from typing import Optional, Union, TypedDict, Any, Literal
from collections.abc import Hashable
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend
from qiskit.transpiler.passmanager import PassManager

from .run import BaseRunArgs
from .transpile import TranspileArgs


class BasicArgs(TypedDict, total=False):
    """Basic output arguments for :meth:`output`."""

    shots: int
    backend: Optional[Backend]
    exp_name: str
    run_args: Optional[Union[BaseRunArgs, dict[str, Any]]]
    transpile_args: Optional[TranspileArgs]
    passmanager: Optional[Union[str, PassManager, tuple[str, PassManager]]]
    tags: Optional[tuple[str, ...]]
    # already built exp
    exp_id: Optional[str]
    new_backend: Optional[Backend]
    revive: bool
    replace_circuits: bool
    # process tool
    qasm_version: Literal["qasm2", "qasm3"]
    export: bool
    save_location: Optional[Union[Path, str]]
    mode: str
    indent: int
    encoding: str
    jsonable: bool
    pbar: Optional[tqdm.tqdm]


class OutputArgs(BasicArgs):
    """Basic output arguments for :meth:`output`."""

    circuits: Optional[list[Union[QuantumCircuit, Hashable]]]
