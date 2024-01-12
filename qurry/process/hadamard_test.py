"""
================================================================
Postprocessing - Renyi Entropy - Hadamard Test
(:mod:`qurry.process.hadamard_test`)
================================================================

"""
import numpy as np


def hadamard_entangled_entropy(
    shots: int,
    counts: list[dict[str, int]],
) -> dict[str, float]:
    """Calculate entangled entropy with more information combined.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

    Raises:
        Warning: Expected '0' and '1', but there is no such keys

    Returns:
        dict[str, float]: Quantity of the experiment.
    """

    purity = -100
    entropy = -100
    only_counts = counts[0]
    sample_shots = sum(only_counts.values())
    assert (
        sample_shots == shots
    ), f"shots {shots} does not match sample_shots {sample_shots}"

    is_zero_include = "0" in only_counts
    is_one_include = "1" in only_counts
    if is_zero_include and is_one_include:
        purity = (only_counts["0"] - only_counts["1"]) / shots
    elif is_zero_include:
        purity = only_counts["0"] / shots
    elif is_one_include:
        purity = only_counts["1"] / shots
    else:
        purity = np.Nan
        raise ValueError("Expected '0' and '1', but there is no such keys")

    entropy = -np.log2(purity)
    quantity = {
        "purity": purity,
        "entropy": entropy,
    }
    return quantity
