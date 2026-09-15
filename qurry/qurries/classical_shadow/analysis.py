"""ShadowUnveil - Analysis (:mod:`qurry.qurries.classical_shadow.analysis`)"""

# pylint: disable=too-many-lines
from typing import Any, Literal, overload, TypeVar, Generic
from collections.abc import Iterable
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt

from .arguments import SUArguments
from .utils import get_random_basis_array
from ...qurrium import (
    Commonparams,
    AnalysisPrototype,
    AnalyzeArgs,
    AnalysisMiddlewarePrototype,
    ProcessEntriesPrototype,
    AnalysisResultsPrototype,
)
from ...qurrium.utils import bitstring_mapping_getter
from ...process.utils import counts_list_recount_pyrust, FloatType
from ...process.classical_shadow import (
    RhoMethod,
    RhoMethodType,
    DEFAULT_RHO_METHOD,
    ShadowBasisType,
    ShadowRandomBasis,
    ShadowRandomBasisData,
    TraceMethod,
    TraceMethodType,
    DEFAULT_TRACE_METHOD,
    ListTraceMethod,
    ListTraceMethodType,
    DEFAULT_LIST_TRACE_METHOD,
    PurityValueKind,
    classical_shadow_complex,
    ClassicalShadowBasic,
    ClassicalShadowPurity,
    EstimationOfObservable,
)


class SUAnalyzeArgs(AnalyzeArgs, total=False):
    """The input of :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiAnalysis` and
    :meth:`~qurry.qurries.classical_shadow.experiment.SUExperiment.analyze`.
    """

    selected_qubits: list[int] | None
    """The selected qubits."""
    # estimation of given operators
    given_operators: list[npt.NDArray] | None
    """The list of the operators to estimate."""
    accuracy_prob_comp_delta: FloatType
    """The accuracy probability for computing delta."""
    max_shadow_norm: FloatType | None
    """The maximum shadow norm of the given operators."""
    # other config
    rho_method: RhoMethodType
    """The method to reconstruct the density matrix."""
    use_projector: bool
    r"""Use the projecter :math:`P_m` instead of the precomputed :math:`\rho_m`. 

    Refer to :func:`qurry.process.classical_shadow.rho_process.rho_m_cell.rho_m_cell_precomputed`
    for more details.
    """
    trace_method: TraceMethodType
    """The method to compute the trace."""

    estimate_trace_method: ListTraceMethodType
    """The method to estimate the trace."""
    counts_used: Iterable[int] | None
    """The index of the counts used."""


