"""
================================================================
Construct (:mod:`qurry.process.utils.construct`)
================================================================

"""

import warnings
from typing import Union

from ..availability import availablility
from ..exceptions import (
    PostProcessingRustImportError,
    PostProcessingRustUnavailableWarning,
)

try:
    from ...boorust import construct  # type: ignore

    qubit_selector_rust_source = construct.qubit_selector_rust  # type: ignore

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
