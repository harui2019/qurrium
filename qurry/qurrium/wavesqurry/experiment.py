"""
================================================================
Waves Qurry (:mod:`qurry.qurrium.wavesqurry`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from typing import Union, Optional, Hashable, NamedTuple

from .analysis import WavesQurryAnalysis
from ..experiment import ExperimentPrototype
from ...exceptions import QurryExperimentCountsNotCompleted


class WavesQurryArguments(NamedTuple):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class."""

    exp_name: str = "exps"
    waves: list[Hashable] = []


class WavesQurryExperiment(ExperimentPrototype):
    """The instance of experiment."""

    __name__ = "WavesQurryExperiment"

    Arguments = WavesQurryArguments
    args: WavesQurryArguments

    analysis_container = WavesQurryAnalysis

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
