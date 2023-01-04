import os
from pathlib import Path
from typing import Union, NamedTuple


class namingComplex(NamedTuple):
    expsName: str
    saveLocation: Path
    exportLocation: Path


def naming(
    isRead: bool = False,
    expsName: str = 'exps',
    saveLocation: Union[Path, str] = Path('./'),
    shortName: str = 'qurry',
    _rjustLen: int = 3,
    _indexRename: int = 1,
) -> namingComplex:
    """The process of naming.

    Args:
        isRead (bool, optional): 
            Whether to read the experiment data.
            Defaults to False.

        expsName (str, optional):
            Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
            This name is also used for creating a folder to store the exports.
            Defaults to `'exps'`.

        saveLocation (Union[Path, str], optional):
            Where to save the export data. Defaults to Path('./')

    Raises:
        TypeError: The :arg:`saveLocation` is not a 'str' or 'Path'.
        FileNotFoundError: The :arg:`saveLocation` is not existed.
        FileNotFoundError: Can not find the exportation data which will be readed.

    Returns:
        dict[str, Union[str, Path]]: Name.
    """

    if isinstance(saveLocation, (Path, str)):
        saveLocation = Path(saveLocation)
    else:
        raise TypeError(
            f"The saveLocation '{saveLocation}' is not the type of 'str' or 'Path' but '{type(saveLocation)}'.")

    if isRead:
        immutableName = expsName
        exportLocation = saveLocation / immutableName
        if not os.path.exists(exportLocation):
            raise FileNotFoundError(
                f"Such exportation data '{immutableName}' not found at '{saveLocation}', " +
                "'exportsName' may be wrong or not in this folder.")
        print(
            f"| Retrieve {immutableName}...\n" +
            f"| at: {exportLocation}"
        )

    else:
        expsName = f'{expsName}.{shortName}'
        indexRename = _indexRename

        immutableName = f"{expsName}.{str(indexRename).rjust(_rjustLen, '0')}"
        exportLocation = saveLocation / immutableName
        while os.path.exists(exportLocation):
            print(f"| {exportLocation} is repeat location.")
            indexRename += 1
            immutableName = f"{expsName}.{str(indexRename).rjust(_rjustLen, '0')}"
            exportLocation = saveLocation / immutableName
        print(
            f"| Write {immutableName}...\n" +
            f"| at: {exportLocation}"
        )
        os.makedirs(exportLocation)

    return namingComplex(
        expsName=immutableName,
        saveLocation=saveLocation,
        exportLocation=exportLocation,
    )
