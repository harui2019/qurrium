"""The JSON Writer (:mod:`qurry.capsule.mori.jsonablize`)"""

from typing import Any
import os
from pathlib import Path
import json
import numpy as np

from ..utils import DEFAULT_ENCODING, DEFAULT_INDENT


SCALAR_VALUES = (str, int, float, bool, type(None))
"""The scalar value types."""


def value_parse(v: Any) -> str | int | float | bool | None:
    """Make value JSON-allowable.
    If a value is not allowed by :func:`~json.dumps`, then return its `str` representation.

    Args:
        v (Any): Value.

    Returns:
        A JSON-allowable value, which can be an iterable, str, int, float, bool or None.
    """

    # skip for basic supported types
    if isinstance(v, SCALAR_VALUES):
        return v
    # Check for complex numbers
    if isinstance(v, complex):
        return str(v)
    return str(v)


def key_parse(k: Any) -> str | int | float | bool | None:
    """Make key JSON-allowable.
    If a key is not allowed by :func:`~json.dumps`, then return its `str` representation.

    Args:
        k (Any): Key.

    Returns:
        A JSON-allowable key, which can be str, int, float, bool or None.
    """

    if isinstance(k, SCALAR_VALUES):
        return k
    # Convert tuple keys to strings
    if isinstance(k, tuple):
        return str(k)
    return str(k)


def parse(o: Any) -> Any:
    """Make a Python object JSON-allowable.

    Args:
        o (Any): Python object.

    Returns:
        Any: JSON-allowable object.
    """

    if isinstance(o, (list, tuple)):
        return [parse(v) for v in o]
    if isinstance(o, dict):
        return {key_parse(k): parse(v) for k, v in o.items()}
    if isinstance(o, np.ndarray):
        if np.iscomplexobj(o):
            return np.array(o, dtype=str).tolist()
        return o.tolist()
    return value_parse(o)


def is_scalar_list(o: Any) -> bool:
    """Check if the object is a list of scalar values.

    Args:
        o (Any): Object to be checked.

    Returns:
        bool: True if the object is a list of scalar values, False otherwise.
    """
    return isinstance(o, list) and all(isinstance(x, SCALAR_VALUES) for x in o)


def quick_json_write(
    content: Any,
    filename: str | Path,
    mode: str,
    indent: int = DEFAULT_INDENT,
    encoding: str = DEFAULT_ENCODING,
    jsonable: bool = False,
    cls: type[json.JSONEncoder] | None = None,
    save_location: Path | str = Path("./"),
    mute: bool = True,
) -> str | None:
    """Configurable quick JSON export.

    Args:
        content (any): Content wants to be written.
        filename (str | Path): Filename of the file.
        mode (str): Mode for :func:`open` function.
        indent (int, optional): Indent length for json. Defaults to 2.
        encoding (str, optional): Encoding method. Defaults to 'utf-8'.
        jsonablize (bool, optional):
            Whether to transpile all object to JSON-allowable object.
            If True, it will use :func:`parse` to transpile the content.
            Defaults to False.
        cls (type[json.JSONEncoder] | None, optional):
            The JSON encoder class. Defaults to :class:`MoriJSONEncoder`.
        save_location (Path | str, optional): Location of files. Defaults to Path('./').
        mute (bool, optional): Mute the exportation. Defaults to True.

    Returns:
        The filename of the file when not mute.
    """

    if not isinstance(save_location, Path):
        save_location = Path(save_location)
    if not os.path.exists(save_location):
        os.makedirs(save_location)
    save_loc_w_name = save_location / filename

    with open(save_loc_w_name, mode, encoding=encoding) as file:
        if jsonable:
            json.dump(parse(content), file, indent=indent, ensure_ascii=False, cls=cls)
        else:
            json.dump(content, file, indent=indent, ensure_ascii=False, cls=cls)
    if not mute:
        return f"'{save_loc_w_name}' exported successfully."
    return None
