"""
================================================================
Kit for Random Unitary Operator
(:mod:`qurry.qurrium.utils.random_unitary`)
================================================================

"""

from typing import Union, Optional
from collections.abc import Sequence
import numpy as np


SeedType = Union[int, np.random.Generator]


def generate_seeds_for_single_circ(
    seed_for_single_circ: Optional[SeedType],
    num_qubits: int,
) -> dict[int, int]:
    """Generate the seed for single circuit.

    Args:
        seed_for_single_circ (Optional[SeedType]):
            The seed for single circuit.
        num_qubits (int):
            The number of qubits.
    Raises:
        ValueError:
            If the seed is not int, np.random.Generator
    Returns:
        dict[int, int]:
            The seed for single circuit.
    """

    if seed_for_single_circ is None:
        return {j: np.random.default_rng().integers(0, 2**32, dtype=int) for j in range(num_qubits)}
    if isinstance(seed_for_single_circ, int):
        return {j: seed_for_single_circ for j in range(num_qubits)}
    if isinstance(seed_for_single_circ, np.random.Generator):
        return {j: seed_for_single_circ.integers(0, 2**32, dtype=int) for j in range(num_qubits)}
    raise ValueError(
        "The seed is not int, np.random.Generator, " + f"but {type(seed_for_single_circ)}"
    )


def check_and_generate_for_single_circ(
    seed_for_single_circ: Optional[Union[SeedType, Sequence[SeedType], dict[int, SeedType]]],
    num_qubits: int,
) -> dict[int, int]:
    """Check the input of generate_random_unitary_seeds.

    Args:
        seed_for_single_circ (Optional[Union[SeedType, Sequence[SeedType], dict[int, SeedType]]]):
            The seed for single circuit.
        num_qubits (int):
            The number of qubits.

    Raises:
        TypeError:
            If the seed is not int, np.random.Generator, Sequence, or dict.
        ValueError:
            If the seed for one qubit is not found.
            If the seed is not int or np.random.Generator.
            If the length of seed is not equal to num_qubits.

    Returns:
        dict[int, int]:
            The seed for single circuit.
    """
    if seed_for_single_circ is None or isinstance(seed_for_single_circ, (int, np.random.Generator)):
        return generate_seeds_for_single_circ(seed_for_single_circ, num_qubits)

    if not isinstance(seed_for_single_circ, (Sequence, dict)):
        raise TypeError(
            "The seed must be int, np.random.Generator, Sequence, or dict, "
            + f"not {type(seed_for_single_circ)}"
        )
    if len(seed_for_single_circ) != num_qubits:
        raise ValueError(
            "The length of seed must be equal to num_qubits: "
            + f"{len(seed_for_single_circ)} != {num_qubits}."
        )
    invalids = {}
    single_seed = {}
    for j in range(num_qubits):
        seed_for_one_qubit = (
            seed_for_single_circ.get(j, None)
            if isinstance(seed_for_single_circ, dict)
            else seed_for_single_circ[j]
        )
        if seed_for_one_qubit is None:
            raise ValueError(f"The seed for qubit {j} is not found.")
        if isinstance(seed_for_one_qubit, int):
            single_seed[j] = seed_for_one_qubit
        elif isinstance(seed_for_one_qubit, np.random.Generator):
            single_seed[j] = seed_for_one_qubit.integers(0, 2**32, dtype=int)
        else:
            invalids[j] = (seed_for_one_qubit, type(seed_for_one_qubit))
    if invalids:
        raise TypeError(
            "The seed must be int or np.random.Generator, " + f"but some of them are: {invalids}."
        )
    if len(single_seed) != num_qubits:
        raise ValueError(
            "The length of seed must be equal to num_qubits: "
            + f"{len(single_seed)} != {num_qubits}."
        )
    return single_seed


