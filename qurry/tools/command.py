"""
================================================================
Command tools (:mod:`qurry.tools.command`)
================================================================
"""

import os
import warnings
from typing import Optional

from ..exceptions import QurryImportWarning


def cmd_wrapper(cmd: str = "") -> None:
    """Use command in anywhere, no matter it's in `.ipynb` or '.py'.

    Args:
        cmd (str, optional): Which execute command in any python or
            jupyter environment. Defaults to "".
    """
    try:
        # pylint: disable=import-outside-toplevel
        from IPython.core.getipython import get_ipython

        # pylint: disable=import-outside-toplevel

        get_ipython().system(cmd)  # type: ignore
    except ImportError:
        os.system(cmd)


def pytorch_cuda_check() -> Optional[bool]:
    """Via pytorch to check Nvidia CUDA available.

    Returns:
        bool: Available of CUDA by pytorch if pytorch is available, else 'None'.
    """
    try:
        # pylint: disable=import-outside-toplevel
        import torch  # type: ignore

        # pylint: disable=import-outside-toplevel

        print(f" - Torch CUDA available --------- {torch.cuda.is_available()}")
        print(
            ">>> Using torch "
            + " ".join(
                (
                    torch.__version__,
                    (torch.cuda.get_device_properties(0) if torch.cuda.is_available() else "CPU"),
                )
            )
        )
        return torch.cuda.is_available()
    except ImportError:
        warnings.warn(
            "Torch CUDA checking method requires pytorch"
            + " which has been installed in this enviornment.",
            category=QurryImportWarning,
        )
        return None
