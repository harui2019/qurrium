"""Post Processing - Classical Shadow - All Observable Calculation - Estimation of Observable
(:mod:`qurry.process.classical_shadow.all_observable.estimation`)

"""

from typing import Literal
from collections.abc import Iterable
import tqdm
import numpy.typing as npt

from .container_kind import ClassicalShadowBasic, isvalid_classical_shadow_basic
from .mean import mean_rho
from ..rho_process import RhoMethodType, DEFAULT_RHO_METHOD, ShadowBasisType, DEFAULT_SHADOW_BASIS
from ..prediction_process import (
    prediction_algorithm,
    EstimationOfObservable,
    comparison_of_prediction,
)
from ..matrix_calculation import ListTraceMethodType, DEFAULT_LIST_TRACE_METHOD
from ...utils import FloatType


def inner_estimation_of_given_operators(
    cs_basic: ClassicalShadowBasic,
    # estimation of given operators
    given_operators: list[npt.NDArray] | None = None,
    accuracy_prob_comp_delta: FloatType = 0.01,
    max_shadow_norm: FloatType | None = None,
    # other config
    estimate_trace_method: ListTraceMethodType = DEFAULT_LIST_TRACE_METHOD,
) -> EstimationOfObservable:
    r"""Calculate the expectation value of given operators from ClassicalShadowBasic.

    Args:
        cs_basic (ClassicalShadowBasic):
            The ClassicalShadowBasic TypedDict object.

        given_operators (list[npt.NDArray]):
            The list of the operators to estimate.
        accuracy_prob_comp_delta (FloatType, optional):
            The accuracy probability component delta. Defaults to 0.01.
        max_shadow_norm (FloatType | None, optional):
            The maximum shadow norm. Defaults to None.
            If it is None, it will be calculated by the largest shadow norm upper bound.
            If it is not None, it must be a positive float number.
            It is :math:`|| O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2` in equation.

        estimate_trace_method (ListTraceMethodType, optional):
            The method to use for the calculation. Defaults to DEFAULT_LIST_TRACE_METHOD.

    Returns:
        EstimationOfObservable: The estimation of the given operators.
    """

    isvalid_classical_shadow_basic(cs_basic)
    if given_operators is None or len(given_operators) == 0:
        raise ValueError("The given_operators must be a non-empty list.")

    cs_estimation_basic = prediction_algorithm(
        classical_snapshots_rho=dict(enumerate(cs_basic["average_snapshots_rho_list"])),
        given_operators=given_operators,
        accuracy_prob_comp_delta=accuracy_prob_comp_delta,
        max_shadow_norm=max_shadow_norm,
        estimate_trace_method=estimate_trace_method,
    )
    cs_comparison = comparison_of_prediction(
        mean_of_rho=cs_basic["mean_of_rho"],
        given_operators=given_operators,
    )

    return EstimationOfObservable(**cs_estimation_basic, **cs_comparison)


def estimation_of_given_operators(
    shots: int,
    counts: list[dict[str, int]],
    random_basis_array: list[list[Literal[0, 1, 2] | int]],
    selected_classical_registers: Iterable[int] | None = None,
    # estimation of given operators
    given_operators: list[npt.NDArray] | None = None,
    accuracy_prob_comp_delta: FloatType = 0.01,
    max_shadow_norm: FloatType | None = None,
    # other config
    rho_method: RhoMethodType = DEFAULT_RHO_METHOD,
    shadow_basis: ShadowBasisType = DEFAULT_SHADOW_BASIS,
    use_projector: bool = False,
    estimate_trace_method: ListTraceMethodType = DEFAULT_LIST_TRACE_METHOD,
    pbar: tqdm.tqdm | None = None,
) -> tuple[ClassicalShadowBasic, EstimationOfObservable]:
    r"""Calculate the expectation value of given operators.

    Reference:
        -   Predicting many properties of a quantum system from very few measurements -
            Huang, Hsin-Yuan and Kueng, Richard and Preskill, John
            `doi:10.1038/s41567-020-0932-7 <https://doi.org/10.1038/s41567-020-0932-7>`_

        .. code-block:: bibtex

            @article{cite-key,
                abstract = {
                    Predicting the properties of complex,
                    large-scale quantum systems is essential for developing quantum technologies.
                    We present an efficient method for constructing an approximate classical
                    description of a quantum state using very few measurements of the state.
                    different properties; order
                    {\$}{\$}{\{}{$\backslash$}mathrm{\{}log{\}}{\}}{$\backslash$},(M){\$}{\$}
                    measurements suffice to accurately predict M different functions of the state
                    with high success probability. The number of measurements is independent of
                    the system size and saturates information-theoretic lower bounds. Moreover,
                    target properties to predict can be
                    selected after the measurements are completed.
                    We support our theoretical findings with extensive numerical experiments.
                    We apply classical shadows to predict quantum fidelities,
                    entanglement entropies, two-point correlation functions,
                    expectation values of local observables and the energy variance of
                    many-body local Hamiltonians.
                    The numerical results highlight the advantages of classical shadows relative to
                    previously known methods.},
                author = {Huang, Hsin-Yuan and Kueng, Richard and Preskill, John},
                date = {2020/10/01},
                date-added = {2024-12-03 15:00:55 +0800},
                date-modified = {2024-12-03 15:00:55 +0800},
                doi = {10.1038/s41567-020-0932-7},
                id = {Huang2020},
                isbn = {1745-2481},
                journal = {Nature Physics},
                number = {10},
                pages = {1050--1057},
                title = {Predicting many properties of a quantum system from very few measurements},
                url = {https://doi.org/10.1038/s41567-020-0932-7},
                volume = {16},
                year = {2020},
                bdsk-url-1 = {https://doi.org/10.1038/s41567-020-0932-7}
            }

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

        given_operators (list[npt.NDArray] | None):
            The list of the operators to estimate.
        accuracy_prob_comp_delta (FloatType, optional):
            The accuracy probability component delta. Defaults to 0.01.
        max_shadow_norm (FloatType | None, optional):
            The maximum shadow norm. Defaults to None.
            If it is None, it will be calculated by the largest shadow norm upper bound.
            If it is not None, it must be a positive float number.
            It is :math:`|| O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2` in equation.
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
        estimate_trace_method (ListTraceMethodType, optional):
            The method to use for the calculation.

            - "einsum_aij_bji_to_ab_numpy":
                Use `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace.
                This is the fastest implementation to calculate the trace of Rho

            Defaults to DEFAULT_LIST_TRACE_METHOD.

        pbar (tqdm.tqdm | None, optional):
            The progress bar. Defaults to None.

    Returns:
        The ClassicalShadowBasic and the estimation of the given operators.
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
    cs_estimation_obj = inner_estimation_of_given_operators(
        cs_basic=cs_basic_obj,
        given_operators=given_operators,
        accuracy_prob_comp_delta=accuracy_prob_comp_delta,
        max_shadow_norm=max_shadow_norm,
        estimate_trace_method=estimate_trace_method,
    )

    if pbar is not None:
        pbar.set_description(
            f"| taking time of estimation: {cs_estimation_obj['taking_time']:.4f} sec"
        )

    return cs_basic_obj, cs_estimation_obj
