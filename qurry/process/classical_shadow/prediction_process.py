"""Post Processing - Classical Shadow - Prediction Process
(:mod:`qurry.process.classical_shadow.prediction_process`)

"""

from typing import TypedDict
import time
import warnings
import numpy as np
import numpy.typing as npt

from .matrix_calculation import (
    prediction_einsum_aij_bji_to_ab,
    ListTraceMethodType,
    DEFAULT_LIST_TRACE_METHOD,
)
from ..exceptions import AccuracyProbabilityCalculationError, AccuracyProbabilityWarning
from ..utils import FloatType


class EstimationOfObservableBasic(TypedDict):
    """The esitimations of the classical shadow from classical snapshots.

    Here, we use the notations that use in the supplementary material of
    `Predicting many properties of a quantum system from very few measurements
    <https://doi.org/10.1038/s41567-020-0932-7>`_

    """

    estimate_of_given_operators: list[np.complex128]
    r"""The esitmation values of measurement primitive :math:`\mathcal{U}`."""
    corresponding_rhos: list[npt.NDArray[np.complex128]]
    r"""The corresponding rho of measurement primitive :math:`\mathcal{U}`.
    It should be a 3-dimensional array for a list of operators. """
    all_candidates_of_estimate: list[list[np.complex128]]
    r"""The all candidates of esitmation values of measurement primitive :math:`\mathcal{U}`."""

    # The accuracy of estimation
    accuracy_prob_comp_delta: FloatType
    r"""The probabiltiy complement of accuracy, which used the notation :math:`\delta`
    and mentioned in Theorem S1 in the supplementary material,
    the equation (S13) in the supplementary material.
    The probabiltiy of accuracy is :math:`1 - \delta`.

    The number of given operators and the accuracy parameters will 
    be used to decide the number of estimators K 
    from the equation (S13) in the supplementary material.

    .. math::
        K = 2 \log(2M / \delta)

    where :math:`\delta` is the probabiltiy complement of accuracy,
    and :math:`M` is the number of given operators.

    But we can see :math:`K` will be not the integer value of the result of the equation.
    So, we will use the ceil value of the result of the equation.
    And recalculate the probabiltiy complement of accuracy from this new value of :math:`K`.
    """
    num_of_estimators_k: int
    r"""The number of esitmators, which used the notation K
    and mentioned in Algorithm 1 in the paper,
    Theorem S1 in the supplementary material,
    the equation (S13) in the supplementary material.

    We can calculate the number of esitmator K from the equation (S13) 
    in the supplementary material, the equation (S13) is as follows,

    .. math::
        K = 2 \log(2M / \delta)

    where :math:`\delta` is the probabiltiy complement of accuracy,
    and :math:`M` is the number of given operators.

    But we can see :math:`K` will be not the integer value of the result of the equation.
    So, we will use the ceil value of the result of the equation.
    And recalculate the probabiltiy complement of accuracy from this new value of :math:`K`.
    """

    accuracy_predict_epsilon: FloatType
    r"""The prediction of accuracy, which used the notation :math:`\epsilon`
    and mentioned in Theorem S1 in the supplementary material,
    the equation (S13) in the supplementary material.

    We can calculate the prediction of accuracy :math:`\epsilon` from the equation (S13)
    in the supplementary material, the equation (S13) is as follows,

    .. math::
        N = \frac{34}{\epsilon^2} \max_{1 \leq i \leq M} 
        || O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2

    where :math:`\epsilon` is the prediction of accuracy,
    and :math:`M` is the number of given operatorsm
    and :math:`N` is the number of classical snapshots.
    The :math:`|| O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2` is maximum shadow norm,
    which is defined in the supplementary material with value between 0 and 1.
    """
    maximum_shadow_norm: FloatType
    r"""The maximum shadow norm, which is defined in the supplementary material.
    The maximum shadow norm is used to calculate the prediction of accuracy :math:`\epsilon`
    from the equation (S13) in the supplementary material.

    We can calculate the prediction of accuracy :math:`\epsilon` from the equation (S13)
    in the supplementary material, the equation (S13) is as follows,

    .. math::
        N = \frac{34}{\epsilon^2} \max_{1 \leq i \leq M} 
        || O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2

    where :math:`\epsilon` is the prediction of accuracy,
    and :math:`M` is the number of given operatorsm
    and :math:`N` is the number of classical snapshots.
    The :math:`|| O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2` is maximum shadow norm.

    Due to its calculation is complex, we curently use the value of np.nan
    to represent the maximum shadow norm.
    """
    epsilon_upperbound: FloatType
    r"""The upper bound of the prediction of accuracy, 
    which used the notation :math:`\epsilon`
    and mentioned in Theorem S1 in the supplementary material,
    the equation (S13) in the supplementary material.

    .. math::
        || O ||_{\text{shadow}}^2 \leq 4^n || O ||_{\infty}^2

    where :math:`O` is the any operator, and :math:`n` is the number of qubits.
    So we set the shadow norm as follows,

    .. math::
        \chi = || O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}} \\
        \chi_{\infty} = 4^n || O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\infty}^2 \\
        \chi^2 \leq \chi_{\infty}

    and we can simplify the equation to:

    .. math::
        N = \frac{34}{\epsilon^2} \max_{1 \leq i \leq M} \chi^2 
            \leq \frac{34}{\epsilon^2} \max_{1 \leq i \leq M} \chi_{\infty}^2

    Then get:

    .. math::
        \epsilon \leq \sqrt{\frac{34}{N}} \max_{1 \leq i \leq M} \chi_\infty

    """
    shadow_norm_upperbound: FloatType
    r"""The largest shadow norm upper bound is defined as follows,

    .. math::
        || O ||_{\text{shadow}}^2 \leq 4^n || O ||_{\infty}^2

    where :math:`O` is the operator, and :math:`n` is the number of qubits,
    which mentioned in the paper at Theorem 1 (informal version).

    This is the worst scenario of the shadow norm
    for its scaling can be reduced to :math:`3^n || O ||_{\infty}^2`,
    which is the significantly lower bound than the worst case scenario.
    """

    taking_time: float
    """The time taken for the calculation."""
    estimate_trace_method: ListTraceMethodType
    """The method to calculate the trace for searching estimators."""


