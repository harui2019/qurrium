"""
================================================================
AnalysisContainer 
(:mod:`qurry.qurry.qurrium.container.analyses`)
================================================================

"""
from typing import Hashable, Any

from ..analysis import AnalysisPrototype


class AnalysesContainer(dict[Hashable, AnalysisPrototype]):
    """A customized dictionary for storing `AnalysisPrototype` objects."""

    __name__ = "AnalysisContainer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def export(
        self,
    ) -> tuple[dict[Hashable, dict[str, Any]], dict[str, dict[Hashable, dict[str, Any]]]]:
        """Export the analysis container.

        Returns:
            tuple[dict[str, dict[str, Any]], dict[str, dict[str, dict[str, Any]]]]:
            The first element is a dictionary of reports formats. The second element is a
            dictionary of tales_reports formats.
        """
        # reports
        reports: dict[Hashable, dict[str, Any]] = {}  # reports formats.
        # tales_reports formats.
        tales_reports: dict[str, dict[Hashable, dict[str, Any]]] = {}
        for k, al in self.items():
            report_main, report_tales = al.export()
            reports[k] = report_main
            for tk, tv in report_tales.items():
                if tk not in tales_reports:
                    tales_reports[tk] = {}
                tales_reports[tk][k] = tv

        return reports, tales_reports

    def __repr__(self):
        inner_lines = "\n".join(f"    {k}: ..." for k in self.keys())
        inner_lines2 = "{\n%s\n}" % inner_lines
        return (
            f"<{self.__name__}={inner_lines2} with {len(self)} "
            + "analysis load, a customized dictionary>"
        )
