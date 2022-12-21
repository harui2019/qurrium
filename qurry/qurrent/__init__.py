from typing import Literal, Union
import warnings

from ..exceptions import UnconfiguredWarning
# v4
from .v4.haarMeasure import EntropyHaarMeasureV4
from .v4.hadamardTest import EntropyHadamardTestV4
# v3
from .v3.qurrent import EntropyMeasureV3
from .v3.haarMeasure import haarMeasureV3
from .v3.hadamardTest import hadamardTestV3
# v2
from .v2.qurrentV2 import EntropyMeasureV2
from .v2.haarMeasure import haarMeasureV2
from .v2.hadamardTest import hadamardTestV2


def EntropyMeasure(
    *args,
    method: Literal['randomized', 'hadamard', 'base'] = 'randomized',
    version: Literal['v4', 'v3', 'v2'] = 'v4',
    **kwargs,
) -> Union[
    EntropyMeasureV2,
    EntropyMeasureV3,
    EntropyHadamardTestV4,
    EntropyHaarMeasureV4
]:
    """Call `EntropyMeasure` methods.

    Args:
        method (Literal[&#39;randomized&#39;, &#39;hadamard&#39;, &#39;base&#39;], optional): 

            - randomized: running by haar randomized measure.
            - hadamard: running by hadamard test.
            - base: the base of `EntropyMeasure`.
            Defaults to 'randomized'.

        version (Literal[&#39;v3&#39;, &#39;v2&#39;], optional): 

            - `EntropyMeasure` is the foundation of this module, this is why there is 'v2', 'v3', and `v4`.
            - `EntropyMeasureV4` is a data and processing structure refined of `v3`.
            - `EntropyMeasureV3` is the predecessor of framework of `qurry`.
            - `EntropyMeasureV2` is the fisrt application of `qurry`. Due to `EntropyMeasureV2` is deprecated but stil workable, so it is kept in this module.
            `- EntropyMeasureV1` is in the legacy branch of `qurry` never contained in current module.
                If you want check it, there is it: 
                https://github.com/harui2019/qurry/tree/entropymeasureV1

            Defaults to 'v4'.

    Returns:
        Union[EntropyMeasureBase, EntropyMeasureV2Base]: method.
    """
    if version == 'v2':
        if method == 'base':
            warnings.warn(
                "This method is a base of 'EntropyMeasureV2' which cannot work before" +
                " introduce measurement like haar randomized measure.", UnconfiguredWarning)
            return EntropyMeasureV2(*args, **kwargs)
        elif method == 'hadamard':
            return hadamardTestV2(*args, **kwargs)
        else:
            return haarMeasureV2(*args, **kwargs)

    elif version == 'v3':
        if method == 'base':
            warnings.warn(
                "This method is a base of 'EntropyMeasureV3' which cannot work before" +
                " introduce measurement like haar randomized measure.", UnconfiguredWarning)
            return EntropyMeasureV3(*args, **kwargs)
        elif method == 'hadamard':
            return hadamardTestV3(*args, **kwargs)
        else:
            return haarMeasureV3(*args, **kwargs)

    elif version == 'v4':
        if method == 'hadamard':
            return EntropyHadamardTestV4(*args, **kwargs)
        elif method == 'haar':
            return EntropyHaarMeasureV4(*args, **kwargs)
        else:
            if method == 'base':
                warnings.warn(
                    "QurryV4 EntropyMeasure does not exist base method, replaced by 'randomized'.", UnconfiguredWarning)
            return EntropyHaarMeasureV4(*args, **kwargs)
    else:
        warnings.warn(
            f"Invalid version {version}, replaced by 'v4'.", UnconfiguredWarning)
        if method == 'hadamard':
            return EntropyHadamardTestV4(*args, **kwargs)
        elif method == 'haar':
            return EntropyHaarMeasureV4(*args, **kwargs)
        else:
            if method == 'base':
                warnings.warn(
                    "QurryV4 EntropyMeasure does not exist base method, replaced by 'randomized'.", UnconfiguredWarning)
            return EntropyHaarMeasureV4(*args, **kwargs)
