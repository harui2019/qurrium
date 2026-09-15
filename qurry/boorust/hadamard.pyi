"""Boorust - Hadamard Test (:mod:`qurry.boorust.hadamard`)"""

def purity_echo_core_rust(shots: int, counts: list[dict[str, int]]) -> float:
    """The core function of entangled entropy by Rust.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        float: Purity or Echo of the experiment.
    """
