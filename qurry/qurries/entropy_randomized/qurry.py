"""EntropyMeasureRandomized - Qurrium (:mod:`qurry.qurries.entropy_randomized.qurry`)"""

from typing import Literal
from collections.abc import Iterable
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend

from .utils import DEFAULT_CLASSICAL_REGISTER_NAME
from .arguments import SHORT_NAME, ACRONYM, EMRMeasureArgs, EMROutputArgs
from .analysis import EMRAnalyzeArgs
from .experiment import EMRExperiment, PostProcessingBackendLabel, DEFAULT_PROCESS_BACKEND
from ...qurrium import (
    QurriumPrototype,
    RunArgsType,
    TranspileArgs,
    PassManagerType,
    SpecificAnalyzeArgs,
    WCKeyable,
)
from ...process.utils import QubitSelectionType


class EntropyMeasureRandomized(
    QurriumPrototype[EMRExperiment, EMRMeasureArgs, EMROutputArgs, EMRAnalyzeArgs]
):
    """Randomized Measure for entangled entropy.
    The entropy we compute is the Second Order Rényi Entropy.

    Reference:
        - Randomized Measure - Entangled Entropy
            -   Probing Rényi entanglement entropy via randomized measurements -
                Tiff Brydges, Andreas Elben, Petar Jurcevic, Benoît Vermersch,
                Christine Maier, Ben P. Lanyon, Peter Zoller, Rainer Blatt ,and Christian F. Roos,
                `doi:10.1126/science.aau4963
                <https://www.science.org/doi/abs/10.1126/science.aau4963>`_

            -   Statistical correlations between locally randomized measurements:
                A toolbox for probing entanglement in many-body quantum states -
                A. Elben, B. Vermersch, C. F. Roos, and P. Zoller,
                `PhysRevA.99.052323 <https://doi.org/10.1103/PhysRevA.99.052323>`_

        .. code-block:: bibtex

            @article{doi:10.1126/science.aau4963,
                author = {Tiff Brydges  and Andreas Elben  and Petar Jurcevic
                    and Benoît Vermersch  and Christine Maier  and Ben P. Lanyon
                    and Peter Zoller  and Rainer Blatt  and Christian F. Roos },
                title = {Probing Rényi entanglement entropy via randomized measurements},
                journal = {Science},
                volume = {364},
                number = {6437},
                pages = {260-263},
                year = {2019},
                doi = {10.1126/science.aau4963},
                URL = {https://www.science.org/doi/abs/10.1126/science.aau4963},
                eprint = {https://www.science.org/doi/pdf/10.1126/science.aau4963},
                abstract = {Quantum systems are predicted to be better at information
                processing than their classical counterparts, and quantum entanglement
                is key to this superior performance. But how does one gauge the degree
                of entanglement in a system? Brydges et al. monitored the build-up of
                the so-called Rényi entropy in a chain of up to 10 trapped calcium ions,
                each of which encoded a qubit. As the system evolved,
                interactions caused entanglement between the chain and the rest of
                the system to grow, which was reflected in the growth of
                the Rényi entropy. Science, this issue p. 260 The buildup of entropy
                in an ion chain reflects a growing entanglement between the chain
                and its complement. Entanglement is a key feature of many-body quantum systems.
                Measuring the entropy of different partitions of a quantum system
                provides a way to probe its entanglement structure.
                Here, we present and experimentally demonstrate a protocol
                for measuring the second-order Rényi entropy based on statistical correlations
                between randomized measurements. Our experiments, carried out with a trapped-ion
                quantum simulator with partition sizes of up to 10 qubits,
                prove the overall coherent character of the system dynamics and
                reveal the growth of entanglement between its parts,
                in both the absence and presence of disorder.
                Our protocol represents a universal tool for probing and
                characterizing engineered quantum systems in the laboratory,
                which is applicable to arbitrary quantum states of up to
                several tens of qubits.}
            }

            @article{PhysRevA.99.052323,
                title = {
                    Statistical correlations between locally randomized measurements:
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

    __name__ = "EntropyMeasureRandomized"
    short_name = SHORT_NAME
    """The short name of this Qurrium class."""
    acronym = ACRONYM
    """The abbreviation of this Qurrium class."""
    reserved_register_names: set[str] = {DEFAULT_CLASSICAL_REGISTER_NAME}
    """The reserved classical register names used in this Qurrium class."""

    @property
    def experiment_instance(self) -> type[EMRExperiment]:
        """The container class responding to this QurryV5 class."""
        return EMRExperiment

    def measure_to_output(
        self,
        wave: QuantumCircuit | WCKeyable | None = None,
        times: int = 100,
        measure: QubitSelectionType = None,
        unitary_loc: QubitSelectionType = None,
        unitary_loc_not_cover_measure: bool = False,
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
    ) -> EMROutputArgs:
        """Trasnform :meth:`measure` arguments form into :meth:`output` form.

        Args:
            wave (QuantumCircuit | WCKeyable | None):
                The key or the circuit to execute.
            times (int, optional):
                The number of random unitary operator.
                It will denote as :math:`N_U` in the experiment name.
                Defaults to `100`.
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
                Whether the range of the unitary operator is not cover the measure range.
                Defaults to `False`.
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
                Arguments of :func:`~qiskit.compiler.transpile`
                Defaults to None.
            passmanager (str | PassManager | tuple[str, PassManager] | None, optional):
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
            The arguments for :meth:`output`.
        """
        if wave is None:
            raise ValueError("The `wave` must be provided.")

        return {
            "circuits": [wave],
            "times": times,
            "measure": measure,
            "unitary_loc": unitary_loc,
            "unitary_loc_not_cover_measure": unitary_loc_not_cover_measure,
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
        }

    def prepare(
        self,
        wave: QuantumCircuit | WCKeyable | None = None,
        times: int = 100,
        measure: QubitSelectionType = None,
        unitary_loc: QubitSelectionType = None,
        unitary_loc_not_cover_measure: bool = False,
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
    ):
        """Prepare the experiment without executing it.

        Args:
            wave (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            times (int, optional):
                The number of random unitary operator.
                It will denote as :math:`N_U` in the experiment name.
                Defaults to `100`.
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
                Whether the range of the unitary operator is not cover the measure range.
                Defaults to `False`.
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
            passmanager (str | PassManager | tuple[str, PassManager] | None, optional):
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
                wave=wave,
                times=times,
                measure=measure,
                unitary_loc=unitary_loc,
                unitary_loc_not_cover_measure=unitary_loc_not_cover_measure,
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
        wave: QuantumCircuit | WCKeyable | None = None,
        times: int = 100,
        measure: QubitSelectionType = None,
        unitary_loc: QubitSelectionType = None,
        unitary_loc_not_cover_measure: bool = False,
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
    ):
        """Execute the experiment immediately.

        Args:
            wave (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            times (int, optional):
                The number of random unitary operator.
                It will denote as :math:`N_U` in the experiment name.
                Defaults to `100`.
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
                Whether the range of the unitary operator is not cover the measure range.
                Defaults to `False`.
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
            passmanager (str | PassManager | tuple[str, PassManager] | None, optional):
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
                wave=wave,
                times=times,
                measure=measure,
                unitary_loc=unitary_loc,
                unitary_loc_not_cover_measure=unitary_loc_not_cover_measure,
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
        specific_analysis_args: SpecificAnalyzeArgs[EMRAnalyzeArgs] = None,
        skip_write: bool = False,
        multiprocess_write: bool = False,
        # analysis arguments
        selected_qubits: list[int] | None = None,
        independent_all_system: bool = False,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        counts_used: Iterable[int] | None = None,
        **analysis_args,
    ) -> tuple[str, str]:
        """Run the analysis for multiple experiments.

        Args:
            summoner_id (str): The summoner_id of multimanager.
            analysis_name (str, optional):
                The name of analysis. Defaults to 'report'.
            no_serialize (bool, optional):
                Whether to serialize the analysis. Defaults to False.
            specific_analysis_args (SpecificAnalyzeArgs[EMRAnalyzeArgs] | None, optional):
                The specific arguments for analysis. Defaults to None.
            skip_write (bool, optional):
                Whether to skip the file writing during the analysis. Defaults to False.
            multiprocess_write (bool, optional):
                Whether use multiprocess for writing. Defaults to False.

            selected_qubits (list[int] | None, optional):
                The selected qubits. Defaults to None.
            independent_all_system (bool, optional):
                Whether to treat all system as independent. Defaults to False.
            backend (PostProcessingBackendLabel, optional):
                The backend for the postprocessing. Defaults to DEFAULT_PROCESS_BACKEND.
            counts_used (Iterable[int] | None, optional):
                The counts used for the analysis. Defaults to None.

        Returns:
            tuple[str, EMRExperiment]: The experiment instance.
        """

        return super().multiAnalysis(
            summoner_id=summoner_id,
            analysis_name=analysis_name,
            no_serialize=no_serialize,
            specific_analysis_args=specific_analysis_args,
            skip_write=skip_write,
            multiprocess_write=multiprocess_write,
            selected_qubits=selected_qubits,
            independent_all_system=independent_all_system,
            backend=backend,
            counts_used=counts_used,
            **analysis_args,
        )
