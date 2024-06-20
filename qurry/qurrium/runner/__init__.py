"""
================================================================
Runner for running on Different Backends (IBM, IBMQ, ThirdParty, etc.)
(:mod:`qurry.qurry.qurrium.runner`)
================================================================

"""

from .runner import Runner, ThirdPartyRunner, retrieve_counter
from .accesor import BACKEND_AVAILABLE, ExtraBackendAccessor

if BACKEND_AVAILABLE["IBMQ"]:
    from .ibmqrunner import IBMQRunner

if BACKEND_AVAILABLE["IBM"]:
    from .ibmrunner import IBMRunner
