"""
================================================================
Waves Qurry (:mod:`qurry.qurrium.wavesqurry`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from typing import Union, Optional, Any, Type
from collections.abc import Hashable
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend
from qiskit.transpiler.passmanager import PassManager

from .experiment import WavesQurryExperiment
from ..qurrium import QurriumPrototype
from ..container import ExperimentContainer
from ...declare import BaseRunArgs, TranspileArgs, BasicOutputArgs


class WaveQurryOutputArgs(BasicOutputArgs):
    """Output arguments for :meth:`output`."""


class WavesExecuter(QurriumPrototype):
    """The pending and retrieve executer for waves."""

    __name__ = "WavesExecuter"

    @property
    def experiment_instance(self) -> Type[WavesQurryExperiment]:
        """The container class responding to this QurryV5 class."""
        return WavesQurryExperiment

    exps: ExperimentContainer[WavesQurryExperiment]

    def measure_to_output(
        self,
        waves: Optional[list[Union[QuantumCircuit, Hashable]]] = None,
        shots: int = 1024,
        backend: Optional[Backend] = None,
        exp_name: str = "experiment",
        run_args: Optional[Union[BaseRunArgs, dict[str, Any]]] = None,
        transpile_args: Optional[TranspileArgs] = None,
        passmanager: Optional[Union[str, PassManager, tuple[str, PassManager]]] = None,
        # process tool
        export: bool = False,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonable: bool = False,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> WaveQurryOutputArgs:
        """Trasnform :meth:`measure` arguments form into :meth:`output` form.

        Args:
            waves (list[Union[QuantumCircuit, Hashable]]):
                The circuits to execute.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Optional[Backend], optional):
                The quantum backend. Defaults to None.
            exp_name (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            run_args (Optional[Union[BaseRunArgs, dict[str, Any]]], optional):
                defaultConfig of :func:`qiskit.execute`. Defaults to `{}`.
            transpile_args (Optional[TranspileArgs], optional):
                defaultConfig of :func:`qiskit.transpile`. Defaults to `{}`.
            passmanager (Optional[Union[str, PassManager, tuple[str, PassManager]], optional):
                The passmanager. Defaults to None.

            exp_id (Optional[str], optional):
                The ID of experiment. Defaults to None.
            new_backend (Optional[Backend], optional):
                The new backend. Defaults to None.
            revive (bool, optional):
                Whether to revive the circuit. Defaults to False.
            replace_circuits (bool, optional):
                Whether to replace the circuits during revive. Defaults to False.

            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Optional[Union[Path, str]], optional):
                The location to save the experiment. Defaults to None.
            mode (str, optional):
                The mode to open the file. Defaults to 'w+'.
            indent (int, optional):
                The indent of json file. Defaults to 2.
            encoding (str, optional):
                The encoding of json file. Defaults to 'utf-8'.
            jsonable (bool, optional):
                Whether to jsonablize the experiment output. Defaults to False.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            str: The experiment ID.
        """
        if waves is None:
            raise ValueError("The `waves` must be provided.")

        return {
            "circuits": waves,
            "shots": shots,
            "backend": backend,
            "exp_name": exp_name,
            "run_args": run_args,
            "transpile_args": transpile_args,
            "passmanager": passmanager,
            "export": export,
            "save_location": save_location,
            "mode": mode,
            "indent": indent,
            "encoding": encoding,
            "jsonable": jsonable,
            "pbar": pbar,
        }

    def measure(
        self,
        waves: Optional[list[Union[QuantumCircuit, Hashable]]] = None,
        shots: int = 1024,
        backend: Optional[Backend] = None,
        exp_name: str = "experiment",
        run_args: Optional[Union[BaseRunArgs, dict[str, Any]]] = None,
        transpile_args: Optional[TranspileArgs] = None,
        passmanager: Optional[Union[str, PassManager, tuple[str, PassManager]]] = None,
        # process tool
        export: bool = False,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonable: bool = False,
        pbar: Optional[tqdm.tqdm] = None,
    ):
        """Execute the experiment.

        Args:
            waves (list[Union[QuantumCircuit, Hashable]]):
                The circuits to execute.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Optional[Backend], optional):
                The quantum backend. Defaults to None.
            exp_name (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            run_args (Optional[Union[BaseRunArgs, dict[str, Any]]], optional):
                defaultConfig of :func:`qiskit.execute`. Defaults to `{}`.
            transpile_args (Optional[TranspileArgs], optional):
                defaultConfig of :func:`qiskit.transpile`. Defaults to `{}`.
            passmanager (Optional[Union[str, PassManager, tuple[str, PassManager]], optional):
                The passmanager. Defaults to None.

            exp_id (Optional[str], optional):
                The ID of experiment. Defaults to None.
            new_backend (Optional[Backend], optional):
                The new backend. Defaults to None.
            revive (bool, optional):
                Whether to revive the circuit. Defaults to False.
            replace_circuits (bool, optional):
                Whether to replace the circuits during revive. Defaults to False.

            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Optional[Union[Path, str]], optional):
                The location to save the experiment. Defaults to None.
            mode (str, optional):
                The mode to open the file. Defaults to 'w+'.
            indent (int, optional):
                The indent of json file. Defaults to 2.
            encoding (str, optional):
                The encoding of json file. Defaults to 'utf-8'.
            jsonable (bool, optional):
                Whether to jsonablize the experiment output. Defaults to False.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            str: The experiment ID.
        """

        output_args = self.measure_to_output(
            waves=waves,
            shots=shots,
            backend=backend,
            exp_name=exp_name,
            run_args=run_args,
            transpile_args=transpile_args,
            passmanager=passmanager,
            export=export,
            save_location=save_location,
            mode=mode,
            indent=indent,
            encoding=encoding,
            jsonable=jsonable,
            pbar=pbar,
        )

        result_exp_id = self.output(**output_args)
        return result_exp_id
