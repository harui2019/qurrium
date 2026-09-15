"""Post Processing - Classical Shadow - Rho Process - Rho M Core
(:mod:`qurry.process.classical_shadow.rho_process.rho_m_core`)

"""

from collections.abc import Iterable
import time
import numpy as np
import numpy.typing as npt

from .unitary_set import ShadowRandomBasis, ShadowBasisMethod, ShadowBasisType, DEFAULT_SHADOW_BASIS
from ..utils import spreadout
from ...utils import (
    BaseMethodEnum,
    counts_list_recount_pyrust,
    shot_counts_selected_clreg_checker_pyrust,
)


class RhoMethod(BaseMethodEnum):
    """Whether to use the multi_shots or single_shots method for rho_m_cell calculation.
    For the "multi_shots" methods, the counts and random basis are used as is.
    For the "single_shots" methods, the counts and random basis are
    converted to single shot per snapshot for classical shadow post-processing.

    **Warning: Although larger snapshots number means more accurate values.**
    **But if your shots number is large, this may significantly increase memory usage,**
    **require a lot of computing resource, and may run out of memory.**
    **Please consider carefully for performance.**

    Default to "multi_shots".
    """

    MULTI_SHOTS = "multi_shots"
    """Use Numpy to calculate the rho_m with precomputed values."""
    SINGLE_SHOTS = "single_shots"
    """Use Numpy to calculate the rho_m with precomputed values 
    with converted single shot counts."""

    @classmethod
    def get_default(cls):
        """Get the default method.

        Returns:
            The default enum member.
        """
        return cls.MULTI_SHOTS

    def is_single_method(self) -> bool:
        """Whether it is a single shot method.

        Returns:
            bool: True if it is a single shot method, False otherwise.
        """
        return "single" in self.value

    def is_multi_method(self) -> bool:
        """Whether it is a multi shot method.

        Returns:
            bool: True if it is a multi shot method, False otherwise.
        """
        return "multi" in self.value


DEFAULT_RHO_METHOD = RhoMethod.get_default()
"""Whether to use the multi_shots or single_shots method for rho_m_cell calculation.
For the "multi_shots" methods, the counts and random basis are used as is.
For the "single_shots" methods, the counts and random basis are
converted to single shot per snapshot for classical shadow post-processing.

**Warning: Although larger snapshots number means more accurate values.**
**But if your shots number is large, this may significantly increase memory usage,**
**require a lot of computing resource, and may run out of memory.**
**Please consider carefully for performance.**

Default to "multi_shots".
"""

RhoMethodType = RhoMethod | str
"""Whether to use the multi_shots or single_shots method for rho_m_cell calculation.
For the "multi_shots" methods, the counts and random basis are used as is.
For the "single_shots" methods, the counts and random basis are
converted to single shot per snapshot for classical shadow post-processing.
"""

# Peak memory cap for intermediate kron-product arrays.
_MAX_BATCH_MEMORY_BYTES: int = 512 * 1024 * 1024  # 512 MB


