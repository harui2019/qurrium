"""Post Processing - String Operator - String Operator Core
(:mod:`qurry.process.string_operator.strop_core`)

"""

from typing import Literal

from ..availability import availability, default_postprocessing_backend, PostProcessingBackendLabel
from ..utils import FloatType

# pylint: disable=import-error,no-name-in-module
from ...boorust.string_operator import string_operator_core_rust  # type: ignore

BACKEND_AVAILABLE = availability("string_operator.strop_core", [("Rust", True, None)])
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(True, False)


def add_or_reducer(bitstring: str) -> Literal[1, -1]:
    """The add or reduce function.
    If the sum of the bitstring is even, return 1.
    If the sum of the bitstring is odd, return -1.

    Args:
        bitstring (str): The bitstring.
    Returns:
        Literal[1, -1]: 1 or -1.
    """
    return 1 if sum(int(bit) for bit in bitstring) % 2 == 0 else -1


def string_operator_core(
    shots: int,
    counts: list[dict[str, int]],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> FloatType:
    """The core function of magnet square.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        backend (PostProcessingBackendLabel, optional):
            Post Processing backend. Defaults to DEFAULT_PROCESS_BACKEND.

    Returns:
        FloatType: String operator value.
    """
    if backend == "Rust":
        return string_operator_core_rust(shots, counts)

    if len(counts) != 1:
        raise ValueError(f"counts should be a list of counts with length 1, but got {len(counts)}")

    only_counts = counts[0]
    sample_shots = sum(only_counts.values())
    assert sample_shots == shots, f"shots {shots} does not match sample_shots {sample_shots}"

    order_per_bitstring_without_div_by_shots = {
        s: add_or_reducer(s) * m for s, m in only_counts.items()
    }

    return sum(order_per_bitstring_without_div_by_shots.values()) / sample_shots
