"""SamplingExecuter - Experiment (:mod:`qurry.qurries.samplingqurry.experiment`)"""

from typing import Any
import warnings

from qiskit import QuantumCircuit

from .arguments import SEArguments, SHORT_NAME
from .analysis import DummyAnalysis
from ...qurrium.exceptions import DummyClassWarning
from ...qurrium import ExperimentPrototype, Commonparams, WCKeyable


class SEExperiment(ExperimentPrototype[SEArguments, DummyAnalysis[SEArguments]]):
    """Experiment instance for QurryV14."""

    __name__ = "SEExperiment"

    @classmethod
    def arguments_type(cls) -> type[SEArguments]:
        """The arguments instance for this experiment."""
        return SEArguments

    @classmethod
    def analysis_type(cls) -> type[DummyAnalysis[SEArguments]]:
        """The analysis instance for this experiment."""
        return DummyAnalysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        exp_name: str = "exps",
        sampling: int = 1,
        **custom_kwargs: Any,
    ) -> tuple[SEArguments, Commonparams, dict[str, Any]]:
        """Control the experiment's parameters.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str):
                The name of the experiment. Defaults to "exps".
            sampling (int, optional):
                The number of sampling. Defaults to 1.
            custom_kwargs (Any):
                The custom parameters.

        Raises:
            ValueError: The number of target circuits should be only one.

        Returns:
            tuple[QurryArguments, Commonparams, dict[str, Any]]:
                The arguments of the experiment, the common parameters, and the custom parameters
        """
        if len(targets) != 1:
            raise ValueError("The number of target circuits should be only one.")

        return SEArguments.filter(
            exp_name=f"{exp_name}.times_{sampling}.{SHORT_NAME}",
            target_keys=[targets[0][0]],
            sampling=sampling,
            **custom_kwargs,
        )

    @classmethod
    def method(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        arguments: SEArguments,
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (SEArguments):
                The arguments of the experiment.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the side products.
        """

        the_chosen_key, q = targets[0]
        the_chosen_key = "" if isinstance(the_chosen_key, int) else str(the_chosen_key)
        old_name = "" if isinstance(q.name, str) else q.name
        old_name = "" if len(old_name) < 1 else old_name
        q_copy = q.copy()
        if len(q_copy.cregs) < 1:
            raise ValueError(
                "| No classical register in the given circuits, counts will be empty. "
                + "Please add classical register to the circuit. "
                + "(Don't be frustrated, I did the same thing on unit test. "
                + "It made me confused and thought what's wrong for a while before ('_').)"
            )
        q_copy.name = ".".join(
            [n for n in [arguments.exp_name, the_chosen_key, old_name] if len(n) > 0]
        )

        return [q_copy.copy() for _ in range(arguments.sampling)], {}

    def analyze(self, ultimate_question: str | None = None) -> DummyAnalysis[SEArguments]:
        """Analysis of the experiment.

        Args:
            ultimate_question (str | None, optional):
                The ultimate question of the universe.

        Returns:
            DummyAnalysis[SEArguments]: The result of the analysis.
        """

        serial = len(self.reports)
        if serial != 0:
            warnings.warn(
                "You already have the answer. "
                + "The Answer to the Ultimate Question of Life, "
                + "The Universe, and Everything.",
                DummyClassWarning,
            )
            return self.reports[0]

        analysis = self.analysis_type().perform_analysis(
            arguments=self.args,
            commonparams=self.commons,
            counts=self.afterwards.counts,
            analyze_arguments={"ultimate_question": ultimate_question},
            serial=serial,
        )
        self.reports[analysis.serial] = analysis
        return analysis
