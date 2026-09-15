"""EchoListenRandomized - Qurrium (:mod:`qurry.qurries.echo_randomized.qurry`)"""

from typing import Any, Literal
from collections.abc import Iterable
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend

from .arguments import SHORT_NAME, ACRONYM, ELRMeasureArgs, ELROutputArgs
from .analysis import ELRAnalyzeArgs
from .experiment import ELRExperiment, PostProcessingBackendLabel, DEFAULT_PROCESS_BACKEND
from ...qurrium import (
    QurriumPrototype,
    WCKeyable,
    TranspileArgs,
    RunArgsType,
    PassManagerType,
    SpecificAnalyzeArgs,
)
from ...qurries.entropy_randomized.utils import DEFAULT_CLASSICAL_REGISTER_NAME
from ...qurrium.container import passmanager_processor
from ...process.utils import QubitSelectionType


class EchoListenRandomized(
    QurriumPrototype[ELRExperiment, ELRMeasureArgs, ELROutputArgs, ELRAnalyzeArgs]
):
    """Randomized Measure for wave function overlap.
    a.k.a. loschmidt echo when processes time evolution system.

    Reference:
        -   Statistical correlations between locally randomized measurements:
            A toolbox for probing entanglement in many-body quantum states -
            A. Elben, B. Vermersch, C. F. Roos, and P. Zoller,
            `PhysRevA.99.052323 <https://doi.org/10.1103/PhysRevA.99.052323>`_

        .. code-block:: bibtex

            @article{PhysRevA.99.052323,
                title = {Statistical correlations between locally randomized measurements:
                A toolbox for probing entanglement in many-body quantum states},
                author = {Elben, A. and Vermersch, B. and Roos, C. F. and Zoller, P.},
                journal = {Phys. Rev. A},
                volume = {99},
                issue = {5},
                pages = {052323},
                numpages = {12},
                year = {2019},
                month = {May},
                publisher = {American Physical Society},
                doi = {10.1103/PhysRevA.99.052323},
                url = {https://link.aps.org/doi/10.1103/PhysRevA.99.052323}
            }
    """

    __name__ = "EchoListenRandomized"
    short_name = SHORT_NAME
    """The short name of this Qurrium class."""
    acronym = ACRONYM
    """The abbreviation of this Qurrium class."""
    reserved_register_names = {DEFAULT_CLASSICAL_REGISTER_NAME}
    """The set of reserved classical register names."""

    @property
    def experiment_instance(self) -> type[ELRExperiment]:
        """The container class responding to this Qurrium class."""
        return ELRExperiment

    def measure_to_output(
        self,
        wave1: QuantumCircuit | WCKeyable | None = None,
        wave2: QuantumCircuit | WCKeyable | None = None,
        times: int = 100,
        measure_1: QubitSelectionType = None,
        measure_2: QubitSelectionType = None,
        unitary_loc_1: QubitSelectionType = None,
        unitary_loc_2: QubitSelectionType = None,
        unitary_loc_not_cover_measure: bool = False,
        second_backend: Backend | None = None,
        second_transpile_args: TranspileArgs | None = None,
        second_passmanager: PassManagerType = None,
        random_unitary_seeds: dict[int, dict[int, int]] | None = None,
        # basic inputs
        shots: int = 1024,
        backend: Backend | None = None,
        exp_name: str = "experiment",
        run_args: RunArgsType = None,
        transpile_args: TranspileArgs | None = None,
        passmanager: PassManagerType = None,
        tags: tuple[str, ...] | None = None,
        # process tool
        qasm_version: Literal["qasm2", "qasm3"] = "qasm3",
        export: bool = False,
        save_location: Path | str | None = None,
        pbar: tqdm.tqdm | None = None,
    ) -> ELROutputArgs:
        """Trasnform :meth:`measure` arguments form into :meth:`output` form.

        Args:
            wave1 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            wave2 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            times (int, optional):
                The number of random unitary operator.
                It will denote as :math:`N_U` in the experiment name.
                Defaults to `100`.
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
                Whether the range of the unitary operator is not cover the measure range.
                Defaults to False.
            second_backend (Backend | None, optional):
                The extra backend for the second quantum circuit.
                If None, then use the same backend as the first quantum circuit.
                Defaults to None.
            second_transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`transpile` from :mod:`qiskit.compiler.transpiler`
                for the second quantum circuit. Defaults to None.
            second_passmanager (PassManagerType | None, optional):
                The passmanager for the second quantum circuit. Defaults to None.
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

            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend | None, optional):
                The quantum backend. Defaults to None.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            run_args (RunArgsType, optional):
                Arguments for :meth:`Backend.run`. Defaults to None.
            transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`~qiskit.compiler.transpile`.
                Defaults to None.
            passmanager (PassManagerType | None, optional):
                The passmanager. Defaults to None.
            tags (tuple[str, ...] | None, optional):
                The tags of the experiment. Defaults to None.

            qasm_version (Literal["qasm2", "qasm3"], optional):
                The version of OpenQASM. Defaults to "qasm3".
            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Path | str | None, optional):
                The location to save the experiment. Defaults to None.
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            The output arguments.
        """
        if wave1 is None:
            raise ValueError("The `wave` must be provided.")
        if wave2 is None:
            raise ValueError("The `wave2` must be provided.")

        second_passmanager_pair = passmanager_processor(
            passmanager=second_passmanager, passmanager_container=self.passmanagers
        )

        if wave1 == "your_darkness" and wave2 == "my_darkness":
            print("| Your darkness and mine, a storm I can't disobey.")
            print("| Let me take you away...")

        return {
            "circuits": [wave1, wave2],
            "times": times,
            "measure_1": measure_1,
            "measure_2": measure_2,
            "unitary_loc_1": unitary_loc_1,
            "unitary_loc_2": unitary_loc_2,
            "unitary_loc_not_cover_measure": unitary_loc_not_cover_measure,
            "second_backend": second_backend,
            "second_transpile_args": second_transpile_args,
            "random_unitary_seeds": random_unitary_seeds,
            "shots": shots,
            "backend": backend,
            "exp_name": exp_name,
            "run_args": run_args,
            "transpile_args": transpile_args,
            "passmanager": passmanager,
            "tags": tags,
            # process tool
            "qasm_version": qasm_version,
            "export": export,
            "save_location": save_location,
            "pbar": pbar,
            "second_passmanager_pair": second_passmanager_pair,
        }

    def prepare(
        self,
        wave1: QuantumCircuit | WCKeyable | None = None,
        wave2: QuantumCircuit | WCKeyable | None = None,
        times: int = 100,
        measure_1: QubitSelectionType = None,
        measure_2: QubitSelectionType = None,
        unitary_loc_1: QubitSelectionType = None,
        unitary_loc_2: QubitSelectionType = None,
        unitary_loc_not_cover_measure: bool = False,
        second_backend: Backend | None = None,
        second_transpile_args: TranspileArgs | None = None,
        second_passmanager: PassManagerType | None = None,
        random_unitary_seeds: dict[int, dict[int, int]] | None = None,
        # basic inputs
        shots: int = 1024,
        backend: Backend | None = None,
        exp_name: str = "experiment",
        run_args: RunArgsType = None,
        transpile_args: TranspileArgs | None = None,
        passmanager: PassManagerType | None = None,
        tags: tuple[str, ...] | None = None,
        # process tool
        qasm_version: Literal["qasm2", "qasm3"] = "qasm3",
        export: bool = False,
        save_location: Path | str | None = None,
        pbar: tqdm.tqdm | None = None,
    ):
        """Prepare the experiment without executing it.

        Args:
            wave1 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            wave2 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            times (int, optional):
                The number of random unitary operator.
                It will denote as :math:`N_U` in the experiment name.
                Defaults to `100`.
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
                Whether the range of the unitary operator is not cover the measure range.
                Defaults to False.
            second_backend (Backend | None, optional):
                The extra backend for the second quantum circuit.
                If None, then use the same backend as the first quantum circuit.
                Defaults to None.
            second_transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`transpile` from :mod:`qiskit.compiler.transpiler`
                for the second quantum circuit. Defaults to None.
            second_passmanager (PassManagerType | None, optional):
                The passmanager for the second quantum circuit. Defaults to None.
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

            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend | None, optional):
                The quantum backend. Defaults to None.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it
                when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            run_args (RunArgsType, optional):
                Arguments for :meth:`Backend.run`. Defaults to None.
            transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`~qiskit.compiler.transpile`.
                Defaults to None.
            passmanager (PassManagerType | None, optional):
                The passmanager. Defaults to None.
            tags (tuple[str, ...] | None, optional):
                The tags of the experiment. Defaults to None.

            qasm_version (Literal["qasm2", "qasm3"], optional):
                The version of OpenQASM. Defaults to "qasm3".
            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Path | str | None, optional):
                The location to save the experiment. Defaults to None.
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            The experiment instance.
        """

        exp_id = self.build(
            **self.measure_to_output(
                wave1=wave1,
                wave2=wave2,
                times=times,
                measure_1=measure_1,
                measure_2=measure_2,
                unitary_loc_1=unitary_loc_1,
                unitary_loc_2=unitary_loc_2,
                unitary_loc_not_cover_measure=unitary_loc_not_cover_measure,
                second_backend=second_backend,
                second_transpile_args=second_transpile_args,
                second_passmanager=second_passmanager,
                random_unitary_seeds=random_unitary_seeds,
                shots=shots,
                backend=backend,
                exp_name=exp_name,
                run_args=run_args,
                transpile_args=transpile_args,
                passmanager=passmanager,
                tags=tags,
                # process tool
                qasm_version=qasm_version,
                export=export,
                save_location=save_location,
                pbar=pbar,
            )
        )
        return self.orphan_exps[exp_id]

    def measure(
        self,
        wave1: QuantumCircuit | WCKeyable | None = None,
        wave2: QuantumCircuit | WCKeyable | None = None,
        times: int = 100,
        measure_1: QubitSelectionType = None,
        measure_2: QubitSelectionType = None,
        unitary_loc_1: QubitSelectionType = None,
        unitary_loc_2: QubitSelectionType = None,
        unitary_loc_not_cover_measure: bool = False,
        second_backend: Backend | None = None,
        second_transpile_args: TranspileArgs | None = None,
        second_passmanager: PassManagerType | None = None,
        random_unitary_seeds: dict[int, dict[int, int]] | None = None,
        # basic inputs
        shots: int = 1024,
        backend: Backend | None = None,
        exp_name: str = "experiment",
        run_args: RunArgsType = None,
        transpile_args: TranspileArgs | None = None,
        passmanager: PassManagerType | None = None,
        tags: tuple[str, ...] | None = None,
        # process tool
        qasm_version: Literal["qasm2", "qasm3"] = "qasm3",
        export: bool = False,
        save_location: Path | str | None = None,
        pbar: tqdm.tqdm | None = None,
    ):
        """Execute the experiment immediately.

        Args:
            wave1 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            wave2 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            times (int, optional):
                The number of random unitary operator.
                It will denote as :math:`N_U` in the experiment name.
                Defaults to `100`.
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
                Whether the range of the unitary operator is not cover the measure range.
                Defaults to False.
            second_backend (Backend | None, optional):
                The extra backend for the second quantum circuit.
                If None, then use the same backend as the first quantum circuit.
                Defaults to None.
            second_transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`transpile` from :mod:`qiskit.compiler.transpiler`
                for the second quantum circuit. Defaults to None.
            second_passmanager (PassManagerType | None, optional):
                The passmanager for the second quantum circuit. Defaults to None.
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

            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend | None, optional):
                The quantum backend. Defaults to None.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it
                when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            run_args (RunArgsType, optional):
                Arguments for :meth:`Backend.run`. Defaults to None.
            transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`~qiskit.compiler.transpile`.
                Defaults to None.
            passmanager (PassManagerType | None, optional):
                The passmanager. Defaults to None.
            tags (tuple[str, ...] | None, optional):
                The tags of the experiment. Defaults to None.

            qasm_version (Literal["qasm2", "qasm3"], optional):
                The version of OpenQASM. Defaults to "qasm3".
            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Path | str | None, optional):
                The location to save the experiment. Defaults to None.
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            The experiment instance.
        """

        exp_id = self.output(
            **self.measure_to_output(
                wave1=wave1,
                wave2=wave2,
                times=times,
                measure_1=measure_1,
                measure_2=measure_2,
                unitary_loc_1=unitary_loc_1,
                unitary_loc_2=unitary_loc_2,
                unitary_loc_not_cover_measure=unitary_loc_not_cover_measure,
                second_backend=second_backend,
                second_transpile_args=second_transpile_args,
                second_passmanager=second_passmanager,
                random_unitary_seeds=random_unitary_seeds,
                shots=shots,
                backend=backend,
                exp_name=exp_name,
                run_args=run_args,
                transpile_args=transpile_args,
                passmanager=passmanager,
                tags=tags,
                # process tool
                qasm_version=qasm_version,
                export=export,
                save_location=save_location,
                pbar=pbar,
            )
        )
        return self.orphan_exps[exp_id]

    def multiAnalysis(
        self,
        summoner_id: str,
        *,
        analysis_name: str = "report",
        no_serialize: bool = False,
        specific_analysis_args: SpecificAnalyzeArgs[ELRAnalyzeArgs] = None,
        skip_write: bool = False,
        multiprocess_write: bool = False,
        # analysis arguments
        selected_classical_registers: Iterable[int] | None = None,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        counts_used: Iterable[int] | None = None,
        **analysis_args: dict[str, Any],
    ) -> tuple[str, str]:
        """Run the analysis for multiple experiments.

        Args:
            summoner_id (str): The summoner_id of multimanager.
            analysis_name (str, optional):
                The name of analysis. Defaults to 'report'.
            no_serialize (bool, optional):
                Whether to serialize the analysis. Defaults to False.
            specific_analysis_args (SpecificAnalyzeArgs[ELRAnalyzeArgs], optional):
                The specific arguments for analysis. Defaults to None.
            skip_write (bool, optional):
                Whether to skip the file writing during the analysis. Defaults to False.
            multiprocess_write (bool, optional):
                Whether use multiprocess for writing. Defaults to False.

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
            The summoner_id of multimanager and the report name.
        """

        return super().multiAnalysis(
            summoner_id=summoner_id,
            analysis_name=analysis_name,
            no_serialize=no_serialize,
            specific_analysis_args=specific_analysis_args,
            skip_write=skip_write,
            multiprocess_write=multiprocess_write,
            selected_classical_registers=selected_classical_registers,
            counts_used=counts_used,
            backend=backend,
            **analysis_args,
        )
