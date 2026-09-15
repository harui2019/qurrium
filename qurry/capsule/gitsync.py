"""GitSync - A quick way to create .gitignore (:mod:`qurry.capsule.mori.gitsync`)"""

import os
from pathlib import Path

from .utils import OpenArgs, PrintArgs, create_open_args, create_print_args


class GitSyncControl(list[str]):
    """A gitignore file generator. A quick way to create .gitignore"""

    def sync(self, filename: str, force: bool = False) -> bool:
        """Add file to sync.

        Args:
            filename (str): Filename.
            force (bool, optional): Force to add the file to sync.
                If the file is already added, then it will be added again.
                Defaults to False.

        Returns:
            bool: The file is added to be synchronized and return True.
                If `force` is True, it will add the file again even if it's already added,
                otherwise it will return False if the file is already added.
        """
        line = f"!{filename}"
        if line in self:
            if force:
                self.append(line)
                return True
            return False

        self.append(line)
        return True

    def ignore(self, filename: str, force: bool = False) -> bool:
        """Add file to ignore from sync.

        Args:
            filename (str): Filename.
            force (bool, optional): Force to add the file to ignore.
                If the file is already added, then it will be added again.
                Defaults to False.

        Returns:
            bool: The file is added to be ignored and return True.
                If `force` is True, it will add the file again even if it's already added,
                otherwise it will return False if the file is already added.
        """
        line = f"{filename}"
        if line in self:
            if force:
                self.append(line)
                return True
            return False
        self.append(line)
        return True

    def comment(self, comment: str) -> None:
        """Add comment to .gitignore.

        Args:
            comment (str): The comment to be added.
        """
        if not comment.startswith("#"):
            comment = f"# {comment}"
        self.append(comment)

    def export(
        self,
        save_location: Path | str = Path("./"),
        open_args: OpenArgs | None = None,
        print_args: PrintArgs | None = None,
    ) -> None:
        """Export .gitignore

        Args:
            save_location (Path): The location of .gitignore.
            open_args (OpenArgs | None, optional):
                The other arguments for :func:`open` function.
                Defaults to None,
                it will be set to :const:`~qurry.capsule.utils.DEFAULT_OPEN_ARGS`.
            print_args (PrintArgs | None, optional):
                The other arguments for :func:`print` function.
                Defaults to None,
                it will be set to :const:`~qurry.capsule.utils.DEFAULT_PRINT_ARGS`.
        """

        open_args = create_open_args(open_args=open_args)
        print_args = create_print_args(print_args=print_args)

        assert "encoding" in open_args, "encoding must be specified in open_args"
        encoding = open_args.pop("encoding")
        assert "encoding" not in open_args, "encoding must not be in open_args after pop"

        if isinstance(save_location, str):
            save_location = Path(save_location)
        elif isinstance(save_location, Path):
            ...
        else:
            raise ValueError("'save_location' needs to be the type of 'str' or 'Path'.")

        if not os.path.exists(save_location):
            raise FileNotFoundError(f"Such location not found: {save_location}")

        with open(save_location / ".gitignore", encoding=encoding, **open_args) as ignore_list:
            for item in self:
                print(item, file=ignore_list, **print_args)

    def clear_duplicates(self) -> None:
        """Clear duplicate items in .gitignore."""
        seen = set()
        unique_items = []
        for item in self:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)
        self.clear()
        self.extend(unique_items)

    def load(
        self,
        save_location: Path | str,
        take_duplicate: bool = False,
        open_args: OpenArgs | None = None,
    ):
        """Read existed .gitignore

        Args:
            save_location (Path): The location of .gitignore.
            take_duplicate (bool, optional):
                Take duplicate item in .gitignore. Defaults to False.
            open_args (OpenArgs | None, optional):
                The other arguments for :func:`open` function.
                Defaults to None,
                it will be set to the returned valuse of
                :func:`~qurry.capsule.utils.create_open_args`
                with `is_read_only` set to True. It will be like:

                .. code-block:: python

                    {
                        "mode": "r",
                        "encoding": "utf-8",
                    }

        Raises:
            FileNotFoundError: The .gitignore is not found.
            TypeError: The save_location is not the type of 'str' or 'Path'.
        """
        open_args = create_open_args(open_args=open_args, is_read_only=True)

        assert "encoding" in open_args, "encoding must be specified in open_args"
        encoding = open_args.pop("encoding")
        assert "encoding" not in open_args, "encoding must not be in open_args after pop"

        if isinstance(save_location, str):
            save_location = Path(save_location)
        elif isinstance(save_location, Path):
            ...
        else:
            raise ValueError("'save_location' needs to be the type of 'str' or 'Path'.")

        if not os.path.exists(save_location):
            raise FileNotFoundError(f"Such location not found: {save_location}")
        actual_file_path = save_location / ".gitignore"

        if not os.path.exists(actual_file_path):
            raise FileNotFoundError(f"The .gitignore is not found on '{save_location}'.")

        tmp_list = []
        with open(actual_file_path, encoding=encoding, **open_args) as ignore_list:
            for line in ignore_list.readlines():
                tmp_list.append(line.strip())
            if not take_duplicate:
                tmp_list = list(set(tmp_list))

        self += tmp_list
