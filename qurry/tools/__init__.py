"""
================================================================
Tools (:mod:`qurry.tools`)
================================================================
"""
import warnings

from .command import cmdWrapper, pytorchCUDACheck
from .backend import BackendWrapper, BackendManager, version_check, backendName
from .processmanager import ProcessManager, workers_distribution, DEFAULT_POOL_SIZE
from .progressbar import qurry_progressbar
from .datetime import current_time, DatetimeDict

# pylint: disable=invalid-name


def backendWrapper(*args, **kwargs):
    """Wrapper around :class:`qurry.tools.backend.BackendWrapper` for backward compatibility."""

    warnings.warn(
        "Please replace `qurry.tools.backendWrapper` with `qurry.tools.BackendWrapper`.",
        DeprecationWarning,
    )
    return BackendWrapper(*args, **kwargs)


def backendManager(*args, **kwargs):
    """Wrapper around :class:`qurry.tools.backend.BackendManager` for backward compatibility."""

    warnings.warn(
        "Please replace `qurry.tools.backendManager` with `qurry.tools.BackendManager`.",
        DeprecationWarning,
    )
    return BackendManager(*args, **kwargs)


# pylint: enable=invalid-name
