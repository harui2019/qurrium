"""

================================================================
TagList (:mod:`qurry.capsule.mori.taglist`)
================================================================
"""

from typing import (
    Optional,
    Literal,
    Union,
    TypeVar,
    NamedTuple,
    Any,
    overload,
)
from collections import defaultdict
from collections.abc import Hashable, Iterable
from pathlib import Path
import os
import json
import csv
import warnings

from .utils import defaultOpenArgs, defaultPrintArgs, defaultJsonDumpArgs
from ..jsonablize import parse
from ..exception import TagListTakeNotIterableWarning

_K = TypeVar("_K", bound=Hashable)
_V = TypeVar("_V")
_T = TypeVar("_T")

AvailableFileType = Literal["json", "csv"]


def tuple_str_parse(k: str) -> Union[tuple[str, ...], str]:
    """Convert tuple strings to real tuple.

    Args:
        k (str): Tuplizing available string.

    Returns:
        Union[tuple[str, ...], str]: Result of tuplizing.
    """
    if k[0] == "(" and k[-1] == ")":
        kt = list(k[1:-1].split(", "))
        kt2 = []
        for ktsub in kt:
            if len(ktsub) > 0:
                if ktsub[0] == "'":
                    kt2.append(ktsub[1:-1])
                elif ktsub[0] == '"':
                    kt2.append(ktsub[1:-1])
                elif ktsub.isdigit():
                    kt2.append(int(ktsub))
                else:
                    kt2.append(ktsub)

            else:
                ...

        kt2 = tuple(kt2)
        return kt2
    return k


@overload
def key_tuple_loads(
    o: dict[Union[Hashable, _K], _T]
) -> dict[Union[Hashable, tuple[Hashable, ...], _K], _T]: ...
@overload
def key_tuple_loads(o: _T) -> _T: ...


def key_tuple_loads(o):
    """If a dictionary with string keys
    which read from json may originally be a python tuple,
    then transplies as a tuple.

    Args:
        o (dict): A dictionary with string keys which read from json.

    Returns:
        dict: Result which turns every possible string keys returning to 'tuple'.
    """

    if not isinstance(o, dict):
        return o

    ks = list(o.keys())
    for k in ks:
        if isinstance(k, str):
            kt2 = tuple_str_parse(k)
            if kt2 != k:
                o[kt2] = o[k]
                del o[k]
    return o


