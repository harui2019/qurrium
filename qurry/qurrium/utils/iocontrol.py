"""
================================================================
The module of IO control. (:mod:`qurry.qurrium.utils.iocontrol`)
================================================================

"""

import os
from pathlib import Path
from typing import Union, NamedTuple

STAND_COMPRESS_FORMAT = "tar.xz"
FULL_SUFFIX_OF_COMPRESS_FORMAT = f"qurry.{STAND_COMPRESS_FORMAT}"
RJUST_LEN = 3
"""The length of the string to be right-justified for serial number."""


class IOComplex(NamedTuple):
    """The complex of IO control."""

    expsName: str
    save_location: Path
    export_location: Path
    tarName: str
    tarLocation: Path


def naming(
    is_read: bool = False,
    exps_name: str = "exps",
    save_location: Union[Path, str] = Path("./"),
    short_name: str = "qurry",
    without_serial: bool = False,
    rjust_len: int = RJUST_LEN,
    index_rename: int = 1,
) -> IOComplex:
    """The process of naming.

    Args:
        is_read (bool, optional):
            Whether to read the experiment data.
            Defaults to False.

        exps_name (str, optional):
            Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
            This name is also used for creating a folder to store the exports.
            Defaults to `'exps'`.

        save_location (Union[Path, str], optional):
            Where to save the export data. Defaults to Path('./')

        short_name (str, optional):
            The short name of Qurry Instance. Defaults to `'qurry'`.

        without_serial (bool, optional):
            Whether to use the serial number. Defaults to False.

        rjust_len (int, optional):
            The length of the serial number. Defaults to 3.

        index_rename (int, optional):
            The serial number. Defaults to 1.

    Raises:
        TypeError: The :arg:`save_location` is not a 'str' or 'Path'.
        FileNotFoundError: The :arg:`save_location` is not existed.
        FileNotFoundError: Can not find the exportation data which will be readed.

    Returns:
        dict[str, Union[str, Path]]: Name.
    """

    if isinstance(save_location, (Path, str)):
        save_location = Path(save_location)
    else:
        raise TypeError(
            f"The save_location '{save_location}' is "
            + f"not the type of 'str' or 'Path' but '{type(save_location)}'."
        )

    if is_read:
        immutable_name = exps_name
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
        immutable_name = exps_name
        export_location = save_location / immutable_name

    else:
        exps_name = f"{exps_name}.{short_name}"
        _index_rename = index_rename

        immutable_name = f"{exps_name}.{str(_index_rename).rjust(rjust_len, '0')}"
        export_location = save_location / immutable_name

        # findIndexProgress = qurryProgressBar(
        #     range(1), bar_format='| {desc}')
        # with findIndexProgress as pb:
        #     while os.path.exists(export_location):
        #         pb.set_description_str(f"{export_location} is repeat location.")
        #         indexRename += 1
        #         immutableName = f"{expsName}.{str(indexRename).rjust(_rjustLen, '0')}"
        #         export_location = save_location / immutableName
        #     pb.set_description_str(
        #         f'Write "{immutableName}", at location "{export_location}"')
        #     os.makedirs(export_location)

        while os.path.exists(export_location):
            print(f"| {export_location} is repeat location.")
            _index_rename += 1
            immutable_name = f"{exps_name}.{str(_index_rename).rjust(rjust_len, '0')}"
            export_location = save_location / immutable_name
        print(f'| Write "{immutable_name}", at location "{export_location}"')
        os.makedirs(export_location)

    return IOComplex(
        expsName=immutable_name,
        save_location=save_location,
        export_location=export_location,
        tarName=f"{immutable_name}.{FULL_SUFFIX_OF_COMPRESS_FORMAT}",
        tarLocation=save_location / f"{immutable_name}.{FULL_SUFFIX_OF_COMPRESS_FORMAT}",
    )
