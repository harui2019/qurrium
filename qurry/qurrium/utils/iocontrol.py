import os
from pathlib import Path
from typing import Union, NamedTuple

from ...tools import qurryProgressBar

STAND_COMPRESS_FORMAT = 'tar.xz'
FULL_SUFFIX_OF_COMPRESS_FORMAT = f'qurry.{STAND_COMPRESS_FORMAT}'


class IOComplex(NamedTuple):
    expsName: str
    saveLocation: Path
    exportLocation: Path

    tarName: str
    tarLocation: Path


def naming(
    is_read: bool = False,
    expsName: str = 'exps',
    saveLocation: Union[Path, str] = Path('./'),
    shortName: str = 'qurry',
    withoutSerial: bool = False,
    _rjustLen: int = 3,
    _indexRename: int = 1,
) -> IOComplex:
    """The process of naming.

    Args:
        is_read (bool, optional): 
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

    if is_read:
        immutableName = expsName
        exportLocation = saveLocation / immutableName
        tarName = f"{immutableName}.{FULL_SUFFIX_OF_COMPRESS_FORMAT}"
        tarLocation = saveLocation / tarName
        if not (exportLocation.exists() or tarLocation.exists()):
            raise FileNotFoundError(
                f"Such exportation data '{immutableName}' or '{tarName}' not found at '{saveLocation}', " +
                "'exportsName' may be wrong or not in this folder.")
        print(
            f"| Retrieve {immutableName}...\n" +
            f"| at: {exportLocation}"
        )
    elif withoutSerial:
        immutableName = expsName
        exportLocation = saveLocation / immutableName

    else:
        expsName = f'{expsName}.{shortName}'
        indexRename = _indexRename

        immutableName = f"{expsName}.{str(indexRename).rjust(_rjustLen, '0')}"
        exportLocation = saveLocation / immutableName

        # findIndexProgress = qurryProgressBar(
        #     range(1), bar_format='| {desc}')
        # with findIndexProgress as pb:
        #     while os.path.exists(exportLocation):
        #         pb.set_description_str(f"{exportLocation} is repeat location.")
        #         indexRename += 1
        #         immutableName = f"{expsName}.{str(indexRename).rjust(_rjustLen, '0')}"
        #         exportLocation = saveLocation / immutableName
        #     pb.set_description_str(
        #         f'Write "{immutableName}", at location "{exportLocation}"')
        #     os.makedirs(exportLocation)
        
        while os.path.exists(exportLocation):
            print(f"| {exportLocation} is repeat location.")
            indexRename += 1
            immutableName = f"{expsName}.{str(indexRename).rjust(_rjustLen, '0')}"
            exportLocation = saveLocation / immutableName
        print(
            f'| Write "{immutableName}", at location "{exportLocation}"')
        os.makedirs(exportLocation)

    return IOComplex(
        expsName=immutableName,
        saveLocation=saveLocation,
        exportLocation=exportLocation,

        tarName=f"{immutableName}.{FULL_SUFFIX_OF_COMPRESS_FORMAT}",
        tarLocation=saveLocation /
        f"{immutableName}.{FULL_SUFFIX_OF_COMPRESS_FORMAT}",
    )
