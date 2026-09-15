"""MagnetSquare - Experiment (:mod:`qurry.qurries.magnet_square.experiment`)"""

from typing import Any, Literal
from itertools import permutations

from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.quantum_info import Operator

from .arguments import MSArguments, SHORT_NAME
from .analysis import MSAnalysis
from .utils import circuit_method
from ...qurrium import ExperimentPrototype, Commonparams, WCKeyable


class MSExperiment(ExperimentPrototype[MSArguments, MSAnalysis]):
    """The instance of experiment."""

    __name__ = "MSExperiment"

    @classmethod
    def arguments_type(cls) -> type[MSArguments]:
        """The arguments instance for this experiment."""
        return MSArguments

    @classmethod
    def analysis_type(cls) -> type[MSAnalysis]:
        """The analysis instance for this experiment."""
        return MSAnalysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        exp_name: str = "exps",
        unitary_operator: Operator | Gate | Literal["x", "y", "z"] = "z",
        **custom_kwargs: Any,
    ) -> tuple[MSArguments, Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            unitary_operator (Operator | Gate | Literal["x", "y", "z"], optional):
                The unitary operator to apply.
                It can be a `qiskit.quantum_info.Operator`, a `qiskit.circuit.Gate`, or a string
                representing the axis of rotation ('x', 'y', or 'z').
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            custom_kwargs (Any):
                The custom parameters.

        Returns:
            tuple[MSArguments, Commonparams, dict[str, Any]]:
                The arguments of the experiment, the common parameters, and the custom parameters.
        """
        if len(targets) > 1:
            raise ValueError("The number of target circuits should be only one.")

        target_key, target_circuit = targets[0]
        actual_qubits = target_circuit.num_qubits

        return MSArguments.filter(
            exp_name=f"{exp_name}.{SHORT_NAME}",
            target_keys=[target_key],
            unitary_operator=unitary_operator,
            num_qubits=actual_qubits,
            **custom_kwargs,
        )

    @classmethod
    def method(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        arguments: MSArguments,
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (MSArguments):
                The arguments of the experiment.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the side products.
        """

        permut = permutations(range(arguments.num_qubits), 2)
        target_key, target_circuit = targets[0]
        target_key = target_key if isinstance(target_key, int) else str(target_key)

        return [
            circuit_method(
                idx,
                target_circuit,
                target_key,
                arguments.exp_name,
                arguments.unitary_operator,
                i,
                j,
            )
            for idx, (i, j) in enumerate(permut)
        ], {}

    def analyze(self) -> MSAnalysis:
        """Calculate magnet square with more information combined.

        Returns:
            MSAnalysis: The analysis instance.
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
