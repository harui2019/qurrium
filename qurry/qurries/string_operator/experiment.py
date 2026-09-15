"""StringOperator - Experiment (:mod:`qurry.qurries.string_operator.experiment`)"""

from typing import Any

from qiskit import QuantumCircuit

from .arguments import SOArguments, SHORT_NAME
from .analysis import SOAnalysis
from .utils import circuit_method, StringOperatorLibType, StringOperatorDirection, STRING_OPERATOR
from ...qurrium import ExperimentPrototype, Commonparams, WCKeyable


class SOExperiment(ExperimentPrototype[SOArguments, SOAnalysis]):
    """The instance of experiment."""

    __name__ = "SOExperiment"

    @classmethod
    def arguments_type(cls) -> type[SOArguments]:
        """The arguments instance for this experiment."""
        return SOArguments

    @classmethod
    def analysis_type(cls) -> type[SOAnalysis]:
        """The analysis instance for this experiment."""
        return SOAnalysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        exp_name: str = "exps",
        i: int | None = None,
        k: int | None = None,
        str_op: StringOperatorLibType = "i",
        on_dir: StringOperatorDirection = "x",
        **custom_kwargs: Any,
    ) -> tuple[SOArguments, Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            i (int | None, optional):
                The index of beginning qubits in the quantum circuit.
            k (int | None, optional):
                The index of ending qubits in the quantum circuit.
            str_op (StringOperatorLibType, optional):
                The string operator. Defaults to "i".
            on_dir (StringOperatorDirection, optional):
                The direction of the string operator, either 'x' or 'y'. Defaults to "x".
            custom_kwargs (Any):
                The custom parameters.

        Returns:
            tuple[StringOperatorArguments, Commonparams, dict[str, Any]]:
                The arguments of the experiment, the common parameters, and the custom parameters.
        """
        if len(targets) > 1:
            raise ValueError("The number of target circuits should be only one.")
        target_key, target_circuit = targets[0]
        num_qubits = target_circuit.num_qubits

        if on_dir not in STRING_OPERATOR:
            raise ValueError("The `on_dir` must be either 'x' or 'y'.")
        if str_op not in STRING_OPERATOR[on_dir]:
            raise ValueError(f"The `str_op` must be one of {list(STRING_OPERATOR[on_dir])}.")

        if k is None:
            k = num_qubits - 1
        if i is None:
            i = 0
        if i >= k:
            raise ValueError(f"i: {i} is not less than k: {k}.")

        if k - i + 1 < len(STRING_OPERATOR[on_dir][str_op]):
            raise ValueError(
                f"The `k - i + 1` must be greater than or equal to "
                f"{len(STRING_OPERATOR[on_dir][str_op])}. But got k: {k} - i: {i} = {k - i + 1}."
            )

        return SOArguments.filter(
            exp_name=f"{exp_name}.i_{i}_k_{k}.op_{str_op}_dir_{on_dir}.{SHORT_NAME}",
            target_keys=[target_key],
            num_qubits=num_qubits,
            str_op=str_op,
            i=i,
            k=k,
            **custom_kwargs,
        )

    @classmethod
    def method(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        arguments: SOArguments,
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (StringOperatorArguments):
                The arguments of the experiment.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the side products.
        """
        target_key, target_circuit = targets[0]
        target_key = target_key if isinstance(target_key, int) else str(target_key)
        assert arguments.i is not None and arguments.k is not None, (
            f"i and k should be given, but got {arguments.i} and {arguments.k}. "
            "Please check the arguments."
        )

        return [
            circuit_method(
                target_circuit,
                target_key,
                arguments.exp_name,
                arguments.i,
                arguments.k,
                arguments.str_op,
                arguments.on_dir,
            )
        ], {}

    def analyze(self) -> SOAnalysis:
        """Calculate magnet square with more information combined.

        Returns:
            SOAnalysis: The result of the analysis.
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
