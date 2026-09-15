"""Post Processing - Classical Shadow - All Observable Calculation - Container/Purity Value Kind
(:mod:`qurry.process.classical_shadow.all_observable.container_kind`)
"""

from typing import TypedDict, Literal
import numpy as np
import numpy.typing as npt

from ..rho_process import ShadowRandomBasisData, RhoMethod, RhoMethodType
from ..trace_process import TraceMethod, TraceMethodType
from ...utils import FloatType


PurityValueKind = Literal["multi_shots", "single_shots"]
"""The kind of purity value calculation.
This will depend on the rho_method and trace_method.

- "multi_shots":
    The *rho_method is one of the multi_shots methods* **and** *trace_method is one of the
    matrix operation methods*.

    .. code-block:: python

        (
            rho_method in [
                "multi_shots",
            ]
        ) and (
            trace_method in [
                "trace_of_matmul", 
                "einsum_ij_ji", 
                "quick_trace_of_matmul",
                "einsum_aij_bji_to_ab_numpy", 
            ]
        )

- "single_shots":
    The *rho_method is one of the single_shots methods* **and** *trace_method is one of the
    matrix operation methods*, or the *trace_method is one of the non-matrix operation methods*.

    .. code-block:: python

        (
            trace_method in [
                "nomatmul_trace_py", 
                "nomatmul_trace_rust",
            ]
        ) or (
            (
                rho_method in [
                    "single_shots", 
                ]
            ) and (
                trace_method in [
                    "trace_of_matmul", 
                    "einsum_ij_ji", 
                    "quick_trace_of_matmul",
                    "einsum_aij_bji_to_ab_numpy", 
                ]
            )
        )
"""


def verify_purity_value_kind(
    rho_method: RhoMethodType, trace_method: TraceMethodType
) -> PurityValueKind:
    """Verify the kind of purity value calculation.

    Args:
        rho_method (RhoMethodType, optional):
            For the "multi_shots" methods, the counts and random basis are used as is.
            For the "single_shots" methods, the counts and random basis are
            converted to single shot per snapshot for classical shadow post-processing.

            **Warning: Although larger snapshots number means more accurate values.**
            **But if your shots number is large, this may significantly increase memory usage,**
            **require a lot of computing resource, and may run out of memory.**
            **Please consider carefully for performance.**

            Default to :data:`DEFAULT_RHO_METHOD`.
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

    Returns:
        PurityValueKind: The kind of purity value calculation.
    """
    if isinstance(rho_method, str):
        rho_method = RhoMethod.from_string(rho_method)
    if isinstance(trace_method, str):
        trace_method = TraceMethod.from_string(trace_method)

    if not trace_method.is_nomatop_method() and rho_method.is_multi_method():
        return "multi_shots"
    return "single_shots"


def default_method_on_value_kind(value_kind: PurityValueKind) -> tuple[RhoMethod, TraceMethod]:
    """Get the default method on each kind of purity value calculation.

    Raises:
        ValueError: If the purity value kind is not recognized.

    Returns:
        tuple[RhoMethod, TraceMethod]: The default method for the given purity value kind.
    """
    if value_kind == "multi_shots":
        return RhoMethod.get_default(), TraceMethod.EINSUM_AIJ_BJI_TO_AB_NUMPY
    if value_kind == "single_shots":
        return RhoMethod.get_default(), TraceMethod.NOMATMUL_TRACE_RUST
    raise ValueError(f"Unknown purity value kind: {value_kind}")


class ClassicalShadowBasic(TypedDict):
    """The basic information of the classical shadow."""

    average_snapshots_rho_list: list[npt.NDArray[np.complex128]]
    """The list of average classical snapshots, which uses the notation rho in 
    `Predicting many properties of a quantum system from very few measurements
    <https://doi.org/10.1038/s41567-020-0932-7>`_

    The numpy array shape is `(2, 2)`.
    
    Formally, this field is defined as `dict[int, npt.NDArray[np.complex128]]` 
    with the name of `average_classical_snapshots_rho`, where the key is 
    the index of the snapshot and the value is the corresponding rho matrix.
    But it is just meaningless to use dictionary here.
    """
    classical_registers_actually: list[int]
    """The list of the selected_classical_registers."""
    taking_time: float
    """The time taken for the calculation."""

    rho_method: RhoMethodType
    """The method to calculate the rho."""
    random_basis_data: ShadowRandomBasisData
    """The random basis data used for classical shadow."""

    mean_of_rho: npt.NDArray[np.complex128]
    """The mean of single classical snapshots."""

    use_projector: bool
    r"""Use the projecter :math:`P_m` instead of the precomputed :math:`\rho_m`. 

    Refer to :func:`qurry.process.classical_shadow.rho_process.rho_m_cell.rho_m_cell_precomputed`
    for more details.
    """


def isvalid_classical_shadow_basic(cs_basic: ClassicalShadowBasic) -> None:
    """Verify if the given ClassicalShadowBasic object is valid.

    Args:
        cs_basic (ClassicalShadowBasic):
            The ClassicalShadowBasic TypedDict object.

    Raises:
        ValueError: If the cs_basic argument is not a valid ClassicalShadowBasic object.
    """
    missing_fields = set(ClassicalShadowBasic.__annotations__.keys()) - set(cs_basic.keys())
    if missing_fields:
        raise ValueError(f"The cs_basic argument is missing fields: {', '.join(missing_fields)}.")


class ClassicalShadowPurity(TypedDict):
    """The expectation value of Rho."""

    purity: FloatType
    """The purity calculated by classical shadow."""
    entropy: FloatType
    """The entropy calculated by classical shadow."""
    purity_value_kind: PurityValueKind | str
    """The kind of purity value calculation.
    This will depend on the rho_method and trace_method.

    If it is not one of the defined kinds, it will be "unknown".
    """
    taking_time: float
    """The time taken for the calculation."""
    trace_method: TraceMethodType
    """The method to calculate the trace of rho."""
