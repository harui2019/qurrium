"""Post Processing - Magnetization Square - Core (:mod:`qurry.process.magnet_square.magsq_core`)"""

import time
from itertools import permutations
import numpy as np

from ..availability import availability, default_postprocessing_backend, PostProcessingBackendLabel
from ..utils import single_counts_recount_proto, FloatType
from ...tools import ParallelManager

# pylint: disable=import-error,no-name-in-module
from ...boorust.magnet_square import (  # type: ignore
    magnet_square_core_rust,
    z_dir_magnet_square_core_rust,
)

BACKEND_AVAILABLE = availability("magnet_square.magnsq_core", [("Rust", True, None)])
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(True, False)


def magsq_cell_py_deprecated(
    idx: int, single_counts: dict[str, int], shots: int
) -> tuple[int, np.float64]:
    """Calculate the magnitudes square cell

    Args:
        idx (int): Index of the cell (counts).
        single_counts (dict[str, int]): Single counts of the cell.
        shots (int): Shots of the experiment on quantum machine.

    Returns:
        tuple[int, np.float64]: Index, one of magnitudes square.
    """

    magnetsq_cell = np.float64(0)
    for bits in single_counts:
        ratio = np.float64(single_counts[bits]) / shots
        magnetsq_cell += ratio if bits[0] == bits[1] else -ratio
    return idx, magnetsq_cell


def magsq_cell_py(idx: int, single_counts: dict[str, int], shots: int) -> tuple[int, np.float64]:
    """Calculate the magnitudes square cell

    Args:
        idx (int): Index of the cell (counts).
        single_counts (dict[str, int]): Single counts of the cell.
        shots (int): Shots of the experiment on quantum machine.

    Returns:
        tuple[int,  np.float64]: Index, one of magnitudes square.
    """

    return idx, sum(
        np.float64(c) * (1 if bits[0] == bits[1] else -1) / shots
        for bits, c in single_counts.items()
    ) + np.float64(0)


def magsq_cell_wrapper(arguments: tuple[int, dict[str, int], int]) -> tuple[int, np.float64]:
    """Wrapper for the magnetic square cell.

    Args:
        arguments (tuple[int, dict[str, int], int]):
            The arguments for the magnetic square cell.

            - idx (int): Index of the cell (counts).
            - single_counts (dict[str, int]): Single counts of the cell.
            - shots (int): Shots of the experiment on quantum machine.

    Returns:
        tuple[int, np.float64]: Index, one of magnitudes square.
    """
    return magsq_cell_py(*arguments)


def magnet_square_core(
    shots: int,
    counts: list[dict[str, int]],
    num_qubits: int,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[FloatType, dict[int, float] | dict[int, np.float64], float]:
    """The core function of Magnetization square.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        num_qubits (int): Number of qubits.
        backend (PostProcessingBackendLabel, optional):
            Post Processing backend. Defaults to DEFAULT_PROCESS_BACKEND.

    Returns:
        Magnetization square, magnetization square cell, time taken.
    """

    if len(counts) != num_qubits * (num_qubits - 1):
        raise ValueError(
            f"Counts length {len(counts)} must be equal to "
            f"num_qubits * (num_qubits - 1) = {num_qubits * (num_qubits - 1)}."
        )

    if backend == "Rust":
        return magnet_square_core_rust(shots, counts, num_qubits)

    sample_counts_sum = sum(counts[0].values())
    assert shots == sample_counts_sum, (
        f"Shots: {shots} must be equal to the sum of counts: {sample_counts_sum}."
    )
    assert all(len(bits) == 2 for bits in counts[0]), f"Bits must be 2 bit, but found: {counts[0]}"

    begin = time.time()
    pm = ParallelManager()
    magnetsq_cell_dict = dict(
        pm.map(magsq_cell_wrapper, [(i, c, shots) for i, c in enumerate(counts)])
    )
    magnetsq = np.float64(sum(magnetsq_cell_dict.values()) + num_qubits) / (num_qubits**2)
    taken = round(time.time() - begin, 3)

    return magnetsq, magnetsq_cell_dict, taken


def z_dir_magnet_square_core(
    shots: int,
    single_counts: dict[str, int],
    num_qubits: int,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[FloatType, dict[int, float] | dict[int, np.float64], float]:
    """The core function of Z direction Magnetization square.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        single_counts (dict[str, int]): Single count.
        num_qubits (int): Number of qubits.
        backend (PostProcessingBackendLabel, optional):
            Post Processing backend. Defaults to DEFAULT_PROCESS_BACKEND.

    Returns:
        Magnetization square, magnetization square cell, time taken.
    """

    if backend == "Rust":
        return z_dir_magnet_square_core_rust(shots, single_counts, num_qubits)

    sample_counts_sum = sum(single_counts.values())
    assert shots == sample_counts_sum, (
        f"Shots: {shots} must be equal to the sum of counts: {sample_counts_sum}."
    )

    begin = time.time()
    pm = ParallelManager()
    magnetsq_cell_dict = dict(
        pm.map(
            magsq_cell_wrapper,
            [
                (idx, single_counts_recount_proto(single_counts, num_qubits, [i, j]), shots)
                for idx, (i, j) in enumerate(permutations(range(num_qubits), 2))
            ],
        )
    )
    magnetsq = np.float64(sum(magnetsq_cell_dict.values()) + num_qubits) / (num_qubits**2)
    taken = round(time.time() - begin, 3)

    return magnetsq, magnetsq_cell_dict, taken
