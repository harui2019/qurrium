"""Post Processing - Classical Shadow - Matrix Calculation
(:mod:`qurry.process.classical_shadow.matrix_calculation`)

The matrix calculation for predicting quantum properties.

"""

from collections.abc import Callable
import numpy as np
import numpy.typing as npt

from ..utils import BaseMethodEnum
from ..availability import availability


BACKEND_AVAILABLE = availability(
    "classical_shadow.matrix_calculation",
    [("Numpy", True, None), ("JAX", "Depr.", None)],
)
"""The availability of backends for classical shadow matrix calculation."""


# single trace calculation
def single_trace_rho_by_trace_of_matmul(
    rho_m1_and_rho_m2: tuple[npt.NDArray[np.complex128], npt.NDArray[np.complex128]],
) -> np.complex128:
    """The single trace of Rho by trace of matmul.

    Args:
        rho_m1_and_rho_m2 (tuple[npt.NDArray[np.complex128], npt.NDArray[np.complex128]]):
            The tuple of rho_m1 and rho_m2.
            It should be two 2-dimensional arrays for matrix multiplication.

    Returns:
        np.complex128: The trace of Rho.
    """
    rho_m1, rho_m2 = rho_m1_and_rho_m2
    return np.trace((rho_m1 @ rho_m2)) + np.trace((rho_m2 @ rho_m1))


def single_trace_rho_by_einsum_ij_ji(
    rho_m1_and_rho_m2: tuple[npt.NDArray[np.complex128], npt.NDArray[np.complex128]],
) -> np.complex128:
    """The single trace of Rho by einsum_ij_ji by Numpy.

    Args:
        rho_m1_and_rho_m2 (tuple[npt.NDArray[np.complex128], npt.NDArray[np.complex128]]):
            The tuple of rho_m1 and rho_m2.
            It should be two 2-dimensional arrays for matrix multiplication.

    Returns:
        np.complex128: The trace of Rho.
    """
    rho_m1, rho_m2 = rho_m1_and_rho_m2
    return np.einsum("ij,ji", rho_m1, rho_m2) + np.einsum("ij,ji", rho_m2, rho_m1)


class SingleTraceMethod(BaseMethodEnum):
    """The method to calculate the trace of single Rho square.

    - "trace_of_matmul": Use `np.trace(np.matmul(rho_m1, rho_m2))` to calculate the trace.
    - "einsum_ij_ji": Use `np.einsum("ij,ji", rho_m1, rho_m2)` to calculate the trace.
    """

    TRACE_OF_MATMUL = "trace_of_matmul"
    """Use `np.trace(np.matmul(rho_m1, rho_m2))` to calculate the trace."""

    EINSUM_IJ_JI = "einsum_ij_ji"
    """Use `np.einsum("ij,ji", rho_m1, rho_m2)` to calculate the trace."""

    @classmethod
    def get_default(cls) -> "SingleTraceMethod":
        """Get the default method.

        Returns:
            The default method.
        """
        return cls.EINSUM_IJ_JI


SingleTraceMethodType = SingleTraceMethod | str
"""The method to use for the trace calculation with matrix multiplication.
- "trace_of_matmul":
    Use `np.trace(np.matmul(rho_m1, rho_m2))` to calculate the trace.
- "einsum_ij_ji":
    Use `np.einsum("ij,ji", rho_m1, rho_m2)` to calculate the trace.
"""

DEFAULT_SINGLE_TRACE_METHOD: SingleTraceMethod = SingleTraceMethod.get_default()
"""The default method for the trace calculation with matrix multiplication."""


def select_single_trace_rho_method(
    method: SingleTraceMethodType = DEFAULT_SINGLE_TRACE_METHOD,
) -> Callable[[tuple[npt.NDArray[np.complex128], npt.NDArray[np.complex128]]], np.complex128]:
    """Select the method for the single trace of Rho.

    Args:
        method (SingleTraceMethodType, optional):
            The method to use for the calculation. Defaults to DEFAULT_SINGLE_TRACE_METHOD.

    Returns:
        The function to calculate the single trace of Rho.
    """

    if isinstance(method, str):
        method = SingleTraceMethod.from_string(method)
    if method == SingleTraceMethod.EINSUM_IJ_JI:
        return single_trace_rho_by_einsum_ij_ji
    if method == SingleTraceMethod.TRACE_OF_MATMUL:
        return single_trace_rho_by_trace_of_matmul
    raise SingleTraceMethod.value_error()