def generate_random_unitary_seeds(
    times: int,
    num_qubits: int,
    seed: Optional[
        Union[
            SeedType,
            Sequence[Union[SeedType, Sequence[SeedType], dict[int, SeedType]]],
            dict[int, Union[SeedType, Sequence[SeedType], dict[int, SeedType]]],
        ]
    ] = None,
) -> dict[int, dict[int, int]]:
    """Generate random unitary seeds.

    Args:
        times (int): The number of random unitary operator.
        num_qubits (int): The number of qubits.
        seed (Union[
            int,
            np.random.Generator,
            Sequence[Union[
                int, np.random.Generator,
                Sequence[Union[int, np.random.Generator]],
                dict[int, Union[int, np.random.Generator]]
            ]],
            dict[int, Union[
                int, np.random.Generator,
                Sequence[Union[int, np.random.Generator]],
                dict[int, Union[int, np.random.Generator]]
            ]]
        ], optional):
            The seed of random generator.

    Raises:
        TypeError:
            If the seed is not int, np.random.Generator, Sequence, or dict.
        ValueError:
            If the length of seed is not equal to times.

    Returns:
        dict[int, dict[int, int]]]:
            The random unitary seeds.
    """
    if seed is None or isinstance(seed, (int, np.random.Generator)):
        return {i: generate_seeds_for_single_circ(seed, num_qubits) for i in range(times)}

    if not isinstance(seed, (Sequence, dict)):
        raise TypeError(
            "The seed must be int, np.random.Generator, Sequence, or dict, " + f"not {type(seed)}"
        )
    if len(seed) != times:
        raise ValueError("The length of seed must be equal to times: " + f"{len(seed)} != {times}.")
    invalids = {}
    single_seed = {}
    for i in range(times):
        seed_for_one_circ = seed.get(i, None) if isinstance(seed, dict) else seed[i]
        try:
            single_seed[i] = check_and_generate_for_single_circ(seed_for_one_circ, num_qubits)
        except (TypeError, ValueError) as e:
            invalids[i] = e
    if invalids:
        raise TypeError(
            "The seed must be int, np.random.Generator, Sequence, or dict, "
            + f"but some of them are: {invalids}."
        )

    return single_seed


def check_input_for_experiment(
    times: int,
    num_qubits: int,
    random_unitary_seeds: Optional[dict[int, dict[int, int]]],
) -> None:
    """Check the input of the experiment.
    If you want to generate the seeds for all random unitary operator,
    you can use the function `generate_random_unitary_seeds`
    in `qurry.qurrium.utils.random_unitary`.

    Args:
        times (int): The number of random unitary operator.
        num_qubits (int): The number of qubits.
        random_unitary_seeds (Optional[dict[int, dict[int, int]]]):
            The random unitary seeds.
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

    Raises:
        TypeError: If the random_unitary_seeds is not dict.
        ValueError: If the length of random_unitary_seeds is not equal to times.
        TypeError: If the random_unitary_seeds[i] is not dict.
        ValueError: If the length of random_unitary_seeds[i] is not equal to num_qubits.
        TypeError: If the random_unitary_seeds[i][j] is not int.

    """
    if random_unitary_seeds is None:
        return None
    if not isinstance(random_unitary_seeds, dict):
        raise TypeError(
            "The random_unitary_seeds must be dict, " + f"not {type(random_unitary_seeds)}"
        )
    if len(random_unitary_seeds) != times:
        raise ValueError(
            "The length of random_unitary_seeds must be equal to times: "
            + f"{len(random_unitary_seeds)} != {times}."
        )
    for i in range(times):
        if not isinstance(random_unitary_seeds[i], dict):
            raise TypeError(
                "The random_unitary_seeds must be dict, "
                + f"not {type(random_unitary_seeds[i])} in {i}."
            )
        if len(random_unitary_seeds[i]) != num_qubits:
            raise ValueError(
                "The length of random_unitary_seeds must be equal to num_qubits: "
                + f"{len(random_unitary_seeds[i])} != {num_qubits} in {i}."
            )
        for j in range(num_qubits):
            if not isinstance(random_unitary_seeds[i][j], int):
                raise TypeError(
                    "The random_unitary_seeds must be int, "
                    + f"not {type(random_unitary_seeds[i][j])} in {i}, {j}."
                )
    return None