class ComparisonOfEstimation(TypedDict):
    """The comparison of the :class:`~EstimationOfObservableBasic`."""

    trace_with_mean_rho_of_given_operators: list[np.complex128]
    r"""The trace of the given operators with the mean of rho."""


class EstimationOfObservable(EstimationOfObservableBasic, ComparisonOfEstimation):
    """The augmented version of :class:`~EstimationOfObservableBasic`
    with the trace of the given operators with the mean of rho
    as the comparison for
    :attr:`~EstimationOfObservableBasic.estimate_of_given_operators`.
    """


def dim_check(op: npt.NDArray[np.complex128]) -> tuple[int, int]:
    r"""Check the dimension of the operator.

    The dimension of the operator is defined as follows,

    .. math::
        \text{dim}(X) = 2^n

    where :math:`X` is the operator, and :math:`n` is the number of qubits.

    Args:
        op (npt.NDArray[np.complex128]):
            The operator to be checked.

    Returns:
        tuple[int, int]: The dimension of the operator and the number of qubits.

    Raises:
        ValueError: If the shape of the operator is not a square matrix with size 2^n,
        where n is the number of qubits.
    """
    n = int(np.log2(op.shape[0]))
    dim = 2**n
    if dim != op.shape[0]:
        raise ValueError(
            "The shape of the operator must be a square matrix with size 2^n, "
            "where n is the number of qubits."
        )
    return dim, n