class ListTraceMethod(BaseMethodEnum):
    """The method to calculate the all trace of Rho square.

    - "einsum_aij_bji_to_ab_numpy": Use\
    `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace.
    """

    EINSUM_AIJ_BJI_TO_AB_NUMPY = "einsum_aij_bji_to_ab_numpy"
    """Use `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace."""

    @classmethod
    def get_default(cls) -> "ListTraceMethod":
        """Get the default method.

        Returns:
            The default method.
        """
        return cls.EINSUM_AIJ_BJI_TO_AB_NUMPY


ListTraceMethodType = ListTraceMethod | str
"""The method to calculate the all trace of Rho square.

- "einsum_aij_bji_to_ab_numpy":
    Use `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace.
    This is the fastest implementation to calculate the trace of Rho

"""

DEFAULT_LIST_TRACE_METHOD: ListTraceMethod = ListTraceMethod.get_default()
"""The default method for the trace calculation with matrix multiplication."""


# trace summation calculation
def all_trace_rho_by_einsum_aij_bji_to_ab(
    rho_m_array: npt.NDArray[np.complex128],
    method: ListTraceMethodType = DEFAULT_LIST_TRACE_METHOD,
) -> np.complex128:
    """The trace of Rho by einsum_aij_bji_to_ab.
    This is the fastest implementation to calculate the trace of Rho.

    Args:
        rho_m_array (npt.NDArray[np.complex128]):
            The Rho M array.
            It should be a 3-dimensional array for a list of operators.
        method (ListTraceMethodType, optional):
            The method to use for the calculation.
            Defaults to DEFAULT_LIST_TRACE_METHOD.

    Returns:
        np.complex128: The trace of Rho.
    """
    if rho_m_array.ndim != 3:
        raise ValueError(
            f"rho_m_array must be a 3-dimensional array. Got {rho_m_array.ndim} dimensions."
        )
    if isinstance(method, str):
        method = ListTraceMethod.from_string(method)

    len_rho_m_array = len(rho_m_array)

    trace_matrix = np.einsum("aij,bji -> ab", rho_m_array, rho_m_array)
    mask = np.ones(trace_matrix.shape, dtype=bool)
    np.fill_diagonal(mask, False)

    sum_off_diagonal = trace_matrix[mask].sum()
    return sum_off_diagonal / (len_rho_m_array * (len_rho_m_array - 1))


def prediction_einsum_aij_bji_to_ab(
    given_operators: npt.NDArray[np.complex128],
    estimators: npt.NDArray[np.complex128],
    method: ListTraceMethodType = DEFAULT_LIST_TRACE_METHOD,
) -> tuple[list[np.complex128], list[list[np.complex128]], list[npt.NDArray[np.complex128]]]:
    """Calculate the prediction of given operators by einsum_aij_bji_to_ab_numpy.

    Args:
        given_operators (npt.NDArray[np.complex128]):
            The given operators.
            It should be a 3-dimensional array for a list of operators.
        estimators (npt.NDArray[np.complex128]):
            The estimators.
            It should be a 3-dimensional array for a list of operators.
        method (ListTraceMethodType, optional):
            The method to use for the calculation.
            - "einsum_aij_bji_to_ab_numpy":
                Use `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace.
                This is the fastest implementation to calculate the trace of Rho
            Defaults to DEFAULT_LIST_TRACE_METHOD.

    Returns:
        A tuple containing:
            - A list of median values for each given operator.
            - A list of a lists containing the candidate estimators for each given operator.
            - A list of the corresponding median estimators for each given operator.
    """
    if given_operators.ndim != 3 or estimators.ndim != 3:
        raise ValueError(
            "given_operators and estimators must be 3-dimensional arrays."
            f"Got {given_operators.ndim} and {estimators.ndim} dimensions respectively."
        )
    if isinstance(method, str):
        method = ListTraceMethod.from_string(method)

    if given_operators.ndim != 3 or estimators.ndim != 3:
        raise ValueError(
            "given_operators and estimators must be 3-dimensional arrays."
            f"Got {given_operators.ndim} and {estimators.ndim} dimensions respectively."
        )

    # the matrix with shape (len(given_operators), len(estimators))
    candidate_esitmators_foreach_given_operator = np.einsum(
        "aij,bji->ab", given_operators, estimators
    )

    # a 1-dim list with length = len(given_operators)
    median_foreach_given_operator = np.median(candidate_esitmators_foreach_given_operator, axis=1)
    # Index j of the estimator
    median_location_given_operator = np.argmin(
        np.abs(
            candidate_esitmators_foreach_given_operator - median_foreach_given_operator[:, None]
        ),
        axis=1,
    )

    return (
        list(median_foreach_given_operator),
        candidate_esitmators_foreach_given_operator.tolist(),
        [estimators[j] for j in median_location_given_operator],
    )
