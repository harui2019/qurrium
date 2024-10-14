"""
================================================================
WavesExecuter - Experiment
(:mod:`qurry.qurrium.wavesqurry.experiment`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from typing import Union, Optional, Type, Any
from collections.abc import Hashable
import tqdm

from qiskit import QuantumCircuit

from .arguments import WavesExecuterArguments, SHORT_NAME
from .analysis import WavesExecuterAnalysis
from ..experiment import ExperimentPrototype, Commonparams
from ...exceptions import QurryExperimentCountsNotCompleted


class WavesExecuterExperiment(ExperimentPrototype):
    """The instance of experiment."""

    __name__ = "WavesExecuterExperiment"

    @property
    def arguments_instance(self) -> Type[WavesExecuterArguments]:
        """The arguments instance for this experiment."""
        return WavesExecuterArguments

    args: WavesExecuterArguments

    @property
    def analysis_instance(self) -> Type[WavesExecuterAnalysis]:
        """The analysis instance for this experiment."""
        return WavesExecuterAnalysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        exp_name: str = "exps",
        **custom_kwargs: Any,
    ) -> tuple[WavesExecuterArguments, Commonparams, dict[str, Any]]:
        """Control the experiment's parameters.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
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
        exp_name = f"{exp_name}.{SHORT_NAME}"

        # pylint: disable=protected-access
        return WavesExecuterArguments._filter(
            exp_name=exp_name,
            target_keys=[k for k, _ in targets],
            **custom_kwargs,
        )
        # pylint: enable=protected-access

    @classmethod
    def method(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        arguments: WavesExecuterArguments,
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
        cirqs = []
        if pbar is not None:
            pbar.set_description("| Loading circuits")
        for i, (k, q) in enumerate(targets):
            q_copy = q.copy()
            chosen_key = "" if isinstance(k, int) else str(k)
            old_name = "" if isinstance(q.name, str) else q.name
            old_name = "" if len(old_name) < 1 else old_name
            q_copy.name = ".".join(
                [n for n in [f"{arguments.exp_name}_{i}", chosen_key, old_name] if len(n) > 0]
            )
            cirqs.append(q_copy)

        return cirqs, {}

    @classmethod
    def quantities(
        cls,
        shots: Optional[int] = None,
        counts: Optional[list[dict[str, int]]] = None,
        ultimate_question: str = "",
    ) -> dict[str, Union[float, int]]:
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            dict[str, float]: Counts, purity, entropy of experiment.
        """
        if shots is None or counts is None:
            print(
                "| shots or counts is None, "
                + "but it doesn't matter with ultimate question over all."
            )
        print("| ultimate_question:", ultimate_question)
        dummy = -100
        utlmatic_answer = 42
        return {
            "dummy": dummy,
            "utlmatic_answer": utlmatic_answer,
        }

    def analyze(
        self,
        ultimate_question: str = "",
        shots: Optional[int] = None,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> WavesExecuterAnalysis:
        """Analysis of the experiment.

        Args:
            ultimate_question (str, optional):
                The ultimate question of the universe.
                Defaults to `''`.
            shots (Optional[int], optional):
                The number of shots.
                Defaults to None.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar. Defaults to None.

        Returns:
            WavesExecuterAnalysis: The analysis of the experiment
        """

        if pbar is not None:
            pbar.set_description("What is the ultimate question of the universe?")

        if shots is None:
            shots = self.commons.shots
        if len(self.afterwards.counts) < 1:
            raise QurryExperimentCountsNotCompleted(
                "The counts of the experiment is not completed. So there is no data to analyze."
            )

        qs = self.quantities(
            shots=shots,
            counts=self.afterwards.counts,
            ultimate_question=ultimate_question,
        )

        serial = len(self.reports)
        analysis = self.analysis_instance(
            ultimate_question=ultimate_question,
            serial=serial,
            **qs,  # type: ignore
        )

        self.reports[serial] = analysis
        return analysis
