"""
================================================================
Availability for the post-processing module.
(:mod:`qurry.process.availability`)
================================================================
"""

from typing import Union, Literal, Optional, Callable

PostProcessingBackendLabel = Union[Literal["Cython", "Rust", "Python"], str]
"""The backend label for post-processing."""

BACKEND_TYPES: list[PostProcessingBackendLabel] = ["Python", "Cython", "Rust"]


def availablility(
    module_location: str,
    import_statement: list[tuple[PostProcessingBackendLabel, bool, Optional[ImportError]]],
) -> tuple[str, dict[PostProcessingBackendLabel, Union[bool, Optional[ImportError]]],]:
    """Returns the availablility of the post-processing backend.

    Args:
        module_location (str): The location of the module.
        import_statement (
            list[tuple[PostProcessingBackendLabel, bool, Optional[QurryPostProcessingError]]]
        ):
            The import statement for the post-processing backend.

    Returns:
        tuple[str, dict[
            PostProcessingBackendLabel,
            Union[bool, Optional[QurryPostProcessingError]]]
        ]:
            The location of the module and the availablility of the post-processing backend.
    """
    return module_location, {
        "Python": True,
        **{
            backend: available if available else error
            for backend, available, error in import_statement
        },
    }


default_postprocessing_backend: Callable[
    [bool, bool], PostProcessingBackendLabel
] = lambda rust_available=False, cython_available=False: (
    "Rust" if rust_available else "Cython" if cython_available else "Python"
)
"""Return the default post-processing backend.

Args:
    rust_available (bool): Rust availability.
    cython_available (bool): Cython availability.

Returns:
    PostProcessingBackendLabel: The default post-processing backend.
"""
