"""ShadowUnveil - Experiment (:mod:`qurry.qurries.classical_shadow.experiment`)"""

from typing import Any
from pathlib import Path
from collections.abc import Iterable
import numpy.typing as npt

from qiskit import QuantumCircuit

from .analysis import SUAnalysis
from .arguments import SUArguments, SHORT_NAME
from .utils import make_samplied_circuit, get_basis_spin
from ..entropy_randomized.exceptions import UnitaryOperatorNotFullCovering
from ...qurrium import ExperimentPrototype, Commonparams, WCKeyable
from ...process.utils import qubit_mapper, QubitSelectionType, FloatType
from ...process.classical_shadow import (
    generate_random_basis,
    check_random_basis,
    ShadowBasisMethod,
    ShadowBasisType,
    RhoMethodType,
    DEFAULT_RHO_METHOD,
    TraceMethodType,
    DEFAULT_TRACE_METHOD,
    ListTraceMethodType,
    DEFAULT_LIST_TRACE_METHOD,
    measurements_export,
)


class SUExperiment(ExperimentPrototype[SUArguments, SUAnalysis]):
    """The instance of experiment."""

    __name__ = "SUExperiment"

    @classmethod
    def arguments_type(cls) -> type[SUArguments]:
        """The arguments instance for this experiment."""
        return SUArguments

    @classmethod
    def analysis_type(cls) -> type[SUAnalysis]:
        """The analysis instance for this experiment."""
        return SUAnalysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        exp_name: str = "exps",
        snapshots: int = 100,
        measure: QubitSelectionType = None,
        unitary_loc: QubitSelectionType = None,
        unitary_loc_not_cover_measure: bool = False,
        shadow_basis_method: ShadowBasisType | None = None,
        random_basis: dict[int, dict[int, int]] | None = None,
        **custom_kwargs: Any,
    ) -> tuple[SUArguments, Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            snapshots (int, optional):
                The number of random unitary operator, previously called `times`
                It will denote as :math:`N_U` in the experiment name.
                Defaults to `100`.
            measure (QubitSelectionType, optional):
                The measure range. Defaults to None.
            unitary_loc (QubitSelectionType, optional):
                The range of the unitary operator. Defaults to None.
            unitary_loc_not_cover_measure (bool, optional):
                Confirm that not all unitary operator are covered by the measure.
                If True, then close the warning.
                Defaults to False.
            shadow_basis_method (ShadowBasisType | None, optional):
                The classical shadow basis for sampling. It can be set to
                :class:`~qurry.process.classical_shadow.rho_process.unitary_set.ShadowRandomBasis`
                or
                :class:`~qurry.process.classical_shadow.rho_process.unitary_set.ShadowBasisMethod`.
                Defaults to None, which use the default Pauli basis from
                :meth:`ShadowBasisMethod.`.
            random_basis (dict[int, dict[int, int]] | None, optional):
                The random basis for classical shadow.

                This argument only takes input as type of `dict[int, dict[int, int]]`.
                The first key is the index if snapshots.
                The second key is the index for the qubit.

                .. code-block:: python

                    {
                        0: {0: 1, 1: 0},
                        1: {0: 2, 1: 1},
                        2: {0: 0, 1: 2},
                    }

                If you want to generate the seeds for all random unitary operator,
                you can use the function :func:`generate_random_basis`
                in :mod:`qurry.process.classical_shadow.utils`.

                .. code-block:: python

                    from qurry import generate_random_basis

                    random_basis = generate_random_basis(100, [0, 1])

            custom_kwargs (Any):
                The custom parameters.

        Raises:
            ValueError: If the number of targets is not one.
            TypeError: If times is not an integer.
            ValueError: If the range of measure is not in the range of unitary_loc.

        Returns:
            The arguments of the experiment, the common parameters, and the custom parameters.
        """
        if len(targets) > 1:
            raise ValueError("The number of target circuits should be only one.")
        if not isinstance(snapshots, int):
            raise TypeError(
                f"times should be an integer, but got {snapshots} as type {type(snapshots)}."
            )
        if snapshots < 2:
            raise ValueError(
                "times should be greater than 1 for classical shadow "
                + f"on the calculation of entangled entropy, but got {snapshots}."
            )
        shadow_basis = ShadowBasisMethod.get_shadow_basis(shadow_basis_method)

        target_key, target_circuit = targets[0]
        actual_qubits = target_circuit.num_qubits

        registers_mapping = qubit_mapper(actual_qubits, measure)
        qubits_measured = list(registers_mapping)

        unitary_located = list(qubit_mapper(actual_qubits, unitary_loc))
        measured_but_not_unitary_located = [
            qi for qi in qubits_measured if qi not in unitary_located
        ]
        if len(measured_but_not_unitary_located) > 0 and not unitary_loc_not_cover_measure:
            raise UnitaryOperatorNotFullCovering(
                f"Some qubits {measured_but_not_unitary_located} are measured "
                + "but not random unitary located. "
                + f"unitary_loc: {unitary_loc}, measure: {measure} "
                + "If you are sure about this, you can set `unitary_loc_not_cover_measure=True` "
                + "to close this warning."
            )

        if random_basis is None:
            actual_random_basis = generate_random_basis(snapshots, unitary_located)
            actual_snapshot = snapshots
        else:
            actual_random_basis = random_basis
            actual_snapshot = len(random_basis)
        check_random_basis(actual_random_basis, unitary_located)

        return SUArguments.filter(
            exp_name=f"{exp_name}.N_U_{actual_snapshot}.{SHORT_NAME}",
            target_keys=[target_key],
            snapshots=actual_snapshot,
            qubits_measured=qubits_measured,
            registers_mapping=registers_mapping,
            actual_num_qubits=actual_qubits,
            unitary_located=unitary_located,
            shadow_basis=shadow_basis,
            random_basis=actual_random_basis,
            **custom_kwargs,
        )

    @classmethod
    def method(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        arguments: SUArguments,
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (SUArguments):
                The arguments of the experiment.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the side products.
        """

        target_key, target_circuit = targets[0]
        target_key = target_key if isinstance(target_key, int) else str(target_key)

        return [
            make_samplied_circuit(
                n_u_i,
                target_circuit,
                target_key,
                arguments.exp_name,
                arguments.registers_mapping,
                arguments.random_basis[n_u_i],
                arguments.shadow_basis,
            )
            for n_u_i in range(arguments.snapshots)
        ], {}

    def prepare_entries_analysis(
        self,
        selected_qubits: Iterable[int] | None = None,
        # estimation of given operators
        given_operators: list[npt.NDArray] | None = None,
        accuracy_prob_comp_delta: FloatType = 0.01,
        max_shadow_norm: FloatType | None = None,
        # other config
        rho_method: RhoMethodType = DEFAULT_RHO_METHOD,
        use_projector: bool = False,
        trace_method: TraceMethodType = DEFAULT_TRACE_METHOD,
        estimate_trace_method: ListTraceMethodType = DEFAULT_LIST_TRACE_METHOD,
        counts_used: Iterable[int] | None = None,
    ) -> dict[str, Any]:
        r"""Prepare the entries for analysis.

        Args:
            selected_qubits (Iterable[int] | None, optional):
                The selected qubits. Defaults to None.

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

            counts_used (Iterable[int] | None, optional):
                The index of the counts used. Defaults to None.

        Returns:
            The entries for the method
            :meth:`~qurry.qurries.classical_shadow.analysis.SUAnalysis.perform_analysis`.
        """
        return {
            "arguments": self.args,
            "commonparams": self.commons,
            "counts": self.afterwards.counts,
            "analyze_arguments": {
                "selected_qubits": list(selected_qubits) if selected_qubits is not None else None,
                "given_operators": given_operators,
                "accuracy_prob_comp_delta": accuracy_prob_comp_delta,
                "max_shadow_norm": max_shadow_norm,
                "rho_method": rho_method,
                "use_projector": use_projector,
                "trace_method": trace_method,
                "estimate_trace_method": estimate_trace_method,
                "counts_used": counts_used,
            },
            "serial": len(self.reports),
            "random_basis": self.args.random_basis,
        }

    def analyze(
        self,
        selected_qubits: Iterable[int] | None = None,
        # estimation of given operators
        given_operators: list[npt.NDArray] | None = None,
        accuracy_prob_comp_delta: FloatType = 0.01,
        max_shadow_norm: FloatType | None = None,
        # other config
        rho_method: RhoMethodType = DEFAULT_RHO_METHOD,
        use_projector: bool = False,
        trace_method: TraceMethodType = DEFAULT_TRACE_METHOD,
        estimate_trace_method: ListTraceMethodType = DEFAULT_LIST_TRACE_METHOD,
        counts_used: Iterable[int] | None = None,
    ) -> SUAnalysis:
        r"""Calculate entangled entropy with more information combined.

        Args:
            selected_qubits (Iterable[int] | None, optional):
                The selected qubits. Defaults to None.

            given_operators (list[npt.NDArray] | None):
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

            counts_used (Iterable[int] | None, optional):
                The index of the counts used. Defaults to None.

        Returns:
            The result of the analysis.
        """

        analysis = self.analysis_type().perform_analysis(
            **self.prepare_entries_analysis(
                selected_qubits=selected_qubits,
                given_operators=given_operators,
                accuracy_prob_comp_delta=accuracy_prob_comp_delta,
                max_shadow_norm=max_shadow_norm,
                rho_method=rho_method,
                trace_method=trace_method,
                use_projector=use_projector,
                estimate_trace_method=estimate_trace_method,
                counts_used=counts_used,
            )
        )
        self.reports[analysis.serial] = analysis
        return analysis

    def get_basis_spin_format(
        self,
        counts_used: Iterable[int] | None = None,
        filename: str | Path | None = None,
    ) -> tuple[list[list[int]], list[list[int]]]:
        """Get the basis-spin format from the counts and random basis of experiment,
        which uses in `Predicting Properties of Quantum Many-Body Systems
        <https://github.com/hsinyuan-huang/predicting-quantum-properties>`_ .

        Args:
            counts_used (Iterable[int] | None, optional):
                The index of the counts used. Defaults to None.
            filename (str | Path | None, optional):
                The filename to export the basis-spin format.
                If it is None, it will not export to a file. Defaults to None.

        Returns:
            A tuple containing a list of pauli basis and a list of spin outcomes.
        """

        basis_and_spin = get_basis_spin(
            self.commons.shots,
            self.afterwards.counts,
            self.args.registers_mapping,
            self.args.random_basis,
            counts_used,
        )
        if filename is None:
            return basis_and_spin

        measurements_export(*basis_and_spin, len(self.args.registers_mapping), filename)

        return basis_and_spin
