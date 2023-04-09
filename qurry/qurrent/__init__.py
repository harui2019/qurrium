from typing import Literal, Union, overload

from .RandomizedMeasure import EntropyRandomizedMeasure
from .HadamardTest import EntropyHadamardTest

    
@overload
def EntropyMeasure(
    *args, method: Literal['hadamard'], **kwargs
) -> EntropyHadamardTest:
    ...

@overload
def EntropyMeasure(
    *args, method: Union[Literal['randomized', 'base'], str], **kwargs
) -> EntropyRandomizedMeasure:
    ...


def EntropyMeasure(
    *args,
    method = 'randomized',
    **kwargs,
):
    """Call `EntropyMeasure` methods.

    Args:
        method (Literal[&#39;randomized&#39;, &#39;hadamard&#39;, &#39;base&#39;], optional): 

            - randomized: running by haar randomized measure.
            - hadamard: running by hadamard test.
            - base: the base of `EntropyMeasure`.
            Defaults to 'randomized'.

    Returns:
        Union[EntropyMeasureBase, EntropyMeasureV2Base]: method.
    """
    if method == 'randomized' or method == 'haar':
        return EntropyRandomizedMeasure(*args, **kwargs)
    elif method == 'hadamard':
        return EntropyHadamardTest(*args, **kwargs)
    else:
        return EntropyRandomizedMeasure(*args, **kwargs)
