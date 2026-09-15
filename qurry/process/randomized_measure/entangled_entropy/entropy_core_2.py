"""Post Processing - Randomized Measure - Entangled Entropy - Core 2
(:mod:`qurry.process.randomized_measure.entangled_entropy.entropy_core_2`)

This version introduces another way to process subsystems.

"""

from collections.abc import Iterable
import time
import warnings
import numpy as np

from .purity_cell_2 import purity_cell_2_py
from ...utils import shot_counts_selected_clreg_checker, selected_clregs_to_optlist
from ...availability import (
    availability,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ...exceptions import PostProcessingBackendDeprecatedWarning
from ....tools import ParallelManager

# pylint: disable=import-error,no-name-in-module
from ....boorust.randomized import entangled_entropy_core_2_rust  # type: ignore


BACKEND_AVAILABLE = availability(
    "randomized_measure.entangled_entropy.entropy_core_2", [("Rust", True, None)]
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(True, False)


def entangled_entropy_core_2_py(
    shots: int,
    counts: list[dict[str, int]],
    selected_classical_registers: Iterable[int] | None = None,
) -> tuple[dict[int, np.float64], list[int], str, float]:
    """The core function of entangled entropy by Python.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (Iterable[int] | None, optional):
            The list of **the index of the selected_classical_registers**.

    Returns:
        tuple[dict[int, np.float64], list[int], str, float]:
            Purity of each cell, Selected classical registers, Message, Time to calculate.
    """

    _measured_system_size, selected_classical_registers = shot_counts_selected_clreg_checker(
        shots,
        counts,
        selected_classical_registers,
    )

    msg = f"| Selected classical registers: {selected_classical_registers}"

    begin = time.time()

    pm = ParallelManager()
    purity_cell_result_list = pm.starmap(
        purity_cell_2_py,
        [(i, c, selected_classical_registers) for i, c in enumerate(counts)],
    )
    taken = round(time.time() - begin, 3)

    selected_classical_registers_sorted = sorted(selected_classical_registers, reverse=True)

    purity_cell_dict: dict[int, np.float64] = {}
    selected_classical_registers_checked: dict[int, bool] = {}
    for (
        idx,
        purity_cell_value,
        selected_classical_registers_sorted_result,
    ) in purity_cell_result_list:
        purity_cell_dict[idx] = purity_cell_value
        if selected_classical_registers_sorted_result != selected_classical_registers_sorted:
            selected_classical_registers_checked[idx] = False

    if len(selected_classical_registers_checked) > 0:
        warnings.warn(
            "Selected qubits are not sorted for "
            + f"{len(selected_classical_registers_checked)} cells.",
            RuntimeWarning,
        )

    return purity_cell_dict, selected_classical_registers_sorted, msg, taken


def entangled_entropy_core_2(
    shots: int,
    counts: list[dict[str, int]],
    selected_classical_registers: Iterable[int] | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[dict[int, np.float64] | dict[int, float], list[int], str, float]:
    """The core function of entangled entropy.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (Iterable[int] | None, optional):
            The list of **the index of the selected_classical_registers**.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.

    Returns:
        Purity of each cell, Selected qubits, Message, Time to calculate.
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
        return entangled_entropy_core_2_rust(shots, counts, selected_classical_registers)

    return entangled_entropy_core_2_py(shots, counts, selected_classical_registers)
