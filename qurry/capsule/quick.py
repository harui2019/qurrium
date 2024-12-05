"""

================================================================
Quick CapSule (:mod:`qurry.capsule.quick`)
================================================================
"""

from typing import Union, Iterable, Literal, Optional, Any
from pathlib import Path
import json

from .jsonablize import quickJSONExport, parse
from .mori.csvlist import SingleColumnCSV


# pylint: disable=invalid-name
def quickJSON(
    content: Iterable,
    filename: Union[str, Path],
    mode: str,
    indent: int = 2,
    encoding: str = "utf-8",
    jsonable: bool = False,
    save_location: Union[Path, str] = Path("./"),
    mute: bool = True,
) -> Optional[str]:
    """Configurable quick JSON export.

    Args:
        content (any): Content wants to be written.
        filename (str): Filename of the file.
        mode (str): Mode for :func:`open` function.
        indent (int, optional): Indent length for json. Defaults to 2.
        encoding (str, optional): Encoding method. Defaults to 'utf-8'.
        jsonablize (bool, optional):
            Whether to transpile all object to jsonable via :func:`mori.jsonablize`.
            Defaults to False.
        save_location (Union[Path, str], optional): Location of files. Defaults to Path('./').
        mute (bool, optional): Mute the exportation. Defaults to True.

    Returns:
        Optional[str]: The filename of the file when not mute.
    """
    return quickJSONExport(
        content=content,
        filename=filename,
        mode=mode,
        indent=indent,
        encoding=encoding,
        jsonable=jsonable,
        save_location=save_location,
        mute=mute,
    )


def quickListCSV(
    content: Iterable,
    filename: str,
    mode: str,
    encoding: str = "utf-8",
    jsonable: bool = False,
    save_location: Union[Path, str] = Path("./"),
    print_args: Optional[dict[str, str]] = None,
) -> None:
    """Quickly export a list to csv file.

    Args:
        content (Iterable): Content of the csv file.
        filename (str): Filename of the csv file.
        mode (str): Mode for :func:`open` function.
        encoding (str, optional): Encoding method. Defaults to 'utf-8'.
        jsonable (bool, optional):
            Whether to transpile all object to jsonable via :func:`mori.jsonablize`.
            Defaults to False.
        save_location (Union[Path, str], optional):
            Location of files. Defaults to Path('./').
        print_args (Optional[dict[str, str]], optional):
            The arguments for :func:`print` function.
    """

    if not isinstance(save_location, Path):
        save_location = Path(save_location)
    if jsonable:
        content = [parse(v) for v in content]

    tmp = SingleColumnCSV(content)
    open_args = {
        "mode": mode,
        "encoding": encoding,
    }

    tmp.export(
        save_location=save_location,
        name=filename,
        open_args=open_args,
        print_args=print_args,
    )


def quickRead(
    filename: Union[str, Path],
    save_location: Union[Path, str] = Path("./"),
    filetype: Literal["json", "txt"] = "json",
    encoding: str = "utf-8",
) -> Any:
    """Quick read file.

    Args:
        filename (Union[str, Path]): Filename.
        encoding (str, optional): Encoding method. Defaults to 'utf-8'.

    Returns:
        str: Content of the file.
    """
    if not isinstance(save_location, Path):
        save_location = Path(save_location)

    if filetype == "json":
        with open(save_location / filename, "r", encoding=encoding) as File:
            return json.load(File)

    else:
        with open(save_location / filename, "r", encoding=encoding) as File:
            return File.read()


# pylint: enable=invalid-name
