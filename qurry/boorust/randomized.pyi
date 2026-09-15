"""Boorust - Randomized Toolkits (:mod:`qurry.boorust.randomized`)"""

def hamming_distance_rust(str1: str, str2: str) -> int:
    """Calculate the Hamming distance between two bit strings.

    Args:
        str1 (str): First string.
        str2 (str): Second string.

    Returns:
        int: Distance between strings.
    """

def ensemble_cell_rust(
    s_i: str, s_i_meas: int, s_j: str, s_j_meas: int, a_num: int, shots: int
) -> float:
    """Calculate the value of two counts from qubits in ensemble average by Rust.

    Args:
        s_i (str): First count's qubits arrange.
        s_i_meas (int): First count.
        s_j (str): Second count's qubits arrange.
        s_j_meas (int): Second count.
        a_num (int): Degree of freedom.
        shots (int): Shots of executation.

    Returns:
        float: the value of two counts from qubits in ensemble average.
    """

def entangled_entropy_core_2_rust(
    shots: int,
    counts: list[dict[str, int]],
    selected_classical_registers: list[int] | None = None,
) -> tuple[dict[int, float], list[int], str, float]:
    """The core function of entangled entropy by Rust.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (list[int] | None, optional):
            The list of **the index of the selected_classical_registers**. Defaults to None.

    Returns:
        tuple[dict[int, float], list[int], str, float]:
            Purity of each cell, Selected classical registers, Message, Time to calculate.
    """

def entangled_entropy_core_rust(
    shots: int,
    counts: list[dict[str, int]],
    degree: tuple[int, int] | int | None,
    measure: tuple[int, int] | None = None,
) -> tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
    """The core function of entangled entropy by Rust.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (tuple[int, int] | int | None): Degree of the subsystem.
        measure (tuple[int, int] | None, optional):
            Measuring range on quantum circuits. Defaults to None.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
            Purity of each cell, Partition range, Measuring range, Message, Time to calculate.
    """

def overlap_echo_core_2_rust(
    shots: int,
    first_counts: list[dict[str, int]],
    second_counts: list[dict[str, int]],
    selected_classical_registers: list[int] | None = None,
) -> tuple[dict[int, float], list[int], str, float]:
    """The core function of wavefunction overlap by Rust.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        first_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        second_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (list[int] | None, optional):
            The list of **the index of the selected_classical_registers**. Defaults to None.

    Returns:
        tuple[dict[int, float], list[int], str, float]:
            Purity of each cell, Selected classical registers, Message, Time to calculate.
    """

def overlap_echo_core_rust(
    shots: int,
    counts: list[dict[str, int]],
    degree: tuple[int, int] | int | None,
    measure: tuple[int, int] | None = None,
) -> tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
    """The core function of wavefunction overlap by Rust.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (tuple[int, int] | int | None): Degree of the subsystem.
        measure (tuple[int, int] | None, optional):
            Measuring range on quantum circuits. Defaults to None.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
            Purity of each cell, Partition range, Measuring range, Message, Time to calculate.
    """
