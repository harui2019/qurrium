"""The module of IO control. (:mod:`qurry.qurrium.utils.iocontrol`)"""

import os
from typing import NamedTuple
from pathlib import Path

STAND_COMPRESS_FORMAT = "tar.xz"
FULL_SUFFIX_OF_COMPRESS_FORMAT = f"qurry.{STAND_COMPRESS_FORMAT}"
RJUST_LEN = 3
"""The length of the string to be right-justified for serial number."""


def serial_naming(name: str, index_rename: int, rjust_len: int = RJUST_LEN) -> str:
    """Create a serial name with right-justified index.

    Args:
        name (str): The base name.
        index_rename (int): The index to be right-justified.
        rjust_len (int, optional): The length of the right-justified string. Defaults to 3.

    Returns:
        str: The formatted name with right-justified index.
    """
    return f"{name}." + str((index_rename + 1)).rjust(rjust_len, "0")


class ExportFolderNaming(NamedTuple):
    """The naming complex for export folder."""

    summoner_name: str
    """The name of :class:`~qurry.qurrium.multimanager.MultiManager`."""
    save_location: Path
    """The save location of :class:`~qurry.qurrium.multimanager.MultiManager`."""
    export_location: Path
    """The file export location of each files belonging to 
    :class:`~qurry.qurrium.multimanager.MultiManager`."""
    tar_name: str
    """The tar compress name of :class:`~qurry.qurrium.multimanager.MultiManager`."""
    tar_location: Path
    """The tar compress file location of :class:`~qurry.qurrium.multimanager.MultiManager`."""


def folder_naming(
    is_read: bool = False,
    exp_or_summoner_name: str = "exps",
    save_location: Path | str = Path("./"),
    without_serial: bool = False,
    rjust_len: int = RJUST_LEN,
    index_rename: int = 0,
) -> ExportFolderNaming:
    """The process of naming.

    Args:
        is_read (bool, optional):
            Whether to read the experiment data.
            Defaults to False.
        exp_or_summoner_name (str, optional):
            Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
            This name is also used for creating a folder to store the exports.
            Defaults to `'exps'`.
        save_location (Path | str, optional):
            Where to save the export data. Defaults to Path('./')
        without_serial (bool, optional):
            Whether to use the serial number. Defaults to False.
        rjust_len (int, optional):
            The length of the serial number. Defaults to 3.
        index_rename (int, optional):
            The serial number. Defaults to 0.

    Raises:
        TypeError: The `save_location` is not a 'str' or 'Path'.
        FileNotFoundError: The `save_location` is not existed.
        FileNotFoundError: Can not find the exportation data which will be readed.

    Returns:
        ExportFolderNaming: The naming complex for export folder.
    """

    if isinstance(save_location, (Path, str)):
        save_location = Path(save_location)
    else:
        raise TypeError(
            f"The save_location '{save_location}' is "
            + f"not the type of 'str' or 'Path' but '{type(save_location)}'."
        )

    if is_read:
        immutable_name = exp_or_summoner_name
        export_location = save_location / immutable_name
        tar_name = f"{immutable_name}.{FULL_SUFFIX_OF_COMPRESS_FORMAT}"
        tar_location = save_location / tar_name
        if not (export_location.exists() or tar_location.exists()):
            raise FileNotFoundError(
                f"Such exportation data '{immutable_name}' or "
                + f"'{tar_name}' not found at '{save_location}', "
                + "'exports name' may be wrong or not in this folder."
            )
        print(f"| Retrieve {immutable_name}...\n" + f"| at: {export_location}")
    elif without_serial:
        immutable_name = exp_or_summoner_name
        export_location = save_location / immutable_name

    else:
        _counting = index_rename

        immutable_name = serial_naming(exp_or_summoner_name, _counting, rjust_len)
        export_location = save_location / immutable_name

        while os.path.exists(export_location):
            print(f"| {export_location} is repeat location.")
            _counting += 1
            immutable_name = serial_naming(exp_or_summoner_name, _counting, rjust_len)
            export_location = save_location / immutable_name
        print(f'| Write "{immutable_name}", at location "{export_location}"')
        os.makedirs(export_location)

    return ExportFolderNaming(
        summoner_name=immutable_name,
        save_location=save_location,
        export_location=export_location,
        tar_name=f"{immutable_name}.{FULL_SUFFIX_OF_COMPRESS_FORMAT}",
        tar_location=save_location / f"{immutable_name}.{FULL_SUFFIX_OF_COMPRESS_FORMAT}",
    )
