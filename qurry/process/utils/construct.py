"""
================================================================
Construct (:mod:`qurry.process.utils.construct`)
================================================================

"""

import warnings
from typing import Union, Optional, overload

from ..availability import availablility
from ..exceptions import PostProcessingRustImportError, PostProcessingRustUnavailableWarning

try:
    from ...boorust import construct  # type: ignore

    qubit_selector_rust_source = construct.qubit_selector_rust  # type: ignore
    cycling_slice_rust_source = construct.cycling_slice_rust  # type: ignore
    degree_handler_rust_source = construct.degree_handler_rust

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def qubit_selector_rust_source(*args, **kwargs):
        """Dummy function for cycling_slice_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate cycling slice."
            + f" More infomation about this error: {FAILED_RUST_IMPORT}",
        )

    def cycling_slice_rust_source(*args, **kwargs):
        """Dummy function for cycling_slice_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate cycling slice."
        ) from FAILED_RUST_IMPORT

    def degree_handler_rust_source(*args, **kwargs):
        """Dummy function for degree_handler_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate degree handler."
        ) from FAILED_RUST_IMPORT


BACKEND_AVAILABLE = availablility(
    "utils.construct",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
    ],
)


def qubit_selector(
    num_qubits: int,
    degree: Union[int, tuple[int, int], None] = None,
) -> tuple[int, int]:
    """Determint the qubits to be used.

    Args:
        num_qubits (int): Number of qubits.
        degree (Union[int, tuple[int, int], None], optional):
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
    subsystem = list(range(num_qubits))

    if degree is None:
        degree = num_qubits

    if isinstance(degree, int):
        if degree > num_qubits:
            raise ValueError(
                f"The subsystem A includes {degree} qubits "
                + f"beyond {num_qubits} which the wave function has."
            )
        if degree < 0:
            raise ValueError("The number of qubits of subsystem A has to be natural number.")

        item_range = (num_qubits - degree, num_qubits)
        subsystem = subsystem[num_qubits - degree : num_qubits]

    elif isinstance(degree, (tuple, list)):
        if len(degree) == 2:
            deg_parsed = [(d % num_qubits if d != num_qubits else num_qubits) for d in degree]
            item_range = (min(deg_parsed), max(deg_parsed))
            subsystem = subsystem[min(deg_parsed) : max(deg_parsed)]

        else:
            raise ValueError(
                "Subsystem range is defined by only two integers, "
                + f"but there is {len(degree)} integers in '{degree}'."
            )

    else:
        raise ValueError(f"'degree' must be 'int' or 'tuple[int, int]', but get '{degree}'.")

    return item_range


