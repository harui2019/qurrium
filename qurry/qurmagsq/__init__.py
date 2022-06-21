from typing import Literal

from .qurmagsq import MagnetSquare as MagnetSquareOrigin


def MagnetSquare(
    *args,
    method: Literal['original'] = 'original',
    **kwargs,
) -> MagnetSquareOrigin:
    """Call `MagnetSquare` methods.

    Args:
        method (Literal[&#39;original&#39;], optional): 

            - original: the original `MagnetSquare`.
            Defaults to 'original'.

    Returns:
        MagnetSquareOrigin: method.
    """
    if method == 'original':
        return MagnetSquareOrigin(*args, **kwargs)
    else:
        return MagnetSquareOrigin(*args, **kwargs)
