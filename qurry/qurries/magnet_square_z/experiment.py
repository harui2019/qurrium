"""ZDirMagnetSquare - Experiment (:mod:`qurry.qurries.magnet_square_z.experiment`)"""

from typing import Any

from qiskit import QuantumCircuit

from .arguments import ZMSArguments, SHORT_NAME
from .analysis import ZMSAnalysis
from .utils import circuit_method
from ...qurrium import ExperimentPrototype, Commonparams, WCKeyable


class ZMSExperiment(ExperimentPrototype[ZMSArguments, ZMSAnalysis]):
    """The instance of experiment."""

    __name__ = "ZMSExperiment"

    @classmethod
    def arguments_type(cls) -> type[ZMSArguments]:
        """The arguments instance for this experiment."""
        return ZMSArguments

    @classmethod
    def analysis_type(cls) -> type[ZMSAnalysis]:
        """The analysis instance for this experiment."""
        return ZMSAnalysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        exp_name: str = "exps",
        **custom_kwargs: Any,
    ) -> tuple[ZMSArguments, Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            custom_kwargs (Any):
                The custom parameters.

        Returns:
            tuple[ZMSArguments, Commonparams, dict[str, Any]]:
                The arguments of the experiment, the common parameters, and the custom parameters.
        """
        if len(targets) > 1:
            raise ValueError("The number of target circuits should be only one.")

        target_key, target_circuit = targets[0]
        actual_qubits = target_circuit.num_qubits

        return ZMSArguments.filter(
            exp_name=f"{exp_name}.{SHORT_NAME}",
            target_keys=[target_key],
            num_qubits=actual_qubits,
            **custom_kwargs,
        )

    @classmethod
    def method(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        arguments: ZMSArguments,
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (ZMSArguments):
                The arguments of the experiment.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the side products.
        """

        target_key, target_circuit = targets[0]
        target_key = target_key if isinstance(target_key, int) else str(target_key)
        return [circuit_method(target_circuit, target_key, arguments.exp_name)], {}

    def analyze(self) -> ZMSAnalysis:
        """Calculate magnet square with more information combined.

        Returns:
            ZMSAnalysis: The result of the magnet square analysis.
        """

        serial = len(self.reports)
        analysis = self.analysis_type().perform_analysis(
            arguments=self.args,
            commonparams=self.commons,
            counts=self.afterwards.counts,
            analyze_arguments={},
            serial=serial,
        )

        self.reports[analysis.serial] = analysis
        return analysis
