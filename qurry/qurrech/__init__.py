from typing import Literal

from .qurrech import EchoListen as EchoListenBase
from .haarMeasure import haarMeasure
from .hadamardTest import hadamardTest


def EchoListen(
    method: Literal['randomized', 'hadamard', 'base'] = 'randomized',
    *args, **kwargs,
) -> EchoListenBase:
    if method == 'base':
        return EchoListenBase(*args, **kwargs)
    elif method == 'hadamard':
        return hadamardTest(*args, **kwargs)
    else:
        return haarMeasure(*args, **kwargs)
