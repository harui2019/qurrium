"""
================================================================
Sampling Qurry Experiment (:mod:`qurry.qurrium.samplingqurry.experiment`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from typing import Optional, NamedTuple

from .analysis import QurryAnalysis
from ..experiment import ExperimentPrototype
from ...exceptions import QurryExperimentCountsNotCompleted


class QurryArguments(NamedTuple):
    """Construct the experiment's parameters for specific options,
    which is overwritable by the inherition class.
    """

    exp_name: str = "exps"
    sampling: int = 1


class QurryExperiment(ExperimentPrototype):
    """Experiment instance for QurryV5."""

    __name__ = "QurryExperiment"

    Arguments = QurryArguments
    args: QurryArguments

    analysis_container = QurryAnalysis

    @classmethod
    def quantities(
        cls,
        shots: Optional[int] = None,
        counts: Optional[list[dict[str, int]]] = None,
    ) -> dict[str, float]:
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
        dummy = -100
        return {
            "dummy": dummy,
            "utlmatic_answer": 42,
        }

    def analyze(
        self,
        ultimate_question: str = "",
        shots: Optional[int] = None,
    ):
        """Analysis of the experiment.
        Where should be overwritten by each construction of new measurement.
        """

        if shots is None:
            shots = self.commons.shots
        if len(self.afterwards.counts) < 1:
            raise QurryExperimentCountsNotCompleted(
                "The counts of the experiment is not completed. So there is no data to analyze."
            )

        qs = self.quantities(shots=shots, counts=self.afterwards.counts)

        serial = len(self.reports)
        analysis = self.analysis_container(
            ultimate_question=ultimate_question,
            serial=serial,
            **qs,  # type: ignore
        )

        self.reports[serial] = analysis
        return analysis
