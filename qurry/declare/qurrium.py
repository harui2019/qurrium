"""
================================================================
Arguments for :meth:`output` 
from :module:`QurriumPrototype` 
(:mod:`qurry.declare.qurrium`)
================================================================

"""

from typing import Optional, Union, TypedDict, NotRequired, Any
from collections.abc import Hashable
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend
from qiskit.transpiler.passmanager import PassManager

from .run import BaseRunArgs
from .transpile import TranspileArgs


class BasicOutputArgs(TypedDict):
    """Basic output arguments for :meth:`output`."""

    circuits: Optional[list[Union[QuantumCircuit, Hashable]]]
    shots: NotRequired[int]
    backend: Optional[Backend]
    exp_name: NotRequired[str]
    run_args: NotRequired[Optional[Union[BaseRunArgs, dict[str, Any]]]]
    transpile_args: NotRequired[Optional[TranspileArgs]]
    passmanager: NotRequired[Optional[Union[str, PassManager, tuple[str, PassManager]]]]
    # already built exp
    exp_id: NotRequired[Optional[str]]
    new_backend: NotRequired[Optional[Backend]]
    revive: NotRequired[bool]
    replace_circuits: NotRequired[bool]
    # process tool
    export: NotRequired[bool]
    save_location: NotRequired[Optional[Union[Path, str]]]
    mode: NotRequired[str]
    indent: NotRequired[int]
    encoding: NotRequired[str]
    jsonable: NotRequired[bool]
    pbar: NotRequired[Optional[tqdm.tqdm]]
