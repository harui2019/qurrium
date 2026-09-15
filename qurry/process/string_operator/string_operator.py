"""Post Processing - String Operator - String Operator
(:mod:`qurry.process.string_operator.string_operator`)

"""

from typing import TypedDict
import tqdm

from .strop_core import string_operator_core, DEFAULT_PROCESS_BACKEND
from ..availability import PostProcessingBackendLabel
from ..utils import FloatType


class StringOperatorResult(TypedDict):
    """String Operator type."""

    order: FloatType
    """The order of the string operator."""


def string_operator_order(
    shots: int,
    counts: list[dict[str, int]],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: tqdm.tqdm | None = None,
) -> StringOperatorResult:
    """Calculate the order of the string operator.

    Reference:
        -   Crossing a topological phase transition with a quantum computer -
            Smith, Adam and Jobst, Bernhard and Green, Andrew G. and Pollmann, Frank,
            `PhysRevResearch.4.L022020
            <https://link.aps.org/doi/10.1103/PhysRevResearch.4.L022020>`_

        .. code-block:: bibtex

            @article{PhysRevResearch.4.L022020,
                title = {Crossing a topological phase transition with a quantum computer},
                author = {
                    Smith, Adam and Jobst, Bernhard and Green, Andrew G. and Pollmann, Frank
                },
                journal = {Phys. Rev. Research},
                volume = {4},
                issue = {2},
                pages = {L022020},
                numpages = {8},
                year = {2022},
                month = {Apr},
                publisher = {American Physical Society},
                doi = {10.1103/PhysRevResearch.4.L022020},
                url = {https://link.aps.org/doi/10.1103/PhysRevResearch.4.L022020}
            }

    Args:
        shots (int): Number of shots.
        counts (list[dict[str, int]]): List of counts.
        backend (PostProcessingBackendLabel, optional):
            Backend to use. Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (tqdm.tqdm | None, optional): Progress bar. Defaults to None.

    Returns:
        StringOperator: String Operator.
    """
    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description("String Operator being calculated.")
    order = string_operator_core(shots=shots, counts=counts, backend=backend)
    return {"order": order}
