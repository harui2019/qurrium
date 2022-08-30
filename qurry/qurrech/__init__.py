from typing import Literal, Union
import warnings

from ..qurrium.exceptions import UnconfiguredWarning
# v4
from .haarMeasure import EchoHaarMeasureV4
from .hadamardTest import EchoHadamardTestV4
# v3
from .v3.qurrech import EchoListen as EchoListenBase
from .v3.haarMeasure import haarMeasure
from .v3.hadamardTest import hadamardTest


def EchoListen(
    *args,
    method: Literal['randomized', 'hadamard', 'base'] = 'randomized',
    version: Literal['v4', 'v3'] = 'v4',
    **kwargs,
) -> Union[
    EchoListenBase,
    EchoHaarMeasureV4,
    EchoHadamardTestV4
]:
    """Call `EchoListen` methods.

    Args:
        method (Literal[&#39;randomized&#39;, &#39;hadamard&#39;, &#39;base&#39;], optional): 

            - randomized: running by haar randomized measure.
            - hadamard: running by hadamard test.
            - base: the base of `EchoListen`.
            Defaults to 'randomized'.

    Returns:
        EchoListenBase: method.
    """
    if version == 'v4':
        if method == 'hadamard':
            return EchoHadamardTestV4(*args, **kwargs)
        else:
            return EchoHaarMeasureV4(*args, **kwargs)
    else:
        if method == 'base':
            warnings.warn(
                "This method is a base of 'EchoListen' which cannot work before" +
                " introduce measurement like haar randomized measure.", UnconfiguredWarning)
            return EchoListenBase(*args, **kwargs)
        elif method == 'hadamard':
            return hadamardTest(*args, **kwargs)
        else:
            return haarMeasure(*args, **kwargs)
