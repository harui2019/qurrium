"""StringOperator - Qurrium (:mod:`qurry.qurries.string_operator.qurry`)"""

from typing import Literal
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend

from .utils import StringOperatorLibType, StringOperatorDirection, DEFAULT_CLASSICAL_REGISTER_NAME
from .arguments import SHORT_NAME, ACRONYM, SOMeasureArgs, SOOutputArgs
from .analysis import SOAnalyzeArgs
from .experiment import SOExperiment
from ...qurrium import QurriumPrototype, RunArgsType, TranspileArgs, PassManagerType, WCKeyable


class StringOperator(QurriumPrototype[SOExperiment, SOMeasureArgs, SOOutputArgs, SOAnalyzeArgs]):
    """String Operator Order

    Reference:
        -   Crossing a topological phase transition with a quantum computer -
            Smith, Adam and Jobst, Bernhard and Green, Andrew G. and Pollmann, Frank,
            `PhysRevResearch.4.L022020
            <https://link.aps.org/doi/10.1103/PhysRevResearch.4.L022020>`_

        .. code-block:: bibtex

            @article{PhysRevResearch.4.L022020,
                title = {Crossing a topological phase transition with a quantum computer},
                author = {
                    Smith, Adam and Jobst, Bernhard and Green, Andrew G. and Pollmann, Frank
                },
                journal = {Phys. Rev. Research},
                volume = {4},
                issue = {2},
                pages = {L022020},
                numpages = {8},
                year = {2022},
                month = {Apr},
                publisher = {American Physical Society},
                doi = {10.1103/PhysRevResearch.4.L022020},
                url = {https://link.aps.org/doi/10.1103/PhysRevResearch.4.L022020}
            }

    """

    __name__ = "StringOperator"
    short_name = SHORT_NAME
    """The short name of this Qurrium class."""
    acronym = ACRONYM
    """The abbreviation of this Qurrium class."""
    reserved_register_names = {DEFAULT_CLASSICAL_REGISTER_NAME}
    """The reserved classical register names used in this Qurrium class."""

    @property
    def experiment_instance(self) -> type[SOExperiment]:
        """The container class responding to this Qurrium class."""
        return SOExperiment

    def measure_to_output(
        self,
        wave: QuantumCircuit | WCKeyable | None = None,
        i: int | None = None,
        k: int | None = None,
        str_op: StringOperatorLibType = "i",
        on_dir: StringOperatorDirection = "x",
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
    ) -> SOOutputArgs:
        """Trasnform :meth:`measure` arguments form into :meth:`output` form.

        Args:
            wave (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            i (int | None, optional):
                The index of beginning qubits in the quantum circuit.
            k (int | None, optional):
                The index of ending qubits in the quantum circuit.
            str_op (StringOperatorLibType, optional):
                The string operator. Defaults to "i".
            on_dir (StringOperatorDirection, optional):
                The direction of the string operator, either 'x' or 'y'. Defaults to "x".
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
        if wave is None:
            raise ValueError("The `wave` must be provided.")

        return {
            "circuits": [wave],
            "i": i,
            "k": k,
            "str_op": str_op,
            "on_dir": on_dir,
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
        i: int | None = None,
        k: int | None = None,
        str_op: StringOperatorLibType = "i",
        on_dir: StringOperatorDirection = "x",
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
            wave (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            i (int | None, optional):
                The index of beginning qubits in the quantum circuit.
            k (int | None, optional):
                The index of ending qubits in the quantum circuit.
            str_op (StringOperatorLibType, optional):
                The string operator. Defaults to "i".
            on_dir (StringOperatorDirection, optional):
                The direction of the string operator, either 'x' or 'y'. Defaults to "x".
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
            The experiment instance.
        """

        exp_id = self.build(
            **self.measure_to_output(
                wave=wave,
                i=i,
                k=k,
                str_op=str_op,
                on_dir=on_dir,
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
        i: int | None = None,
        k: int | None = None,
        str_op: StringOperatorLibType = "i",
        on_dir: StringOperatorDirection = "x",
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
            wave (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            i (int | None, optional):
                The index of beginning qubits in the quantum circuit.
            k (int | None, optional):
                The index of ending qubits in the quantum circuit.
            str_op (StringOperatorLibType, optional):
                The string operator. Defaults to "i".
            on_dir (StringOperatorDirection, optional):
                The direction of the string operator, either 'x' or 'y'. Defaults to "x".
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
            The experiment instance.
        """

        exp_id = self.output(
            **self.measure_to_output(
                wave=wave,
                i=i,
                k=k,
                str_op=str_op,
                on_dir=on_dir,
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
