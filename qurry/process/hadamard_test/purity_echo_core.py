"""Post Processing - Hadamard Test - Purity/Echo
(:mod:`qurry.process.hadamard_test.purity_echo_core`)

"""

import warnings
import numpy as np

from ..availability import (
    availability,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ..exceptions import PostProcessingBackendDeprecatedWarning

# pylint: disable=import-error,no-name-in-module
from ...boorust.hadamard import purity_echo_core_rust  # type: ignore


BACKEND_AVAILABLE = availability("hadamard_test.purity_echo_core", [("Rust", True, None)])
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(True, False)


def purity_echo_core(
    shots: int,
    counts: list[dict[str, int]],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> float:
    """Calculate entangled entropy with more information combined.
    The entropy we compute is the Second Order Rényi Entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

    Raises:
        Warning: Expected '0' and '1', but there is no such keys
        ValueError: The length of counts is not 1.
        ValueError: shots does not match sample_shots.

    Returns:
        dict[str, float]: Quantity of the experiment.
    """
    if len(counts) != 1:
        raise ValueError(f"counts should be a list of counts with length 1, but got {len(counts)}")

    if backend == "Cython":
        warnings.warn(
            "Cython backend is deprecated, using Python or Rust to calculate purity cell.",
            PostProcessingBackendDeprecatedWarning,
        )
        backend = DEFAULT_PROCESS_BACKEND
    if backend == "Rust":
        return purity_echo_core_rust(shots, counts)

    only_counts = counts[0]
    sample_shots = sum(only_counts.values())
    assert sample_shots == shots, f"shots {shots} does not match sample_shots {sample_shots}"

    is_zero_include = "0" in only_counts
    is_one_include = "1" in only_counts
    if is_zero_include and is_one_include:
        purity = (only_counts["0"] - only_counts["1"]) / shots
    elif is_zero_include:
        purity = only_counts["0"] / shots
    elif is_one_include:
        purity = only_counts["1"] / shots
    else:
        purity = np.nan
        raise ValueError("Expected '0' and '1', but there is no such keys")

    return purity