def inverted_quantum_channel(op: npt.NDArray[np.complex128]) -> npt.NDArray[np.complex128]:
    r"""Inverted quantum channel.

    The inverted quantum channel is defined as follows,

    .. math::
        \mathcal{M}_{n}^{-1}(X) = (2^n + 1)X - \mathbb{I}

    where :math:`\mathcal{M}_{n}^{-1}` is the inverted quantum channel,
    which mentioned in the paper before Algorithm 1,
    :math:`X` is the operator, and :math:`n` is the number of qubits.

    Args:
        op (npt.NDArray[np.complex128]):
            The operator to be inverted.

    Returns:
        npt.NDArray[np.complex128]:
            The inverted operator.

    Raises:
        ValueError: If the shape of the operator is not a square matrix with size 2^n,
        where n is the number of qubits.
    """
    dim, _ = dim_check(op)
    return (dim + 1) * op - np.eye(dim, dtype=np.complex128)  # type: ignore


def traceless(op: npt.NDArray[np.complex128]) -> npt.NDArray[np.complex128]:
    r"""Make the operator traceless.

    The traceless operator is defined as follows,

    .. math::
        \text{traceless}(O) = O - \frac{\text{tr}(O)}{2^n} \mathbb{I}

    where :math:`O` is the operator, and :math:`n` is the number of qubits,
    which mentioned in the supplementary material Lemma S1.

    Args:
        op (npt.NDArray[np.complex128]):
            The operator to be made traceless.

    Returns:
        npt.NDArray[np.complex128]:
            The traceless operator.
    """
    dim, _ = dim_check(op)
    return op - (np.trace(op) / dim) * np.eye(dim, dtype=np.complex128)


def largest_shadow_norm_squared_upperbound(op: npt.NDArray[np.complex128]) -> FloatType:
    r"""Calculate the largest shadow norm upper bound.

    The largest shadow norm upper bound is defined as follows,

    .. math::
        || O ||_{\text{shadow}}^2 \leq 4^n || O ||_{\infty}^2

    where :math:`O` is the operator, and :math:`n` is the number of qubits,
    which mentioned in the paper at Theorem 1 (informal version).

    This is the worst scenario of the shadow norm
    for its scaling can be reduced to :math:`3^n || O ||_{\infty}^2`,
    which is the significantly lower bound than the worst case scenario.

    Args:
        op (npt.NDArray[np.complex128]):
            The operator to be calculated.

    Returns:
        FloatType: The largest shadow norm upper bound.
    """
    _dim, n = dim_check(op)
    return (4**n) * (np.linalg.norm(op, ord=np.inf) ** 2)


def accuracy_predict_epsilon_calc(
    num_classical_snapshot: int, max_shadow_norm: FloatType = 1.0
) -> FloatType:
    r"""Calculate the prediction of accuracy, which used the notation :math:`\epsilon`
    and mentioned in Theorem S1 in the supplementary material,
    the equation (S13) in the supplementary material.

    We can calculate the prediction of accuracy :math:`\epsilon` from the equation (S13)
    in the supplementary material, the equation (S13) is as follows,

    .. math::
        N = \frac{34}{\epsilon^2} \max_{1 \leq i \leq M}
        || O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2

    where :math:`\epsilon` is the prediction of accuracy,
    and :math:`M` is the number of given operators,
    and :math:`N` is the number of classical snapshots.
    The :math:`|| O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2` is maximum shadow norm,

    Due to maximum shadow norm is complex, we suppose 1 for it should be under the order of 1.
    Thus, we can simplify the equation to:

    .. math::
        N = \frac{34}{\epsilon^2}

    Args:
        num_classical_snapshot (int):
            The number of classical snapshots.
            It is :math:`N` in the equation.
        max_shadow_norm (FloatType, optional):
            The maximum shadow norm. Defaults to 1.
            It is :math:`|| O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2` in equation.

    Returns:
        FloatType: The accuracy prediction epsilon.
    """

    return np.sqrt(34 / num_classical_snapshot) * max_shadow_norm


