"""
================================================================
GitSync - A quick way to create .gitignore
(:mod:`qurry.capsule.mori.gitsync`)
================================================================

"""

import os
from pathlib import Path
from typing import Union, Optional, Any

from .utils import defaultOpenArgs, defaultPrintArgs


class GitSyncControl(list[str]):
    """A gitignore file generator.
    A quick way to create .gitignore

    """

    def sync(
        self,
        filename: str,
        force: bool = False,
    ) -> bool:
        """Add file to sync.

        Args:
            filename (str): Filename.

        Returns:
            bool: The file is added to be synchronized,
                otherwise it's already added then return False.
        """
        line = f"!{filename}"
        if line in self:
            if force:
                self.append(line)
                return True
            return False

        self.append(line)
        return True

    def ignore(
        self,
        filename: str,
        force: bool = False,
    ) -> bool:
        """Add file to ignore from sync.

        Args:
            filename (str): Filename.

        Returns:
            bool: The file is added to be ignored, otherwise it's already added then return False.
        """
        line = f"{filename}"
        if line in self:
            if force:
                self.append(line)
                return True
            return False
        self.append(line)
        return True

    def export(
        self,
        save_location: Union[Path, str] = Path("./"),
        open_args: Optional[dict[str, Any]] = None,
        print_args: Optional[dict[str, Any]] = None,
    ) -> None:
        """Export .gitignore

        Args:
            save_location (Path): The location of .gitignore.
            open_args (dict, optional): The other arguments for :func:`open` function.
            print_args (dict, optional): The other arguments for :func:`print` function.

        """
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
        encoding = open_args.pop("encoding")

        if isinstance(save_location, (Path)):
            ...
        elif isinstance(save_location, (str)):
            save_location = Path(save_location)
        else:
            raise TypeError("The save_location is not the type of 'str' or 'Path'.")

        if not os.path.exists(save_location):
            raise FileNotFoundError("The save_location is not found.")

        with open(save_location / ".gitignore", encoding=encoding, **open_args) as ignore_list:
            for item in self:
                print(item, file=ignore_list, **print_args)

    def read(
        self,
        save_location: Union[Path, str],
        take_duplicate: bool = False,
        raise_not_found_error: bool = False,
        open_args: Optional[dict[str, Any]] = None,
    ) -> bool:
        """ead existed .gitignore

        Args:
            save_location (Path): The location of .gitignore.
            take_duplicate (bool, optional): Take duplicate item in .gitignore. Defaults to False.
            raise_not_found_error (bool, optional):
                Raise error if .gitignore is not found. Defaults to False.
            open_args (dict, optional): The other arguments for :func:`open` function.

        Raises:
            FileNotFoundError: The .gitignore is not found.
            TypeError: The save_location is not the type of 'str' or 'Path'.

        Returns:
            bool: The .gitignore is read successfully.

        """
        if open_args is None:
            open_args = defaultOpenArgs.copy()
        else:
            open_args = {k: v for k, v in open_args.items() if k != "file"}
            open_args = {**defaultOpenArgs.copy(), **open_args}
        open_args["mode"] = "r"
        encoding = open_args.pop("encoding")

        if isinstance(save_location, (Path)):
            ...
        elif isinstance(save_location, (str)):
            save_location = Path(save_location)
        else:
            raise TypeError("The save_location is not the type of 'str' or 'Path'.")

        if os.path.exists(save_location / ".gitignore"):
            with open(save_location / ".gitignore", encoding=encoding, **open_args) as ignore_list:
                for line in ignore_list.readlines():
                    new_line = line.strip()
                    if new_line not in self:
                        self.append(new_line)
                    elif take_duplicate:
                        self.append(new_line)
            return True

        if raise_not_found_error:
            raise FileNotFoundError("The .gitignore is not found.")
        return False
