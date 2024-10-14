"""
================================================================
Multiprocess component for multimanager
(:mod:`qurry.qurry.qurrium.multimanager.process`)
================================================================
"""

from typing import Union, Optional, Any
from collections.abc import Hashable
from pathlib import Path
import gc
import tqdm

from .arguments import MultiCommonparams
from ..experiment import ExperimentPrototype
from ..experiment.export import Export
from ..utils.iocontrol import IOComplex


def exporter(
    id_exec: Hashable,
    exps: ExperimentPrototype,
    save_location: Union[Path, str],
) -> tuple[Hashable, Export]:
    """Multiprocess exporter for experiment.

    Args:
        id_exec (Hashable): ID of experiment.
        exps (ExperimentPrototype): The experiment.
        save_location (Union[Path, str]): Location of saving experiment.

    Returns:
        tuple[Hashable, Export]: The ID of experiment and the export of experiment.
    """

    exps_export = exps.export(save_location=save_location)
    return id_exec, exps_export


def exporter_wrapper(
    args: tuple[Hashable, ExperimentPrototype, Union[Path, str]],
) -> tuple[Hashable, Export]:
    """Multiprocess exporter for experiment.

    Args:
        args (tuple[Hashable, ExperimentPrototype]): The arguments of multiprocess exporter.

    Returns:
        tuple[Hashable, Export]: The ID of experiment and the export of experiment.
    """
    return exporter(*args)


def writer(
    id_exec: Hashable,
    exps_export: Export,
    mode: str = "w+",
    indent: int = 2,
    encoding: str = "utf-8",
    jsonable: bool = False,
    mute: bool = True,
) -> tuple[Hashable, dict[str, str]]:
    """Multiprocess writer for experiment.

    Args:
        id_exec (Hashable): ID of experiment.
        exps_export (Export): The export of experiment.
        mode (str, optional): The mode of writing. Defaults to "w+".
        indent (int, optional): The indent of writing. Defaults to 2.
        encoding (str, optional): The encoding of writing. Defaults to "utf-8".
        jsonable (bool, optional): The jsonable of writing. Defaults to False.
        mute (bool, optional): The mute of writing. Defaults to True.

    Returns:
        tuple[Hashable, dict[str, str]]: The ID of experiment and the files of experiment.
    """

    qurryinfo_exp_id, qurryinfo_files = exps_export.write(
        mode=mode,
        indent=indent,
        encoding=encoding,
        jsonable=jsonable,
        mute=mute,
    )
    assert id_exec == qurryinfo_exp_id, (
        f"{id_exec} is not equal to {qurryinfo_exp_id}" + " which is not supported."
    )
    return qurryinfo_exp_id, qurryinfo_files


def writer_wrapper(
    args: tuple[Hashable, Export, str, int, str, bool, bool],
) -> tuple[Hashable, dict[str, str]]:
    """Multiprocess writer for experiment.

    Args:
        args (tuple[Hashable, Export, str, int, str, bool, bool]):
            The arguments of multiprocess writer.

    Returns:
        tuple[Hashable, dict[str, str]]: The ID of experiment and the files of experiment.
    """
    return writer(*args)


def multiprocess_exporter_and_writer(
    id_exec: str,
    exps: ExperimentPrototype,
    save_location: Union[Path, str],
    mode: str = "w+",
    indent: int = 2,
    encoding: str = "utf-8",
    jsonable: bool = False,
    mute: bool = True,
    export_transpiled_circuit: bool = False,
    _pbar: Optional[tqdm.tqdm] = None,
) -> tuple[str, dict[str, str]]:
    """Multiprocess exporter and writer for experiment.

    Args:
        id_exec (Hashable): ID of experiment.
        exps (ExperimentPrototype): The experiment.
        save_location (Union[Path, str]): Location of saving experiment.
        mode (str, optional): The mode of writing. Defaults to "w+".
        indent (int, optional): The indent of writing. Defaults to 2.
        encoding (str, optional): The encoding of writing. Defaults to "utf-8".
        jsonable (bool, optional): The jsonable of writing. Defaults to False.
        mute (bool, optional): The mute of writing. Defaults to True.
        export_transpiled_circuit (bool, optional):
            Export the transpiled circuit. Defaults to False.
        _pbar (Optional[tqdm.tqdm], optional): The progress bar. Defaults to None.

    Returns:
        tuple[Hashable, dict[str, str]]: The ID of experiment and the files of experiment.
    """
    exps_export = exps.export(
        save_location=save_location,
        export_transpiled_circuit=export_transpiled_circuit,
    )
    qurryinfo_exp_id, qurryinfo_files = exps_export.write(
        mode=mode,
        indent=indent,
        encoding=encoding,
        jsonable=jsonable,
        mute=mute,
        multiprocess=True,
        _pbar=_pbar,
    )
    assert id_exec == qurryinfo_exp_id, (
        f"{id_exec} is not equal to {qurryinfo_exp_id}" + " which is not supported."
    )
    del exps_export
    gc.collect()
    return qurryinfo_exp_id, qurryinfo_files


def datetimedict_process(
    multicommons: MultiCommonparams,
    naming_complex: IOComplex,
    multiconfig_name_v5: Path,
    multiconfig_name_v7: Path,
    is_read_or_retrieve: bool,
    read_from_tarfile: bool,
    old_files: dict[str, Any],
):
    """Process the datetime dict of multimanager.

    Args:
        multicommons (MultiCommonparams): The common parameters of multimanager.
        naming_complex (IOComplex): The complex of IO.
        multiconfig_name_v5 (Path): The path of multiConfig in v5.
        multiconfig_name_v7 (Path): The path of multiConfig in v7.
        is_read_or_retrieve (bool): Whether read or retrieve.
        read_from_tarfile (bool): Whether read from tarfile.
        old_files (dict[str, Any]): The old files.
    """

    if "build" not in multicommons.datetimes and not is_read_or_retrieve:
        multicommons.datetimes.add_only("build")

    if naming_complex.tarLocation.exists():
        if (not multiconfig_name_v5.exists()) and (not multiconfig_name_v7.exists()):
            multicommons.datetimes.add_serial("decompress")
        elif read_from_tarfile:
            multicommons.datetimes.add_serial("decompressOverwrite")

    # readV5 files re-export
    if multiconfig_name_v5.exists():
        multicommons.datetimes.add_only("readV7")
        for k in old_files.keys():
            multicommons.files.pop(k, None)
