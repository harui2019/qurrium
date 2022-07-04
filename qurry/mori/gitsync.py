from pathlib import Path

class syncControl(list):
    __version__ = (0, 3, 0)
    """A quick way to create .gitignore

    Args:
        list ([type]): The list of ignored items.
    """

    def sync(
        self,
        fileName: str
    ) -> None:
        """Add file to sync.

        Args:
            fileName (str): Filename.
        """
        self.append(f"!{fileName}")

    def ignore(
        self,
        fileName: str
    ) -> None:
        """Add file to ignore from sync.

        Args:
            fileName (str): Filename.
        """
        self.append(f"{fileName}")

    defaultOpenArgs = {
        'mode': 'w+',
        'encoding': 'utf-8',
    }
    defaultPrintArgs = {
    }

    def export(
        self,
        saveLocation: Path,
        openArgs: dict = {},
        printArgs: dict = {},
    ) -> None:
        """Export .gitignore

        Args:
            saveLocation (Path): The location of .gitignore.
            openArgs (dict): The other arguments for :func:`open` function.
            printArgs (dict): The other arguments for :func:`print` function.

        """
        printArgs = {k: v for k, v in printArgs.items() if k != 'file'}
        printArgs = {**self.defaultPrintArgs, **printArgs}
        openArgs = {k: v for k, v in openArgs.items() if k != 'file'}
        openArgs = {**self.defaultOpenArgs, **openArgs}

        with open(
            saveLocation / f".gitignore", **openArgs
        ) as ignoreList:
            [print(item, file=ignoreList, **printArgs) for item in self]