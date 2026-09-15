"""Post Processing - Randomized Measure - Wavefunction Overlap - Echo Core 2
(:mod:`qurry.process.randomized_measure.wavefunction_overlap.echo_core_2`)

"""

from collections.abc import Iterable
import time
import warnings
import numpy as np

from .echo_cell_2 import echo_cell_2_py
from ...utils import shot_counts_selected_clreg_checker, selected_clregs_to_optlist
from ...availability import (
    availability,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ...exceptions import PostProcessingBackendDeprecatedWarning
from ....tools import ParallelManager

# pylint: disable=import-error,no-name-in-module
from ....boorust.randomized import overlap_echo_core_2_rust  # type: ignore

BACKEND_AVAILABLE = availability(
    "randomized_measure.wavefunction_overlap.echo_core_2", [("Rust", True, None)]
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(True, False)


def overlap_echo_core_2_py(
    shots: int,
    first_counts: list[dict[str, int]],
    second_counts: list[dict[str, int]],
    selected_classical_registers: Iterable[int] | None = None,
) -> tuple[dict[int, np.float64] | dict[int, float], list[int], str, float]:
    """The core function of wavefunction overlap by Python or Rust for just purity cell part.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        first_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        second_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (Iterable[int] | None, optional):
            The list of **the index of the selected_classical_registers**.

    Returns:
        Purity of each cell, Selected classical registers, Message, Time to calculate.
    """
    assert len(first_counts) == len(second_counts), (
        "The number of counts must be equal, "
        + f"but the first counts is {len(first_counts)}, "
        + f"and the second counts is {len(second_counts)}"
    )

    sample_bitstrings_num_01, selected_classical_registers = shot_counts_selected_clreg_checker(
        shots,
        first_counts,
        selected_classical_registers,
    )
    sample_bitstrings_num_02, _selected_classical_registers_02 = shot_counts_selected_clreg_checker(
        shots,
        second_counts,
        selected_classical_registers,
    )
    assert sample_bitstrings_num_01 == sample_bitstrings_num_02, (
        "The number of bitstrings must be equal, "
        + f"but the first counts is {sample_bitstrings_num_01}, "
        + f"and the second counts is {sample_bitstrings_num_02}",
    )
    msg = f"| Selected classical registers: {selected_classical_registers}"

    counts_pair = zip(first_counts, second_counts)

    begin = time.time()

    pm = ParallelManager()
    echo_cell_result_list = pm.starmap(
        echo_cell_2_py,
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


def overlap_echo_core_2(
    shots: int,
    first_counts: list[dict[str, int]],
    second_counts: list[dict[str, int]],
    selected_classical_registers: Iterable[int] | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[dict[int, np.float64] | dict[int, float], list[int], str, float]:
    """The core function of wavefunction overlap for just purity cell part.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        first_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        second_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (Iterable[int] | None, optional):
            The list of **the index of the selected_classical_registers**.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.

    Returns:
        Purity of each cell, Selected classical registers, Message, Time to calculate.
    """

    if backend not in BACKEND_AVAILABLE[1]:
        warnings.warn(
            f"{backend} is unknown, "
            + f"using {DEFAULT_PROCESS_BACKEND} to calculate entangled_entropy.",
        )
        backend = DEFAULT_PROCESS_BACKEND
    elif backend == "Cython":
        warnings.warn(
            "The Cython is deprecated, "
            + f"using {DEFAULT_PROCESS_BACKEND} to calculate entangled_entropy.",
            PostProcessingBackendDeprecatedWarning,
        )
        backend = DEFAULT_PROCESS_BACKEND

    if backend == "Rust":
        selected_classical_registers = selected_clregs_to_optlist(selected_classical_registers)
        return overlap_echo_core_2_rust(
            shots, first_counts, second_counts, selected_classical_registers
        )

    return overlap_echo_core_2_py(shots, first_counts, second_counts, selected_classical_registers)