def worst_accuracy_predict_epsilon_calc(
    num_classical_snapshot: int, given_operators: list[npt.NDArray[np.complex128]]
) -> tuple[FloatType, FloatType]:
    r"""Calculate the prediction of accuracy in worst scenario, 
    which used the notation :math:`\epsilon`
    and mentioned in Theorem S1 in the supplementary material,
    the equation (S13) in the supplementary material.

    We can calculate the prediction of accuracy :math:`\epsilon` from the equation (S13)
    in the supplementary material, the equation (S13) is as follows,

    .. math::
        N = \frac{34}{\epsilon^2} \max_{1 \leq i \leq M}
        || O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2

    where :math:`\epsilon` is the prediction of accuracy,
    and :math:`M` is the number of given operators,
    and :math:`N` is the number of classical snapshots.
    The :math:`|| O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2` is maximum shadow norm,

    And we also know the largest upper bound of the shadow norm is

    .. math::
        || O ||_{\text{shadow}}^2 \leq 4^n || O ||_{\infty}^2

    where :math:`O` is the any operator, and :math:`n` is the number of qubits,

    So we set the shadow norm as follows,

    .. math::
        \chi = || O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}} \\
        \chi_{\infty} = 4^n || O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\infty}^2 \\
        \chi^2 \leq \chi_{\infty}

    and we can simplify the equation to:

    .. math::
        N = \frac{34}{\epsilon^2} \max_{1 \leq i \leq M} \chi^2 
            \leq \frac{34}{\epsilon^2} \max_{1 \leq i \leq M} \chi_{\infty}^2

    Then get:

    .. math::
        \epsilon \leq \sqrt{\frac{34}{N}} \max_{1 \leq i \leq M} \chi_\infty

    Args:
        num_classical_snapshot (int):
            The number of classical snapshots.
            It is :math:`N` in the equation.
        given_operators (list[npt.NDArray[np.complex128]]):
            The list of the operators to estimate.
            It should be a list of operators a.k.a a list of 2-dimensional arrays.

    Returns:
        tuple[FloatType, FloatType]: 
            The worst accuracy prediction epsilon and the worst maximum shadow norm.
    """
    if num_classical_snapshot <= 0:
        raise ValueError("The number of classical snapshots must be greater than 0.")
    if len(given_operators) == 0:
        raise ValueError("The list of given operators must not be empty.")
    squared_upperbound_list = [
        largest_shadow_norm_squared_upperbound(traceless(op)) for op in given_operators
    ]
    max_inf_norms = np.sqrt(max(squared_upperbound_list))

    return np.sqrt(34 / num_classical_snapshot) * max_inf_norms, max_inf_norms


def accuracy_prob_comp_delta_calc(num_of_given_operators: int, num_of_esitmators: int) -> FloatType:
    r"""Calculate the accuracy probability component delta.

    The accuracy probability component delta is calculated by the following equation,

    .. math::
        K = 2 \log(2M / \delta) \Rightarrow \delta = 2M \exp(-K / 2)

    where :math:`K` is the number of estimators,
    and :math:`M` is the number of given operators.

    Args:
        num_of_given_operators (int):
            The number of given operators.
            It is :math:`M` in the equation.
        num_of_esitmators (int):
            The number of estimators.
            It is :math:`K` in the equation.

    Returns:
        FloatType: The accuracy probability component delta.
    """
    if num_of_given_operators <= 0 or num_of_esitmators <= 0:
        raise ValueError(
            "The number of given operators and the number of estimators must be greater than 0."
        )
    if not isinstance(num_of_given_operators, int) or not isinstance(num_of_esitmators, int):
        raise TypeError(
            "The number of given operators and the number of estimators must be integers."
        )

    delta = 2 * num_of_given_operators * np.exp(-num_of_esitmators / 2)
    if delta >= 1:
        raise AccuracyProbabilityCalculationError(
            f"The accuracy probability component delta is too large: {delta}. "
            "It must be less than 1. "
            "You may need to increase the number of estimators to reduce the delta."
        )
    return delta