def rho_core(
    shots: int,
    counts: list[dict[str, int]],
    random_unitary_array: list[list[int]],
    selected_classical_registers: Iterable[int] | None = None,
    rho_method: RhoMethodType = DEFAULT_RHO_METHOD,
    shadow_basis: ShadowBasisType = DEFAULT_SHADOW_BASIS,
    use_projector: bool = False,
) -> tuple[list[npt.NDArray[np.complex128]], list[int], ShadowRandomBasis, float]:
    r"""Rho M Cell Core calculation.

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The list of the counts.
        random_unitary_array (list[list[int]]):
            The shadow direction of the unitary operators.
        selected_classical_registers (Iterable[int] | None, optional):
            The list of **the index of the selected_classical_registers**.
            Defaults to None.
        rho_method (RhoMethodType, optional):
            For the "multi_shots" methods, the counts and random basis are used as is.
            For the "single_shots" methods, the counts and random basis are
            converted to single shot per snapshot for classical shadow post-processing.

            **Warning: Although larger snapshots number means more accurate values.**
            **But if your shots number is large, this may significantly increase memory usage,**
            **require a lot of computing resource, and may run out of memory.**
            **Please consider carefully for performance.**

            Default to "multi_shots".
        shadow_basis (ShadowBasisType, optional):
            The shadow basis to use. Defaults to :data:`DEFAULT_SHADOW_BASIS`.

            Here are the built-in basis sets:
            - `RY_RX_RZ`:
                Uses :math:`R_Y(-\frac{\pi}{2})`, :math:`R_X(\frac{\pi}{2})`,
                and :math:`R_Z(0)` gates.
            - `H_H-Sdg_I`:
                Uses :math:`H`, :math:`H` followed by :math:`S^\dagger`,
                and Identity gates.
        use_projector (bool):
            Use the projecter :math:`P_m` instead of the precomputed :math:`\rho_m`.
            Refer to
            :func:`qurry.process.classical_shadow.rho_process.rho_m_cell.rho_m_cell_precomputed`
            for more details.
            Default is False, which means using the precomputed :math:`\rho_{mk}^{i}`.

    Returns:
        The dictionary of :math:`\rho_{m}` or :math:`P_m`
        depending on the value of :attr:`use_projector`,
        the sorted list of the selected qubits,
        the shadow basis object, and calculation time.
    """

    if isinstance(rho_method, str):
        rho_method = RhoMethod.from_string(rho_method)
    shadow_basis_obj = ShadowBasisMethod.get_shadow_basis(shadow_basis)

    total_system_size, selected_classical_registers = shot_counts_selected_clreg_checker_pyrust(
        shots=shots,
        counts=counts,
        selected_classical_registers=selected_classical_registers,
    )
    if rho_method == RhoMethod.SINGLE_SHOTS:
        shots, counts, random_unitary_array = spreadout(shots, counts, random_unitary_array)

    begin = time.time()

    selected_clregs_sorted = sorted(selected_classical_registers, reverse=True)
    counts_under_degree_list = counts_list_recount_pyrust(
        counts,
        num_classical_register=total_system_size,
        selected_classical_registers=selected_clregs_sorted,
    )

    # =========================================================================
    # Legacy implementation
    # =========================================================================
    # import os
    # from .rho_m_cell import rho_m_cell_precomputed
    #
    # return (
    #     [
    #         rho_m_cell_precomputed(
    #             single_counts,
    #             random_unitary_array[idx],
    #             selected_clregs_sorted,
    #             shadow_basis_obj,
    #             use_projector=use_projector,
    #         )
    #         for idx, single_counts in enumerate(counts_under_degree_list)
    #     ],
    #     selected_clregs_sorted,
    #     shadow_basis_obj,
    #     time.time() - begin,
    # )
    # =========================================================================
    # The following implementation is made by GitHub Copilot Claude Sonnet 4.6
    # Don't ask me how it works :P

    n_cells = len(counts_under_degree_list)
    n_qubits = len(selected_clregs_sorted)
    matrix_dim = 2**n_qubits
    _bytes_per_sample = matrix_dim * matrix_dim * np.dtype(np.complex128).itemsize

    unit_array = (
        shadow_basis_obj.basis_projecters_array
        if use_projector
        else shadow_basis_obj.basis_precomputed_rho_m_k_i_array
    )

    # Pre-compute basis indices for every cell in one numpy op (no Python loop over qubits per cell)
    selected_arr = np.array(selected_clregs_sorted, dtype=np.intp)
    all_basis_indices = np.asarray(random_unitary_array[:n_cells], dtype=np.intp)[:, selected_arr]
    # shape: (n_cells, n_qubits)

    rho_m_list: list[npt.NDArray[np.complex128]] = []

    if rho_method.is_single_method():
        # SINGLE_SHOTS: each cell has exactly 1 bitstring with count 1.
        # Process all cells in one batched numpy path, chunked to bound peak memory.
        chunk_size = max(1, _MAX_BATCH_MEMORY_BYTES // _bytes_per_sample)
        all_bits = (
            np.frombuffer(
                "".join(next(iter(c.keys())) for c in counts_under_degree_list).encode("ascii"),
                dtype=np.uint8,
            ).reshape(n_cells, n_qubits)
            - ord("0")
        ).astype(np.intp)

        for start in range(0, n_cells, chunk_size):
            end = min(start + chunk_size, n_cells)
            sm = unit_array[all_basis_indices[start:end], all_bits[start:end]]
            # shape: (chunk, n_qubits, 2, 2)
            r: npt.NDArray[np.complex128] = sm[:, 0]
            for j in range(1, n_qubits):
                d = r.shape[1]
                r = np.einsum("sij,skl->sikjl", r, sm[:, j]).reshape(end - start, d * 2, d * 2)
            rho_m_list.extend(r)

        return (rho_m_list, selected_clregs_sorted, shadow_basis_obj, time.time() - begin)

    # MULTI_SHOTS: batch all bitstrings from all cells into one fancy-index + kron pass,
    # then segment-reduce per cell.  Chunked by cells to bound peak memory.
    bs_lists = [list(sc.keys()) for sc in counts_under_degree_list]
    c_lists = [list(sc.values()) for sc in counts_under_degree_list]
    sizes = np.fromiter((len(x) for x in bs_lists), dtype=np.intp, count=n_cells)

    # Chunk by cells so that peak kron array ≤ _MAX_BATCH_MEMORY_BYTES
    avg_bs = max(1, int(sizes.mean())) if n_cells else 1
    chunk_cells = max(1, _MAX_BATCH_MEMORY_BYTES // (_bytes_per_sample * avg_bs))

    for c_start in range(0, n_cells, chunk_cells):
        c_end = min(c_start + chunk_cells, n_cells)
        chunk_bs = bs_lists[c_start:c_end]
        chunk_cl = c_lists[c_start:c_end]
        chunk_sizes = sizes[c_start:c_end]
        chunk_offsets = np.empty(c_end - c_start, dtype=np.intp)
        chunk_offsets[0] = 0
        np.cumsum(chunk_sizes[:-1], out=chunk_offsets[1:])
        total_bs = int(chunk_sizes.sum())

        flat_bits = (
            np.frombuffer(
                "".join(bs for bl in chunk_bs for bs in bl).encode("ascii"),
                dtype=np.uint8,
            ).reshape(total_bs, n_qubits)
            - ord("0")
        ).astype(np.intp)
        # Expand pre-computed basis to match each bitstring's parent cell
        flat_basis = all_basis_indices[
            np.repeat(np.arange(c_start, c_end, dtype=np.intp), chunk_sizes)
        ]
        flat_counts = np.fromiter(
            (v for cl in chunk_cl for v in cl), dtype=np.float64, count=total_bs
        )

        sm = unit_array[flat_basis, flat_bits]  # (total_bs, n_qubits, 2, 2)
        r = sm[:, 0]
        for j in range(1, n_qubits):
            d = r.shape[1]
            r = np.einsum("sij,skl->sikjl", r, sm[:, j]).reshape(total_bs, d * 2, d * 2)

        # Weighted segment-sum then normalise per cell
        weighted = r * flat_counts[:, np.newaxis, np.newaxis]
        seg_sum = np.add.reduceat(weighted, chunk_offsets, axis=0)
        seg_w = np.add.reduceat(flat_counts, chunk_offsets)
        for i in range(c_end - c_start):
            rho_m_list.append(seg_sum[i] / seg_w[i])

    return (rho_m_list, selected_clregs_sorted, shadow_basis_obj, time.time() - begin)


def mean_rho_core(
    rho_m_list: list[npt.NDArray[np.complex128]], selected_classical_registers_sorted: list[int]
) -> npt.NDArray[np.complex128]:
    """Calculate the expectation value of Rho.

    Args:
        rho_m_list (list[npt.NDArray[np.complex128]]):
            The list of rho_m.
        selected_classical_registers_sorted (list[int]):
            The list of the selected_classical_registers.

    Returns:
        npt.NDArray[np.complex128]: The expectation value of Rho.
    """

    expect_rho = np.sum(rho_m_list, axis=0, dtype=np.complex128)
    assert expect_rho.shape == (2 ** len(selected_classical_registers_sorted),) * 2, (
        f"The shape of expect_rho: {expect_rho.shape} "
        + f"and the shape of rho_m_list: {rho_m_list[0].shape} are different."
    )

    return expect_rho / len(rho_m_list)
