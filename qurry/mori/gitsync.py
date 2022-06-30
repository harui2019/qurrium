from pathlib import Path
import json


class syncControl(list):
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

        with open(
            saveLocation / f".gitignore", 'w+', encoding='utf-8', **openArgs
        ) as ignoreList:
            [print(item, file=ignoreList, **printArgs) for item in self]

    def add(
        self,
        saveFolderName: Path,
    ) -> None:
        """Export .gitignore

        Args:
            saveFolderName (Path): The location of .gitignore.
        """
        with open(
            saveFolderName / f".gitignore", 'a', encoding='utf-8'
        ) as ignoreList:
            [print(item, file=ignoreList) for item in self]


def exportSyncJson(
    savePath: Path,
    syncList: syncControl,
    data: dict
) -> None:
    """A Quick expression to export json files.

    This function is *deprecated* due to `syncControl` now has its export method.

    Args:
        savePath (Path): Location to export.
        syncList (syncControl): Let .gitignore file track and sync.
        data (dict): The data will export.
    """

    with open(
        savePath, 'w', encoding='utf-8'
    ) as File:
        syncList.sync(savePath.name)
        json.dump(data, File, indent=2, ensure_ascii=False)
