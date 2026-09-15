"""Post Processing - Hadamard Test - Entangled Entropy
(:mod:`qurry.process.hadamard_test.entangled_entropy`)

"""

from typing import TypedDict
import numpy as np
import tqdm


from .purity_echo_core import purity_echo_core, DEFAULT_PROCESS_BACKEND
from ..availability import PostProcessingBackendLabel
from ..utils import FloatType


class HadamardEntropyResult(TypedDict):
    """The return type of the post-processing for entangled entropy."""

    purity: FloatType
    """The purity of the system."""
    entropy: FloatType
    """The entropy of the system."""


def hadamard_entangled_entropy(
    shots: int,
    counts: list[dict[str, int]],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: tqdm.tqdm | None = None,
) -> HadamardEntropyResult:
    """Calculate entangled entropy with more information combined.
    The entropy we compute is the Second Order Rényi Entropy.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        backend (PostProcessingBackendLabel, optional):
            Backend of the postprocessing. Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (tqdm.tqdm | None, optional):
            Progress bar. Defaults to None.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        Quantity of the experiment.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str("Calculate entropy by Hadamard Test.")
    purity = purity_echo_core(shots, counts, backend)

    return {"purity": purity, "entropy": -np.log2(purity)}