@dataclass(frozen=True)
class SUMiddleware(AnalysisMiddlewarePrototype):
    """The middleware entries between analyze and actual post-processing function."""

    __name__ = "SUMiddleware"

    num_qubits: int
    """The number of qubits."""
    selected_qubits: list[int]
    """The selected qubits."""
    registers_mapping: dict[int, int]
    """The mapping of the classical registers with quantum registers.

    .. code-block:: python

        {
            0: 0, # The quantum register 0 is mapped to the classical register 0.
            1: 1, # The quantum register 1 is mapped to the classical register 1.
            5: 2, # The quantum register 5 is mapped to the classical register 2.
            7: 3, # The quantum register 7 is mapped to the classical register 3.
        }

    The key is the index of the quantum register with the numerical order.
    The value is the index of the classical register with the numerical order.
    """
    bitstring_mapping: dict[int, int]
    """The mapping of the bitstring with the classical registers.
    When there are mulitple classical registers, 
    the bitstring is the concatenation of the classical registers with space on bitstring.
    For example, there are three registers with the size of 4, 4, and 6, 
    which the first six bits are for the randomized measurement.

    .. code-block:: python

        {'010000 0100 0001': 1024}
        # The bitstring is '010000 0100 0001'.
        # The last four bits are the first classical register.
        # The middle four bits are the second classical register.
        # The first six bits are the last classical register for the randomized measurement.

    So, the mapping will be like this.

    .. code-block:: python


        {
            0: 10, # The classical register 0 is mapped to the bitstring on the index 0.
            1: 11, # The classical register 0 is mapped to the bitstring on the index 1.
            2: 12, # The classical register 0 is mapped to the bitstring on the index 2.
            3: 13, # The classical register 0 is mapped to the bitstring on the index 3.
            4: 14, # The classical register 0 is mapped to the bitstring on the index 4.
            5: 15, # The classical register 0 is mapped to the bitstring on the index 5.
        }

    But, if there is only one classical register, 
    the bitstring will map to the classical register directly.

    .. code-block:: python

        {'010000': 1024}

    Will be like this.

    .. code-block:: python

        {
            0: 0, # The classical register 0 is mapped to the bitstring on the index 0.
            1: 1, # The classical register 0 is mapped to the bitstring on the index 1.
            2: 2, # The classical register 0 is mapped to the bitstring on the index 2.
            3: 3, # The classical register 0 is mapped to the bitstring on the index 3.
            4: 4, # The classical register 0 is mapped to the bitstring on the index 4.
            5: 5, # The classical register 0 is mapped to the bitstring on the index 5.
        }

    """
    final_mapping: dict[int, int]
    """The final mapping of the classical registers after selection with the quantum registers.

    .. code-block:: python

        {
            "registers_mapping": {
                2: 0,
                3: 1
            },  # qubit index to original classical index
            "bitstring_mapping": {
                0: 5,
                1: 6,
            },  # original classical index to shifted index, which the index on full bitstring
            "final_mapping": {
                2: 5,
                3: 6
            },  # qubit index to shifted index, which the index on full bitstring
        }
    
    More details can be found in :func:`~qurry.qurrium.utils.counts.bitstring_mapping_getter`.
    """
    unitary_located: list[int] | None = None
    """The range of the unitary operator."""
    counts_used: Iterable[int] | None = None
    """The index of the counts used. If not specified, then use all counts."""

    def export(self) -> dict[str, Any]:
        """Export the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """

        return {
            **self.asdict(),
            "counts_used": list(self.counts_used) if self.counts_used is not None else None,
        }

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Load the results from a dictionary.

        Args:
            raw_dict (dict[str, Any]): The data to load.

        Returns:
            The loaded results object.
        """
        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {missing_fields}")

        return cls(
            num_qubits=raw_dict["num_qubits"],
            selected_qubits=raw_dict["selected_qubits"],
            registers_mapping={int(k): int(v) for k, v in raw_dict["registers_mapping"].items()},
            bitstring_mapping={int(k): int(v) for k, v in raw_dict["bitstring_mapping"].items()},
            final_mapping={int(k): int(v) for k, v in raw_dict["final_mapping"].items()},
            unitary_located=(
                None
                if raw_dict.get("unitary_located") is None
                else [int(v) for v in raw_dict["unitary_located"]]
            ),
            counts_used=(
                None
                if raw_dict.get("counts_used") is None
                else [int(v) for v in raw_dict["counts_used"]]
            ),
        )


@dataclass(frozen=True)
class SUProcessEntries(ProcessEntriesPrototype):
    """The entries for post-processing."""

    __name__ = "SUProcessEntries"

    random_basis_array: list[list[Literal[0, 1, 2] | int]]
    """The random basis for classical shadow."""
    selected_classical_registers: list[int] | None
    """The list of **the index of the selected_classical_registers**."""

    # esitimation of given operators
    given_operators: list[npt.NDArray] | None
    """The list of the operators to estimate."""
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
    maximum_shadow_norm: FloatType | None
    r"""The maximum shadow norm, which is defined in the supplementary material 
    with value between 0 and 1.
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
    The :math:`|| O_i - \frac{\text{tr}(O_i)}{2^n} ||_{\text{shadow}}^2` is maximum shadow norm,
    which is defined in the supplementary material with value between 0 and 1.

    Due to maximum shadow norm is complex and it is a norm,
    we suppose we have the worst case scenario,
    where the maximum shadow norm is 1 as default.
    Thus, we can simplify the equation to:

    .. math::
        N = \frac{34}{\epsilon^2}
    """

    rho_method: RhoMethodType
    """The method to reconstruct the density matrix."""
    shadow_basis: ShadowRandomBasis
    """The shadow basis used for classical shadow."""
    use_projector: bool
    r"""Use the projecter :math:`P_m` instead of the precomputed :math:`\rho_m`. 

    Refer to :func:`qurry.process.classical_shadow.rho_process.rho_m_cell.rho_m_cell_precomputed`
    for more details.
    """
    trace_method: TraceMethodType
    """The method to calculate the trace of Rho."""
    estimate_trace_method: ListTraceMethodType
    """The method to calculate the trace of Rho."""

    def export(self) -> dict[str, Any]:
        """Export the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """

        return {
            "shots": self.shots,
            "random_basis_array": self.random_basis_array,
            "selected_classical_registers": (
                list(self.selected_classical_registers)
                if self.selected_classical_registers is not None
                else None
            ),
            "given_operators": (
                [
                    np.array(np.array(op, dtype=np.complex128), dtype=str).tolist()
                    for op in self.given_operators
                ]
                if self.given_operators is not None
                else None
            ),
            "accuracy_predict_epsilon": float(self.accuracy_predict_epsilon),
            "maximum_shadow_norm": (
                None if self.maximum_shadow_norm is None else float(self.maximum_shadow_norm)
            ),
            "rho_method": (
                self.rho_method
                if isinstance(self.rho_method, RhoMethod)
                else RhoMethod.from_string(self.rho_method)
            ).value,
            "shadow_basis": self.shadow_basis.export(),
            "use_projector": self.use_projector,
            "trace_method": (
                self.trace_method
                if isinstance(self.trace_method, TraceMethod)
                else TraceMethod.from_string(self.trace_method)
            ).value,
            "estimate_trace_method": (
                self.estimate_trace_method
                if isinstance(self.estimate_trace_method, ListTraceMethod)
                else ListTraceMethod.from_string(self.estimate_trace_method)
            ).value,
        }

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw read dictionary.
        """
        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {', '.join(missing_fields)}")
        given_operators = (
            [np.array(op, dtype=complex) for op in raw_dict["given_operators"]]
            if raw_dict["given_operators"] is not None
            else None
        )

        return cls(
            shots=raw_dict["shots"],
            random_basis_array=raw_dict["random_basis_array"],
            selected_classical_registers=raw_dict["selected_classical_registers"],
            given_operators=given_operators,
            accuracy_predict_epsilon=float(raw_dict["accuracy_predict_epsilon"]),
            maximum_shadow_norm=(
                None
                if raw_dict["maximum_shadow_norm"] is None
                else float(raw_dict["maximum_shadow_norm"])
            ),
            rho_method=raw_dict["rho_method"],
            shadow_basis=ShadowRandomBasis.ingest(raw_dict["shadow_basis"]),
            use_projector=raw_dict.get("use_projector", False),
            trace_method=TraceMethod.from_string(raw_dict["trace_method"]),
            estimate_trace_method=ListTraceMethod.from_string(raw_dict["estimate_trace_method"]),
        )

    def __repr__(self) -> str:
        """The representation of the process entries."""
        entries_str_dict = {
            field: f"{field}={getattr(self, field)!r}"
            for field in self.fields
            if field not in ["random_basis_array", "given_operators"]
        }

        entries_str_dict["random_basis_array"] = (
            (f"random_basis_array=[...{len(self.random_basis_array)} items...]")
            if self.random_basis_array is not None
            else "random_basis_array=None"
        )
        entries_str_dict["given_operators"] = (
            (f"given_operators=[...{len(self.given_operators)} items...]")
            if self.given_operators is not None
            else "given_operators=None"
        )

        field_strs = [entries_str_dict[field] for field in self.fields]
        return f"{self.__class__.__name__}({', '.join(field_strs)})"


