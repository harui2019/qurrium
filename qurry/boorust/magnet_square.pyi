"""Boorust - Magnetization Square (:mod:`qurry.boorust.magnet_square`)"""

def magnet_square_core_rust(
    shots: int, counts: list[dict[str, int]], num_qubits: int
) -> tuple[float, dict[int, float], float]:
    """The core function of Magnetization square.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        num_qubits (int): Number of qubits.

    Returns:
        tuple[float, dict[int, float], float]:
            Magnetization square, magnetization square cell, time taken.
    """

def z_dir_magnet_square_core_rust(
    shots: int, single_counts: dict[str, int], num_qubits: int
) -> tuple[float, dict[int, float], float]:
    """The core function of Z direction Magnetization square.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        single_counts (dict[str, int]): Single count.
        num_qubits (int): Number of qubits.

    Returns:
        tuple[float, dict[int, float], float]:
            Magnetization square, magnetization square cell, time taken.
    """
