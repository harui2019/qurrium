from typing import Literal, Union
import warnings

from ..qurrium.exceptions import UnconfiguredWarning
from .qurrent import EntropyMeasureV3 as EntropyMeasureBase
from .haarMeasure import haarMeasureV3
from .hadamardTest import hadamardTestV3

from .qurrentV2.qurrentV2 import EntropyMeasureV2 as EntropyMeasureV2Base
from .qurrentV2.haarMeasure import haarMeasureV2
from .qurrentV2.hadamardTest import hadamardTestV2


def EntropyMeasure(
    *args, 
    method: Literal['randomized', 'hadamard', 'base'] = 'randomized',
    version: Literal['v3', 'v2'] = 'v3',
    **kwargs,
) -> Union[EntropyMeasureBase, EntropyMeasureV2Base]:
    """Call `EntropyMeasure` methods.

    Args:
        method (Literal[&#39;randomized&#39;, &#39;hadamard&#39;, &#39;base&#39;], optional): 
            
            - randomized: running by haar randomized measure.
            - hadamard: running by hadamard test.
            - base: the base of `EntropyMeasure`.
            Defaults to 'randomized'.
            
        version (Literal[&#39;v3&#39;, &#39;v2&#39;], optional): 
            
            `EntropyMeasure` is the foundation of this module, this is why there is 'v2' and 'v3'.
            `EntropyMeasureV2` is the predecessor of framework of `qurry`.
            `EntropyMeasureV3` is the fisrt application of `qurry`.
            Due to `EntropyMeasureV2` is deprecated but stil workable, so it is kept in this module.
            `EntropyMeasureV1` is in the legacy branch of `qurry` never contained in current module.
            If you want check it, there is it: 
                https://github.com/harui2019/qurry/tree/entropymeasureV1
                
            Defaults to 'v3'.

    Returns:
        Union[EntropyMeasureBase, EntropyMeasureV2Base]: method.
    """
    if version == 'v2':
        if method == 'base':
            warnings.warn(
                "This method is a base of 'EntropyMeasureV2' which cannot work before" +
                " introduce measurement like haar randomized measure.", UnconfiguredWarning)
            return EntropyMeasureV2Base(*args, **kwargs)
        elif method == 'hadamard':
            return hadamardTestV2(*args, **kwargs)
        else:
            return haarMeasureV2(*args, **kwargs)
        
    else:
        if method == 'base':
            warnings.warn(
                "This method is a base of 'EntropyMeasureV3' which cannot work before" +
                " introduce measurement like haar randomized measure.", UnconfiguredWarning)
            return EntropyMeasureBase(*args, **kwargs)
        elif method == 'hadamard':
            return hadamardTestV3(*args, **kwargs)
        else:
            return haarMeasureV3(*args, **kwargs)