"""EchoListenHadamard - Experiment (:mod:`qurry.qurries.echo_hadamard.experiment`)"""

from typing import Any

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from .analysis import ELHAnalysis
from .arguments import ELHArguments, SHORT_NAME
from ...qurrium import ExperimentPrototype, Commonparams, WCKeyable, naming_circuit
from ...process.utils import qubit_selector


DEFAULT_CLASSICAL_REGISTER_NAME = "m0"
"""The default name for classical register used for measurement."""


class ELHxperiment(ExperimentPrototype[ELHArguments, ELHAnalysis]):
    """The instance of experiment."""

    __name__ = "ELHxperiment"

    @classmethod
    def arguments_type(cls) -> type[ELHArguments]:
        """The arguments instance for this experiment."""
        return ELHArguments

    @classmethod
    def analysis_type(cls) -> type[ELHAnalysis]:
        """The analysis instance for this experiment."""
        return ELHAnalysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        exp_name: str = "exps",
        degree: tuple[int, int] | None = None,
        **custom_kwargs: Any,
    ) -> tuple[ELHArguments, Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            degree (tuple[int, int] | None, optional):
                The degree range. Defaults to None.
            custom_kwargs (Any):
                The custom parameters.

        Raises:
            ValueError: The number of target circuits should be 2.
            ValueError: If the number of qubits in two circuits is not the same.

        Returns:
            tuple[EntropyMeasureHadamardArguments, Commonparams, dict[str, Any]]:
                The arguments of the experiment, the common parameters, and the custom parameters.
        """
        if len(targets) != 2:
            raise ValueError("The number of target circuits should be 2.")

        target_key_01, target_circuit_01 = targets[0]
        num_qubits_01 = target_circuit_01.num_qubits
        target_key_02, target_circuit_02 = targets[1]
        num_qubits_02 = target_circuit_02.num_qubits

        if len(target_circuit_01.clbits) > 0 or len(target_circuit_02.clbits) > 0:
            raise ValueError(
                "The target circuits should not contain classical registers, but got "
                + f"{target_key_01} with {len(target_circuit_01.clbits)} classical bits and "
                + f"{target_key_02} with {len(target_circuit_02.clbits)} classical bits."
            )
        if num_qubits_01 != num_qubits_02:
            raise ValueError(
                "The number of qubits in two circuits should be the same, "
                + f"but got {target_key_01}: {num_qubits_01} and {target_key_02}: {num_qubits_02}."
            )

        degree = qubit_selector(num_qubits_01, degree=degree)

        return ELHArguments.filter(
            exp_name=f"{exp_name}.{SHORT_NAME}",
            target_keys=[target_key_01, target_key_02],
            degree=degree,
            **custom_kwargs,
        )

    @classmethod
    def method(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        arguments: ELHArguments,
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (ELHArguments):
                The arguments of the experiment.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the arguments of the experiment.
        """

        target_key_01, target_circuit_01 = targets[0]
        target_key_02, target_circuit_02 = targets[1]

        num_qubits_01 = target_circuit_01.num_qubits
        num_qubits_02 = target_circuit_02.num_qubits
        assert num_qubits_01 == num_qubits_02, (
            "The number of qubits in two circuits should be the same, "
            + f"but got {target_key_01}: {num_qubits_01} and {target_key_02}: {num_qubits_02}. "
            + "This should be checked in 'params_control' already."
        )

        naming_01 = naming_circuit(target_circuit_01, target_key_01, "")
        naming_02 = naming_circuit(target_circuit_02, target_key_02, "")

        q_ancilla = QuantumRegister(1, "ancilla_1")
        q_func1 = QuantumRegister(num_qubits_01, "q1")
        q_func2 = QuantumRegister(num_qubits_01, "q2")
        c_meas1 = ClassicalRegister(1, DEFAULT_CLASSICAL_REGISTER_NAME)
        qc_exp1 = QuantumCircuit(
            q_ancilla,
            q_func1,
            q_func2,
            c_meas1,
            name=f"{arguments.exp_name}." + "_".join([naming_01, naming_02]),
        )

        qc_exp1.compose(target_circuit_01, [q_func1[i] for i in range(num_qubits_01)], inplace=True)

        qc_exp1.compose(target_circuit_02, [q_func2[i] for i in range(num_qubits_01)], inplace=True)

        qc_exp1.barrier()
        qc_exp1.h(q_ancilla)
        for i in range(*arguments.degree):
            qc_exp1.cswap(q_ancilla[0], q_func1[i], q_func2[i])
        qc_exp1.h(q_ancilla)
        qc_exp1.measure(q_ancilla, c_meas1)

        return [qc_exp1], {}

    def analyze(self) -> ELHAnalysis:
        """Calculate the analysis of wave function overlap.

        Returns:
            ELHAnalysis: The result of the analysis.
        """

        analysis = self.analysis_type().perform_analysis(
            arguments=self.args,
            commonparams=self.commons,
            counts=self.afterwards.counts,
            analyze_arguments={},
            serial=len(self.reports),
        )

        self.reports[analysis.serial] = analysis
        return analysis
