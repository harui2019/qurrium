"""
================================================================
Backend tools for Qurry. (:mod:`qurry.tools.backend`)
================================================================

"""

from .import_manage import (
    shorten_name,
    backendName,
    real_backend_loader,
    fack_backend_loader,
    version_check,
)
from .backend_manager import BackendWrapper, BackendManager
from .import_ibm import DummyProvider
from .import_simulator import GeneralBackend, GeneralSimulator, GeneralProvider
