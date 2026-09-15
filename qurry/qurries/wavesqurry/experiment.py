"""WavesExecuter - Experiment (:mod:`qurry.qurries.wavesqurry.experiment`)"""

from typing import Any
import warnings

from qiskit import QuantumCircuit

from .arguments import WEArguments, SHORT_NAME
from ..samplingqurry.analysis import DummyAnalysis
from ...qurrium import ExperimentPrototype, Commonparams, WCKeyable
from ...qurrium.exceptions import DummyClassWarning, NoExperimentCountsAvailable


class WEExperiment(ExperimentPrototype[WEArguments, DummyAnalysis[WEArguments]]):
    """The instance of experiment."""

    __name__ = "WEExperiment"

    @classmethod
    def arguments_type(cls) -> type[WEArguments]:
        """The arguments instance for this experiment."""
        return WEArguments

    @classmethod
    def analysis_type(cls) -> type[DummyAnalysis[WEArguments]]:
        """The analysis instance for this experiment."""
        return DummyAnalysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        exp_name: str = "exps",
        **custom_kwargs: Any,
    ) -> tuple[WEArguments, Commonparams, dict[str, Any]]:
        """Control the experiment's parameters.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            custom_kwargs (Any):
                The custom parameters.

        Returns:
            tuple[WavesExecuterArguments, Commonparams, dict[str, Any]]:
                The arguments of the experiment, the common parameters, and the custom parameters.
        """

        return WEArguments.filter(
            exp_name=f"{exp_name}.{SHORT_NAME}",
            target_keys=[k for k, _ in targets],
            **custom_kwargs,
        )

    @classmethod
    def method(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        arguments: WEArguments,
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (WEArguments):
                The arguments of the experiment.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the side products.
        """
        cirqs = []
        no_cregs = []
        for i, (k, q) in enumerate(targets):
            q_copy = q.copy()
            if len(q_copy.cregs) < 1:
                no_cregs.append(i)
            chosen_key = "" if isinstance(k, int) else str(k)
            old_name = "" if isinstance(q.name, str) else q.name
            old_name = "" if len(old_name) < 1 else old_name
            q_copy.name = ".".join(
                [n for n in [f"{arguments.exp_name}_{i}", chosen_key, old_name] if len(n) > 0]
            )
            cirqs.append(q_copy)
        if len(no_cregs) == len(targets):
            raise NoExperimentCountsAvailable(
                "| No classical register in ALL circuits, counts will be empty. "
                + "Please add classical register to the circuit. "
                + "(Don't be frustrated, I did the same thing on unit test. "
                + "It made me confused and thought what's wrong for a while before ('_').)"
            )
        if len(no_cregs) > 0:
            raise NoExperimentCountsAvailable(
                "| No classical register in the following circuits, counts will be empty. "
                + "Please add classical register to the circuit. "
                + f"The index of circuit without classical register: {no_cregs}"
            )

        return cirqs, {}

    def analyze(self, ultimate_question: str | None = None) -> DummyAnalysis[WEArguments]:
        """Analysis of the experiment.

        Args:
            ultimate_question (str | None, optional):
                The ultimate question of the universe.

        Returns:
            DummyAnalysis[WEArguments]: The result of the analysis.
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
