"""
===========================================================
EntropyMeasureRandomizedV1 - Arguments
(:mod:`qurry.qurrent.randomized_measure_v1.arguments`)
===========================================================

This is a deprecated version of the randomized measure module.

"""

from typing import Optional, Union, Iterable
from collections.abc import Hashable
from dataclasses import dataclass

from qiskit import QuantumCircuit

from ...qurrium.experiment import ArgumentsPrototype
from ...process.randomized_measure.entangled_entropy_v1 import (
    PostProcessingBackendLabel,
)
from ...declare import BasicArgs, OutputArgs, AnalyzeArgs
from ...tools import DEFAULT_POOL_SIZE


@dataclass(frozen=True)
class EntropyMeasureRandomizedV1Arguments(ArgumentsPrototype):
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
    random_unitary_seeds: Optional[dict[int, dict[int, int]]] = None
    """The seeds for all random unitary operator.
    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index for the random unitary operator.
    The second key is the index for the qubit.

    .. code-block:: python
        {
            0: {0: 1234, 1: 5678},
            1: {0: 2345, 1: 6789},
            2: {0: 3456, 1: 7890},
        }

    If you want to generate the seeds for all random unitary operator,
    you can use the function `generate_random_unitary_seeds` 
    in `qurry.qurrium.utils.random_unitary`.

    .. code-block:: python
        from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
        random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    """
    workers_num: int = DEFAULT_POOL_SIZE
    """The number of workers for multiprocessing."""


class EntropyMeasureRandomizedV1MeasureArgs(BasicArgs, total=False):
    """Output arguments for :meth:`output`."""

    wave: Optional[Union[QuantumCircuit, Hashable]]
    """The key or the circuit to execute."""
    times: int
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    measure: Union[int, tuple[int, int], None]
    """The measure range."""
    unitary_loc: Union[int, tuple[int, int], None]
    """The range of the unitary operator."""
    random_unitary_seeds: Optional[dict[int, dict[int, int]]]
    """The seeds for all random unitary operator.
    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index for the random unitary operator.
    The second key is the index for the qubit.

    .. code-block:: python
        {
            0: {0: 1234, 1: 5678},
            1: {0: 2345, 1: 6789},
            2: {0: 3456, 1: 7890},
        }

    If you want to generate the seeds for all random unitary operator,
    you can use the function `generate_random_unitary_seeds` 
    in `qurry.qurrium.utils.random_unitary`.

    .. code-block:: python
        from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
        random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    """


class EntropyMeasureRandomizedV1OutputArgs(OutputArgs):
    """Output arguments for :meth:`output`."""

    times: int
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    measure: Union[int, tuple[int, int], None]
    """The measure range."""
    unitary_loc: Union[int, tuple[int, int], None]
    """The range of the unitary operator."""
    random_unitary_seeds: Optional[dict[int, dict[int, int]]]
    """The seeds for all random unitary operator.
    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index for the random unitary operator.
    The second key is the index for the qubit.

    .. code-block:: python
        {
            0: {0: 1234, 1: 5678},
            1: {0: 2345, 1: 6789},
            2: {0: 3456, 1: 7890},
        }

    If you want to generate the seeds for all random unitary operator,
    you can use the function `generate_random_unitary_seeds` 
    in `qurry.qurrium.utils.random_unitary`.

    .. code-block:: python
        from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
        random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    """


class EntropyMeasureRandomizedV1AnalyzeArgs(AnalyzeArgs, total=False):
    """The input of the analyze method."""

    degree: Optional[Union[tuple[int, int], int]]
    """The degree range."""
    counts_used: Optional[Iterable[int]]
    """The index of the counts used."""
    workers_num: Optional[int]
    """The number of workers for multiprocessing."""
    independent_all_system: bool
    """If True, then calculate the all system independently."""
    backend: PostProcessingBackendLabel
    """The backend for the process."""


SHORT_NAME = "qurrent_randomized_v1"
