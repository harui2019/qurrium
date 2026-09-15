"""Boorust - Bit Slice (:mod:`qurry.boorust.bit_slice`)"""

def qubit_selector_rust(
    num_qubits: int, degree: tuple[int, int] | int | None = None
) -> tuple[int, int]:
    """Determint the qubits to be used.

    Args:
        num_qubits (int): Number of qubits.
        degree (tuple[int, int] | int | None, optional):
            Degree of freedom or specific subsystem range.
            Defaults to None then will use number of qubits as degree.

    Raises:
        ValueError: The specific degree of subsystem qubits
            beyond number of qubits which the wave function has.
        ValueError: The number of qubits of subsystem A is not a natural number.
        ValueError: Invalid input for subsystem range defined by only two integers.
        ValueError: Degree of freedom is not given.

    Returns:
        tuple[int]: The range of qubits to be used.
    """

def cycling_slice_rust(target: str, start: int, end: int, step: int = 1) -> str:
    """Slice a iterable object with cycling.

    Args:
        target (str): The target object.
        start (int): Index of start.
        end (int): Index of end.
        step (int, optional): Step of slice. Defaults to 1.

    Raises:
        IndexError: Slice out of range.

    Returns:
        str: The sliced object.
    """

def degree_handler_rust(
    allsystem_size: int,
    degree: tuple[int, int] | int | None,
    measure: tuple[int, int] | None,
) -> tuple[tuple[int, int], tuple[int, int], int]:
    """Handle the degree of freedom for the subsystem.

    Args:
        allsystem_size (int):
            The size of the whole system.
        degree (Otuple[int, int] | int | None):
            The degree of freedom.
        measure (tuple[int, int] | None):
            The measure range.

    Returns:
        tuple[tuple[int, int], tuple[int, int], int]:
            The degree of freedom, measure range, and subsystem size.
    """
