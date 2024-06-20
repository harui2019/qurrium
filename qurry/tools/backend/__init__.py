"""
================================================================
Backend tools for Qurry. (:mod:`qurry.tools.backend`)
================================================================

"""

from .utils import backendName, backend_name_getter, shorten_name
from .env_check import version_check
from .backend_manager import BackendWrapper, BackendManager
from .import_ibm import DummyProvider
from .import_simulator import GeneralBackend, GeneralSimulator, GeneralProvider
