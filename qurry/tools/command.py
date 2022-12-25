import os
import warnings
from typing import Optional

from ..exceptions import QurryImportWarning

def cmdWrapper(
    cmd: str = ""
) -> None:
    """Use command in anywhere, no matter it's in `.ipynb` or '.py'.

    Args:
        cmd (str, optional): Which execute command in any python or
            jupyter environment. Defaults to "".
    """
    try:
        from IPython import get_ipython
        get_ipython().system(cmd)
    except:
        os.system(cmd)


def pytorchCUDACheck() -> Optional[bool]:
    """Via pytorch to check Nvidia CUDA available.

    Returns:
        bool: Available of CUDA by pytorch if pytorch is available, else 'None'.
    """
    try:
        import torch
        print(" - Torch CUDA available --------- %s" %
              (torch.cuda.is_available()))
        print(">>> Using torch %s %s" % (
            torch.__version__,
            torch.cuda.get_device_properties(
                0) if torch.cuda.is_available() else 'CPU'
        ))
        return torch.cuda.is_available()
    except ImportError as e:
        warnings.warn(
            "Torch CUDA checking method requires pytorch" +
            " which has been installed in this enviornment.",
            category=QurryImportWarning
        )
        return None
