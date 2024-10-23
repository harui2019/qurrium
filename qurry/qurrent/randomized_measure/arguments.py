"""
===========================================================
EntropyMeasureRandomized - Arguments
(:mod:`qurry.qurrent.randomized_measure.arguments`)
===========================================================

"""

from typing import Optional, Union
from collections.abc import Hashable
from dataclasses import dataclass

from qiskit import QuantumCircuit

from ...qurrium.experiment import ArgumentsPrototype
from ...declare import BasicArgs, OutputArgs
from ...tools import DEFAULT_POOL_SIZE


@dataclass(frozen=True)
class EntropyMeasureRandomizedArguments(ArgumentsPrototype):
    """Arguments for the experiment."""

    exp_name: str = "exps"
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    times: int = 100
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    qubits_measured: Optional[list[int]] = None
    """The measure range."""
    registers_mapping: Optional[dict[int, int]] = None
    """The mapping of the classical registers with quantum registers.

    Example:
    ```python
    {
        0: 0, # The quantum register 0 is mapped to the classical register 0.
        1: 1, # The quantum register 1 is mapped to the classical register 1.
        5: 2, # The quantum register 5 is mapped to the classical register 2.
        7: 3, # The quantum register 7 is mapped to the classical register 3.
    }
    ```

    The key is the index of the quantum register with the numerical order.
    The value is the index of the classical register with the numerical order.
    """
    actual_num_qubits: int = 0
    """The actual number of qubits."""
    unitary_located: Optional[list[int]] = None
    """The range of the unitary operator."""
    random_unitary_seeds: Optional[dict[int, dict[int, int]]] = None
    """The seeds for all random unitary operator.
    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index for the random unitary operator.
    The second key is the index for the qubit.

    Example:
    ```python
    {
        0: {0: 1234, 1: 5678},
        1: {0: 2345, 1: 6789},
        2: {0: 3456, 1: 7890},
    }
    ```

    If you want to generate the seeds for all random unitary operator,
    you can use the function `generate_random_unitary_seeds` 
    in `qurry.qurrium.utils.random_unitary`.

    Example:
    ```python
    from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
    random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    ```

    """
    workers_num: int = DEFAULT_POOL_SIZE
    """The number of workers for multiprocessing."""


class EntropyMeasureRandomizedMeasureArgs(BasicArgs):
    """Output arguments for :meth:`output`."""

    wave: Optional[Union[QuantumCircuit, Hashable]]
    """The key or the circuit to execute."""
    times: int
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    measure: Optional[Union[tuple[int, int], int, list[int]]]
    """The measure range."""
    unitary_loc: Optional[Union[tuple[int, int], int, list[int]]]
    """The range of the unitary operator."""
    unitary_loc_not_cover_measure: bool
    """Whether the range of the unitary operator is not cover the measure range."""
    random_unitary_seeds: Optional[dict[int, dict[int, int]]]
    """The seeds for all random unitary operator.
    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index for the random unitary operator.
    The second key is the index for the qubit.

    Example:
    ```python
    {
        0: {0: 1234, 1: 5678},
        1: {0: 2345, 1: 6789},
        2: {0: 3456, 1: 7890},
    }
    ```

    If you want to generate the seeds for all random unitary operator,
    you can use the function `generate_random_unitary_seeds` 
    in `qurry.qurrium.utils.random_unitary`.

    Example:
    ```python
    from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
    random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    ```

    """


class EntropyMeasureRandomizedOutputArgs(OutputArgs):
    """Output arguments for :meth:`output`."""

    times: int
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    measure: Optional[Union[tuple[int, int], int, list[int]]]
    """The measure range."""
    unitary_loc: Optional[Union[tuple[int, int], int, list[int]]]
    """The range of the unitary operator."""
    unitary_loc_not_cover_measure: bool
    """Whether the range of the unitary operator is not cover the measure range."""
    random_unitary_seeds: Optional[dict[int, dict[int, int]]]
    """The seeds for all random unitary operator.
    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index for the random unitary operator.
    The second key is the index for the qubit.

    Example:
    ```python
    {
        0: {0: 1234, 1: 5678},
        1: {0: 2345, 1: 6789},
        2: {0: 3456, 1: 7890},
    }
    ```

    If you want to generate the seeds for all random unitary operator,
    you can use the function `generate_random_unitary_seeds` 
    in `qurry.qurrium.utils.random_unitary`.

    Example:
    ```python
    from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
    random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    ```

    """


SHORT_NAME = "qurrent_randomized"
