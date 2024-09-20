"""
================================================================
Waves Qurry (:mod:`qurry.qurrium.wavesqurry`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from typing import Union, Optional, Type, Any
from collections.abc import Hashable
import tqdm

from qiskit import QuantumCircuit

from .analysis import WavesQurryAnalysis
from ..experiment import ExperimentPrototype, Commonparams, ArgumentsPrototype
from ...exceptions import QurryExperimentCountsNotCompleted


class WavesQurryArguments(ArgumentsPrototype):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class."""


class WavesQurryExperiment(ExperimentPrototype):
    """The instance of experiment."""

    __name__ = "WavesQurryExperiment"

    @property
    def arguments_instance(self) -> Type[WavesQurryArguments]:
        """The arguments instance for this experiment."""
        return WavesQurryArguments

    args: WavesQurryArguments

    @property
    def analysis_container(self) -> Type[WavesQurryAnalysis]:
        """The analysis instance for this experiment."""
        return WavesQurryAnalysis

    @classmethod
    def params_control(
        cls,
        targets: dict[Hashable, QuantumCircuit],
        exp_name: str = "exps",
        **custom_kwargs: Any,
    ) -> tuple[WavesQurryArguments, Commonparams, dict[str, Any]]:
        """Control the experiment's parameters.

        Args:
            targets (dict[Hashable, QuantumCircuit]):
                The circuits of the experiment.
            exp_name (str):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """

        # pylint: disable=protected-access
        return WavesQurryArguments._filter(
            exp_name=exp_name,
            target_keys=list(targets.keys()),
            **custom_kwargs,
        )
        # pylint: enable=protected-access

    @classmethod
    def method(
        cls,
        targets: dict[Hashable, QuantumCircuit],
        /,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> list[QuantumCircuit]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Args:
            targets (dict[Hashable, QuantumCircuit]):
                The circuits of the experiment.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            list[QuantumCircuit]: The circuits of the experiment.
        """
        if pbar is not None:
            pbar.set_description("| Loading circuits")
        return list(targets.values())

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

    def analyze(self, ultimate_question: str = "", shots: Optional[int] = None):
        """Analysis of the experiment.
        Where should be overwritten by each construction of new measurement.
        """

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
        analysis = self.analysis_container(
            ultimate_question=ultimate_question,
            serial=serial,
            **qs,  # type: ignore
        )

        self.reports[serial] = analysis
        return analysis