def decide_num_of_estimators(
    num_classical_snapshot: int,
    num_of_given_operators: int,
    accuracy_prob_comp_delta: FloatType = 0.01,
) -> tuple[int, FloatType]:
    r"""Decide the number of estimators K from the equation (S13) in the supplementary material.

    The number of estimators is calculated by the following equation,

    .. math::
        K = 2 \log(2M / \delta)

    where :math:`\delta` is the probabiltiy complement of accuracy,
    and :math:`M` is the number of given operators.

    But we can see :math:`K` will be not the integer value of the result of the equation.
    So, we will use the ceil value of the result of the equation.
    And recalculate the probabiltiy complement of accuracy from this new value of :math:`K`.

    But we will check :math:`K` is not less than 1
    and larger than :math:`M` the number of given operators.
    If so, we will raise an error.

    Args:
        num_classical_snapshot (int):
            The number of classical snapshots.
            It is :math:`N` in the equation.
        num_of_given_operators (int):
            The number of given operators.
            It is :math:`M` in the equation.
        accuracy_prob_comp_delta (FloatType, optional):
            The accuracy probability component delta. Defaults to None.
            It is :math:`\delta` in the equation. The probabiltiy of accuracy is :math:`1 - \delta`.
            If it is 0, it will raise an error.

    Returns:
        The number of estimators and the accuracy probability component delta.
        The first element is the number of estimators,
        and the second element is the accuracy probability component delta.
    """
    if accuracy_prob_comp_delta <= 0:
        raise ValueError("The accuracy probability component delta must be greater than 0.")
    if accuracy_prob_comp_delta >= 1:
        raise ValueError("The accuracy probability component delta must be less than 1.")
    if num_classical_snapshot <= 0:
        raise ValueError("The number of classical snapshots must be greater than 0.")
    if num_of_given_operators <= 0:
        raise ValueError("The number of given operators must be greater than 0.")
    if not isinstance(num_classical_snapshot, int) or not isinstance(num_of_given_operators, int):
        raise TypeError(
            "The number of classical snapshots and the number of given operators must be integers."
        )

    try:
        min_accuracy_prob_comp_delta = accuracy_prob_comp_delta_calc(
            num_of_given_operators, num_classical_snapshot
        )
    except AccuracyProbabilityCalculationError as e:
        raise AccuracyProbabilityCalculationError(
            f"Failed to calculate the minimum accuracy probability component delta for "
            f"{num_of_given_operators} operators and {num_classical_snapshot} classical snapshots. "
            "There are too few classical snapshots for the given number of operators. "
            "Please increase the number of classical snapshots or reduce the number of operators."
        ) from e

    if accuracy_prob_comp_delta < min_accuracy_prob_comp_delta:
        warnings.warn(
            f"The accuracy probability component delta is too small: {accuracy_prob_comp_delta}. "
            f"It is smaller than the minimum value: {min_accuracy_prob_comp_delta}. "
            "It may cause the number of estimators to "
            "be larger than the number of given operators.",
            category=AccuracyProbabilityWarning,
        )
        accuracy_prob_comp_delta = min_accuracy_prob_comp_delta

    raw_k = 2 * np.log(2 * num_of_given_operators / accuracy_prob_comp_delta)
    actual_k = int(np.ceil(raw_k)) if raw_k > 1 else 1
    actual_delta = accuracy_prob_comp_delta_calc(num_of_given_operators, actual_k)

    return actual_k, actual_delta


