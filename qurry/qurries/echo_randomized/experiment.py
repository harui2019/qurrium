"""EchoListenRandomized - Experiment (:mod:`qurry.qurries.echo_randomized.experiment`)"""

from typing import Any, Literal
from collections.abc import Iterable
from pathlib import Path
import warnings
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend, JobV1 as Job
from qiskit.transpiler.passmanager import PassManager

from .analysis import ELRAnalysis
from .arguments import ELRArguments, SHORT_NAME
from .utils import (
    overlapping_given_check,
    overlapping_size_check,
    unitary_full_cover_check,
    create_config,
    method_process,
)
from .exceptions import SeperatedExecutingOverlapResult
from ..entropy_randomized import RandomizedMeasureTales
from ...qurrium import ExperimentPrototype, Commonparams, RunArgsType, TranspileArgs, WCKeyable
from ...qurrium.utils import get_counts_and_exceptions, qasm_dumps
from ...qurrium.experiment import (
    memory_usage_factor_expect,
    ensure_runnable_backend,
    process_duo_transpilation,
)
from ...process.utils import QubitSelectionType
from ...process.availability import PostProcessingBackendLabel
from ...process.randomized_measure import check_random_unitary_seeds
from ...process.randomized_measure.wavefunction_overlap import DEFAULT_PROCESS_BACKEND
from ...tools import set_pbar_description, backend_name_getter


