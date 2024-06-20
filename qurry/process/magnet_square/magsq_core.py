"""
================================================================
Postprocessing - Magnet Square - Magnet Square Core
(:mod:`qurry.process.magnet_square.magsq_core`)
================================================================

"""

import time
import warnings
from typing import Union, Optional
import numpy as np

from .magsq_cell import magsq_cell_py  # , magsq_cell_rust
from ..availability import (
    availablility,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ..exceptions import (
    # PostProcessingRustImportError,
    PostProcessingRustUnavailableWarning,
)
from ...tools import ParallelManager, workers_distribution


# try:
#     from ...boorust import magsq  # type: ignore

#     magnetic_square_core_rust_source = magsq.magnetic_square_core_rust

#     RUST_AVAILABLE = True
#     FAILED_RUST_IMPORT = None
# except ImportError as err:
#     RUST_AVAILABLE = False
#     FAILED_RUST_IMPORT = err

#     def magnetic_square_core_rust_source(*args, **kwargs):
#         """Dummy function for magnetic_square_core_rust."""
#         raise PostProcessingRustImportError(
#             "Rust is not available, using python to calculate magnetic square."
#         ) from FAILED_RUST_IMPORT


BACKEND_AVAILABLE = availablility(
    "magnet_square.magnsq_core",
    [
        # ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(
    # RUST_AVAILABLE, False
    False,
    False,
)


# def magnetic_square_core_allrust(
#     shots: int,
#     counts: list[dict[str, int]],
#     num_qubits: int,
# ) -> tuple[Union[float, np.float64], dict[int, Union[float, np.float64]], int, float]:
#     """The core function of magnet square by Rust."""
#     return magnetic_square_core_rust_source(counts, shots, num_qubits)


def magnetic_square_core_pyrust(
    counts: list[dict[str, int]],
    shots: int,
    num_qubits: int,
    multiprocess_pool_size: Optional[int] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[Union[float, np.float64], dict[int, Union[float, np.float64]], int, float, str]:
    """The core function of magnet square by Python and Rust.

    Args:
        counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        shots (int):
            Shots of the experiment on quantum machine.
        num_qubits (int):
            Number of qubits.
        multiprocess_pool_size (int, optional):
            Number of workers. Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Postprocessing backend. Defaults to DEFAULT_PROCESS_BACKEND.

    Returns:
        tuple[
            Union[float, np.float64],
            dict[int, Union[float, np.float64]],
            int,
            float,
            str
        ]:
            Magnitudes square, Magnitudes square cell,
            Length of counts, Time taken, Message.
    """

    # Determine worker number
    launch_worker = workers_distribution(multiprocess_pool_size)
    msg = ""

    length = len(counts)
    begin = time.time()

    if backend == "Rust":
        warnings.warn(
            PostProcessingRustUnavailableWarning(
                "Rust is not ready, using python to calculate magnetic square."
            )
        )
    cell_calculations = magsq_cell_py  # if backend == "Python" else magsq_cell_rust

    if launch_worker == 1:
        magnetsq_cell_items: list[tuple[int, Union[float, np.float64]]] = []
        msg += f", single process, {length} overlaps, it will take a lot of time."
        print(msg)
        for i, c in enumerate(counts):
            magnetsq_cell_items.append(cell_calculations(i, c, shots))

    else:
        msg += f", {launch_worker} workers, {length} counts."
        pool = ParallelManager(launch_worker)
        magnetsq_cell_items = pool.starmap(
            cell_calculations, [(i, c, shots) for i, c in enumerate(counts)]
        )

    taken = round(time.time() - begin, 3)
    magnetsq_cell_dict = dict(magnetsq_cell_items)
    magnetsq = (sum(magnetsq_cell_dict.values()) + num_qubits) / (num_qubits**2)

    return magnetsq, magnetsq_cell_dict, length, taken, msg


def magnetic_square_core(
    counts: list[dict[str, int]],
    shots: int,
    num_qubits: int,
    multiprocess_pool_size: Optional[int] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[Union[float, np.float64], dict[int, Union[float, np.float64]], int, float, str]:
    """The core function of magnet square by Python.

    Args:
        counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        shots (int):
            Shots of the experiment on quantum machine.
        num_qubits (int):
            Number of qubits.
        multiprocess_pool_size (int, optional):
            Number of workers. Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Postprocessing backend. Defaults to DEFAULT_PROCESS_BACKEND.

    Returns:
        tuple[
            Union[float, np.float64],
            dict[int, Union[float, np.float64]],
            int,
            float,
            str
        ]:
            Magnitudes square, Magnitudes square cell,
            Length of counts, Time taken, Message.
    """

    # if backend == "Rust":
    #     if RUST_AVAILABLE:
    #         return magnetic_square_core_rust_source(counts, shots, num_qubits)

    #     warnings.warn(
    #         PostProcessingRustUnavailableWarning(
    #             "Rust is not available, using python to calculate magnetic square."
    #         )
    #     )
    if backend == "Rust":
        warnings.warn(
            PostProcessingRustUnavailableWarning(
                "Rust is not ready, using python to calculate magnetic square."
            )
        )

    return magnetic_square_core_pyrust(counts, shots, num_qubits, multiprocess_pool_size, backend)