def prediction_algorithm(
    classical_snapshots_rho: dict[int, npt.NDArray[np.complex128]],
    given_operators: list[npt.NDArray[np.complex128]],
    accuracy_prob_comp_delta: FloatType = 0.01,
    max_shadow_norm: FloatType | None = None,
    estimate_trace_method: ListTraceMethodType = DEFAULT_LIST_TRACE_METHOD,
) -> EstimationOfObservableBasic:
    r"""Calculate the prediction of accuracy and the number of estimators.

    Args:
        classical_snapshots_rho (dict[int, npt.NDArray[np.complex128]]):
            The classical snapshots.
            The key is the index of the classical snapshot,
            and the value is the classical snapshot.
        given_operators (list[npt.NDArray[np.complex128]]):
            The list of the operators to estimate.
        accuracy_prob_comp_delta (FloatType, optional):
            The accuracy probability component delta. Defaults to 0.01.
        max_shadow_norm (FloatType | None, optional):
            The maximum shadow norm. Defaults to None.
            If it is None, it will be calculated by the largest shadow norm upper bound.
            If it is not None, it must be a positive float number.
            It is :math:`|| O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2` in equation.
        estimate_trace_method (ListTraceMethodType, optional):
            The method to calculate the trace for searching estimators.

            - "einsum_aij_bji_to_ab_numpy":
                Use np.einsum("aij,bji->ab", rho_m_list, rho_m_list) to calculate the trace.

    Returns:
        EstimationOfObservable:
            The esitimations of the classical shadow from classical snapshots.

    Raises:
        ValueError: If the shape of classical snapshots and the shape of given operators
            are not the same.
        ValueError: If the number of classical snapshots or the number of given operators
            is less than or equal to 0.
    """

    num_classical_snapshot = len(classical_snapshots_rho)
    shape_of_classical_snapshots = next(iter(classical_snapshots_rho.values())).shape
    num_of_given_operators = len(given_operators)

    if any(shape_of_classical_snapshots != op.shape for op in given_operators):
        raise ValueError(
            "The shape of classical snapshots and the shape of given operators must be the same."
        )
    if num_classical_snapshot == 0 or num_of_given_operators == 0:
        raise ValueError(
            "The number of classical snapshots and "
            "the number of given operators must be greater than 0."
        )

    epsilon_upperbound, shadow_norm_upperbound = worst_accuracy_predict_epsilon_calc(
        num_classical_snapshot, given_operators
    )
    if max_shadow_norm is not None:
        accuracy_predict_epsilon = accuracy_predict_epsilon_calc(
            num_classical_snapshot, max_shadow_norm
        )
    else:
        accuracy_predict_epsilon = epsilon_upperbound
        max_shadow_norm = np.nan

    num_of_estimators, actual_accuracy_prob_comp_delta = decide_num_of_estimators(
        num_classical_snapshot, num_of_given_operators, accuracy_prob_comp_delta
    )
    n_div_k_floor = int(np.floor(num_classical_snapshot / num_of_estimators))
    estimators = np.array(
        [
            np.sum(
                [classical_snapshots_rho[i * n_div_k_floor + j] for j in range(n_div_k_floor)],
                axis=0,
                dtype=np.complex128,
            )
            / n_div_k_floor
            for i in range(num_of_estimators)
        ]
    )

    begin = time.time()
    estimate_of_given_operators, all_candidates_of_estimate, corresponding_rhos = (
        prediction_einsum_aij_bji_to_ab(
            np.array(given_operators), estimators, method=estimate_trace_method
        )
    )

    return EstimationOfObservableBasic(
        estimate_of_given_operators=estimate_of_given_operators,
        all_candidates_of_estimate=all_candidates_of_estimate,
        corresponding_rhos=corresponding_rhos,
        accuracy_prob_comp_delta=actual_accuracy_prob_comp_delta,
        num_of_estimators_k=num_of_estimators,
        accuracy_predict_epsilon=accuracy_predict_epsilon,
        maximum_shadow_norm=max_shadow_norm,
        epsilon_upperbound=epsilon_upperbound,
        shadow_norm_upperbound=shadow_norm_upperbound,
        taking_time=time.time() - begin,
        estimate_trace_method=estimate_trace_method,
    )


def comparison_of_prediction(
    mean_of_rho: npt.NDArray[np.complex128], given_operators: list[npt.NDArray[np.complex128]]
) -> ComparisonOfEstimation:
    r"""Calculate the comparison of the :class:`~EstimationOfObservable`.

    Args:
        mean_of_rho (npt.NDArray[np.complex128]):
            The mean of the classical snapshots.
        given_operators (list[npt.NDArray[np.complex128]]):
            The list of the operators to estimate.

    Returns:
        ComparisonOfEstimation:
            The comparison of the :class:`~EstimationOfObservable`.
    """

    return ComparisonOfEstimation(
        trace_with_mean_rho_of_given_operators=[
            np.trace(mean_of_rho @ op) for op in given_operators
        ]
    )
