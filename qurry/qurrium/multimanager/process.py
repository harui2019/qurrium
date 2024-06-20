"""
================================================================
Multiprocess component for multimanager
(:mod:`qurry.qurry.qurrium.multimanager.process`)
================================================================
"""
from pathlib import Path
from typing import Union, Hashable, Optional
import gc
import tqdm

from ..experiment import ExperimentPrototype
from ..experiment.export import Export


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
    id_exec: Hashable,
    exps: ExperimentPrototype,
    save_location: Union[Path, str],
    mode: str = "w+",
    indent: int = 2,
    encoding: str = "utf-8",
    jsonable: bool = False,
    mute: bool = True,
    export_transpiled_circuit: bool = False,
    _pbar: Optional[tqdm.tqdm] = None,
) -> tuple[Hashable, dict[str, str]]:
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
