"""
================================================================
MultiManager for Qurry (:mod:`qurry.qurrium.multimanager`)
================================================================

"""

import os
import gc
import shutil
import tarfile
import warnings

from pathlib import Path
from typing import Union, Optional, Hashable, Any
from uuid import uuid4, UUID

from .container import MultiCommonparams, Before, After
from .process import multiprocess_exporter_and_writer
from ..experiment import ExperimentPrototype
from ..container import ExperimentContainer, QuantityContainer
from ..utils.iocontrol import naming, RJUST_LEN
from ...tools import qurry_progressbar, current_time, DatetimeDict
from ...declare.multimanager import multicommonConfig
from ...capsule import quickJSON
from ...capsule.mori import TagList, GitSyncControl
from ...exceptions import (
    QurryProtectContent,
    QurryResetAccomplished,
    QurryResetSecurityActivated,
    QurryHashIDInvalid,
)


class MultiManager:
    """The manager of multiple experiments."""

    __name__ = "MultiManager"

    MultiCommonparams = MultiCommonparams
    Before = Before
    After = After

    def reset_afterwards(
        self,
        *args,
        security: bool = False,
        mute_warning: bool = False,
    ) -> None:
        """Reset the measurement and release memory for overwrite.

        Args:
            security (bool, optional): Security for reset. Defaults to `False`.
            muteWarning (bool, optional): Mute the warning message. Defaults to `False`.
        """

        if len(args) > 0:
            raise ValueError(f"{self.__name__} can't be reset with positional arguments.")

        if security and isinstance(security, bool):
            self.afterwards = self.afterwards._replace(retrievedResult=TagList(), allCounts={})
            gc.collect()
            if not mute_warning:
                warnings.warn("Afterwards reset accomplished.", QurryResetAccomplished)
        else:
            warnings.warn(
                "Reset does not execute to prevent executing accidentally, "
                + "if you are sure to do this, then use '.reset(security=True)'.",
                QurryResetSecurityActivated,
            )

    _unexports: list[str] = ["retrievedResult"]
    """The content would not be exported."""
    _syncPrevent = ["allCounts", "retrievedResult"]
    """The content would not be synchronized."""

    after_lock: bool = False
    """Protect the :cls:`afterward` content to be overwritten. 
    When setitem is called and completed, it will be setted as `False` automatically.
    """
    mute_auto_lock: bool = False
    """Whether mute the auto-lock message."""

    def unlock_afterward(self, mute_auto_lock: bool = False):
        """Unlock the :cls:`afterward` content to be overwritten.

        Args:
            mute_auto_lock (bool, optional):
                Mute anto-locked message for the unlock of this time. Defaults to False.
        """
        self.after_lock = True
        self.mute_auto_lock = mute_auto_lock

    def __setitem__(self, key, value) -> None:
        if key in self.Before._fields:
            self.beforewards = self.beforewards._replace(**{key: value})

        elif key in self.After._fields:
            if self.after_lock and isinstance(self.after_lock, bool):
                self.afterwards = self.afterwards._replace(**{key: value})
            else:
                raise QurryProtectContent(
                    f"Can't set value to :cls:`afterward` field {key} "
                    + "because it's locked, use `.unlock_afterward()` "
                    + "to unlock before setting item ."
                )

        else:
            raise ValueError(
                f"{key} is not a valid field of "
                + f"'{self.Before.__name__}' and '{self.After.__name__}'."
            )

        gc.collect()
        if self.after_lock is not False:
            self.after_lock = False
            if not self.mute_auto_lock:
                print(
                    "after_lock is locked automatically now, "
                    + "you can unlock by using `.unlock_afterward()` "
                    + "to set value to :cls:`afterward`."
                )
            self.mute_auto_lock = False

    def __getitem__(self, key) -> Any:
        if key in self.Before._fields:
            return getattr(self.beforewards, key)
        if key in self.After._fields:
            return getattr(self.afterwards, key)
        raise ValueError(
            f"{key} is not a valid field of '{self.Before.__name__}' and '{self.After.__name__}'."
        )

    # pylint: disable=invalid-name

    @property
    def summoner_id(self) -> str:
        """ID of experiment of the MultiManager."""
        return self.multicommons.summoner_id

    @property
    def summoner_name(self) -> str:
        """Name of experiment of the MultiManager."""
        return self.multicommons.summoner_name

    # pylint: enable=invalid-name

    quantity_container: QuantityContainer
    """The container of quantity."""

    def __init__(
        self,
        *args,
        summoner_id: Optional[str],
        summoner_name: str,
        save_location: Union[Path, str] = Path("./"),
        is_read: bool = False,
        encoding: str = "utf-8",
        read_from_tarfile: bool = False,
        **kwargs,
    ) -> None:
        """Initialize the multi-experiment.
        (The replacement of `QurryV4._multiDataGenOrRead` in V4 format.)

        Args:
            summoner_id (Hashable): ID of experiment of the MultiManager.
            summoner_name (str): Name of experiment of the MultiManager.
            save_location (Union[Path, str]): Location of saving experiment.
            is_read (bool, optional): Whether read the experiment. Defaults to False.
            encoding (str, optional): The encoding of json file. Defaults to "utf-8".
            read_from_tarfile (bool, optional): Whether read from tarfile. Defaults to False.
            filetype (TagList._availableFileType, optional):
                The filetype of json file. Defaults to "json".
            **kwargs (Any): The other arguments of multi-experiment.

        Raises:
            ValueError: Can't be initialized with positional arguments.
            FileNotFoundError: Can't find the multi.config file.
        """

        if len(args) > 0:
            raise ValueError(f"{self.__name__} can't be initialized with positional arguments.")
        try:
            if summoner_id is not None:
                UUID(summoner_id, version=4)
        except ValueError as e:
            summoner_id = None
            warnings.warn(
                f"summoner_id is not a valid UUID, it will be generated automatically.\n{e}",
                category=QurryHashIDInvalid,
            )
        finally:
            if summoner_id is None:
                summoner_id = "" if is_read else str(uuid4())
            else:
                ...

        self.gitignore = GitSyncControl()
        self.naming_complex = naming(
            is_read=is_read,
            exps_name=summoner_name,
            save_location=save_location,
        )

        is_tarfile_existed = os.path.exists(self.naming_complex.tarLocation)
        multiconfig_name_v5 = (
            self.naming_complex.export_location / f"{self.naming_complex.expsName}.multiConfig.json"
        )
        multiconfig_name_v7 = self.naming_complex.export_location / "multi.config.json"
        old_files: dict[str, Union[str, dict[str, str]]] = {}

        if is_tarfile_existed:
            print(
                f"| Found the tarfile '{self.naming_complex.tarName}' "
                + f"in '{self.naming_complex.save_location}', decompressing is available."
            )
            if (not multiconfig_name_v5.exists()) and (not multiconfig_name_v7.exists()):
                print(
                    "| No multi.config file found, "
                    + f"decompressing all files in the tarfile '{self.naming_complex.tarName}'."
                )
                self.easydecompress()
            elif read_from_tarfile:
                print(
                    f"| Decompressing all files in the tarfile '{self.naming_complex.tarName}'"
                    + f", replace all files in '{self.naming_complex.export_location}'."
                )
                self.easydecompress()

        if is_read:
            if multiconfig_name_v5.exists():
                print("| Found the multiConfig.json, reading in 'v5' file structure.")
                rawread_multiconfig = self.MultiCommonparams._read_as_dict(
                    mutlticonfig_name=multiconfig_name_v5,
                    save_location=self.naming_complex.save_location,
                    export_location=self.naming_complex.export_location,
                    encoding=encoding,
                )
                files = rawread_multiconfig["files"]
                old_files = rawread_multiconfig["files"].copy()

                self.beforewards = self.Before._read(
                    export_location=self.naming_complex.export_location,
                    file_location=files,
                    version="v5",
                )
                self.afterwards = self.After._read(
                    export_location=self.naming_complex.export_location,
                    file_location=files,
                    version="v5",
                )
                self.quantity_container = QuantityContainer()
                for qk in files["tagMapQuantity"].keys():
                    self.quantity_container.read(
                        key=qk,
                        save_location=self.naming_complex.export_location,
                        taglist_name="tagMapQuantity",
                        name=f"{self.naming_complex.expsName}.{qk}",
                    )

            elif multiconfig_name_v7.exists():
                rawread_multiconfig = self.MultiCommonparams._read_as_dict(
                    mutlticonfig_name=multiconfig_name_v7,
                    save_location=self.naming_complex.save_location,
                    export_location=self.naming_complex.export_location,
                    encoding=encoding,
                )
                files = rawread_multiconfig["files"]

                self.beforewards = self.Before._read(
                    export_location=self.naming_complex.export_location, version="v7"
                )
                self.afterwards = self.After._read(
                    export_location=self.naming_complex.export_location, version="v7"
                )
                self.quantity_container = QuantityContainer()
                for qk in files["quantity"].keys():
                    self.quantity_container.read(
                        key=qk,
                        save_location=self.naming_complex.export_location,
                        taglist_name="quantity",
                        name=f"{qk}",
                    )
            else:
                print(f"| v5: {multiconfig_name_v5}")
                print(f"| v7: {multiconfig_name_v7}")
                raise FileNotFoundError(
                    f"Can't find the multi.config file in '{self.naming_complex.expsName}'."
                )

        else:
            files = {}
            rawread_multiconfig = {
                "tags": [],
                **kwargs,
                "summoner_id": summoner_id,
                "summoner_name": self.naming_complex.expsName,
                "save_location": self.naming_complex.save_location,
                "export_location": self.naming_complex.export_location,
            }
            self.beforewards = self.Before(
                exps_config={},
                circuits_num={},
                circuits_map=TagList(),
                pending_pool=TagList(),
                job_id=[],
                job_taglist=TagList(),
                files_taglist=TagList(),
                index_taglist=TagList(),
            )
            self.afterwards = self.After(
                retrievedResult=TagList(),
                allCounts={},
            )
            self.quantity_container = QuantityContainer()

        # multicommon prepare
        multicommons = multicommonConfig.make()
        outfields = {}
        for k in rawread_multiconfig:
            if k in self.MultiCommonparams._fields:
                multicommons[k] = rawread_multiconfig[k]
            elif k == "outfields":
                outfields = {**rawread_multiconfig[k]}
            else:
                outfields[k] = rawread_multiconfig[k]

        # datetimes
        if "datetimes" not in multicommons:
            multicommons["datetimes"] = DatetimeDict()
        else:
            multicommons["datetimes"] = DatetimeDict(**multicommons["datetimes"])

        if "build" not in multicommons["datetimes"] and not is_read:
            multicommons["datetimes"]["bulid"] = current_time()

        if is_tarfile_existed:
            if (not multiconfig_name_v5.exists()) and (not multiconfig_name_v7.exists()):
                multicommons["datetimes"].add_serial("decompress")
            elif read_from_tarfile:
                multicommons["datetimes"].add_serial("decompressOverwrite")

        # readV5 files re-export
        if multiconfig_name_v5.exists():
            multicommons["datetimes"]["v7Read"] = current_time()
            for k, pathstr in old_files.items():
                multicommons["files"].pop(k, None)

        self.multicommons = self.MultiCommonparams(**multicommons)
        self.outfields: dict[str, Any] = outfields
        assert (
            self.naming_complex.save_location == self.multicommons.save_location
        ), "| save_location is not consistent with namingCpx.save_location."

        # readV5 files re-export
        if multiconfig_name_v5.exists():
            print(
                f"| {self.naming_complex.expsName} auto-export "
                + 'in "v7" format and remove "v5" format.'
            )
            self.write()
            remove_v5_progress = qurry_progressbar(
                old_files.items(),
                bar_format="| {percentage:3.0f}%[{bar}] - remove v5 - {desc} - {elapsed}",
            )
            for k, pathstr in remove_v5_progress:
                if isinstance(pathstr, str):
                    remove_v5_progress.set_description_str(f"{k}")
                    path = Path(pathstr)
                    if path.exists():
                        path.unlink()
                elif isinstance(pathstr, dict):
                    for k2, pathstr2 in pathstr.items():
                        remove_v5_progress.set_description_str(f"{k} - {k2}")
                        path = Path(pathstr2)
                        if path.exists():
                            path.unlink()

    def register(
        self,
        current_id: str,
        config: dict[str, Any],
        exps_instance: ExperimentPrototype,
    ):
        """Register the experiment to multimanager.

        Args:
            current_id (str): ID of experiment.
            config (dict[str, Any]): The config of experiment.
            exps_instance (ExperimentPrototype): The instance of experiment.
        """

        assert exps_instance.commons.exp_id == current_id, (
            f"ID is not consistent, exp_id: {exps_instance.commons.exp_id} and "
            + f"current_id: {current_id}."
        )
        self.beforewards.exps_config[current_id] = config
        self.beforewards.circuits_num[current_id] = len(exps_instance.beforewards.circuit)
        self.beforewards.job_taglist[exps_instance.commons.tags].append(current_id)
        assert isinstance(exps_instance.commons.serial, int), (
            f"Serial is not int, exp_id: {exps_instance.commons.exp_id} and "
            + f"serial: {exps_instance.commons.serial}."
            + "It should be int."
        )
        self.beforewards.index_taglist[exps_instance.commons.tags].append(
            exps_instance.commons.serial
        )

    def update_save_location(
        self,
        save_location: Union[Path, str],
        without_serial: bool = True,
    ) -> dict[str, Any]:
        """Update the save location of the multi-experiment.

        Args:
            save_location (Union[Path, str]): Location of saving experiment.
            without_serial (bool, optional): Whether without serial number. Defaults to True.

        Returns:
            dict[str, Any]: The dict of multiConfig.
        """
        save_location = Path(save_location)
        self.naming_complex = naming(
            without_serial=without_serial,
            exps_name=self.multicommons.summoner_name,
            save_location=save_location,
        )
        self.multicommons = self.multicommons._replace(
            save_location=self.naming_complex.save_location,
            export_location=self.naming_complex.export_location,
        )

        return self.naming_complex._asdict()

    def _write_multiconfig(
        self,
        encoding: str = "utf-8",
        mute: bool = True,
    ) -> dict[str, Any]:
        multiconfig_name = Path(self.multicommons.export_location) / "multi.config.json"
        self.multicommons.files["multi.config"] = str(multiconfig_name)
        self.gitignore.sync("multi.config.json")
        multiconfig = {
            **self.multicommons._asdict(),
            "outfields": self.outfields,
            "files": self.multicommons.files,
        }
        quickJSON(
            content=multiconfig,
            filename=multiconfig_name,
            mode="w+",
            jsonable=True,
            encoding=encoding,
            mute=mute,
        )

        return multiconfig

    def write(
        self,
        save_location: Optional[Union[Path, str]] = None,
        exps_container: Optional[ExperimentContainer] = None,
        indent: int = 2,
        encoding: str = "utf-8",
        export_transpiled_circuit: bool = False,
        _only_quantity: bool = False,
    ) -> dict[str, Any]:
        """Export the multi-experiment.

        Args:
            save_location (Union[Path, str], optional): Location of saving experiment.
                Defaults to None.
            wave_container (Optional[ExperimentContainer], optional): The container of experiments.
                Defaults to None.
            indent (int, optional): The indent of json file. Defaults to 2.
            encoding (str, optional): The encoding of json file. Defaults to "utf-8".
            export_transpiled_circuit (bool, optional):
                Export the transpiled circuit. Defaults to False.
            _only_quantity (bool, optional): Whether only export quantity. Defaults to False.

        Returns:
            dict[str, Any]: The dict of multiConfig.
        """
        self.gitignore.read(self.multicommons.export_location)
        print("| Export multimanager...")
        if save_location is None:
            save_location = self.multicommons.save_location
        else:
            self.update_save_location(save_location=save_location, without_serial=True)

        self.gitignore.ignore("*.json")
        self.gitignore.sync("qurryinfo.json")
        if not os.path.exists(save_location):
            os.makedirs(save_location)
        if not os.path.exists(self.multicommons.export_location):
            os.makedirs(self.multicommons.export_location)
        self.gitignore.export(self.multicommons.export_location)

        exporting_name = {
            **self.After.exporting_name(),
            **self.Before.exporting_name(),
        }

        export_progress = qurry_progressbar(
            [
                fname
                for fname in self.Before._fields
                if fname != "files_taglist" or exps_container is None
            ]
            + list(self.After._fields),
            desc="exporting",
            bar_format="qurry-barless",
        )

        # beforewards amd afterwards
        for i, k in enumerate(export_progress):
            if _only_quantity or (k in self._unexports):
                export_progress.set_description_str(f"{k} as {exporting_name[k]} - skip")
            elif isinstance(self[k], TagList):
                export_progress.set_description_str(f"{k} as {exporting_name[k]}")
                tmp: TagList = self[k]
                filename = tmp.export(
                    save_location=self.multicommons.export_location,
                    taglist_name=f"{exporting_name[k]}",
                    filetype=self.multicommons.filetype,
                    open_args={
                        "mode": "w+",
                        "encoding": encoding,
                    },
                    json_dump_args={
                        "indent": indent,
                    },
                )
                self.multicommons.files[exporting_name[k]] = str(filename)
                self.gitignore.sync(f"{exporting_name[k]}.{self.multicommons.filetype}")

            elif isinstance(self[k], (dict, list)):
                export_progress.set_description_str(f"{k} as {exporting_name[k]}")
                filename = Path(self.multicommons.export_location) / f"{exporting_name[k]}.json"
                self.multicommons.files[exporting_name[k]] = str(filename)
                if k not in self._syncPrevent:
                    self.gitignore.sync(f"{exporting_name[k]}.json")
                quickJSON(
                    content=self[k],
                    filename=filename,
                    mode="w+",
                    jsonable=True,
                    indent=indent,
                    encoding=encoding,
                    mute=True,
                )

            else:
                warnings.warn(f"'{k}' is type '{type(self[k])}' which is not supported to export.")

            if i == len(export_progress) - 1:
                export_progress.set_description_str("exporting done")

        # tagMapQuantity or quantity
        self.multicommons.files["quantity"] = self.quantity_container.write(
            save_location=self.multicommons.export_location,
            filetype=self.multicommons.filetype,
            indent=indent,
            encoding=encoding,
        )
        self.gitignore.sync(f"*.quantity.{self.multicommons.filetype}")
        # multiConfig
        multiconfig = self._write_multiconfig(encoding=encoding, mute=True)
        print(f"| Export multi.config.json for {self.summoner_id}")

        self.gitignore.export(self.multicommons.export_location)

        if exps_container is not None:
            # pool = ProcessManager(6)
            all_qurryinfo_loc = self.multicommons.export_location / "qurryinfo.json"

            # all_qurryinfo_items = pool.process_map(
            #     multiprocess_exporter_and_writer_wrapper,
            #     [
            #         (
            #             id_exec,
            #             exps_container[id_exec],
            #             self.multicommons.save_location,
            #             "w+",
            #             indent,
            #             encoding,
            #             True,
            #             True,
            #         )
            #         for id_exec in self.beforewards.exps_config
            #     ],
            #     desc="Exporting and writring...",
            # )
            exps_export_progress = qurry_progressbar(
                self.beforewards.exps_config,
                desc="Exporting and writring...",
                bar_format="qurry-barless",
            )
            all_qurryinfo = {}
            for id_exec in exps_export_progress:
                tmp_id, tmp_qurryinfo = multiprocess_exporter_and_writer(
                    id_exec=id_exec,
                    exps=exps_container[id_exec],
                    save_location=self.multicommons.save_location,
                    mode="w+",
                    indent=indent,
                    encoding=encoding,
                    jsonable=True,
                    mute=True,
                    export_transpiled_circuit=export_transpiled_circuit,
                    _pbar=None,
                )
                assert id_exec == tmp_id, "ID is not consistent."
                all_qurryinfo[id_exec] = tmp_qurryinfo

            # for id_exec, files in all_qurryinfo_items:
            for id_exec, files in all_qurryinfo.items():
                self.beforewards.files_taglist[exps_container[id_exec].commons.tags].append(files)
            self.beforewards.files_taglist.export(
                save_location=self.multicommons.export_location,
                taglist_name=f"{exporting_name['files_taglist']}",
                filetype=self.multicommons.filetype,
                open_args={
                    "mode": "w+",
                    "encoding": encoding,
                },
                json_dump_args={
                    "indent": indent,
                },
            )

            # all_qurryinfo = dict(all_qurryinfo_items)

            quickJSON(
                content=all_qurryinfo,
                filename=all_qurryinfo_loc,
                mode="w+",
                jsonable=True,
                indent=indent,
                encoding=encoding,
                mute=True,
            )

        gc.collect()
        return multiconfig

    def compress(
        self,
        compress_overwrite: bool = False,
        remain_only_compressed: bool = False,
    ) -> Path:
        """Compress the export_location to tar.xz.

        Args:
            compress_overwrite (bool, optional):
                Reproduce all the compressed files. Defaults to False.
            remain_only_compressed (bool, optional):
                Remove uncompressed files. Defaults to False.

        Returns:
            Path: Path of the compressed file.
        """

        if remain_only_compressed:
            self.multicommons.datetimes.add_serial("uncompressedRemove")
        _multiconfig = self._write_multiconfig()

        print(f"| Compress multimanager of '{self.naming_complex.expsName}'...", end="\r")
        loc = self.easycompress(overwrite=compress_overwrite)
        print(f"| Compress multimanager of '{self.naming_complex.expsName}'...done")

        if remain_only_compressed:
            print(
                f"| Remove uncompressed files in '{self.naming_complex.export_location}' ...",
                end="\r",
            )
            shutil.rmtree(self.multicommons.export_location)
            print(f"| Remove uncompressed files in '{self.naming_complex.export_location}' ...done")

        return loc

    def analyze(
        self,
        wave_continer: ExperimentContainer,
        analysis_name: str = "report",
        no_serialize: bool = False,
        specific_analysis_args: Optional[dict[Hashable, Union[dict[str, Any], bool]]] = None,
        **analysis_args: Any,
    ) -> str:
        """Run the analysis for multiple experiments.

        Args:
            analysisName (str, optional):
                The name of the analysis.
                Defaults to 'report'.
            specificAnalysisArgs (dict[Hashable, dict[str, Any]], optional):
                Specific some experiment to run the analysis arguments for each experiment.
                Defaults to {}.

        Raises:
            ValueError: No positional arguments allowed except `summoner_id`.
            ValueError: summoner_id not in multimanagers.
            ValueError: No counts in multimanagers, which experiments are not ready.

        Returns:
            Hashable: SummonerID (ID of multimanager).
        """
        if specific_analysis_args is None:
            specific_analysis_args = {}

        if len(self.afterwards.allCounts) == 0:
            raise ValueError("No counts in multimanagers.")

        idx_tagmap_quantities = len(self.quantity_container)
        name = (
            analysis_name
            if no_serialize
            else f"{analysis_name}." + f"{idx_tagmap_quantities+1}".rjust(RJUST_LEN, "0")
        )
        self.quantity_container[name] = TagList()

        all_counts_progress = qurry_progressbar(
            self.afterwards.allCounts.keys(),
            bar_format=("| {n_fmt}/{total_fmt} - Analysis: {desc} - {elapsed} < {remaining}"),
        )
        for k in all_counts_progress:
            tqdm_handleable = wave_continer[k].tqdm_handleable

            if k in specific_analysis_args:
                v_args = specific_analysis_args[k]
                if isinstance(v_args, bool):
                    if v_args is False:
                        all_counts_progress.set_description_str(
                            f"Skipped {k} in {self.summoner_id}."
                        )
                        continue
                    report = wave_continer[k].analyze(
                        **analysis_args,
                        **({"pbar": all_counts_progress} if tqdm_handleable else {}),
                    )
                else:
                    report = wave_continer[k].analyze(
                        **v_args,
                        **({"pbar": all_counts_progress} if tqdm_handleable else {}),
                    )
            else:
                report = wave_continer[k].analyze(
                    **analysis_args,
                    **({"pbar": all_counts_progress} if tqdm_handleable else {}),
                )

            wave_continer[k].write()
            main, _tales = report.export()
            self.quantity_container[name][wave_continer[k].commons.tags].append(main)

        self.multicommons.datetimes.add_only(name)

        return name

    def remove_analysis(self, name: str):
        """Removes the analysis.

        Args:
            name (str): The name of the analysis.
        """
        self.quantity_container.remove(name)
        print(f"| Removing analysis: {name}")
        self.multicommons.datetimes.add_only(f"{name}_remove")

    def easycompress(
        self,
        overwrite: bool = False,
    ) -> Path:
        """Compress the export_location to tar.xz.

        Args:
            overwrite (bool, optional): Reproduce all the compressed files. Defaults to False.

        Returns:
            Path: Path of the compressed file.
        """

        self.multicommons.datetimes.add_serial("compressed")
        _multiconfig = self._write_multiconfig()

        is_exists = os.path.exists(self.naming_complex.tarLocation)
        if is_exists and overwrite:
            os.remove(self.naming_complex.tarLocation)
            with tarfile.open(self.naming_complex.tarLocation, "x:xz") as tar:
                tar.add(
                    self.naming_complex.export_location,
                    arcname=os.path.basename(self.naming_complex.export_location),
                )

        else:
            with tarfile.open(self.naming_complex.tarLocation, "w:xz") as tar:
                tar.add(
                    self.naming_complex.export_location,
                    arcname=os.path.basename(self.naming_complex.export_location),
                )

        return self.naming_complex.tarLocation

    def easydecompress(self) -> Path:
        """Decompress the tar.xz file of experiment.

        Returns:
            Path: Path of the decompressed file.
        """

        with tarfile.open(self.naming_complex.tarLocation, "r:xz") as tar:
            tar.extractall(self.naming_complex.save_location)

        return self.naming_complex.tarLocation

    @property
    def name(self) -> Hashable:
        """Name of experiment of the MultiManager."""
        return self.multicommons.summoner_name
