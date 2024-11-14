"""
================================================================
Postprocessing - Classical Shadow - Classical Shadow
(:mod:`qurry.process.classical_shadow.classical_shadow`)
================================================================

"""

from typing import Literal, Union, Optional, TypedDict
import warnings
from itertools import combinations
import tqdm
import numpy as np

from .rho_m_core import rho_m_core_py
from ..availability import (
    availablility,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)


RUST_AVAILABLE = False
FAILED_RUST_IMPORT = None

BACKEND_AVAILABLE = availablility(
    "classical_shadow.classical_shadow",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(RUST_AVAILABLE, False)


class ClassicalShadowBasic(TypedDict):
    """The basic information of the classical shadow."""

    rho_m_dict: dict[int, np.ndarray[tuple[int, int], np.dtype[np.complex128]]]
    """The dictionary of Rho M."""
    rho_m_i_dict: dict[
        int, dict[int, np.ndarray[tuple[Literal[2], Literal[2]], np.dtype[np.complex128]]]
    ]
    """The dictionary of Rho M I."""
    selected_classical_registers_sorted: list[int]
    """The list of the selected_classical_registers."""
    taken: float
    """The time taken for the calculation."""


class ClassicalShadowExpectation(ClassicalShadowBasic):
    """The expectation value of Rho."""

    expect_rho: np.ndarray[tuple[int, int], np.dtype[np.complex128]]
    """The expectation value of Rho."""


def expectation_rho_core(
    rho_m_dict: dict[int, np.ndarray[tuple[int, int], np.dtype[np.complex128]]],
    selected_classical_registers_sorted: list[int],
) -> np.ndarray[tuple[int, int], np.dtype[np.complex128]]:
    """Calculate the expectation value of Rho.

    Args:
        rho_m_dict (dict[int, np.ndarray[tuple[int, int], np.dtype[np.complex128]]]):
            The dictionary of Rho M.
            The dictionary of Rho M I.
        selected_classical_registers_sorted (list[int]):
            The list of the selected_classical_registers.

    Returns:
        np.ndarray[tuple[int, int], np.dtype[np.complex128]]: The expectation value of Rho.
    """

    expect_rho = np.zeros(
        (
            2 ** len(selected_classical_registers_sorted),
            2 ** len(selected_classical_registers_sorted),
        ),
        dtype=np.complex128,
    )
    for _, rho_m in rho_m_dict.items():
        expect_rho += rho_m
    expect_rho /= len(rho_m_dict)

    return expect_rho


def expectation_rho(
    shots: int,
    counts: list[dict[str, int]],
    random_unitary_um: dict[int, dict[int, Union[Literal[0, 1, 2], int]]],
    selected_classical_registers: list[int],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: Optional[tqdm.tqdm] = None,
) -> ClassicalShadowExpectation:
    """Expectation value of Rho.

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The list of the counts.
        random_unitary_um (dict[int, dict[int, Union[Literal[0, 1, 2], int]]]):
            The shadow direction of the unitary operators.
        selected_classical_registers (list[int]):
            The list of **the index of the selected_classical_registers**.
        backend (PostProcessingBackendLabel, optional):
            The backend for the postprocessing.
            Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (Optional[tqdm.tqdm], optional):
            The progress bar.
            Defaults to None.

    Returns:
        ClassicalShadowExpectation: The expectation value of Rho.
    """

    if backend == "Rust":
        warnings.warn(
            "Rust is not available, using python to calculate classical shadow.",
        )
        backend = "Python"

    rho_m_dict, rho_m_i_dict, selected_classical_registers_sorted, msg, taken = rho_m_core_py(
        shots,
        counts,
        random_unitary_um,
        selected_classical_registers,
    )
    if pbar is not None:
        pbar.set_description(msg)
    assert len(counts) == len(
        rho_m_dict
    ), f"The number of counts: {len(counts)} and rho_m: {len(rho_m_dict)} are different"

    expect_rho = expectation_rho_core(
        rho_m_dict=rho_m_dict,
        selected_classical_registers_sorted=selected_classical_registers_sorted,
    )

    return ClassicalShadowExpectation(
        expect_rho=expect_rho,
        rho_m_dict=rho_m_dict,
        rho_m_i_dict=rho_m_i_dict,
        selected_classical_registers_sorted=selected_classical_registers_sorted,
        taken=taken,
    )


class ClassicalShadowPurity(ClassicalShadowBasic):
    """The expectation value of Rho."""

    purity: float
    """The purity calculated by classical shadow."""


def trace_rho_square_core(
    rho_m_dict: dict[int, np.ndarray[tuple[int, int], np.dtype[np.complex128]]],
) -> float:
    """Calculate the trace of Rho square.

    Args:
        rho_m_dict (dict[int, np.ndarray[tuple[int, int], np.dtype[np.complex128]]]):
            The dictionary of Rho M.

    Returns:
        float: The trace of Rho square.
    """

    num_n_u = len(rho_m_dict)
    rho_traced_sum = 0

    rho_m_dict_combinations = combinations(rho_m_dict.items(), 2)
    for (_idx1, rho_m1), (_idx2, rho_m2) in rho_m_dict_combinations:
        rho_traced_sum += np.trace(np.dot(rho_m1, rho_m2))
    rho_traced_sum /= num_n_u * (num_n_u - 1)

    return rho_traced_sum


def trace_rho_square(
    shots: int,
    counts: list[dict[str, int]],
    random_unitary_um: dict[int, dict[int, Union[Literal[0, 1, 2], int]]],
    selected_classical_registers: list[int],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: Optional[tqdm.tqdm] = None,
) -> ClassicalShadowPurity:
    """Trace of Rho square.

    Args:
        expect_rho (np.ndarray[tuple[int, int], np.dtype[np.complex128]]):
            The expectation value of Rho.

    Returns:
        float: The trace of Rho.
    """

    if backend == "Rust":
        warnings.warn(
            "Rust is not available, using python to calculate classical shadow.",
        )
        backend = "Python"

    rho_m_dict, rho_m_i_dict, selected_classical_registers_sorted, msg, taken = rho_m_core_py(
        shots,
        counts,
        random_unitary_um,
        selected_classical_registers,
    )
    if pbar is not None:
        pbar.set_description(msg)

    rho_traced_sum = trace_rho_square_core(rho_m_dict=rho_m_dict)

    return ClassicalShadowPurity(
        purity=rho_traced_sum,
        rho_m_dict=rho_m_dict,
        rho_m_i_dict=rho_m_i_dict,
        selected_classical_registers_sorted=selected_classical_registers_sorted,
        taken=taken,
    )


class ClassicalShadowComplex(ClassicalShadowBasic):
    """The expectation value of Rho and the purity calculated by classical shadow."""

    expect_rho: np.ndarray[tuple[int, int], np.dtype[np.complex128]]
    """The expectation value of Rho."""
    purity: float
    """The purity calculated by classical shadow."""


def classical_shadow_complex(
    shots: int,
    counts: list[dict[str, int]],
    random_unitary_um: dict[int, dict[int, Union[Literal[0, 1, 2], int]]],
    selected_classical_registers: list[int],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: Optional[tqdm.tqdm] = None,
) -> ClassicalShadowComplex:
    """Calculate the expectation value of Rho and the purity by classical shadow.

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The list of the counts.
        random_unitary_um (dict[int, dict[int, Union[Literal[0, 1, 2], int]]]):
            The shadow direction of the unitary operators.
        selected_classical_registers (list[int]):
            The list of **the index of the selected_classical_registers**.
        backend (PostProcessingBackendLabel, optional):
            The backend for the postprocessing.
            Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (Optional[tqdm.tqdm], optional):
            The progress bar.
            Defaults to None.

    Returns:
        ClassicalShadowComplex:
            The expectation value of Rho and the purity calculated by classical shadow.
    """

    if backend == "Rust":
        warnings.warn(
            "Rust is not available, using python to calculate classical shadow.",
        )
        backend = "Python"

    rho_m_dict, rho_m_i_dict, selected_classical_registers_sorted, msg, taken = rho_m_core_py(
        shots,
        counts,
        random_unitary_um,
        selected_classical_registers,
    )
    if pbar is not None:
        pbar.set_description(msg)

    expect_rho = expectation_rho_core(
        rho_m_dict=rho_m_dict,
        selected_classical_registers_sorted=selected_classical_registers_sorted,
    )

    trace_rho_sum = trace_rho_square_core(rho_m_dict=rho_m_dict)

    return ClassicalShadowComplex(
        expect_rho=expect_rho,
        purity=trace_rho_sum,
        rho_m_dict=rho_m_dict,
        rho_m_i_dict=rho_m_i_dict,
        selected_classical_registers_sorted=selected_classical_registers_sorted,
        taken=taken,
    )