@dataclass(frozen=True)
class SUBasicResult(AnalysisResultsPrototype):
    """The target system result of :class:`~qurry.qurries.classical_shadow.analysis.SUAnalysis`."""

    __name__ = "SUBasicResult"

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

    def side_product_fields(self) -> tuple[str, ...]:
        """The side product fields for the analysis result.

        Returns:
            tuple[str, ...]: The side product fields.
        """
        return ("average_snapshots_rho_list",)

    def export(self) -> dict[str, Any]:
        """Export the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """
        return {
            "average_snapshots_rho_list": [
                np.array(rho, dtype=str).tolist() for rho in self.average_snapshots_rho_list
            ],
            "classical_registers_actually": self.classical_registers_actually,
            "taking_time": float(self.taking_time),
            "rho_method": (
                self.rho_method
                if isinstance(self.rho_method, RhoMethod)
                else RhoMethod.from_string(self.rho_method)
            ).value,
            "random_basis_data": self.random_basis_data,
            "mean_of_rho": np.array(self.mean_of_rho, dtype=str).tolist(),
            "use_projector": self.use_projector,
        }

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw read dictionary.
        """
        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {', '.join(missing_fields)}")

        return cls(
            average_snapshots_rho_list=[
                np.array(rho, dtype=np.complex128) for rho in raw_dict["average_snapshots_rho_list"]
            ],
            classical_registers_actually=raw_dict["classical_registers_actually"],
            taking_time=float(raw_dict["taking_time"]),
            rho_method=RhoMethod.from_string(raw_dict["rho_method"]),
            random_basis_data=raw_dict["random_basis_data"],
            mean_of_rho=np.array(raw_dict["mean_of_rho"], dtype=np.complex128),
            use_projector=raw_dict.get("use_projector", False),
        )


@dataclass(frozen=True)
class SUPurityResult(AnalysisResultsPrototype):
    """The purity result of :class:`~qurry.qurries.classical_shadow.analysis.SUAnalysis`."""

    __name__ = "SUPurityResult"

    purity: FloatType
    """The purity of the density matrix."""
    entropy: FloatType
    """The second Renyi entropy of the density matrix."""
    purity_value_kind: PurityValueKind | str
    """The kind of purity value."""
    taking_time: float
    """The time taken for the calculation."""
    trace_method: TraceMethodType
    """The method to calculate the trace of Rho."""

    def export(self) -> dict[str, Any]:
        """Export the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """
        return {
            "purity": float(self.purity),
            "entropy": float(self.entropy),
            "purity_value_kind": self.purity_value_kind,
            "taking_time": float(self.taking_time),
            "trace_method": (
                TraceMethod.from_string(self.trace_method)
                if isinstance(self.trace_method, str)
                else self.trace_method
            ).value,
        }

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw read dictionary.
        """
        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {', '.join(missing_fields)}")

        return cls(
            purity=float(raw_dict["purity"]),
            entropy=float(raw_dict["entropy"]),
            purity_value_kind=raw_dict["purity_value_kind"],
            taking_time=float(raw_dict["taking_time"]),
            trace_method=TraceMethod.from_string(raw_dict["trace_method"]),
        )


