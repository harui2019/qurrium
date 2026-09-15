"""Post Processing - Classical Shadow - Trace Process - Rho Trace Core
(:mod:`qurry.process.classical_shadow.trace_process.rho_trace_core`)

This module is used to process the rho dictionary for classical shadow.
"""

from itertools import combinations
import numpy as np
import numpy.typing as npt

from ..matrix_calculation import (
    select_single_trace_rho_method,
    SingleTraceMethod,
    all_trace_rho_by_einsum_aij_bji_to_ab,
    ListTraceMethod,
)
from ...utils import BaseMethodEnum


class RhoTraceMethod(BaseMethodEnum):
    """The method to use for the trace calculation of Rho square.

    - "trace_of_matmul": Use `np.trace(np.matmul(rho_m1, rho_m2))`
        to calculate the each summation item in `rho_m_list`.
    - "einsum_ij_ji": Use `np.einsum("ij,ji", rho_m1, rho_m2)`
        to calculate the each summation item in `rho_m_list`.
    - "einsum_aij_bji_to_ab_numpy": Use
        `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace.
        This is the fastest implementation to calculate the trace of Rho
    """

    TRACE_OF_MATMUL = SingleTraceMethod.TRACE_OF_MATMUL.value
    """Use `np.trace(np.matmul(rho_m1, rho_m2))` to calculate 
    the each summation item in `rho_m_list`."""

    EINSUM_IJ_JI = SingleTraceMethod.EINSUM_IJ_JI.value
    """Use `np.einsum("ij,ji", rho_m1, rho_m2)` to calculate 
    the each summation item in `rho_m_list`."""

    EINSUM_AIJ_BJI_TO_AB_NUMPY = ListTraceMethod.EINSUM_AIJ_BJI_TO_AB_NUMPY.value
    """Use `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace."""


    @classmethod
    def get_default(cls) -> "RhoTraceMethod":
        """Get the default method.
        Returns:
            RhoTraceMethod: The default method.
        """
        return cls.EINSUM_AIJ_BJI_TO_AB_NUMPY

    def is_list_method(self) -> bool:
        """Whether it is a list method.

        Returns:
            bool: True if it is a list method, False otherwise.
        """
        return self in [self.EINSUM_AIJ_BJI_TO_AB_NUMPY]

    def is_single_method(self) -> bool:
        """Whether it is a single method.

        Returns:
            bool: True if it is a single method, False otherwise.
        """
        return self in [self.TRACE_OF_MATMUL, self.EINSUM_IJ_JI]

    def to_single_enum(self) -> SingleTraceMethod:
        """Convert to SingleTraceMethod enum.

        Raises:
            ValueError: If the method is not a single method.

        Returns:
            SingleTraceMethod: The corresponding SingleTraceMethod enum.
        """
        if not self.is_single_method():
            raise ValueError(f"{self.value} is not a single method")
        return SingleTraceMethod.from_string(self.value)

    def to_list_enum(self) -> ListTraceMethod:
        """Convert to ListTraceMethod enum.

        Raises:
            ValueError: If the method is not a list method.

        Returns:
            ListTraceMethod: The corresponding ListTraceMethod enum.
        """
        if not self.is_list_method():
            raise ValueError(f"{self.value} is not a list method")
        return ListTraceMethod.from_string(self.value)


RhoTraceMethodType = RhoTraceMethod | str
"""The method to calculate the trace of Rho square.

- "trace_of_matmul":
    Use `np.trace(np.matmul(rho_m1, rho_m2))`
    to calculate the each summation item in `rho_m_list`.
- "einsum_ij_ji":
    Use `np.einsum("ij,ji", rho_m1, rho_m2)`
    to calculate the each summation item in `rho_m_list`.
- "einsum_aij_bji_to_ab_numpy":
    Use `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace.
    This is the fastest implementation to calculate the trace of Rho.
"""

DEFAULT_RHO_TRACE_METHOD: RhoTraceMethod = RhoTraceMethod.get_default()
"""The default method for the trace of Rho square."""


def trace_rho_square_core(
    rho_m_list: list[npt.NDArray[np.complex128]],
    trace_method: RhoTraceMethod = DEFAULT_RHO_TRACE_METHOD,
) -> np.complex128:
    r"""Calculate the trace of Rho square.

    Args:
        rho_m_list (list[npt.NDArray[np.complex128]]):
            The list of rho_m matrices.
            It should be a list of 2-dimensional arrays.
        trace_method (RhoTraceMethod , optional):
            The method to calculate the trace of Rho square.
            - "trace_of_matmul":
                Use `np.trace(np.matmul(rho_m1, rho_m2))`
                to calculate the each summation item in `rho_m_list`.
            - "einsum_ij_ji":
                Use `np.einsum("ij,ji", rho_m1, rho_m2)`
                to calculate the each summation item in `rho_m_list`.
            - "einsum_aij_bji_to_ab_numpy":
                Use `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)`
                to calculate the trace.
                This is the fastest implementation to calculate the trace of Rho

    Returns:
        np.complex128: The trace of Rho square.
    """
    if isinstance(trace_method, str):
        trace_method = RhoTraceMethod.from_string(trace_method)

    if trace_method.is_list_method():
        list_enum = trace_method.to_list_enum()
        rho_m_array = np.array(rho_m_list)
        return all_trace_rho_by_einsum_aij_bji_to_ab(rho_m_array, method=list_enum)

    if trace_method.is_single_method():
        single_enum = trace_method.to_single_enum()
        num_n_u = len(rho_m_list)
        rho_m_list_combinations = combinations(rho_m_list, 2)

        addition_method = select_single_trace_rho_method(single_enum)
        trace_array = np.array(
            [addition_method(rho_m1_and_rho_m2) for rho_m1_and_rho_m2 in rho_m_list_combinations]
        )
        rho_traced_sum = trace_array.sum(dtype=np.complex128)
        rho_traced_sum /= num_n_u * (num_n_u - 1)

        return rho_traced_sum

    raise trace_method.value_error()
