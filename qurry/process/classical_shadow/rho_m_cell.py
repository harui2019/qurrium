"""
================================================================
Postprocessing - Classical Shadow - Rho M Cell
(:mod:`qurry.process.classical_shadow.rho_m_cell`)
================================================================

"""

from typing import Literal, Union
import numpy as np

from .unitary_set import U_M_MATRIX, OUTER_PRODUCT, IDENTITY
from ..availability import (
    availablility,
    default_postprocessing_backend,
    # PostProcessingBackendLabel,
)

# from ..exceptions import (
#     PostProcessingRustImportError,
#     PostProcessingRustUnavailableWarning,
#     PostProcessingBackendDeprecatedWarning,
# )

# try:

#     from ...boorust import randomized  # type: ignore

#     purity_cell_2_rust_source = randomized.purity_cell_2_rust

#     RUST_AVAILABLE = True
#     FAILED_RUST_IMPORT = None
# except ImportError as err:
#     RUST_AVAILABLE = False
#     FAILED_RUST_IMPORT = err

#     def purity_cell_rust_source(*args, **kwargs):
#         """Dummy function for purity_cell_rust."""
#         raise PostProcessingRustImportError(
#             "Rust is not available, using python to calculate purity cell."
#         ) from FAILED_RUST_IMPORT


RUST_AVAILABLE = False
FAILED_RUST_IMPORT = None

BACKEND_AVAILABLE = availablility(
    "classical_shadow.rho_m_cell",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(RUST_AVAILABLE, False)


def rho_m_cell_py(
    idx: int,
    single_counts: dict[str, int],
    nu_shadow_direction: dict[int, Union[Literal[0, 1, 2], int]],
    selected_classical_registers: list[int],
) -> tuple[
    int,
    np.ndarray[tuple[int, int], np.dtype[np.complex128]],
    dict[int, np.ndarray[tuple[Literal[2], Literal[2]], np.dtype[np.complex128]]],
    list[int],
]:
    r"""rho_m calculation for single cell.

    The matrix :math:`\rho_{m_i}` is calculated by the following equation,
    .. math::
        \rho_{m_i} = \sum_{s} \frac{3}{\text{shots}} U_M^{(s) \dagger}
        \otimes \mathbb{1} U_M^{(s)} - \mathbb{1}

    The matrix :math:`\rho_m` is calculated by the following equation,
    .. math::
        \rho_m = \bigotimes_{i=0}^{n-1} \rho_{m_i}

    Args:
        idx (int):
            Index of the cell (counts).
        single_counts (dict[str, int]):
            Counts measured by the single quantum circuit.
        nu_shadow_direction (dict[int, Union[Literal[0, 1, 2], int]]):
            The shadow direction of the unitary operators.
        selected_classical_registers (list[int]):
            The list of **the index of the selected_classical_registers**.

    Returns:
        tuple[
            int,
            np.ndarray[tuple[int, int], np.dtype[np.complex128]],
            dict[int, np.ndarray[tuple[Literal[2], Literal[2]], np.dtype[np.complex128]]],
            list[int]
        ]:
            Index, rho_m, the set of rho_m_i, the sorted list of the selected qubits
    """

    num_classical_register = len(list(single_counts.keys())[0])
    shots = sum(single_counts.values())
    assert num_classical_register == len(
        nu_shadow_direction
    ), "The number of qubits and the number of shadow directions should be the same."

    # subsystem making
    selected_classical_registers_sorted = sorted(selected_classical_registers, reverse=True)
    single_counts_under_degree = {}
    for bitstring_all, num_counts_all in single_counts.items():
        bitstring = "".join(
            bitstring_all[num_classical_register - q_i - 1]
            for q_i in selected_classical_registers_sorted
        )
        if bitstring in single_counts_under_degree:
            single_counts_under_degree[bitstring] += num_counts_all
        else:
            single_counts_under_degree[bitstring] = num_counts_all

    # core calculation
    rho_m_i_k = {q_i: {} for q_i in selected_classical_registers_sorted}
    for bitstring in single_counts_under_degree:
        for q_i, s_q in zip(selected_classical_registers_sorted, bitstring):
            rho_m_i_k[q_i][bitstring] = (
                3
                * U_M_MATRIX[nu_shadow_direction[q_i]].conj().T
                @ OUTER_PRODUCT[s_q]
                @ U_M_MATRIX[nu_shadow_direction[q_i]]
            ) - IDENTITY
    rho_m_i = {
        q_i: np.zeros((2, 2), dtype=np.complex128) for q_i in selected_classical_registers_sorted
    }
    for q_i in selected_classical_registers_sorted:
        for bitstring, num_counts in single_counts_under_degree.items():
            rho_m_i[q_i] += rho_m_i_k[q_i][bitstring] * num_counts
        rho_m_i[q_i] /= shots

    rho_m = np.eye(2, dtype=np.complex128)
    for q_i in selected_classical_registers_sorted:
        rho_m = np.kron(rho_m, rho_m_i[q_i])

    return idx, rho_m, rho_m_i, selected_classical_registers_sorted
