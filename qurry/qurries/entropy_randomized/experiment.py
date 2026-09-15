"""EntropyMeasureRandomized - Experiment (:mod:`qurry.qurries.entropy_randomized.experiment`)"""

from typing import Any
from collections.abc import Iterable

from qiskit import QuantumCircuit

from .analysis import EMRAnalysis
from .arguments import EMRArguments, SHORT_NAME
from .tales import RandomizedMeasureTales
from .utils import method_process
from .exceptions import UnitaryOperatorNotFullCovering
from ...qurrium import ExperimentPrototype, Commonparams, WCKeyable
from ...process.utils import qubit_mapper, QubitSelectionType
from ...process.randomized_measure import check_random_unitary_seeds
from ...process.randomized_measure.entangled_entropy import (
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)


class EMRExperiment(ExperimentPrototype[EMRArguments, EMRAnalysis]):
    """The instance of experiment."""

    __name__ = "EMRExperiment"

    @classmethod
    def arguments_type(cls) -> type[EMRArguments]:
        """The arguments instance for this experiment."""
        return EMRArguments

    @classmethod
    def analysis_type(cls) -> type[EMRAnalysis]:
        """The analysis instance for this experiment."""
        return EMRAnalysis

    @classmethod
    def side_product_type(cls) -> type[RandomizedMeasureTales]:
        return RandomizedMeasureTales

    side_products: RandomizedMeasureTales

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        exp_name: str = "exps",
        times: int = 100,
        measure: QubitSelectionType = None,
        unitary_loc: QubitSelectionType = None,
        unitary_loc_not_cover_measure: bool = False,
        random_unitary_seeds: dict[int, dict[int, int]] | None = None,
        **custom_kwargs: Any,
    ) -> tuple[EMRArguments, Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            times (int, optional):
                The number of random unitary operator. Defaults to 100.
                It will denote as :math:`N_U` in the experiment name.
            measure (QubitSelectionType, optional):
                The selected qubits for the measurement.
                If it is None, then it will return the mapping of all qubits.
                If it is int, then it will return the mapping of the last n qubits.
                If it is tuple, then it will return the mapping of the qubits in the range.
                If it is list, then it will return the mapping of the selected qubits.
                Defaults to None.
            unitary_loc (QubitSelectionType, optional):
                The range of the unitary operator. Defaults to None.
            unitary_loc_not_cover_measure (bool, optional):
                Confirm that not all unitary operator are covered by the measure.
                If True, then close the warning.
                Defaults to False.
            random_unitary_seeds (dict[int, dict[int, int]] | None, optional):
                The seeds for all random unitary operator.
                This argument only takes input as type of `dict[int, dict[int, int]]`.
                The first key is the index for the random unitary operator.
                The second key is the index for the qubit.

                .. code-block:: python

                    {
                        0: {0: 1234, 1: 5678},
                        1: {0: 2345, 1: 6789},
                        2: {0: 3456, 1: 7890},
                    }

                If you want to generate the seeds for all random unitary operator,
                you can use the function :func:`generate_random_unitary_seeds`
                in :mod:`qurry.process.randomized_measure.utils`.

                .. code-block:: python

                    from qurry import generate_random_unitary_seeds

                    random_unitary_seeds = generate_random_unitary_seeds(100, 2)

            custom_kwargs (Any):
                The custom parameters.

        Raises:
            ValueError: If the number of targets is not one.
            TypeError: If times is not an integer.
            ValueError: If the range of measure is not in the range of unitary_loc.

        Returns:
            tuple[EntropyMeasureRandomizedArguments, Commonparams, dict[str, Any]]:
                The arguments of the experiment, the common parameters, and the custom parameters.
        """
        if len(targets) > 1:
            raise ValueError("The number of target circuits should be only one.")
        if not isinstance(times, int):
            raise TypeError(f"times should be an integer, but got {times}.")

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

        exp_name = f"{exp_name}.N_U_{times}.{SHORT_NAME}"

        check_random_unitary_seeds(times, len(unitary_located), random_unitary_seeds)

        return EMRArguments.filter(
            exp_name=exp_name,
            target_keys=[target_key],
            times=times,
            qubits_measured=qubits_measured,
            registers_mapping=registers_mapping,
            actual_num_qubits=actual_qubits,
            unitary_located=unitary_located,
            random_unitary_seeds=random_unitary_seeds,
            **custom_kwargs,
        )

    @classmethod
    def method(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        arguments: EMRArguments,
    ) -> tuple[list[QuantumCircuit], RandomizedMeasureTales]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (EntropyMeasureRandomizedArguments):
                The arguments of the experiment.

        Returns:
            The circuits of the experiment and the side products.
        """

        return method_process(targets, arguments)

    def analyze(
        self,
        selected_qubits: Iterable[int] | None = None,
        independent_all_system: bool = False,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        counts_used: Iterable[int] | None = None,
    ) -> EMRAnalysis:
        """Calculate entangled entropy with more information combined.

        Args:
            selected_qubits (Iterable[int] | None, optional):
                The selected qubits. Defaults to None.
            independent_all_system (bool, optional):
                If True, then calculate the all system independently. Defaults to False.
            backend (PostProcessingBackendLabel, optional):
                The backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
            counts_used (Iterable[int] | None, optional):
                The index of the counts used. Defaults to None.

        Returns:
            EntropyMeasureRandomizedAnalysis: The result of the analysis.
        """

        available_all_system_source = [
            k
            for k, v in self.reports.items()
            if v.is_independent_all_system(
                range(len(self.afterwards.counts)) if counts_used is None else counts_used
            )
        ]
        all_system_source = (
            self.reports[available_all_system_source[-1]]
            if len(available_all_system_source) > 0 and not independent_all_system
            else None
        )

        serial = len(self.reports)
        analysis = self.analysis_type().perform_analysis(
            arguments=self.args,
            commonparams=self.commons,
            counts=self.afterwards.counts,
            analyze_arguments={
                "selected_qubits": list(selected_qubits) if selected_qubits is not None else None,
                "independent_all_system": independent_all_system,
                "backend": backend,
                "counts_used": counts_used,
            },
            serial=serial,
            existed_all_system=(
                all_system_source.get_all_system_result() if all_system_source is not None else None
            ),
        )

        self.reports[analysis.serial] = analysis
        return analysis
