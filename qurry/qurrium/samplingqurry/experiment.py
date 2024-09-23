"""
================================================================
SamplingExecuter - Experiment
(:mod:`qurry.qurrium.samplingqurry.experiment`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from typing import Union, Optional, Type, Any
from collections.abc import Hashable
import tqdm

from qiskit import QuantumCircuit

from .arguments import QurryArguments, SHORT_NAME
from .analysis import QurryAnalysis
from ..experiment import ExperimentPrototype, Commonparams
from ...exceptions import QurryExperimentCountsNotCompleted


class QurryExperiment(ExperimentPrototype):
    """Experiment instance for QurryV9."""

    __name__ = "QurryExperiment"

    @property
    def arguments_instance(self) -> Type[QurryArguments]:
        """The arguments instance for this experiment."""
        return QurryArguments

    args: QurryArguments

    @property
    def analysis_instance(self) -> Type[QurryAnalysis]:
        """The analysis instance for this experiment."""
        return QurryAnalysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        exp_name: str = "exps",
        sampling: int = 1,
        **custom_kwargs: Any,
    ) -> tuple[QurryArguments, Commonparams, dict[str, Any]]:
        """Control the experiment's parameters.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
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

        exp_name = f"{exp_name}.times_{sampling}.{SHORT_NAME}"

        # pylint: disable=protected-access
        return QurryArguments._filter(
            exp_name=exp_name,
            target_keys=[targets[0][0]],
            sampling=sampling,
            **custom_kwargs,
        )
        # pylint: enable=protected-access

    @classmethod
    def method(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        arguments: QurryArguments,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
                The circuits of the experiment.
            arugments (ArgumentsPrototype):
                The arguments of the experiment.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the side products.
        """

        if pbar is not None:
            pbar.set_description("| Loading circuits")

        the_chosen_key, q = targets[0]
        the_chosen_key = "" if isinstance(the_chosen_key, int) else str(the_chosen_key)
        old_name = "" if isinstance(q.name, str) else q.name
        old_name = "" if len(old_name) < 1 else old_name
        q_copy = q.copy()
        q_copy.name = ".".join(
            [n for n in [arguments.exp_name, the_chosen_key, old_name] if len(n) > 0]
        )

        return [q_copy.copy() for _ in range(arguments.sampling)], {}

    @classmethod
    def quantities(
        cls,
        shots: Optional[int] = None,
        counts: Optional[list[dict[str, int]]] = None,
    ) -> dict[str, Union[float, int]]:
        """Computing specific squantity.

        Args:
            shots (Optional[int], optional):
                The number of shots.
            counts (Optional[list[dict[str, int]]], optional):
                The counts of the experiment.

        Returns:
            dict[str, Union[float, int]]: Counts, purity, entropy of experiment.
        """

        if shots is None or counts is None:
            print(
                "| shots or counts is None, "
                + "but it doesn't matter with ultimate question over all."
            )
        dummy = -100
        return {
            "dummy": dummy,
            "utlmatic_answer": 42,
        }

    def analyze(
        self,
        ultimate_question: str = "",
        shots: Optional[int] = None,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> QurryAnalysis:
        """Analysis of the experiment.

        Args:
            ultimate_question (str, optional):
                The ultimate question of the universe.
            shots (Optional[int], optional):
                The number of shots.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            QurryAnalysis: The analysis of the experiment.
        """

        if pbar is not None:
            pbar.set_description("What is the ultimate question of the universe?")

        if shots is None:
            shots = self.commons.shots
        if len(self.afterwards.counts) < 1:
            raise QurryExperimentCountsNotCompleted(
                "The counts of the experiment is not completed. So there is no data to analyze."
            )

        qs = self.quantities(shots=shots, counts=self.afterwards.counts)

        serial = len(self.reports)
        analysis = self.analysis_instance(
            ultimate_question=ultimate_question,
            serial=serial,
            **qs,  # type: ignore
        )

        self.reports[serial] = analysis
        return analysis
