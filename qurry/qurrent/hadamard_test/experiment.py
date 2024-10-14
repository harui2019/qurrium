"""
================================================================
EntropyMeasureHadamard - Experiment
(:mod:`qurry.qurrent.hadamard_test.experiment`)
================================================================

"""

from typing import Optional, Type, Any
from collections.abc import Hashable
import tqdm

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from .analysis import EntropyMeasureHadamardAnalysis
from .arguments import EntropyMeasureHadamardArguments, SHORT_NAME
from ...qurrium.experiment import ExperimentPrototype, Commonparams
from ...process.utils import qubit_selector
from ...process.hadamard_test import hadamard_entangled_entropy


class EntropyMeasureHadamardExperiment(ExperimentPrototype):
    """The instance of experiment."""

    __name__ = "EntropyMeasureHadamardExperiment"

    @property
    def arguments_instance(self) -> Type[EntropyMeasureHadamardArguments]:
        """The arguments instance for this experiment."""
        return EntropyMeasureHadamardArguments

    args: EntropyMeasureHadamardArguments

    @property
    def analysis_instance(self) -> Type[EntropyMeasureHadamardAnalysis]:
        """The analysis instance for this experiment."""
        return EntropyMeasureHadamardAnalysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        exp_name: str = "exps",
        degree: Optional[tuple[int, int]] = None,
        **custom_kwargs: Any,
    ) -> tuple[EntropyMeasureHadamardArguments, Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            degree (Optional[tuple[int, int]], optional):
                The degree range.
                Defaults to None.
            custom_kwargs (Any):
                The custom parameters.

        Raises:
            ValueError: The number of target circuits should be 1.

        Returns:
            tuple[EntropyMeasureHadamardArguments, Commonparams, dict[str, Any]]:
                The arguments of the experiment, the common parameters, and the custom parameters.
        """
        if len(targets) != 1:
            raise ValueError("The number of target circuits should be 1.")

        target_key, target_circuit = targets[0]
        num_qubits = target_circuit.num_qubits
        degree = qubit_selector(num_qubits, degree=degree)

        exp_name = f"{exp_name}.degree_{degree[0]}_{degree[1]}.{SHORT_NAME}"

        # pylint: disable=protected-access
        return EntropyMeasureHadamardArguments._filter(
            exp_name=exp_name,
            target_keys=[target_key],
            degree=degree,
            **custom_kwargs,
        )
        # pylint: enable=protected-access

    @classmethod
    def method(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        arguments: EntropyMeasureHadamardArguments,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (EntropyMeasureHadamardArguments):
                The arguments of the experiment.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar. Defaults to None.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the arguments of the experiment.
        """

        assert isinstance(
            arguments.degree, tuple
        ), f"The degree should be a tuple, got {arguments.degree}."

        target_key, target_circuit = targets[0]
        target_key = "" if isinstance(target_key, int) else str(target_key)
        num_qubits = target_circuit.num_qubits
        old_name = "" if isinstance(target_circuit.name, str) else target_circuit.name

        q_ancilla = QuantumRegister(1, "ancilla_1")
        q_func1 = QuantumRegister(num_qubits, "q1")
        q_func2 = QuantumRegister(num_qubits, "q2")
        c_meas1 = ClassicalRegister(1, "c1")
        qc_exp1 = QuantumCircuit(q_ancilla, q_func1, q_func2, c_meas1)
        qc_exp1.name = (
            f"{arguments.exp_name}" + ""
            if len(target_key) < 1
            else f".{target_key}" + "" if len(old_name) < 1 else f".{old_name}"
        )

        qc_exp1.compose(
            target_circuit,
            [q_func1[i] for i in range(num_qubits)],
            inplace=True,
        )

        qc_exp1.compose(
            target_circuit,
            [q_func2[i] for i in range(num_qubits)],
            inplace=True,
        )

        qc_exp1.barrier()
        qc_exp1.h(q_ancilla)
        for i in range(*arguments.degree):
            qc_exp1.cswap(q_ancilla[0], q_func1[i], q_func2[i])
        qc_exp1.h(q_ancilla)
        qc_exp1.measure(q_ancilla, c_meas1)

        return [qc_exp1], {}

    def analyze(
        self,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> EntropyMeasureHadamardAnalysis:
        """Calculate entangled entropy with more information combined.

        Args:
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar. Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy.
        """

        if pbar is not None:
            pbar.set_description("Calculating entangled entropy")

        shots = self.commons.shots
        counts = self.afterwards.counts

        qs = self.quantities(
            shots=shots,
            counts=counts,
        )

        serial = len(self.reports)
        analysis = self.analysis_instance(
            serial=serial,
            shots=shots,
            **qs,  # type: ignore
        )

        self.reports[serial] = analysis
        return analysis

    @classmethod
    def quantities(
        cls,
        shots: Optional[int] = None,
        counts: Optional[list[dict[str, int]]] = None,
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy.
        """

        if shots is None or counts is None:
            raise ValueError("shots and counts should be specified.")

        return hadamard_entangled_entropy(
            shots=shots,
            counts=counts,
        )
