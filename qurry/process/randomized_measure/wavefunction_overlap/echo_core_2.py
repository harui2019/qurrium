"""
=========================================================================================
Postprocessing - Randomized Measure - Wavefunction Overlap - Echo Core 2
(:mod:`qurry.process.randomized_measure.wavefunction_overlap.echo_core_2`)
=========================================================================================

"""

import time
import warnings
from typing import Optional, Iterable
import numpy as np

from .echo_cell_2 import echo_cell_2_py, echo_cell_2_rust
from ...availability import (
    availablility,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ...exceptions import (
    PostProcessingRustImportError,
    PostProcessingRustUnavailableWarning,
    PostProcessingBackendDeprecatedWarning,
)
from ....tools import ParallelManager, workers_distribution

try:
    from ....boorust import randomized  # type: ignore

    overlap_echo_core_2_rust_source = randomized.overlap_echo_core_2_rust

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def overlap_echo_core_2_rust_source(*args, **kwargs):
        """Dummy function for entangled_entropy_core_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate overlap echo."
        ) from FAILED_RUST_IMPORT


BACKEND_AVAILABLE = availablility(
    "randomized_measure.wavefunction_overlap.echo_core_2",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
        ("Cython", "Depr.", None),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(
    RUST_AVAILABLE,
    False,
)


def overlap_echo_core_2_pyrust(
    shots: int,
    first_counts: list[dict[str, int]],
    second_counts: list[dict[str, int]],
    selected_classical_registers: Optional[Iterable[int]] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[
    dict[int, np.float64],
    list[int],
    str,
    float,
]:
    """The core function of wavefunction overlap by Python or Rust for just purity cell part.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        first_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        second_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (Optional[Iterable[int]], optional):
            The list of **the index of the selected_classical_registers**.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.

    Returns:
        tuple[dict[int, np.float64], list[int], str, float]:
            Purity of each cell, Selected classical registers, Message, Time to calculate.
    """
    assert len(first_counts) == len(second_counts), (
        "The number of counts must be equal, "
        + f"but the first counts is {len(first_counts)}, "
        + f"and the second counts is {len(second_counts)}"
    )

    # check shots
    sample_shots_01 = sum(first_counts[0].values())
    sample_shots_02 = sum(second_counts[0].values())
    for tmp01, tmp02, tmp01_name, tmp02_name in [
        (sample_shots_01, shots, "first counts", "shots"),
        (sample_shots_02, shots, "second counts", "shots"),
        (sample_shots_01, sample_shots_02, "first counts", "second counts"),
    ]:
        assert tmp01 == tmp02, (
            "The number of shots must be equal, "
            + f"but the {tmp01_name} is {tmp01}, and the {tmp02_name} is {tmp02}"
        )

    # Determine worker number
    launch_worker = workers_distribution()

    # Determine subsystem size
    measured_system_size = len(list(first_counts[0].keys())[0])
    measured_system_size_02 = len(list(second_counts[0].keys())[0])
    assert measured_system_size == measured_system_size_02, (
        "The number of bitstrings must be equal, "
        + f"but the first counts is {measured_system_size}, "
        + f"and the second counts is {measured_system_size_02}",
    )

    if selected_classical_registers is None:
        selected_classical_registers = list(range(measured_system_size))
    elif not isinstance(selected_classical_registers, Iterable):
        raise ValueError(
            "selected_classical_registers should be Iterable, "
            + f"but get {type(selected_classical_registers)}"
        )
    else:
        selected_classical_registers = list(selected_classical_registers)
    # dummy_list = range(measured_system_size)
    # selected_classical_registers_actual = [
    # dummy_list[c_i] for c_i in selected_classical_registers]
    # assert len(selected_classical_registers_actual) == len(
    #     set(selected_classical_registers_actual)
    # ), (
    #     "The selected_classical_registers should not have duplicated values, "
    #     + f"but get {selected_classical_registers_actual} from {selected_classical_registers}"
    # )
    # msg = f"| Selected qubits: {selected_classical_registers_actual}"
    assert all(
        0 <= q_i < measured_system_size for q_i in selected_classical_registers
    ), f"Invalid selected classical registers: {selected_classical_registers}"
    msg = f"| Selected classical registers: {selected_classical_registers}"

    counts_pair = list(zip(first_counts, second_counts))

    begin = time.time()

    if backend == "Cython":
        warnings.warn(
            f"Cython is deprecated, using {DEFAULT_PROCESS_BACKEND} to calculate purity cell.",
            PostProcessingBackendDeprecatedWarning,
        )
        backend = DEFAULT_PROCESS_BACKEND
    cell_calculation = echo_cell_2_rust if backend == "Rust" else echo_cell_2_py

    pool = ParallelManager(launch_worker)
    echo_cell_result_list = pool.starmap(
        cell_calculation,
        [(i, c1, c2, selected_classical_registers) for i, (c1, c2) in enumerate(counts_pair)],
    )

    taken = round(time.time() - begin, 3)

    selected_classical_registers_sorted = sorted(selected_classical_registers, reverse=True)

    echo_cell_dict: dict[int, np.float64] = {}
    selected_classical_registers_checked: dict[int, bool] = {}
    for (
        idx,
        echo_cell_value,
        selected_classical_registers_sorted_result,
    ) in echo_cell_result_list:
        echo_cell_dict[idx] = echo_cell_value
        if selected_classical_registers_sorted_result != selected_classical_registers_sorted:
            selected_classical_registers_checked[idx] = False

    if len(selected_classical_registers_checked) > 0:
        warnings.warn(
            "Selected qubits are not sorted for "
            + f"{len(selected_classical_registers_checked)} cells.",
            RuntimeWarning,
        )

    return echo_cell_dict, selected_classical_registers_sorted, msg, taken


def overlap_echo_core_2_allrust(
    shots: int,
    first_counts: list[dict[str, int]],
    second_counts: list[dict[str, int]],
    selected_classical_registers: Optional[Iterable[int]] = None,
) -> tuple[
    dict[int, np.float64],
    list[int],
    str,
    float,
]:
    """The core function of wavefunction overlap by Rust for just purity cell part.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        first_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        second_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (Optional[Iterable[int]], optional):
            The list of **the index of the selected_classical_registers**.

    Returns:
        tuple[dict[int, np.float64], list[int], str, float]:
            Purity of each cell, Selected classical registers, Message, Time to calculate.
    """

    return overlap_echo_core_2_rust_source(
        shots,
        first_counts,
        second_counts,
        (
            selected_classical_registers
            if selected_classical_registers is None
            else list(selected_classical_registers)
        ),
    )


def overlap_echo_core_2(
    shots: int,
    first_counts: list[dict[str, int]],
    second_counts: list[dict[str, int]],
    selected_classical_registers: Optional[Iterable[int]] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[
    dict[int, np.float64],
    list[int],
    str,
    float,
]:
    """The core function of wavefunction overlap for just purity cell part.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        first_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        second_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (Optional[Iterable[int]], optional):
            The list of **the index of the selected_classical_registers**.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.

    Returns:
        tuple[dict[int, np.float64], list[int], str, float]:
            Purity of each cell, Selected classical registers, Message, Time to calculate.
    """

    if backend == "Cython":
        warnings.warn(
            "Cython backend is deprecated, using Python or Rust to calculate purity cell.",
            PostProcessingBackendDeprecatedWarning,
        )
        backend = DEFAULT_PROCESS_BACKEND

    if backend == "Rust":
        if RUST_AVAILABLE:
            return overlap_echo_core_2_allrust(
                shots, first_counts, second_counts, selected_classical_registers
            )
        backend = "Python"
        warnings.warn(
            f"Rust is not available, using {backend} to calculate purity cell."
            + f" Check the error: {FAILED_RUST_IMPORT}",
            PostProcessingRustUnavailableWarning,
        )

    return overlap_echo_core_2_pyrust(
        shots, first_counts, second_counts, selected_classical_registers, backend
    )
