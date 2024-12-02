"""
================================================================
Command tools (:mod:`qurry.tools.command`)
================================================================
"""

import os
import warnings
import platform
import subprocess
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
    """Via pytorch to check the availability of Nvidia CUDA.

    Returns:
        bool: Available of CUDA by pytorch if pytorch is available, else 'None'.
    """
    try:
        # pylint: disable=import-outside-toplevel
        import torch  # type: ignore

        # pylint: disable=import-outside-toplevel

        print(f" - CUDA availability check by Torch --------- {torch.cuda.is_available()}")
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


def fun_platform_check():
    """Check platform information."""

    platform_uname = platform.uname()
    if platform_uname.system == "Linux":
        try:
            uname_all_read = subprocess.check_output(["uname", "-a"]).strip()
            uname_all_read = uname_all_read.decode("utf-8")
            uname_all_split = uname_all_read.split("\n")
            uname_all = uname_all_split[0]
        # pylint: disable=broad-except
        except Exception:
            uname_all = platform_uname.version
        # pylint: enable=broad-except
    else:
        uname_all = platform_uname.version

    if "PRoot-Distro" in platform_uname.release:
        print(f"| Whao! You are using '{platform_uname.release}' !!!")
        print("| Is it on Termux on Android Phone or Tablet?")
        print('| "The Quantum Computing Right At Your Fingertips" :smile:')

        if "synology" in uname_all.lower():
            print(f"| uname -a: '{uname_all}'")
            print("| Seriously? You're running Quantum Computing on a Synology NAS?")
            print('| "Your NAS can also perform Quantum Computing!" :smile:')
            print("| You're a true geek! :smile:")