@dataclass(frozen=True)
class SUEstimationResult(AnalysisResultsPrototype):
    """The estimation result of :class:`~qurry.qurries.classical_shadow.analysis.SUAnalysis`."""

    __name__ = "SUEstimationResult"

    estimate_of_given_operators: list[np.complex128] | list[complex]
    """The estimation of the given operators."""
    corresponding_rhos: list[npt.NDArray[np.complex128]]
    """The corresponding Rho for each given operator."""
    all_candidates_of_estimate: list[list[np.complex128]] | list[list[complex]]
    r"""The all candidates of esitmation values of measurement primitive :math:`\mathcal{U}`."""
    trace_with_mean_rho_of_given_operators: list[np.complex128] | list[complex]
    r"""The trace of the given operators with the mean of rho."""

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

    def side_product_fields(self) -> tuple[str, ...]:
        """The side product fields for the analysis result.

        Returns:
            tuple[str, ...]: The side product fields.
        """
        return ("corresponding_rhos",)

    def export(self) -> dict[str, Any]:
        """Export the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """
        return {
            "estimate_of_given_operators": [
                str(complex(est)) for est in self.estimate_of_given_operators
            ],
            "corresponding_rhos": [
                np.array(rho, dtype=str).tolist() for rho in self.corresponding_rhos
            ],
            "all_candidates_of_estimate": [
                [str(complex(est)) for est in candidate]
                for candidate in self.all_candidates_of_estimate
            ],
            "trace_with_mean_rho_of_given_operators": [
                str(complex(val)) for val in self.trace_with_mean_rho_of_given_operators
            ],
            "accuracy_prob_comp_delta": float(self.accuracy_prob_comp_delta),
            "num_of_estimators_k": int(self.num_of_estimators_k),
            "accuracy_predict_epsilon": float(self.accuracy_predict_epsilon),
            "maximum_shadow_norm": float(self.maximum_shadow_norm),
            "epsilon_upperbound": float(self.epsilon_upperbound),
            "shadow_norm_upperbound": float(self.shadow_norm_upperbound),
            "taking_time": float(self.taking_time),
            "estimate_trace_method": (
                ListTraceMethod.from_string(self.estimate_trace_method)
                if isinstance(self.estimate_trace_method, str)
                else self.estimate_trace_method
            ).value,
        }

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw read dictionary.
        """
        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {', '.join(missing_fields)}")

        return cls(
            estimate_of_given_operators=[
                complex(est) for est in raw_dict["estimate_of_given_operators"]
            ],
            corresponding_rhos=[
                np.array(rho, dtype=np.complex128) for rho in raw_dict["corresponding_rhos"]
            ],
            all_candidates_of_estimate=[
                [complex(est) for est in candidate]
                for candidate in raw_dict["all_candidates_of_estimate"]
            ],
            trace_with_mean_rho_of_given_operators=[
                complex(val) for val in raw_dict["trace_with_mean_rho_of_given_operators"]
            ],
            accuracy_prob_comp_delta=float(raw_dict["accuracy_prob_comp_delta"]),
            num_of_estimators_k=int(raw_dict["num_of_estimators_k"]),
            accuracy_predict_epsilon=float(raw_dict["accuracy_predict_epsilon"]),
            maximum_shadow_norm=float(raw_dict["maximum_shadow_norm"]),
            epsilon_upperbound=float(raw_dict["epsilon_upperbound"]),
            shadow_norm_upperbound=float(raw_dict["shadow_norm_upperbound"]),
            taking_time=float(raw_dict["taking_time"]),
            estimate_trace_method=ListTraceMethod.from_string(raw_dict["estimate_trace_method"]),
        )


_KInst = TypeVar("_KInst", bound=str)
"""The key type variable for SUResultsType and SUResults."""
_VInst = TypeVar("_VInst", bound=AnalysisResultsPrototype)
"""The value type variable for SUResultsType and SUResults."""


class SUResultsType(
    Generic[_KInst, _VInst],
    dict[
        Literal["basic", "purity", "estimation"] | _KInst | str,
        type[SUBasicResult] | type[SUPurityResult] | type[SUEstimationResult] | type[_VInst],
    ],
):
    """The results of :class:`~qurry.qurries.classical_shadow.analysis.SUAnalysis`."""

    @overload
    def __getitem__(self, key: Literal["basic"]) -> type[SUBasicResult]: ...
    @overload
    def __getitem__(self, key: Literal["purity"]) -> type[SUPurityResult]: ...
    @overload
    def __getitem__(self, key: Literal["estimation"]) -> type[SUEstimationResult]: ...
    @overload
    def __getitem__(self, key: _KInst) -> type[_VInst]: ...
    @overload
    def __getitem__(
        self, key: str
    ) -> type[SUBasicResult] | type[SUPurityResult] | type[SUEstimationResult] | type[_VInst]: ...

    def __getitem__(self, key):
        return super().__getitem__(key)


class SUResults(
    Generic[_KInst, _VInst],
    dict[
        Literal["basic", "purity", "estimation"] | _KInst | str,
        SUBasicResult | SUPurityResult | SUEstimationResult | _VInst,
    ],
):
    """The results of :class:`~qurry.qurries.classical_shadow.analysis.SUAnalysis`."""

    @overload
    def __getitem__(self, key: Literal["basic"]) -> SUBasicResult: ...
    @overload
    def __getitem__(self, key: Literal["purity"]) -> SUPurityResult: ...
    @overload
    def __getitem__(self, key: Literal["estimation"]) -> SUEstimationResult: ...
    @overload
    def __getitem__(self, key: _KInst) -> _VInst: ...
    @overload
    def __getitem__(
        self, key: str
    ) -> SUBasicResult | SUPurityResult | SUEstimationResult | _VInst: ...

    def __getitem__(self, key):
        return super().__getitem__(key)


class SUAnalysis(
    Generic[_KInst, _VInst],
    AnalysisPrototype[
        SUArguments,
        SUAnalyzeArgs,
        SUMiddleware,
        SUProcessEntries,
        SUResultsType[_KInst, _VInst],
        SUResults[_KInst, _VInst],
    ],
):
    """The container for the analysis of
    :class:`~qurry.qurries.classical_shadow.experiment.SUExperiment`."""

    __name__ = "SUAnalysis"

    results: SUResults[_KInst, _VInst]
    """The results of the analysis."""

    @classmethod
    def analyze_arguments_type(cls) -> type[SUAnalyzeArgs]:
        """The type of analyze arguments."""
        return SUAnalyzeArgs

    @classmethod
    def middleware_entries_type(cls) -> type[SUMiddleware]:
        """The middleware entries type for this analysis."""
        return SUMiddleware

    @classmethod
    def postprocess_entries_type(cls) -> type[SUProcessEntries]:
        """The post-process entries type for this analysis."""
        return SUProcessEntries

    @classmethod
    def available_results_types(cls) -> SUResultsType[_KInst, _VInst]:
        """The available result types for this analysis."""
        return SUResultsType(
            {
                "basic": SUBasicResult,
                "purity": SUPurityResult,
                "estimation": SUEstimationResult,
            }
        )

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[dict[str, int]],
        random_basis_array: list[list[Literal[0, 1, 2] | int]],
        selected_classical_registers: Iterable[int] | None,
        # estimation of given operators
        given_operators: list[npt.NDArray] | None,
        accuracy_prob_comp_delta: FloatType,
        max_shadow_norm: FloatType | None,
        # other config
        rho_method: RhoMethodType,
        shadow_basis: ShadowBasisType,
        use_projector: bool,
        trace_method: TraceMethodType,
        estimate_trace_method: ListTraceMethodType,
    ) -> tuple[ClassicalShadowBasic, ClassicalShadowPurity | None, EstimationOfObservable | None]:
        r"""Calculate the classical shadow quantities.

        Args:
            shots (int):
                The number of shots.
            counts (list[dict[str, int]]):
                The list of the counts.
            random_basis_array (list[list[Literal[0, 1, 2] | int]]):
                The random basis for classical shadow.
            selected_classical_registers (Iterable[int]):
                The list of **the index of the selected_classical_registers**.

            given_operators (list[npt.NDArray] | None, optional):
                The list of the operators to estimate. Defaults to None.
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
                    Uses :math:`H`, :math:`H` followed by :math:`S^\dagger`, and Identity gates.
            use_projector (bool):
                Use the projecter :math:`P_m` instead of the precomputed :math:`\rho_m`.
                Refer to
                :func:`qurry.process.classical_shadow.rho_process.rho_m_cell.rho_m_cell_precomputed`
                for more details.
                When :attr:`use_projector` is False,
                which means using the precomputed :math:`\rho_{mk}^{i}`.
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
                        This is the fastest implementation to calculate the trace of Rho.

                - Non-matrix operation methods:
                    - "nomatmul_trace_py": Use pure Python implementation without multiprocessing.
                    - "nomatmul_trace_rust": Use Rust implementation via PyO3.

                - Skip calculation of trace:
                    - "skip_trace": Skip the trace calculation and return NaN.

                For the non-matrix operation methods, it will directly calculate the trace from
                the counts and random basis.

                Default to DEFAULT_TRACE_METHOD.
            estimate_trace_method (ListTraceMethodType, optional):
                The method to use for the calculation.

                - "einsum_aij_bji_to_ab_numpy":
                    Use `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace.
                    This is the fastest implementation to calculate the trace of Rho.

                Defaults to DEFAULT_LIST_TRACE_METHOD.

        Returns:
            ClassicalShadowComplex: The result of the classical shadow.
        """

        return classical_shadow_complex(
            shots=shots,
            counts=counts,
            random_basis_array=random_basis_array,
            selected_classical_registers=selected_classical_registers,
            # estimation of given operators
            given_operators=given_operators,
            accuracy_prob_comp_delta=accuracy_prob_comp_delta,
            max_shadow_norm=max_shadow_norm,
            # other config
            rho_method=rho_method,
            shadow_basis=shadow_basis,
            use_projector=use_projector,
            trace_method=trace_method,
            estimate_trace_method=estimate_trace_method,
        )

    @classmethod
    def generate_entries(
        cls,
        arguments: SUArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: SUAnalyzeArgs,
        random_basis: dict[int, dict[int, int]] | None = None,
    ) -> tuple[SUAnalyzeArgs, SUMiddleware, SUProcessEntries, list[dict[str, int]]]:
        """Generate the entries for analysis.

        Args:
            arguments (SUArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (SUAnalyzeArgs): The analyze arguments.
            random_basis (dict[int, dict[int, int]] | None, optional):
                The random basis for classical shadow. Defaults to None.

        Returns:
            The generated entries for analysis and the possibly filtered counts.
        """

        if random_basis is None:
            raise ValueError("random_basis should be specified.")
        if len(random_basis) != arguments.snapshots:
            raise ValueError(
                f"The number of random basis should be {arguments.snapshots}, "
                + f"but got {len(random_basis)}."
            )

        counts_used = analyze_arguments.get("counts_used", None)
        if isinstance(counts_used, Iterable):
            if max(counts_used) >= len(counts):
                raise ValueError(
                    f"counts_used should be less than {len(counts)}, but get {max(counts_used)}."
                )
            counts = [counts[i] for i in counts_used]
        elif counts_used is not None:
            raise TypeError(
                f"counts_used should be Iterable[int] or None, but got {type(counts_used)}."
            )

        bitstring_mapping, final_mapping = bitstring_mapping_getter(
            counts, arguments.registers_mapping
        )

        selected_qubits = analyze_arguments.get("selected_qubits", None)
        selected_qubits = (
            [qi % arguments.actual_num_qubits for qi in selected_qubits]
            if selected_qubits
            else list(arguments.registers_mapping.keys())
        )
        if len(set(selected_qubits)) != len(selected_qubits):
            raise ValueError(
                f"selected_qubits should not have duplicated elements, but got {selected_qubits}."
            )

        counts_of_last_clreg = counts_list_recount_pyrust(
            counts,
            len(next(iter(counts[0]))),
            list(final_mapping.values()),
        )

        # random basis follow normal register mapping
        # for it does not need to consider extra classical registers
        # but effect by count_used
        random_basis_array = get_random_basis_array(
            arguments.registers_mapping, random_basis, counts_used
        )

        return (
            analyze_arguments,
            SUMiddleware(
                num_qubits=arguments.actual_num_qubits,
                selected_qubits=selected_qubits,
                registers_mapping=arguments.registers_mapping,
                bitstring_mapping=bitstring_mapping,
                final_mapping=final_mapping,
                unitary_located=arguments.unitary_located,
                counts_used=counts_used,
            ),
            SUProcessEntries(
                shots=commonparams.shots,
                random_basis_array=random_basis_array,
                selected_classical_registers=[
                    arguments.registers_mapping[qi] for qi in selected_qubits
                ],
                # estimation of given operators
                given_operators=analyze_arguments.get("given_operators", None),
                accuracy_predict_epsilon=analyze_arguments.get("accuracy_prob_comp_delta", 0.01),
                maximum_shadow_norm=analyze_arguments.get("max_shadow_norm", None),
                # other config
                rho_method=analyze_arguments.get("rho_method", DEFAULT_RHO_METHOD),
                shadow_basis=arguments.shadow_basis,
                use_projector=analyze_arguments.get("use_projector", False),
                trace_method=analyze_arguments.get("trace_method", DEFAULT_TRACE_METHOD),
                estimate_trace_method=analyze_arguments.get(
                    "estimate_trace_method", DEFAULT_LIST_TRACE_METHOD
                ),
            ),
            counts_of_last_clreg,
        )

    @classmethod
    def perform_analysis(
        cls,
        arguments: SUArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: SUAnalyzeArgs,
        serial: int,
        outfields: dict[str, Any] | None = None,
        datetime: str | None = None,
        random_basis: dict[int, dict[int, int]] | None = None,
    ):
        """Perform the analysis for the experiment.

        Args:
            arguments (SUArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (SUAnalyzeArgs): The analyze arguments.
            serial (int): The serial number of the analysis.
            outfields (dict[str, Any] | None, optional): The output fields. Defaults to None.
            datetime (str | None, optional): The datetime string. Defaults to None.
            random_basis (dict[int, dict[int, int]] | None, optional):
                The random basis for classical shadow. Defaults to None.

        Returns:
            The analysis result.
        """

        analyze_arguments, middleware_entries, postprocess_entries, selected_counts = (
            cls.generate_entries(arguments, commonparams, counts, analyze_arguments, random_basis)
        )

        cs_basic_obj, cs_trace_obj, cs_estimation_obj = cls.quantities(
            shots=commonparams.shots,
            counts=selected_counts,
            random_basis_array=postprocess_entries.random_basis_array,
            selected_classical_registers=postprocess_entries.selected_classical_registers,
            # estimation of given operators
            given_operators=postprocess_entries.given_operators,
            accuracy_prob_comp_delta=postprocess_entries.accuracy_predict_epsilon,
            max_shadow_norm=postprocess_entries.maximum_shadow_norm,
            # other config
            rho_method=postprocess_entries.rho_method,
            shadow_basis=arguments.shadow_basis,
            use_projector=postprocess_entries.use_projector,
            trace_method=postprocess_entries.trace_method,
            estimate_trace_method=postprocess_entries.estimate_trace_method,
        )

        results = SUResults[_KInst, _VInst]({"basic": SUBasicResult(**cs_basic_obj)})
        if cs_trace_obj is not None:
            results["purity"] = SUPurityResult(**cs_trace_obj)
        if cs_estimation_obj is not None:
            results["estimation"] = SUEstimationResult(**cs_estimation_obj)

        return cls(
            analyze_arguments=analyze_arguments,
            middleware_entries=middleware_entries,
            postprocess_entries=postprocess_entries,
            results=results,
            serial=serial,
            outfields=outfields,
            datetime=datetime,
        )
