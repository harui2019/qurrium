"""

================================================================
Single column csv file (:mod:`qurry.capsule.mori.csvlist`)
================================================================
"""

from typing import (
    Optional,
    Literal,
    Union,
    TypeVar,
    NamedTuple,
    Any,
)
from pathlib import Path
import os
import csv
import glob

from .utils import defaultOpenArgs, defaultPrintArgs

_T = TypeVar("_T")


class SingleColumnCSV(list[_T]):
    """A single column csv file."""

    __name__ = "SingleCol"

    def __init__(
        self,
        *args,
        name: str = "untitled",
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.name = name

    class ParamsControl(NamedTuple):
        """The type of arguments for :func:`params_control`."""

        open_args: dict[Union[Literal["encoding"], str], Any]
        print_args: dict[str, Any]
        save_location: Path

    @classmethod
    def params_control(
        cls,
        open_args: Optional[dict[str, Any]] = None,
        print_args: Optional[dict[str, Any]] = None,
        save_location: Union[Path, str] = Path("./"),
        is_read_only: bool = False,
    ) -> ParamsControl:
        """Handling all arguments.

        Args:
            openArgs (dict, optional):
                The other arguments for :func:`open` function.
                Defaults to :attr:`self.defaultOpenArgs`, which is:
                >>> {
                    'mode': 'w+',
                    'encoding': 'utf-8',
                }
            printArgs (dict, optional):
                The other arguments for :func:`print` function.
                Defaults to :attr:`self.defaultPrintArgs`, which is:
                >>> {}
            save_location (Path, optional):
                The exported location. Defaults to `Path('./')`.
            isReadOnly (bool, optional):
                Is reading a file of `tagList` exportation. Defaults to False.

        Returns:
            dict[str, dict[str, str]]: Current arguments.
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

        # save_location
        if isinstance(save_location, (Path, str)):
            save_location = Path(save_location)
        else:
            raise ValueError("'save_location' needs to be the type of 'str' or 'Path'.")

        if not os.path.exists(save_location):
            raise FileNotFoundError(f"Such location not found: {save_location}")

        return cls.ParamsControl(
            open_args=open_args,
            print_args=print_args,
            save_location=save_location,
        )

    def export(
        self,
        name: Optional[str] = "untitled",
        save_location: Union[Path, str] = Path("./"),
        open_args: Optional[dict[str, Any]] = None,
        print_args: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Export `tagList`.

        Args:
            name (str, optional):
                Name for this `tagList`.
                Defaults to 'untitled'.
            save_location (Path): The location of file.
            open_args (dict, optional):
                The other arguments for :func:`open` function.
                Defaults to :attr:`self.defaultOpenArgs`, which is:
                >>> {
                    'mode': 'w+',
                    'encoding': 'utf-8',
                }
            print_args (dict, optional):
                The other arguments for :func:`print` function.
                Defaults to :attr:`self.defaultPrintArgs`, which is:
                >>> {}

        Raises:
            ValueError: When filetype is not supported.

        Return:
            Path: The path of exported file.
        """

        args = self.params_control(
            open_args=open_args,
            print_args=print_args,
            save_location=save_location,
        )
        encoding = args.open_args.pop("encoding")

        if name is None:
            name = self.name

        filename = name + ".csv"

        with open(
            args.save_location / filename,
            encoding=encoding,
            **args.open_args,
            newline="",
        ) as export_csv:
            csvlist_writer = csv.writer(export_csv, quotechar="|")
            for v in self:
                csvlist_writer.writerow((v,))

        return args.save_location / filename

    @classmethod
    def read(
        cls,
        name: str,
        save_location: Union[Path, str] = Path("./"),
        open_args: Optional[dict[str, Any]] = None,
        print_args: Optional[dict[str, Any]] = None,
        which_num: int = 0,
        raise_not_found_error: bool = True,
    ):
        """Export `tagList`.

        Args:
            name (str, optional):
                Name for this `tagList`.
                Defaults to 'untitled'.
            save_location (Path): The location of file.
            additionName (Optional[str], optional):
                Name for this `tagList`,
            secondFilenameExt (Optional[str], optional):
            openArgs (dict, optional):
                The other arguments for :func:`open` function.
                Defaults to :attr:`self.defaultOpenArgs`, which is:
                >>> {
                    'mode': 'w+',
                    'encoding': 'utf-8',
                }
            printArgs (dict, optional):
                The other arguments for :func:`print` function.
                Defaults to :attr:`self.defaultPrintArgs`, which is:
                >>> {}

        Raises:
            ValueError: When filetype is not supported.
            FileNotFoundError: _description_
            FileNotFoundError: _description_

        Return:
            Path: The path of exported file.
        """

        args = cls.params_control(
            open_args=open_args,
            print_args=print_args,
            save_location=save_location,
            is_read_only=True,
        )
        encoding = args.open_args.pop("encoding")

        ls_loc1 = glob.glob(str(args.save_location / f"*{name}.*"))
        if len(ls_loc1) == 0:
            if raise_not_found_error:
                raise FileNotFoundError(f"The file '*{name}.*' not found at '{save_location}'.")
            return cls(name=name)

        ls_loc2 = list(ls_loc1) if name is None else [f for f in ls_loc1 if name in f]

        if len(ls_loc2) < 1:
            if raise_not_found_error:
                raise FileNotFoundError(f"The file '{name}.csv' not found at '{save_location}'.")
            return cls(name=name)
        if len(ls_loc2) > 1:
            ls_loc2 = [ls_loc2[which_num]]
            print(
                f"The following files '{ls_loc2}' are fitting giving 'name', "
                + f"choosing the '{ls_loc2[0]}'."
            )

        filename = ls_loc2[0]
        filename = Path(filename).name
        obj = None

        with open(
            args.save_location / filename,
            encoding=encoding,
            **args.open_args,
            newline="",
        ) as read_csv:
            csv_reaper = csv.reader(read_csv, quotechar="|")
            obj = cls(name=name, save_location=args.save_location)
            for (v,) in csv_reaper:
                obj.append(v)  # type: ignore

        return obj
