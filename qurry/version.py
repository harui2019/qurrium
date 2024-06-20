"""
================================================================
Qurry Version (:mod:`qurry.version`)
================================================================

"""

import os
import subprocess
from typing import Union, Sequence

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

_Cmd = Union[
    str,
    bytes,
    os.PathLike[str],
    os.PathLike[bytes],
    Sequence[Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]],
]


def _minimal_ext_cmd(cmd: _Cmd) -> bytes:
    """Run a command in a subprocess.

    Well, this function is 'referred to' (aka copied from)(:smile:)
    the :func:`_minimal_ext_cmd` in qiskit.version
    For this finction is better than:
    ```py
    import subprocess
    label = subprocess.check_output(["git", "describe"]).strip()
    ```
    to get the git label due to better error handling.

    Args:
        cmd (_Cmd): The command to run.

    Returns:
        bytes: The output of the command.

    """
    # construct minimal environment
    env = {}
    for k in ["SYSTEMROOT", "PATH"]:
        v = os.environ.get(k)
        if v is not None:
            env[k] = v
    # LANGUAGE is used on win32
    env["LANGUAGE"] = "C"
    env["LANG"] = "C"
    env["LC_ALL"] = "C"
    with subprocess.Popen(
        cmd,  # type: ignore
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=os.path.join(os.path.dirname(ROOT_DIR)),
    ) as proc:
        stdout, stderr = proc.communicate()
        if proc.returncode > 0:
            error_message = stderr.strip().decode("ascii")
            raise OSError(f"Command {cmd} exited with code {proc.returncode}: {error_message}")
    return stdout


def git_version() -> str:
    """Get the current git head sha1.

    Returns:
        str: The git head sha1.
    """
    try:
        out = _minimal_ext_cmd(["git", "rev-parse", "HEAD"])
        git_revision = out.strip().decode("ascii")
    except OSError:
        git_revision = "Unknown"

    return git_revision


def git_describe() -> str:
    """Get the current git describe label.

    Returns:
        str: The git describe label.
    """
    try:
        out = _minimal_ext_cmd(["git", "describe", "--tags"])
        git_describe_version = out.strip().decode("ascii")
    except OSError:
        git_describe_version = "Unknown"

    return git_describe_version


with open(os.path.join(ROOT_DIR, "VERSION.txt"), encoding="utf-8") as version_file:
    VERSION = version_file.read().strip()


def get_version_info() -> str:
    """Get the full version string and git describe output.

    Returns:
        tuple[str, str]: The full version string, git describe output.
    """
    full_version = VERSION

    if not os.path.exists(os.path.join(os.path.dirname(ROOT_DIR), ".git")):
        return full_version
    try:
        release = _minimal_ext_cmd(["git", "tag", "-l", "--points-at", "HEAD"])
    except Exception:  # pylint: disable=broad-except
        return full_version
    if not release:
        git_describe_version = git_describe()[1:]
        return git_describe_version
    return full_version


__version__ = get_version_info()


version_info = {
    "full_version": __version__,
    "git_revision": git_version(),
    "git_describe": git_describe(),
    "version": VERSION,
    "is_nightly": "dev" in __version__,
}