def qubit_selector_rust(
    num_qubits: int,
    degree: Union[int, tuple[int, int], None] = None,
) -> tuple[int, int]:
    """Determint the qubits to be used.

    Args:
        num_qubits (int): Number of qubits.
        degree (Union[int, tuple[int, int], None], optional):
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
    if RUST_AVAILABLE:
        return qubit_selector_rust_source(num_qubits, degree)
    warnings.warn(
        "Rust is not available, using python to calculate qubit selector."
        + f" More infomation about this error: {FAILED_RUST_IMPORT}",
        category=PostProcessingRustUnavailableWarning,
    )
    return qubit_selector(num_qubits, degree)


@overload
def cycling_slice(target: list, start: int, end: int, step: int = 1) -> list: ...


@overload
def cycling_slice(target: str, start: int, end: int, step: int = 1) -> str: ...


@overload
def cycling_slice(target: tuple, start: int, end: int, step: int = 1) -> tuple: ...


def cycling_slice(target, start, end, step=1):
    """Slice a iterable object with cycling.

    Args:
        target (_ListT): The target object.
        start (int): Index of start.
        end (int): Index of end.
        step (int, optional): Step of slice. Defaults to 1.

    Raises:
        IndexError: Slice out of range.

    Returns:
        Iterable: The sliced object.
    """
    length = len(target)
    slice_check = {
        "start <= -length": (start <= -length),
        "end >= length ": (end >= length),
    }
    if all(slice_check.values()):
        raise IndexError(
            "Slice out of range" + ", ".join([f" {k};" for k, v in slice_check.items() if not v])
        )
    if length <= 0:
        return target
    if start < 0 <= end:
        new_string = target[start:] + target[:end]
    else:
        new_string = target[start:end]

    return new_string[::step]


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
    if RUST_AVAILABLE:
        return cycling_slice_rust_source(target, start, end, step)
    warnings.warn(
        "Rust is not available, using python to calculate cycling slice."
        + f" Check: {FAILED_RUST_IMPORT}",
        PostProcessingRustUnavailableWarning,
    )
    return cycling_slice(target, start, end, step)


def degree_handler(
    allsystem_size: int,
    degree: Optional[Union[int, tuple[int, int]]],
    measure: Optional[tuple[int, int]],
) -> tuple[tuple[int, int], tuple[int, int], int]:
    """Handle the degree of freedom for the subsystem.

    Args:
        allsystem_size (int):
            The size of the whole system.
        degree (Optional[Union[int, tuple[int, int]]]):
            The degree of freedom.
        measure (Optional[tuple[int, int]]):
            The measure range.

    Returns:
        tuple[tuple[int, int], tuple[int, int], int]:
            The degree of freedom, measure range, and subsystem size.
    """

    # Determine degree
    degree = qubit_selector(allsystem_size, degree=degree)
    subsystem_size = max(degree) - min(degree)

    # Check whether the bitstring range is valid
    bitstring_range = degree
    bitstring_check = {
        "b > a": (bitstring_range[1] > bitstring_range[0]),
        "a >= -allsystemSize": bitstring_range[0] >= -allsystem_size,
        "b <= allsystemSize": bitstring_range[1] <= allsystem_size,
        "b-a <= allsystemSize": ((bitstring_range[1] - bitstring_range[0]) <= allsystem_size),
    }
    if not all(bitstring_check.values()):
        raise ValueError(
            f"Invalid 'bitStringRange = {bitstring_range} for allsystemSize = {allsystem_size}'. "
            + "Available range 'bitStringRange = [a, b)' should be"
            + ", ".join([f" {k};" for k, v in bitstring_check.items() if not v])
        )

    if measure is None:
        measure = qubit_selector(allsystem_size)

    return bitstring_range, measure, subsystem_size


def degree_handler_rust(
    allsystem_size: int,
    degree: Optional[Union[int, tuple[int, int]]],
    measure: Optional[tuple[int, int]],
) -> tuple[tuple[int, int], tuple[int, int], int]:
    """Handle the degree of freedom for the subsystem.

    Args:
        allsystem_size (int):
            The size of the whole system.
        degree (Optional[Union[int, tuple[int, int]]]):
            The degree of freedom.
        measure (Optional[tuple[int, int]]):
            The measure range.

    Returns:
        tuple[tuple[int, int], tuple[int, int], int]:
            The degree of freedom, measure range, and subsystem size.
    """
    if RUST_AVAILABLE:
        return degree_handler_rust_source(allsystem_size, degree, measure)
    warnings.warn(
        "Rust is not available, using python to calculate degree handler."
        + f" Check: {FAILED_RUST_IMPORT}",
        PostProcessingRustUnavailableWarning,
    )
    return degree_handler(allsystem_size, degree, measure)


def is_cycling_slice_active(
    allsystem_size: int,
    bitstring_range: tuple[int, int],
    subsystem_size: int,
) -> bool:
    """Check whether the cycling slice is active.

    Args:
        allsystem_size (int):
            The size of the whole system.
        bitstring_range (tuple[int, int]):
            The range of the bitstring.
        subsystem_size (int):
            The size of the subsystem

    Returns:
        bool: Whether the cycling slice is active.
    """
    _dummy_string = "".join(str(ds) for ds in range(allsystem_size))
    _dummy_string_slice = cycling_slice(_dummy_string, bitstring_range[0], bitstring_range[1], 1)
    is_avtive_cycling_slice = (
        _dummy_string[bitstring_range[0] : bitstring_range[1]] != _dummy_string_slice
    )
    if is_avtive_cycling_slice:
        assert len(_dummy_string_slice) == subsystem_size, (
            f"| All system size '{subsystem_size}' "
            + f"does not match dummyStringSlice '{_dummy_string_slice}'"
        )
    return is_avtive_cycling_slice
