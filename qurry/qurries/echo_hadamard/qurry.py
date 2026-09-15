"""EchoListenHadamard - Qurrium (:mod:`qurry.qurries.echo_hadamard.qurry`)"""

from typing import Literal
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend

from .arguments import SHORT_NAME, ACRONYM, ELHMeasureArgs, ELHOutputArgs
from .analysis import ELHAnalyzeArgs
from .experiment import ELHxperiment
from ...qurrium import QurriumPrototype, RunArgsType, TranspileArgs, PassManagerType, WCKeyable


class EchoListenHadamard(
    QurriumPrototype[ELHxperiment, ELHMeasureArgs, ELHOutputArgs, ELHAnalyzeArgs]
):
    """The experiment for calculating entangled entropy with more information combined."""

    __name__ = "EchoListenHadamard"
    short_name = SHORT_NAME
    """The short name of this Qurrium class."""
    acronym = ACRONYM
    """The abbreviation of this Qurrium class."""

    @property
    def experiment_instance(self) -> type[ELHxperiment]:
        """The experiment instance for this experiment."""
        return ELHxperiment

    def measure_to_output(
        self,
        wave1: QuantumCircuit | WCKeyable | None = None,
        wave2: QuantumCircuit | WCKeyable | None = None,
        degree: int | tuple[int, int] | None = None,
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
    ) -> ELHOutputArgs:
        """Trasnform :meth:`measure` arguments form into :meth:`output` form.

        Args:
            wave1 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            wave2 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            degree (int | tuple[int, int] | None, optional):
                The degree of the experiment. Defaults to None.
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
                Arguments of :func:`~qiskit.compiler.transpile`. Defaults to None.
            passmanager (PassManagerType, optional):
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
                The progress bar for showing the progress of the experiment. Defaults to None.

        Returns:
            The output arguments.
        """
        if wave1 is None:
            raise ValueError("The `wave` must be provided.")
        if wave2 is None:
            raise ValueError("The `wave2` must be provided.")

        return {
            "circuits": [wave1, wave2],
            "degree": degree,
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
        wave1: QuantumCircuit | WCKeyable | None = None,
        wave2: QuantumCircuit | WCKeyable | None = None,
        degree: int | tuple[int, int] | None = None,
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
            wave1 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            wave2 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            degree (int | tuple[int, int] | None, optional):
                The degree of the experiment. Defaults to None.
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
                Arguments of :func:`~qiskit.compiler.transpile`. Defaults to None.
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
                The progress bar for showing the progress of the experiment. Defaults to None.

        Returns:
            The experiment instance.
        """

        exp_id = self.build(
            **self.measure_to_output(
                wave1=wave1,
                wave2=wave2,
                degree=degree,
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
        degree: int | tuple[int, int] | None = None,
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
            wave1 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            wave2 (QuantumCircuit | WCKeyable):
                The key or the circuit to execute.
            degree (int | tuple[int, int] | None, optional):
                The degree of the experiment. Defaults to None.
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
                Arguments of :func:`~qiskit.compiler.transpile`. Defaults to None.
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
                The progress bar for showing the progress of the experiment. Defaults to None.

        Returns:
            The experiment instance.
        """

        exp_id = self.output(
            **self.measure_to_output(
                wave1=wave1,
                wave2=wave2,
                degree=degree,
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
