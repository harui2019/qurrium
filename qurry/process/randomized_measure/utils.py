"""Post Processing - Randomized Measure - Utilities
(:mod:`qurry.process.randomized_measure.utils`)

"""

from collections.abc import Sequence
import hashlib
import numpy as np

from ..utils import FloatType

SeedType = int | np.random.Generator
"""The type of seed for random generator."""


def generate_seeds_for_single_circ(
    seed_for_single_circ: SeedType | None, num_qubits: int
) -> dict[int, int]:
    """Generate the seed for single circuit.

    Args:
        seed_for_single_circ (SeedType | None): The seed for single circuit.
        num_qubits (int): The number of qubits.

    Raises:
        ValueError: If the seed is not int, np.random.Generator

    Returns:
        dict[int, int]: The seed for single circuit.
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
    seed_for_single_circ: SeedType | Sequence[SeedType] | dict[int, SeedType] | None,
    num_qubits: int,
) -> dict[int, int]:
    """Check the input of :func:`generate_random_unitary_seeds`.

    Args:
        seed_for_single_circ (SeedType | Sequence[SeedType] | dict[int, SeedType] | None):
            The seed for single circuit.
        num_qubits (int):
            The number of qubits.

    Raises:
        TypeError:
            If the seed is not int, :class:`~numpy.random.Generator`,
            :class:`~typing.Sequence`, or :class:`dict`.
        ValueError:
            If the seed for one qubit is not found.
            If the seed is not int or :class:`~numpy.random.Generator`.
            If the length of seed is not equal to num_qubits.

    Returns:
        dict[int, int]: The seed for single circuit.
    """
    if seed_for_single_circ is None or isinstance(seed_for_single_circ, (int, np.random.Generator)):
        return generate_seeds_for_single_circ(seed_for_single_circ, num_qubits)

    if not isinstance(seed_for_single_circ, (Sequence, dict)):
        raise TypeError(
            "The seed must be int, numpy.random.Generator, Sequence, or dict, "
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
            f"The seed must be int or np.random.Generator, but some of them are: {invalids}."
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
    seed: SeedType
    | Sequence[SeedType | Sequence[SeedType] | dict[int, SeedType] | None]
    | dict[int, SeedType | Sequence[SeedType] | dict[int, SeedType] | None]
    | None = None,
) -> dict[int, dict[int, int]]:
    """Generate random unitary seeds.

    Args:
        times (int): The number of random unitary operator.
        num_qubits (int): The number of qubits.
        seed (SeedType\
| Sequence[SeedType | Sequence[SeedType] | dict[int, SeedType] | None]\
| dict[int, SeedType | Sequence[SeedType] | dict[int, SeedType] | None]\
| None, optional):
            The seed of random generator. Defaults to None.

    Raises:
        TypeError:
            If the seed is not int, np.random.Generator, Sequence, or dict.
        ValueError:
            If the length of seed is not equal to times.

    Returns:
        dict[int, dict[int, int]]]: The random unitary seeds.
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


def check_random_unitary_seeds(
    times: int,
    num_qubits: int,
    random_unitary_seeds: dict[int, dict[int, int]] | None,
) -> None:
    """Check the input of the experiment.
    If you want to generate the seeds for all random unitary operator,
    you can use the function :func:`generate_random_unitary_seeds`
    in :mod:`qurry.process.randomized_measure.utils`.

    Args:
        times (int): The number of random unitary operator.
        num_qubits (int): The number of qubits.
        random_unitary_seeds (dict[int, dict[int, int]] | None):
            The seeds for all random unitary operator.
            This argument only takes input as type of :class:`dict[int, dict[int, int]]`.
            The first key is the index for the random unitary operator.
            The second key is the index for the qubit.

            .. code-block:: python

                {
                    0: {0: 1234, 1: 5678},
                    1: {0: 2345, 1: 6789},
                    2: {0: 3456, 1: 7890},
                }

    Raises:
        TypeError: If the `random_unitary_seeds` is not dict.
        ValueError: If the length of `random_unitary_seeds` is not equal to times.
        TypeError: If the `random_unitary_seeds[i]` is not dict.
        ValueError: If the length of `random_unitary_seeds[i]` is not equal to `num_qubits`.
        TypeError: If the `random_unitary_seeds[i][j]` is not int.

    """
    if random_unitary_seeds is None:
        return
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
    return


def generate_hash_from_trace_result(
    purity_or_echo: FloatType,
    classical_registers_actually: list[int],
    taking_time: float,
    counts_num: int,
    shots: int,
    preparing_datetime: str,
) -> str:
    """Generate the hash string from the trace result.
    We use SHA-1 algorithm to generate the hash string.

    Args:
        purity_or_echo (FloatType):
            The purity or echo value.
        classical_registers_actually (list[int]):
            The list of the selected classical registers.
        taking_time (float):
            The time taken for the calculation.
        counts_num (int):
            The number of counts.
        shots (int):
            The number of shots.
        preparing_datetime (str):
            The datetime string when preparing the all system result.

    Returns:
        str: The generated hash string.
    """
    hash_input = (
        f"purity_or_echo={purity_or_echo};"
        + f"classical_registers_actually={classical_registers_actually};"
        + f"taking_time={taking_time};"
        + f"counts_num={counts_num};"
        + f"shots={shots};"
        + f"preparing_datetime={preparing_datetime}"
    )
    hash_object = hashlib.sha1(hash_input.encode())
    hash_string = hash_object.hexdigest()
    return hash_string
