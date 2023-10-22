from .command import cmdWrapper, pytorchCUDACheck
from .backend import (
    BackendWrapper, BackendManager,
    version_check, backendName
)
from .watch import ResoureWatch
from .processmanager import ProcessManager, workers_distribution, DEFAULT_POOL_SIZE
from .progressbar import qurryProgressBar

import warnings


def backendWrapper(*args, **kwargs):
    """Wrapper around :class:`qurry.tools.backend.BackendWrapper` for backward compatibility.
    """

    warnings.warn(
        "Please replace `qurry.tools.backendWrapper` with `qurry.tools.BackendWrapper`.",
        DeprecationWarning)
    return BackendWrapper(*args, **kwargs)


def backendManager(*args, **kwargs):
    """Wrapper around :class:`qurry.tools.backend.BackendManager` for backward compatibility.
    """

    warnings.warn(
        "Please replace `qurry.tools.backendManager` with `qurry.tools.BackendManager`.",
        DeprecationWarning)
    return BackendManager(*args, **kwargs)
