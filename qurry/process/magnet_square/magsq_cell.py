"""
================================================================
Postprocessing - Magnet Square - Magnet Square Cell
(:mod:`qurry.process.magnet_square.magsq_cell`)
================================================================

"""

from typing import Union
import numpy as np

from ..availability import availablility, default_postprocessing_backend

# from ..exceptions import (
#     PostProcessingRustImportError,
# )


# try:
#     from ...boorust import magsq  # type: ignore

#     magnetic_square_core_rust_source = magsq.magnetic_square_core_rust

#     RUST_AVAILABLE = True
#     FAILED_RUST_IMPORT = None
# except ImportError as err:
#     RUST_AVAILABLE = False
#     FAILED_RUST_IMPORT = err

#     def magsq_cell_rust_source(*args, **kwargs):
#         """Dummy function for  magsq_cell_rust."""
#         raise PostProcessingRustImportError(
#             "Rust is not available, using python to calculate magnetic square."
#         ) from FAILED_RUST_IMPORT


BACKEND_AVAILABLE = availablility(
    "magnet_square.magnsq_cell",
    [
        # ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(
    # RUST_AVAILABLE, False
    False,
    False,
)


# def magsq_cell_rust(
#     idx: int,
#     single_counts: dict[str, int],
#     shots: int,
# ) -> tuple[int, Union[float, np.float64]]:
#     """Calculate the magnitudes square cell by Rust.

#     Args:
#         idx (int): Index of the cell (counts).
#         single_counts (dict[str, int]): Single counts of the cell.
#         shots (int): Shots of the experiment on quantum machine.

#     Returns:
#         tuple[int, Union[float, np.float64]]: One of magnitudes square.
#     """
#     return magnetic_square_core_rust_source(idx, single_counts, shots)


def magsq_cell_py(
    idx: int,
    single_counts: dict[str, int],
    shots: int,
) -> tuple[int, Union[float, np.float64]]:
    """Calculate the magnitudes square cell

    Args:
        idx (int): Index of the cell (counts).
        single_counts (dict[str, int]): Single counts of the cell.
        shots (int): Shots of the experiment on quantum machine.

    Returns:
        tuple[int, Union[float, np.float64]]: Index, one of magnitudes square.
    """
    sum_counts = sum(single_counts.values())
    assert shots == sum_counts, f"Shots: {shots} must be equal to the sum of counts: {sum_counts}."

    _magnetsq_cell = np.float64(0)
    for bits in single_counts:
        assert len(bits) == 2, f"Bits must be 2 bit: {bits}"
        # if bits in ("00", "11"):
        ratio = np.float64(single_counts[bits]) / shots
        _magnetsq_cell += ratio if bits[0] == bits[1] else -ratio
    return idx, _magnetsq_cell
