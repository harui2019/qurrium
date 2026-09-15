"""Boorust - String Operator (:mod:`qurry.boorust.string_operator`)"""

def string_operator_core_rust(shots: int, counts: list[dict[str, int]]) -> float:
    """The core function of magnet square by Rust.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

    Returns:
        float: String operator value.
    """
