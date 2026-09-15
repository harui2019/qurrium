"""Post Processing - Classical Shadow - All Observable Calculation - Trace of Rho Square
(:mod:`qurry.process.classical_shadow.all_observable.trace`)

"""

from typing import Literal
from collections.abc import Iterable
import tqdm

from .container_kind import (
    ClassicalShadowBasic,
    isvalid_classical_shadow_basic,
    ClassicalShadowPurity,
    verify_purity_value_kind,
)
from .mean import mean_rho
from ..rho_process import RhoMethodType, DEFAULT_RHO_METHOD, ShadowBasisType, DEFAULT_SHADOW_BASIS
from ..trace_process import all_trace_core, TraceMethodType, DEFAULT_TRACE_METHOD


def inner_trace_rho_square(
    shots: int,
    counts: list[dict[str, int]],
    random_basis_array: list[list[Literal[0, 1, 2] | int]],
    cs_basic: ClassicalShadowBasic,
    trace_method: TraceMethodType = DEFAULT_TRACE_METHOD,
) -> ClassicalShadowPurity:
    """Calculate the trace of Rho square from ClassicalShadowBasic.

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The list of the counts.
        random_basis_array: list[list[Literal[0, 1, 2] | int]],
            The random basis for classical shadow.

        cs_basic (ClassicalShadowBasic):
            The ClassicalShadowBasic TypedDict object.

        trace_method (TraceMethodType, optional):
            The method to calculate the trace of rho. Defaults to DEFAULT_TRACE_METHOD.

    Returns:
        ClassicalShadowPurity: The ClassicalShadowPurity TypedDict object.
    """
    isvalid_classical_shadow_basic(cs_basic)
    if len(counts) < 2:
        raise ValueError(
            "The method of classical shadow require at least 2 counts for the calculation. "
            + f"The number of counts is {len(counts)}."
        )

    purity, entropy, taken = all_trace_core(
        shots=shots,
        counts=counts,
        random_basis_array=random_basis_array,
        rho_m_list=cs_basic["average_snapshots_rho_list"],
        selected_classical_registers_sorted=cs_basic["classical_registers_actually"],
        trace_method=trace_method,
    )

    return ClassicalShadowPurity(
        purity=purity,
        entropy=entropy,
        trace_method=trace_method,
        taking_time=taken,
        purity_value_kind=verify_purity_value_kind(cs_basic["rho_method"], trace_method),
    )


def trace_rho_square(
    shots: int,
    counts: list[dict[str, int]],
    random_basis_array: list[list[Literal[0, 1, 2] | int]],
    selected_classical_registers: Iterable[int] | None = None,
    rho_method: RhoMethodType = DEFAULT_RHO_METHOD,
    shadow_basis: ShadowBasisType = DEFAULT_SHADOW_BASIS,
    trace_method: TraceMethodType = DEFAULT_TRACE_METHOD,
    use_projector: bool = False,
    pbar: tqdm.tqdm | None = None,
) -> tuple[ClassicalShadowBasic, ClassicalShadowPurity]:
    r"""Trace of Rho square.

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The list of the counts.
        random_basis_array (list[list[Literal[0, 1, 2] | int]]):
            The random basis for classical shadow.
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

            Default to :data:`DEFAULT_RHO_METHOD`.
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
        trace_method (TraceMethodType, optional):
            The method to calculate the trace of rho.

            - Matrix operation methods:
                For the matrix operation methods, it will require rho has been calculated first.
                - "trace_of_matmul": Use `np.trace(np.matmul(rho_m1, rho_m2))`
                    to calculate the each summation item in `rho_m_list`.
                - "einsum_ij_ji": Use `np.einsum("ij,ji", rho_m1, rho_m2)`
                    to calculate the each summation item in `rho_m_list`.
                - "einsum_aij_bji_to_ab_numpy": Use
                    `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace.
                    This is the fastest implementation to calculate the trace of Rho

            - Non-matrix operation methods:
                - "nomatmul_trace_py": Use pure Python implementation without multiprocessing.
                - "nomatmul_trace_rust": Use Rust implementation via PyO3.

            - Skip calculation of trace:
                - "skip_trace": Skip the trace calculation and return NaN.

            For the non-matrix operation methods, it will directly calculate the trace from
            the counts and random basis.

            Default to DEFAULT_TRACE_METHOD.

        pbar (tqdm.tqdm | None, optional):
            The progress bar. Defaults to None.

    Returns:
        A tuple of ClassicalShadowBasic and ClassicalShadowPurity.
    """

    cs_basic_obj = mean_rho(
        shots=shots,
        counts=counts,
        random_basis_array=random_basis_array,
        selected_classical_registers=selected_classical_registers,
        rho_method=rho_method,
        shadow_basis=shadow_basis,
        use_projector=use_projector,
        pbar=pbar,
    )
    cs_trace_obj = inner_trace_rho_square(
        shots=shots,
        counts=counts,
        random_basis_array=random_basis_array,
        cs_basic=cs_basic_obj,
        trace_method=trace_method,
    )

    if pbar is not None:
        pbar.set_description(
            f"| taking time of trace of rho^2: {cs_trace_obj['taking_time']:.4f} sec"
        )

    return cs_basic_obj, cs_trace_obj
