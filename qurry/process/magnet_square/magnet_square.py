"""Post Processing - Magnetization Square - Magnetization Square
(:mod:`qurry.process.magnet_square.magnet_square`)

"""

from typing import TypedDict
import numpy as np
import tqdm

from .magsq_core import magnet_square_core, z_dir_magnet_square_core, DEFAULT_PROCESS_BACKEND
from ..availability import PostProcessingBackendLabel
from ..utils import FloatType


class MagnetSquareResult(TypedDict):
    """Magnetization Square type."""

    magnet_square: FloatType
    """Magnetization Square."""
    magnet_square_cells: dict[int, float] | dict[int, np.float64]
    """Magnetization Square cells."""
    taking_time: float
    """Taking time."""


def magnetization_square(
    shots: int,
    counts: list[dict[str, int]],
    num_qubits: int,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: tqdm.tqdm | None = None,
) -> MagnetSquareResult:
    """Calculate the magnetization square.

    Args:
        shots (int): Number of shots.
        counts (list[dict[str, int]]): List of counts.
        num_qubits (int): Number of qubits.
        backend (PostProcessingBackendLabel, optional):
            Backend to use. Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (tqdm.tqdm | None, optional): Progress bar. Defaults to None.

    Returns:
        MagnetSquare: Magnetization Square.
    """
    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description("Magnetization Square being calculated.")

    magsq, magnet_square_cells, taking_time = magnet_square_core(
        shots=shots, counts=counts, num_qubits=num_qubits, backend=backend
    )
    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description(f"Magnetization Square calculated in {taking_time} seconds.")

    return {
        "magnet_square": magsq,
        "magnet_square_cells": magnet_square_cells,
        "taking_time": taking_time,
    }


def z_dir_magnetization_square(
    shots: int,
    single_counts: dict[str, int],
    num_qubits: int,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: tqdm.tqdm | None = None,
) -> MagnetSquareResult:
    """Calculate the magnetization square for Z direction.

    Args:
        shots (int): Number of shots.
        single_counts (dict[str, int]): Single count.
        num_qubits (int): Number of qubits.
        backend (PostProcessingBackendLabel, optional):
            Backend to use. Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (tqdm.tqdm | None, optional): Progress bar. Defaults to None.
    Returns:
        MagnetSquare: Magnetization Square.
    """
    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description("Z Direction Magnetization Square being calculated.")

    magsq, magnet_square_cells, taking_time = z_dir_magnet_square_core(
        shots=shots, single_counts=single_counts, num_qubits=num_qubits, backend=backend
    )

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description(
            f"Z Direction Magnetization Square calculated in {taking_time} seconds."
        )

    return {
        "magnet_square": magsq,
        "magnet_square_cells": magnet_square_cells,
        "taking_time": taking_time,
    }