class TagList(defaultdict[_K, list[Union[_V, Any]]]):
    """Specific data structures of :module:`qurry` like `dict[str, list[any]]`.

    >>> bla = TagList()

    >>> bla.guider('strTag1', [...])
    >>> bla.guider(('tupleTag1', ), [...])
    >>> # other adding of key and value via `.guider()`
    >>> bla
    ... {
    ...     (): [...], # something which does not specify tags.
    ...     'strTag1': [...], # something
    ...     ('tupleTag1', ): [...],
    ...     ... # other hashable as key in python
    ... }

    Args:
        name (str, optional):
            The name of this `tagList`. Defaults to `TagList`.

    Raises:
        ValueError: When input is not a dict.

    """

    __name__ = "TagList"
    protect_keys = ["_all", ()]

    def __init__(
        self,
        o: Optional[dict[_K, Iterable[Any]]] = None,
        name: str = __name__,
        tuple_str_auto_transplie: bool = True,
    ) -> None:
        pass_o = {} if o is None else o
        if not isinstance(pass_o, dict):
            raise ValueError("Input needs to be a dict with all values are iterable.")
        super().__init__(list)
        self.__name__ = name

        pass_o = key_tuple_loads(pass_o) if tuple_str_auto_transplie else pass_o
        not_list_v = []
        for k, v in pass_o.items():
            if isinstance(v, Iterable):
                self[k].extend(v)  # type: ignore
            else:
                not_list_v.append(k)

        if len(not_list_v) > 0:
            warnings.warn(
                f"The following keys '{not_list_v}' "
                + "with the values are not iterable won't be added.",
                category=TagListTakeNotIterableWarning,
            )

    def all(self) -> list[_V]:
        """Export all values in `tagList`.

        Returns:
            list: All values in `tagList`.
        """
        d = []
        for v in self.values():
            if isinstance(v, list):
                d += v
        return d

    def guider(
        self,
        legacy_tag: Optional[_K] = None,
        v: Any = None,
    ) -> None:
        """

        Args:
            legacyTag (any): The tag for legacy as key.
            v (any): The value for legacy.

        Returns:
            dict: _description_
        """
        for k in self.protect_keys:
            if legacy_tag == k:
                warnings.warn(f"'{k}' is a reserved key for export data.")

        if legacy_tag is None:
            self[()].append(v)  # type: ignore
        elif legacy_tag in self:
            self[legacy_tag].append(v)
        else:
            self[legacy_tag] = [v]

    availableFile = ["json", "csv"]

    class ParamsControl(NamedTuple):
        """The type of arguments for :func:`params_control`."""

        open_args: dict[Union[Literal["encoding"], str], Any]
        print_args: dict[str, Any]
        json_dump_args: dict[str, Any]
        save_location: Path

    @classmethod
    def params_control(
        cls,
        open_args: Optional[dict[str, Any]] = None,
        print_args: Optional[dict[str, Any]] = None,
        json_dump_args: Optional[dict[str, Any]] = None,
        save_location: Union[Path, str] = Path("./"),
        filetype: AvailableFileType = "json",
        is_read_only: bool = False,
    ) -> ParamsControl:
        """Handling all arguments.

        Args:
            open_args (dict[str, Any], optional):
                The other arguments for :func:`open` function.
                Defaults to :attr:`self.defaultOpenArgs`, which is:
                >>> {
                    'mode': 'w+',
                    'encoding': 'utf-8',
                }
            print_args (dict[str, Any], optional):
                The other arguments for :func:`print` function.
                Defaults to :attr:`self.defaultPrintArgs`, which is:
                >>> {}
            json_dump_args (dict[str, Any], optional):
                The other arguments for :func:`json.dump` function.
                Defaults to :attr:`self.defaultJsonDumpArgs`, which is:
                >>> {
                    'indent': 2,
                }
            save_location (Path, optional):
                The exported location. Defaults to `Path('./')`.
            filetype (Literal[&#39;json&#39;, &#39;csv&#39;], optional):
                Export type of `tagList`. Defaults to 'json'.
            isReadOnly (bool, optional):
                Is reading a file of `tagList` exportation. Defaults to False.


        Returns:
            ParamsControl: Current arguments.
        """

        # working args
        if print_args is None:
            print_args = defaultPrintArgs.copy()
        else:
            print_args = {k: v for k, v in print_args.items() if k != "file"}
            print_args = {**defaultPrintArgs.copy(), **print_args}
        if open_args is None:
            open_args = defaultOpenArgs.copy()
        else:
            open_args = {k: v for k, v in open_args.items() if k != "file"}
            open_args = {**defaultOpenArgs.copy(), **open_args}
        if is_read_only:
            open_args["mode"] = "r"
        if json_dump_args is None:
            json_dump_args = defaultJsonDumpArgs.copy()
        else:
            json_dump_args = {k: v for k, v in json_dump_args.items() if k != "obj" or k != "fp"}
            json_dump_args = {**defaultJsonDumpArgs.copy(), **json_dump_args}

        # save_location
        if isinstance(save_location, (Path, str)):
            save_location = Path(save_location)
        else:
            raise ValueError("'save_location' needs to be the type of 'str' or 'Path'.")

        if not os.path.exists(save_location):
            raise FileNotFoundError(f"Such location not found: {save_location}")

        # file type check
        if filetype not in cls.availableFile:
            raise ValueError(f"Instead of '{filetype}', Only {cls.availableFile} can be exported.")

        # return {
        #     "open_args": open_args,
        #     "print_args": print_args,
        #     "json_dump_args": json_dump_args,
        #     "save_location": save_location,
        # }
        return cls.ParamsControl(
            open_args=open_args,
            print_args=print_args,
            json_dump_args=json_dump_args,
            save_location=save_location,
        )

    def export(
        self,
        name: Optional[str],
        save_location: Union[Path, str] = Path("./"),
        filetype: AvailableFileType = "json",
        taglist_name: str = __name__,
        open_args: Optional[dict[str, Any]] = None,
        print_args: Optional[dict[str, Any]] = None,
        json_dump_args: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Export `tagList`.

        Args:
            name (Optional[str], optional):
                File name for this `tagList`.
                The file name should be something like:
                    `f"{name}.{taglist_name}.{filetype}"`.
                or
                    `f"{taglist_name}.{filetype}"` when `name` is `None`.
                For example, if `name` is `example`, `taglist_name` is `tagList`,
                and `filetype` is `json`, the file name will be `example.tagList.json`.
            save_location (Path): The location of file.
            filetype (Literal[&#39;json&#39;, &#39;csv&#39;], optional):
                Export type of `tagList`. Defaults to 'json'.
            taglist_name (str, optional):
                The suffix name for this `tagList`.
                Defaults to `__name__`.
                The file name will be: `f"{name}.{taglist_name}.{filetype}"`.
            open_args (dict[str, Any], optional):
                The other arguments for :func:`open` function.
                Defaults to :attr:`self.defaultOpenArgs`, which is:
                >>> {
                    'mode': 'w+',
                    'encoding': 'utf-8',
                }
            print_args (dict[str, Any], optional):
                The other arguments for :func:`print` function.
                Defaults to :attr:`self.defaultPrintArgs`, which is:
                >>> {}
            json_dump_args (dict[str, Any], optional):
                The other arguments for :func:`json.dump` function.
                Defaults to :attr:`self.defaultJsonDumpArgs`, which is:
                >>> {
                    'indent': 2,
                }

        Raises:
            ValueError: When filetype is not supported.

        Return:
            Path: The path of exported file.
        """

        args = self.params_control(
            open_args=open_args,
            print_args=print_args,
            json_dump_args=json_dump_args,
            save_location=save_location,
            filetype=filetype,
        )

        encoding = args.open_args.pop("encoding")
        assert isinstance(encoding, str), "encoding must be str"

        filename = (
            f"{taglist_name}.{filetype}" if name is None else f"{name}.{taglist_name}.{filetype}"
        )

        if filetype == "json":
            with open(
                args.save_location / filename, encoding=encoding, **args.open_args
            ) as export_json:
                json.dump(parse(self), export_json, **args.json_dump_args)

        elif filetype == "csv":
            with open(
                args.save_location / filename,
                encoding=encoding,
                **args.open_args,
                newline="",
            ) as export_csv:
                taglist_writer = csv.writer(export_csv, quotechar="|")
                for k, vs in self.items():
                    for v in vs:
                        taglist_writer.writerow((k, v))

        else:
            warnings.warn("Exporting cancelled for no specified filetype.")

        return args.save_location / filename

    @classmethod
    def read(
        cls,
        filename: str,
        save_location: Union[Path, str] = Path("./"),
        filetype: AvailableFileType = "json",
        taglist_name: str = __name__,
        tuple_str_auto_transplie: bool = True,
        open_args: Optional[dict[str, Any]] = None,
        print_args: Optional[dict[str, Any]] = None,
        json_dump_args: Optional[dict[str, Any]] = None,
    ) -> "TagList":
        """Export `tagList`.

        Args:
            save_location (Path): The location of file.
            filename (Optional[str], optional):
                File name for this `tagList` with suffix name of `tagList`.
                The file name should be something like:
                    `f"{name}.{taglist_name}.{filetype}"`.
                or
                    `f"{taglist_name}.{filetype}"`.
                For example, if `name` is `example`, `taglist_name` is `tagList`,
                and `filetype` is `json`, the file name will be `example.tagList.json`.
                You need put the `name` and `taglist_name` in the filename like:
                >>> filename="example.tagList"
                `tagList` is the suffix name of this `tagList`.
                >>> taglist_name="tagList"
                `filetype` is the file type of the file.
                >>> filetype="json"
            filetype (Literal[&#39;json&#39;, &#39;csv&#39;], optional):
                Export type of `tagList`. Defaults to 'json'.
            taglist_name (str, optional):
                The suffix name for this `tagList`.
                Defaults to `__name__`.
                The file name will be: `f"{name}.{taglist_name}.{filetype}"`.
            tuple_str_auto_transplie (bool, optional):
                Whether to transplie tuple string to tuple.
            open_args (Optional[dict[str, Any]], optional):
                The other arguments for :func:`open` function.
                Defaults to :attr:`self.defaultOpenArgs`, which is:
                >>> {
                    'mode': 'w+',
                    'encoding': 'utf-8',
                }
            print_args (Optional[dict[str, Any]], optional):
                The other arguments for :func:`print` function.
                Defaults to :attr:`self.defaultPrintArgs`, which is:
                >>> {}
            json_dump_args (Optional[dict[str, Any]], optional):
                The other arguments for :func:`json.dump` function.
                Defaults to :attr:`self.defaultJsonDumpArgs`, which is:
                >>> {
                    'indent': 2,
                }

        Raises:
            FileNotFoundError: When file not found.
            ValueError: When filetype is not supported.

        Return:
            TagList: The path of exported file.

        """
        args = cls.params_control(
            open_args=open_args,
            print_args=print_args,
            json_dump_args=json_dump_args,
            save_location=save_location,
            filetype=filetype,
            is_read_only=True,
        )
        encoding = args.open_args.pop("encoding")
        assert isinstance(encoding, str), "encoding must be str"

        assert taglist_name in filename, (
            f"taglist_name: '{taglist_name}' must be a part of filename: '{filename}', "
            + f"like 'example.{taglist_name}.{filetype}'."
        )

        if filetype == "json":
            with open(
                args.save_location / filename, encoding=encoding, **args.open_args
            ) as read_json:
                raw_data = json.load(read_json)
                obj = cls(
                    o=raw_data,
                    name=taglist_name,
                    tuple_str_auto_transplie=tuple_str_auto_transplie,
                )
            return obj

        if filetype == "csv":
            with open(
                args.save_location / filename,
                encoding=encoding,
                **args.open_args,
                newline="",
            ) as read_csv:
                taglist_reaper = csv.reader(read_csv, quotechar="|")
                obj = cls(name=taglist_name)
                for k, v in taglist_reaper:
                    kt = tuple_str_parse(k) if tuple_str_auto_transplie else k
                    obj[kt].append(v)  # type: ignore
            return obj

        raise ValueError(f"Instead of '{filetype}', Only {cls.availableFile} can be exported.")
