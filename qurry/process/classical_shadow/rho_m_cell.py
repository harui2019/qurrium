"""
================================================================
Postprocessing - Classical Shadow - Rho M Cell
(:mod:`qurry.process.classical_shadow.rho_m_cell`)
================================================================

"""

from typing import Literal, Union
import numpy as np

from .unitary_set import U_M_MATRIX, OUTER_PRODUCT, IDENTITY


def rho_m_py(
    idx: int,
    single_counts: dict[str, int],
    nu_shadow_direction: dict[int, Union[Literal[0, 1, 2], int]],
    selected_qubits: list[int],
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
        selected_qubits (list[int]):
            The list of the selected qubits.

    Returns:
        tuple[
            int,
            np.ndarray[tuple[int, int], np.dtype[np.complex128]],
            dict[int, np.ndarray[tuple[Literal[2], Literal[2]], np.dtype[np.complex128]]],
            list[int]
        ]:
            Index, rho_m, the set of rho_m_i, the sorted list of the selected qubits
    """

    num_qubits = len(list(single_counts.keys())[0])
    shots = sum(single_counts.values())
    assert num_qubits == len(
        nu_shadow_direction
    ), "The number of qubits and the number of shadow directions should be the same."

    # subsystem making
    selected_qubits_sorted = sorted(selected_qubits, reverse=True)
    single_counts_under_degree = {}
    for bitstring_all, num_counts_all in single_counts.items():
        bitstring = "".join(bitstring_all[num_qubits - q_i - 1] for q_i in selected_qubits_sorted)
        if bitstring in single_counts_under_degree:
            single_counts_under_degree[bitstring] += num_counts_all
        else:
            single_counts_under_degree[bitstring] = num_counts_all

    # core calculation
    rho_m_i_k = {q_i: {} for q_i in selected_qubits_sorted}
    for bitstring in single_counts:
        for q_i, s_q in zip(selected_qubits_sorted, bitstring):
            rho_m_i_k[q_i][bitstring] = (
                3
                * U_M_MATRIX[nu_shadow_direction[q_i]].conj().T
                @ OUTER_PRODUCT[s_q]
                @ U_M_MATRIX[nu_shadow_direction[q_i]]
            ) - IDENTITY
    rho_m_i = {q_i: np.zeros((2, 2), dtype=np.complex128) for q_i in selected_qubits_sorted}
    for q_i in selected_qubits_sorted:
        for bitstring, num_counts in single_counts.items():
            rho_m_i[q_i] += rho_m_i_k[q_i][bitstring] * num_counts
        rho_m_i[q_i] /= shots

    rho_m = np.eye(2, dtype=np.complex128)
    for q_i in selected_qubits_sorted:
        rho_m = np.kron(rho_m, rho_m_i[q_i])

    return idx, rho_m, rho_m_i, selected_qubits_sorted
