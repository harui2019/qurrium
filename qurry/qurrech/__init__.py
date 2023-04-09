from typing import Literal, Union

from ..exceptions import UnconfiguredWarning
from .HadamardTest import EchoHadamardTest
from .RandomizedMeasure import EchoRandomizedListen


def EchoListen(
    *args,
    method: Literal['randomized', 'hadamard'] = 'randomized',
    **kwargs,
) -> Union[EchoRandomizedListen, EchoHadamardTest]:
    """Call `EchoListen` methods.

    Args:
        method (Literal[&#39;randomized&#39;, &#39;hadamard&#39], optional): 

            - randomized: running by haar randomized measure.
            - hadamard: running by hadamard test.
            Defaults to 'randomized'.

    Returns:
        EchoListenBase: method.
    """
    if method == 'hadamard':
        return EchoHadamardTest(*args, **kwargs)
    else:
        return EchoRandomizedListen(*args, **kwargs)
