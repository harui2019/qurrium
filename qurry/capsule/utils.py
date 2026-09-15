"""Utility functions and type definitions for :mod:`~qurry.capsule`.
(:mod:`qurry.capsule.utils`)"""

from typing import TypedDict, Any
from collections.abc import Callable
import warnings
from json import JSONEncoder

DEFAULT_ENCODING = "utf-8"
"""Default encoding for file operations."""
DEFAULT_INDENT = 2
"""Default indentation for JSON serialization."""
DEFAULT_MODE = "w+"
"""Default mode for file operations."""
DEFAULT_ENSURE_ASCII = False
"""Default ensure_ascii for JSON serialization."""


class OpenArgs(TypedDict, total=False):
    """Default arguments for open function."""

    mode: str
    """Mode in which the file is opened"""
    buffering: int
    """Buffering policy for the file"""
    encoding: str | None
    """Encoding used for the file"""
    errors: str | None
    """Error handling scheme for the file"""
    newline: str | None
    """Newline character handling for the file"""
    closefd: bool
    """Whether to close the file descriptor when the file is closed"""
    opener: Callable[[str, int], int] | None
    """Custom opener for the file, if needed"""


DEFAULT_OPEN_ARGS: OpenArgs = {"mode": DEFAULT_MODE, "encoding": DEFAULT_ENCODING}
"""Default arguments for open function.

This includes:
- `mode`: The mode in which the file is opened, default is 'w+'.
- `encoding`: The encoding used for the file, default is 'utf-8'.
"""


def create_open_args(
    open_args: dict[str, Any] | OpenArgs | None = None, is_read_only: bool = False
) -> OpenArgs:
    """Create open arguments.

    If `open_args` is not provided or a null dictionary,
    it will return :const:`DEFAULT_OPEN_ARGS`
    Otherwise, it will merge the provided `open_args` with :const:`DEFAULT_OPEN_ARGS`.

    If `is_read_only` is True, the mode will be set to 'r'.

    Args:
        open_args (dict[str, Any] | OpenArgs | None): Arguments for open function.
        is_read_only (bool, optional): Whether the file is read-only. Defaults to False.

    Raises:
        TypeError: If 'open_args' is not a dict.

    Returns:
        OpenArgs: The open arguments.
    """

    new_open_args = DEFAULT_OPEN_ARGS.copy()
    if open_args is not None:
        if not isinstance(open_args, dict):
            raise TypeError("'open_args' must be a dict.")
        if open_args.pop("file", None):
            warnings.warn(
                "Argument 'file' is ignored for it will be used by 'TagList.export'.",
                UserWarning,
            )
        for k, v in open_args.items():
            new_open_args[k] = v
    open_args = new_open_args
    if is_read_only:
        open_args["mode"] = "r"

    return open_args


class PrintArgs(TypedDict, total=False):
    """Default arguments for print function."""

    flush: bool
    """Whether to flush the output buffer after printing."""
    end: str
    """String appended after the last value, default is newline."""
    sep: str
    """String inserted between values, default is space."""


DEFAULT_PRINT_ARGS: PrintArgs = {}
"""Default arguments for print function.
"""


def create_print_args(print_args: dict[str, Any] | PrintArgs | None = None) -> PrintArgs:
    """Create print arguments.

    If `print_args` is not provided or a null dictionary,
    it will return :const:`DEFAULT_PRINT_ARGS`.
    Otherwise, it will merge the provided `print_args` with :const:`DEFAULT_PRINT_ARGS`.

    Args:
        print_args (dict[str, Any] | PrintArgs | None): Arguments for print function.

    Returns:
        PrintArgs: The print arguments.
    """

    new_print_args = DEFAULT_PRINT_ARGS.copy()
    if print_args is not None:
        if not isinstance(print_args, dict):
            raise TypeError("'print_args' must be a dict.")
        for k, v in print_args.items():
            if k == "file":
                warnings.warn(
                    "Argument 'file' is ignored for it will be used by 'TagList.export'.",
                    UserWarning,
                )
            new_print_args[k] = v
    return new_print_args


class JSONDumpArgs(TypedDict, total=False):
    """Default arguments for print function."""

    skipkeys: bool
    """Whether to skip keys that are not serializable."""
    ensure_ascii: bool
    """Whether to escape non-ASCII characters."""
    check_circular: bool
    """Whether to check for circular references."""
    allow_nan: bool
    """Whether to allow NaN and Infinity values."""
    cls: type[JSONEncoder] | None
    """Custom JSONEncoder class to use for serialization."""
    indent: int | str | None
    """Indentation level for pretty-printing JSON, default is 2."""
    separators: tuple[str, str] | None
    """Tuple of separators for JSON serialization, default is (', ', ': ')."""
    default: Callable[[Any], Any] | None
    """Function to call for objects that are not serializable."""
    sort_keys: bool
    """Whether to sort the keys in the JSON output."""


DEFAULT_JSON_DUMP_ARGS: JSONDumpArgs = {
    "indent": DEFAULT_INDENT,
    "ensure_ascii": DEFAULT_ENSURE_ASCII,
}
"""Default arguments for JSON dump function.

This includes:
- `indent`: The indentation level for pretty-printing JSON, default is 2.
- `ensure_ascii`: Whether to escape non-ASCII characters, default is False.
"""


def create_json_dump_args(
    json_dump_args: dict[str, Any] | JSONDumpArgs | None = None,
) -> JSONDumpArgs:
    """Create JSON dump arguments.

    If `json_dump_args` is not provided or a null dictionary,
    it will return :const:`DEFAULT_JSON_DUMP_ARGS`.
    Otherwise, it will merge the provided `json_dump_args` with :const:`DEFAULT_JSON_DUMP_ARGS`.

    Args:
        json_dump_args (dict[str, Any] | JSONDumpArgs | None): Arguments for json.dump function.

    Returns:
        JSONDumpArgs: The JSON dump arguments.
    """

    new_json_dump_args = DEFAULT_JSON_DUMP_ARGS.copy()
    if json_dump_args is not None:
        if not isinstance(json_dump_args, dict):
            raise TypeError("'json_dump_args' must be a dict.")
        for k, v in json_dump_args.items():
            if k in ["obj", "fp"]:
                warnings.warn(
                    f"Argument '{k}' is ignored for it will be used by 'TagList.export'.",
                    UserWarning,
                )
            new_json_dump_args[k] = v
    return new_json_dump_args