class ELRExperiment(ExperimentPrototype[ELRArguments, ELRAnalysis]):
    """The instance of experiment."""

    __name__ = "ELRExperiment"

    @classmethod
    def arguments_type(cls) -> type[ELRArguments]:
        """The arguments instance for this experiment."""
        return ELRArguments

    @classmethod
    def analysis_type(cls) -> type[ELRAnalysis]:
        """The analysis instance for this experiment."""
        return ELRAnalysis

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
        measure_1: QubitSelectionType = None,
        measure_2: QubitSelectionType = None,
        unitary_loc_1: QubitSelectionType = None,
        unitary_loc_2: QubitSelectionType = None,
        unitary_loc_not_cover_measure: bool = False,
        second_backend: Backend | None = None,
        second_transpile_args: TranspileArgs | None = None,
        random_unitary_seeds: dict[int, dict[int, int]] | None = None,
        **custom_kwargs: Any,
    ) -> tuple[ELRArguments, Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            times (int):
                The number of random unitary operator. Defaults to 100.
                It will denote as :math:`N_U` in the experiment name.
            measure_1 (QubitSelectionType, optional):
                The selected qubits for the measurement for the first quantum circuit.
                If it is None, then it will return the mapping of all qubits.
                If it is int, then it will return the mapping of the last n qubits.
                If it is tuple, then it will return the mapping of the qubits in the range.
                If it is list, then it will return the mapping of the selected qubits.
                Defaults to None.
            measure_2 (QubitSelectionType, optional):
                The selected qubits for the measurement for the second quantum circuit.
                If it is None, then it will return the mapping of all qubits.
                If it is int, then it will return the mapping of the last n qubits.
                If it is tuple, then it will return the mapping of the qubits in the range.
                If it is list, then it will return the mapping of the selected qubits.
                Defaults to None.
            unitary_loc_1 (QubitSelectionType, optional):
                The range of the unitary operator for the first quantum circuit.
                Defaults to None.
            unitary_loc_2 (QubitSelectionType, optional):
                The range of the unitary operator for the second quantum circuit.
                Defaults to None.
            unitary_loc_not_cover_measure (bool, optional):
                Confirm that not all unitary operator are covered by the measure.
                If True, then close the warning.
                Defaults to False.
            second_backend (Backend | None, optional):
                The extra backend for the second quantum circuit.
                If None, then use the same backend as the first quantum circuit.
                Defaults to None.
            second_transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`transpile` from :mod:`qiskit.compiler.transpiler`
                for the second quantum circuit. Defaults to None.
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
            ValueError: If the number of target circuits is not two.
            TypeError: If times is not an integer.
            ValueError: If the number of qubits in two circuits is not the same.

        Returns:
            tuple[EntropyMeasureRandomizedArguments, Commonparams, dict[str, Any]]:
                The arguments of the experiment, the common parameters, and the custom parameters.
        """
        if len(targets) != 2:
            raise ValueError("The number of target circuits should be two.")
        if not isinstance(times, int):
            raise TypeError(f"times should be an integer, but got {times}.")

        target_key_1, target_circuit_1 = targets[0]
        actual_qubits_1 = target_circuit_1.num_qubits
        target_key_2, target_circuit_2 = targets[1]
        actual_qubits_2 = target_circuit_2.num_qubits

        overlapping_given_check(
            actual_qubits_1, actual_qubits_2, measure_1, measure_2, unitary_loc_1, unitary_loc_2
        )

        (
            registers_mapping_1,
            qubits_measured_1,
            unitary_located_mapping_1,
            measured_but_not_unitary_located_1,
        ) = create_config(actual_qubits_1, measure_1, unitary_loc_1, "1")
        (
            registers_mapping_2,
            qubits_measured_2,
            unitary_located_mapping_2,
            measured_but_not_unitary_located_2,
        ) = create_config(actual_qubits_2, measure_2, unitary_loc_2, "2")

        overlapping_size_check(
            qubits_measured_1,
            qubits_measured_2,
            unitary_located_mapping_1,
            unitary_located_mapping_2,
        )
        unitary_full_cover_check(
            unitary_loc_not_cover_measure,
            measured_but_not_unitary_located_1,
            measured_but_not_unitary_located_2,
            measure_1,
            measure_2,
            unitary_loc_1,
            unitary_loc_2,
        )

        exp_name = f"{exp_name}.N_U_{times}.{SHORT_NAME}"

        check_random_unitary_seeds(times, len(unitary_located_mapping_1), random_unitary_seeds)
        check_random_unitary_seeds(times, len(unitary_located_mapping_2), random_unitary_seeds)

        if not any([isinstance(second_backend, Backend), second_backend is None]):
            raise TypeError(
                f"second_backend should be Backend or not given, but got {type(second_backend)}."
            )

        return ELRArguments.filter(
            exp_name=exp_name,
            target_keys=[target_key_1, target_key_2],
            times=times,
            qubits_measured_1=qubits_measured_1,
            qubits_measured_2=qubits_measured_2,
            registers_mapping_1=registers_mapping_1,
            registers_mapping_2=registers_mapping_2,
            actual_num_qubits_1=actual_qubits_1,
            actual_num_qubits_2=actual_qubits_2,
            unitary_located_mapping_1=unitary_located_mapping_1,
            unitary_located_mapping_2=unitary_located_mapping_2,
            second_backend=second_backend,
            second_transpile_args=second_transpile_args,
            random_unitary_seeds=random_unitary_seeds,
            **custom_kwargs,
        )

    @classmethod
    def method(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        arguments: ELRArguments,
    ) -> tuple[list[QuantumCircuit], RandomizedMeasureTales]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (EchoListenRandomizedArguments):
                The arguments of the experiment.

        Returns:
            The circuits of the experiment and the side products.
        """

        return method_process(targets, arguments)

    def replace_second_backend(self, backend: Backend | None) -> None:
        """Replace the second backend of the experiment.

        Args:
            backend (Backend | None): The new backend.
        Raises:
            ValueError: If the new backend is not a valid backend.
            ValueError: If the new backend is not a runnable backend.
        """
        if backend is None:
            if self.args.second_backend is None:
                return
            self.commons.datetimes.add_serial("remove-second-backend")
            self.args = self.args.replace_second_backend(None)
            return

        if not isinstance(backend, Backend):
            raise ValueError(f"Require a valid backend, but new backend: {backend} does not.")
        if not hasattr(backend, "run"):
            raise ValueError(f"Require a runnable backend, but new backend: {backend} does not.")

        old_backend = self.args.second_backend
        if old_backend is None:
            new_backend_name = backend_name_getter(backend)
            self.commons.datetimes.add_serial(f"add-second-backend-{new_backend_name}")
        else:
            old_backend_name = backend_name_getter(old_backend)
            new_backend_name = backend_name_getter(backend)
            self.commons.datetimes.add_serial(f"replace-{old_backend_name}-to-{new_backend_name}")
        self.args = self.args.replace_second_backend(backend)

    @classmethod
    def build(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        shots: int = 1024,
        backend: Backend | None = None,
        exp_name: str = "experiment",
        run_args: RunArgsType = None,
        transpile_args: TranspileArgs | None = None,
        passmanager_pair: tuple[str, PassManager] | None = None,
        tags: tuple[str, ...] | None = None,
        # multimanager
        serial: int | None = None,
        summoner_id: str | None = None,
        summoner_name: str | None = None,
        # process tool
        qasm_version: Literal["qasm2", "qasm3"] = "qasm3",
        export: bool = False,
        save_location: Path | str | None = None,
        pbar: tqdm.tqdm | None = None,
        multiprocess: bool = True,
        # special
        second_passmanager_pair: tuple[str, PassManager] | None = None,
        **custom_and_main_kwargs: Any,
    ):
        """Construct the experiment.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend | None, optional):
                The quantum backend. Defaults to None.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            run_args (RunArgsType, optional):
                Arguments for :meth:`Backend.run`. Defaults to None.
            transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`~qiskit.compiler.transpile`
                Defaults to None.
            passmanager_pair (tuple[str, PassManager] | None, optional):
                The passmanager pair for transpile. Defaults to None.
            tags (tuple[str, ...] | None, optional):
                Given tags for the experiment to describe it.
                Defaults to None.

            serial (int | None, optional):
                Index of experiment in
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                **!!ATTENTION, this should only be used by
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`!!**
                Defaults to None.
            summoner_id (str | None, optional):
                ID of experiment of
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                **!!ATTENTION, this should only be used by
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`!!**
                Defaults to None.
            summoner_name (str | None, optional):
                Name of experiment of
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                **!!ATTENTION, this should only be used by
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`!!**
                Defaults to None.

            qasm_version (Literal["qasm2", "qasm3"], optional):
                The export version of OpenQASM. Defaults to 'qasm3'.
            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Path | str | None, optional):
                The location to save the experiment. Defaults to None.
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.
            multiprocess (bool, optional):
                Whether to use multiprocessing. Defaults to `True`.

            second_passmanager_pair (tuple[str, PassManager] | None, optional):
                The passmanager pair for transpile of the second circuit.
                Defaults to None.
            custom_and_main_kwargs (Any):
                Other custom arguments.

        Returns:
            ExperimentPrototype: The experiment.
        """

        # preparing
        set_pbar_description(pbar, "Parameter loading...")

        current_exp = cls._params_control_core(
            targets=targets,
            shots=shots,
            backend=backend,
            run_args=run_args,
            transpile_args=transpile_args,
            tags=tags,
            exp_name=exp_name,
            serial=serial,
            summoner_id=summoner_id,
            summoner_name=summoner_name,
            pbar=pbar,
            **custom_and_main_kwargs,
        )
        assert isinstance(current_exp.commons.backend, Backend), (
            f"Invalid backend: {current_exp.commons.backend} as "
            + f"type {type(current_exp.commons.backend)}. "
        )
        assert isinstance(current_exp.args.second_backend, (Backend, type(None))), (
            f"Invalid second backend: {current_exp.args.second_backend} as "
            + f"type {type(current_exp.args.second_backend)}. "
        )

        # circuit
        set_pbar_description(pbar, "Circuit creating...")
        current_exp.beforewards.target.extend(targets)
        circs, side_products = current_exp.method(targets, current_exp.args)
        current_exp.side_products.update(side_products)

        # qasm
        set_pbar_description(pbar, "Exporting OpenQASM string...")
        current_exp.beforewards.circuit_qasm.extend(
            qasm_dumps(circ, qasm_version) for circ in circs
        )
        current_exp.beforewards.target_qasm.extend(
            (str(key), qasm_dumps(circ, qasm_version)) for key, circ in targets
        )

        transpiled_circs = process_duo_transpilation(
            circuits=circs,
            backend=current_exp.commons.backend,
            transpile_args=current_exp.commons.transpile_args.copy(),
            passmanager_pair=passmanager_pair,
            second_backend=current_exp.args.second_backend,
            second_transpile_args=current_exp.args.second_transpile_args,
            second_passmanager_pair=second_passmanager_pair,
            times=current_exp.args.times,
            exp_id=current_exp.exp_id,
            multiprocess=multiprocess,
            pbar=pbar,
        )
        set_pbar_description(pbar, "Circuit loading...")
        current_exp.beforewards.circuit.extend(transpiled_circs)

        # memory usage factor
        current_exp.memory_usage_factor = memory_usage_factor_expect(
            target=current_exp.beforewards.target,
            circuits=current_exp.beforewards.circuit,
            commonparams=current_exp.commons,
        )

        # commons
        note_and_date = current_exp.commons.datetimes.add_only("build")
        set_pbar_description(
            pbar, f"Building Completed, denoted '{note_and_date[0]}' date: {note_and_date[1]}..."
        )

        # export may be slow, consider export at finish or something
        if isinstance(save_location, (Path, str)) and export:
            set_pbar_description(pbar, "Setup data exporting...")
            current_exp.write(save_location=save_location)

        return current_exp

    # local execution
    def run(self, pbar: tqdm.tqdm | None = None) -> str:
        """Export the result after running the job.

        Args:
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment. Defaults to None.

        Raises:
            ValueError: No circuit ready.
            ValueError: The circuit has not been constructed yet.

        Returns:
            str: The ID of the experiment.
        """
        if len(self.beforewards.circuit) == 0:
            raise ValueError("The circuit has not been constructed yet.")

        ensure_runnable_backend(self.commons.backend)
        assert isinstance(self.commons.backend, Backend), "Backend should be ensured at this point."

        if self.args.second_backend is None:
            set_pbar_description(pbar, "Executing with single backend...")
            event_name, date = self.commons.datetimes.add_serial("run")
            execution_1: Job = self.commons.backend.run(  # type: ignore
                self.beforewards.circuit,
                shots=self.commons.shots,
                **self.commons.run_args,
            )
            # commons
            set_pbar_description(
                pbar, f"Executing completed '{event_name}', denoted date: {date}..."
            )
            # beforewards
            self.beforewards.job_id.append(execution_1.job_id())
            # afterwards
            result_1 = execution_1.result()
            self.afterwards.result.append(result_1)

            return self.exp_id

        ensure_runnable_backend(self.args.second_backend)

        if backend_name_getter(self.args.second_backend) == backend_name_getter(
            self.commons.backend
        ):
            warnings.warn(
                f"The second backend {self.args.second_backend} is seem to be "
                + f"the same as the first backend {self.commons.backend}. "
                + "But since they will excute separately, "
                + "it will return different results although the same backend",
                category=SeperatedExecutingOverlapResult,
            )

        set_pbar_description(pbar, "Executing with two backends...")
        event_name, date = self.commons.datetimes.add_serial("run")
        execution_1: Job = self.commons.backend.run(  # type: ignore
            self.beforewards.circuit[: self.args.times],
            shots=self.commons.shots,
            **self.commons.run_args,
        )
        execution_2: Job = self.args.second_backend.run(  # type: ignore
            self.beforewards.circuit[self.args.times :],
            shots=self.commons.shots,
            **self.commons.run_args,
        )
        # commons
        set_pbar_description(pbar, f"Executing completed '{event_name}', denoted date: {date}...")
        # beforewards
        self.beforewards.job_id.append(f"{execution_1.job_id()}_{execution_2.job_id()}")
        # afterwards
        result_1 = execution_1.result()
        self.afterwards.result.append(result_1)
        result_2 = execution_2.result()
        self.afterwards.result.append(result_2)

        return self.exp_id

    def result(
        self,
        export: bool = False,
        save_location: Path | str | None = None,
        pbar: tqdm.tqdm | None = None,
    ) -> str:
        """Export the result of the experiment.

        Args:
            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Path | str | None, optional):
                The location to save the experiment. Defaults to None.
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            str: The ID of the experiment.
        """
        if len(self.afterwards.result) > 2:
            raise ValueError(
                "The number of results should be one or two, "
                + f"but got {len(self.afterwards.result)}."
            )

        if len(self.afterwards.result) == 1:
            set_pbar_description(pbar, "Result loading from single job...")
            counts_1, exceptions_1 = get_counts_and_exceptions(
                result=self.afterwards.result[0], num=self.args.times * 2
            )
            if len(exceptions_1) > 0:
                if "exceptions" not in self.outfields:
                    self.outfields["exceptions"] = {}
                for result_id, exception_item in exceptions_1.items():
                    self.outfields["exceptions"][result_id] = exception_item

            set_pbar_description(pbar, "Counts loading from single job...")
            self.afterwards.counts.extend(counts_1)

        else:
            set_pbar_description(pbar, "Result loading from two jobs...")
            counts_1, exceptions_1 = get_counts_and_exceptions(
                result=self.afterwards.result[0],
                num=self.args.times,
            )
            counts_2, exceptions_2 = get_counts_and_exceptions(
                result=self.afterwards.result[1],
                num=self.args.times,
            )
            exceptions = {**exceptions_1, **exceptions_2}
            if len(exceptions) > 0:
                if "exceptions" not in self.outfields:
                    self.outfields["exceptions"] = {}
                for result_id, exception_item in exceptions.items():
                    self.outfields["exceptions"][result_id] = exception_item

            set_pbar_description(pbar, "Counts loading from two jobs...")
            self.afterwards.counts.extend(counts_1 + counts_2)

        if export:
            # export may be slow, consider export at finish or something
            if isinstance(save_location, (Path, str)):
                set_pbar_description(pbar, "Setup data exporting...")
                self.write(save_location=save_location)

        return self.exp_id

    def analyze(
        self,
        selected_classical_registers: Iterable[int] | None = None,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        counts_used: Iterable[int] | None = None,
    ) -> ELRAnalysis:
        """Calculate wave function overlap with more information combined.

        Args:
            selected_classical_registers (Iterable[int] | None, optional):
                The list of **the index of the selected_classical_registers**.
                It's not the qubit index of first or second quantum circuit,
                but their corresponding classical registers.
                Defaults to None.
            backend (PostProcessingBackendLabel, optional):
                The backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
            counts_used (Iterable[int] | None, optional):
                The index of the counts used. Defaults to None.

        Returns:
            EchoListenRandomizedAnalysis: The result of the experiment
        """

        serial = len(self.reports)
        analysis = self.analysis_type().perform_analysis(
            arguments=self.args,
            commonparams=self.commons,
            counts=self.afterwards.counts,
            analyze_arguments={
                "selected_classical_registers": selected_classical_registers,
                "backend": backend,
                "counts_used": counts_used,
            },
            serial=serial,
        )

        self.reports[serial] = analysis
        return analysis
