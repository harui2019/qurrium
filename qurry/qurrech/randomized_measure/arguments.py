"""
===========================================================
EchoListenRandomized - Arguments
(:mod:`qurry.qurrech.randomized_measure.arguments`)
===========================================================

"""

from typing import Optional, Union
from collections.abc import Hashable
from dataclasses import dataclass
import numpy as np

from qiskit import QuantumCircuit

from ...qurrium.experiment import ArgumentsPrototype
from ...declare import BasicArgs, OutputArgs
from ...tools import DEFAULT_POOL_SIZE


@dataclass(frozen=True)
class EchoListenRandomizedArguments(ArgumentsPrototype):
    """Arguments for the experiment."""

    exp_name: str = "exps"
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    times: int = 100
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    measure: Optional[tuple[int, int]] = None
    """The measure range."""
    unitary_loc: Optional[tuple[int, int]] = None
    """The range of the unitary operator."""
    random_unitary_seed: Optional[Union[int, np.random.Generator]] = None
    """The seed for the random unitary operator."""
    workers_num: int = DEFAULT_POOL_SIZE
    """The number of workers for multiprocessing."""


class EchoListenRandomizedMeasureArgs(BasicArgs):
    """Output arguments for :meth:`output`."""

    wave1: Optional[Union[QuantumCircuit, Hashable]]
    """The key or the circuit to execute."""
    wave2: Optional[Union[QuantumCircuit, Hashable]]
    """The key or the circuit to execute."""
    times: int
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    measure: Union[int, tuple[int, int], None]
    """The measure range."""
    unitary_loc: Union[int, tuple[int, int], None]
    """The range of the unitary operator."""
    random_unitary_seed: Optional[Union[int, np.random.Generator]]
    """The seed for the random unitary operator."""


class EchoListenRandomizedOutputArgs(OutputArgs):
    """Output arguments for :meth:`output`."""

    times: int
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    measure: Union[int, tuple[int, int], None]
    """The measure range."""
    unitary_loc: Union[int, tuple[int, int], None]
    """The range of the unitary operator."""
    random_unitary_seed: Optional[Union[int, np.random.Generator]]
    """The seed for the random unitary operator."""


SHORT_NAME = "qurrech_randomized"
