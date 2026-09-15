"""Availability for the post-processing module. (:mod:`qurry.process.availability`)"""

from typing import Literal

PostProcessingBackendLabel = Literal["Cython", "Rust", "Python", "JAX"] | str
"""The backend label for post-processing."""

BACKEND_TYPES: list[PostProcessingBackendLabel] = ["Python", "Cython", "Rust", "JAX"]
"""The backend types for post-processing.

- Python: The default backend for post-processing.
- Cython: The Cython backend for post-processing.
- Rust: The Rust backend for post-processing.
- JAX: The Python backend for post-processing with JAX.
"""


def availability(
    module_location: str,
    import_statement: list[
        tuple[PostProcessingBackendLabel, bool | Literal["Depr."], ImportError | None]
    ],
) -> tuple[
    str,
    dict[PostProcessingBackendLabel, Literal["Yes", "Error", "Depr.", "No"]],
    dict[PostProcessingBackendLabel, ImportError | None],
]:
    """Returns the availablility of the post-processing backend.

    Args:
        module_location (str): The location of the module.
        import_statement (list[tuple[
            PostProcessingBackendLabel, bool | Literal["Depr."], ImportError | None
        ]]):
            The import statement for the post-processing backend.

    Returns:
        The tuple of location of the module,
        the availablility of the post-processing backend,
        and the errors.
    """
    avails: dict[PostProcessingBackendLabel, Literal["Yes", "Error", "Depr.", "No"]] = {
        "Python": "Yes"
    }
    errors: dict[PostProcessingBackendLabel, ImportError | None] = {}
    for backend, available, error in import_statement:
        if available is True:
            avails[backend] = "Yes"
        elif error is not None:
            avails[backend] = "Error"
            errors[backend] = error
        elif available == "Depr.":
            avails[backend] = "Depr."
        else:
            avails[backend] = "No"

    return module_location, avails, errors


def default_postprocessing_backend(
    rust_available: bool = False, cython_available: bool = False
) -> PostProcessingBackendLabel:
    """Return the default post-processing backend.

    Args:
        rust_available (bool): Rust availability.
        cython_available (bool): Cython availability.

    Returns:
        PostProcessingBackendLabel: The default post-processing backend.
    """
    return "Rust" if rust_available else "Cython" if cython_available else "Python"
