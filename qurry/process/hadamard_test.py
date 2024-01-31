"""
================================================================
Postprocessing - Hadamard Test
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
        purity = np.nan
        raise ValueError("Expected '0' and '1', but there is no such keys")

    entropy = -np.log2(purity)
    quantity = {
        "purity": purity,
        "entropy": entropy,
    }
    return quantity


def hadamard_overlap_echo(
    shots: int,
    counts: list[dict[str, int]],
) -> dict[str, float]:
    """Calculate overlap echo with more information combined.

    - Which echo:

            The echo we compute is the overlap echo.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

    Raises:
        Warning: Expected '0' and '1', but there is no such keys

    Returns:
        dict[str, float]: Quantity of the experiment.
    """

    echo = -100
    only_count = counts[0]
    sample_shots = sum(only_count.values())
    assert (
        sample_shots == shots
    ), f"shots {shots} does not match sample_shots {sample_shots}"

    is_zero_include = "0" in only_count
    is_one_include = "1" in only_count
    if is_zero_include and is_one_include:
        echo = (only_count["0"] - only_count["1"]) / shots
    elif is_zero_include:
        echo = only_count["0"] / shots
    elif is_one_include:
        echo = only_count["1"] / shots
    else:
        echo = np.nan
        raise ValueError("Expected '0' and '1', but there is no such keys")

    quantity = {
        "echo": echo,
    }
    return quantity
