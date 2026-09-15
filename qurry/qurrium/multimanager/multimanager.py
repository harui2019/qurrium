"""MultiManager - The manager of multiple experiments.
(:mod:`qurry.qurrium.multimanager.multimanager`)"""

import os
import warnings
from pathlib import Path
from typing import Any, Generic
from uuid import uuid4
from dataclasses import replace

from qiskit.providers import Backend

from .arguments import MultiCommonparams, PendingStrategyLiteral, PendingTargetProviderLiteral
from .beforewards import Before, STANDARD_FILE_INDEX
from .exps_container import ExperimentContainer, _E, experiment_writer
from .multiquantity import MutltiQuantityInfo
from ..analysis import AnalyzeArgs, SpecificAnalyzeArgs, AnalysisPrototype, _RA
from ..container import BaseRunArgs
from ..experiment import QurryInfo
from ..utils import folder_naming, ExportFolderNaming
from ..exceptions import ResetAccomplished, ResetSecurityActivated
from ...tools import (
    qurry_progressbar,
    GeneralSimulator,
    DatetimeDict,
    DEFAULT_POOL_SIZE,
    make_multiprocess_pool,
    very_easy_chunk_size,
)
from ...capsule import (
    quick_json_write,
    DEFAULT_ENCODING,
    DEFAULT_MODE,
    GitSyncControl,
    DEFAULT_INDENT,
)


class MultiManager(Generic[_E]):
    """The manager of multiple experiments."""

    multicommons: MultiCommonparams
    """The common parameters of multi-experiment."""
    beforewards: Before
    """The beforewards of multi-experiment."""

    exps: ExperimentContainer[_E]
    """The experiments container."""

    quantity_info: MutltiQuantityInfo
    """The quantity information among multiple experiments."""

    qurryinfo: QurryInfo
    """The qurryinfo of the multi-experiment.

    This is a dictionary with experiment IDs as keys,
    and the values are dictionaries containing the exported information.
    """

    def clear_all_exps_result(
        self,
        *args,
        security: bool = False,
        mute_warning: bool = False,
    ) -> None:
        """Clear the result of all experiments.

        Args:
            security (bool, optional): Security for clearing. Defaults to `False`.
            mute_warning (bool, optional): Mute the warning when clearing. Defaults to `False`.
        """
        if len(args) > 0:
            raise ValueError("Use '.clear_all_exps_result(security=True)' to clear all results.")

        if security and isinstance(security, bool):
            for exp in qurry_progressbar(
                self.exps.values(),
                desc="Clear jobs result...",
                bar_format="qurry-barless",
            ):
                exp.afterwards.clear_result(security=security, mute_warning=True)
            if not mute_warning:
                warnings.warn(
                    "All experiments' results are cleared.",
                    ResetAccomplished,
                )
        else:
            warnings.warn(
                "Reset does not execute to prevent executing accidentally, "
                + "if you are sure to do this, then use '.reset(security=True)'.",
                ResetSecurityActivated,
            )

    @property
    def summoner_id(self) -> str:
        """ID of experiment of the MultiManager."""
        return self.multicommons.summoner_id

    @property
    def id(self) -> str:
        """ID of experiment of the MultiManager."""
        return self.multicommons.summoner_id

    def __hash__(self):
        """Hash the MultiManager by its ID."""
        return hash(self.multicommons.summoner_id)

    @property
    def summoner_name(self) -> str:
        """Name of experiment of the MultiManager."""
        return self.multicommons.summoner_name

    @property
    def name(self) -> str:
        """Name of experiment of the MultiManager."""
        return self.multicommons.summoner_name

    def __init__(
        self,
        naming_complex: ExportFolderNaming,
        multicommons: MultiCommonparams,
        beforewards: Before,
        quantity_info: MutltiQuantityInfo,
        outfields: dict[str, Any],
        gitignore: GitSyncControl | list[str] | None = None,
    ):
        """Initialize the multi-experiment."""

        if gitignore is None:
            self.gitignore = GitSyncControl()
        elif isinstance(gitignore, list):
            self.gitignore = GitSyncControl(gitignore)
        elif isinstance(gitignore, GitSyncControl):
            self.gitignore = gitignore
        else:
            raise ValueError(f"gitignore must be list or GitSyncControl, not {type(gitignore)}.")

        self.exps = ExperimentContainer()
        self.qurryinfo = QurryInfo()
        self.quantity_info = quantity_info

        self.naming_complex = naming_complex
        self.multicommons = multicommons
        self.beforewards = beforewards
        self.outfields = outfields

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            + f'id="{self.multicommons.summoner_id}", '
            + f'name="{self.multicommons.summoner_name}", '
            + f"tags={self.multicommons.tags}, "
            + f'jobstype="{self.multicommons.jobstype}", '
            + f'pending_strategy="{self.multicommons.pending_strategy}", '
            + f"available_reports={list(self.quantity_info.keys())}, "
            + f"events={self.multicommons.datetimes}, "
            + f"exps_num={len(self.beforewards.exps_config)})>"
        )

    def _repr_oneline(self):
        return (
            f"<{self.__class__.__name__}("
            + f'id="{self.multicommons.summoner_id}", '
            + f'name="{self.multicommons.summoner_name}", '
            + f'jobstype="{self.multicommons.jobstype}", ..., '
            + f"exps_num={len(self.beforewards.exps_config)})>"
        )

    def _repr_oneline_no_id(self):
        return (
            f"<{self.__class__.__name__}("
            + f'name="{self.multicommons.summoner_name}", '
            + f'jobstype="{self.multicommons.jobstype}", ..., '
            + f"exps_num={len(self.beforewards.exps_config)})>"
        )

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(self._repr_oneline())
            return

        basic_info = {
            "id": self.multicommons.summoner_id,
            "name": self.multicommons.summoner_name,
            "tags": self.multicommons.tags,
            "jobstype": self.multicommons.jobstype,
            "pending_strategy": self.multicommons.pending_strategy,
            "available_reports": list(self.quantity_info.keys()),
            "events": self.multicommons.datetimes,
            "exps_num": len(self.beforewards.exps_config),
        }
        with p.group(DEFAULT_INDENT, f"<{self.__class__.__name__}(", ")>"):
            for i, (k, v) in enumerate(basic_info.items()):
                p.breakable()
                p.text(f"{k}=")
                p.pretty(v)
                if i != len(basic_info) - 1:
                    p.text(",")

    def register(self, current_id: str, config: dict[str, Any], exps_instance: _E) -> None:
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
        assert isinstance(exps_instance.commons.serial, int), (
            f"Serial is not int, exp_id: {exps_instance.commons.exp_id} and "
            + f"serial: {exps_instance.commons.serial}."
            + "It should be ensured when building the experiment."
        )
        self.beforewards.exps_config[current_id] = config
        self.exps[current_id] = exps_instance
        if isinstance(exps_instance.commons.tags, tuple) and len(exps_instance.commons.tags) > 0:
            if exps_instance.commons.tags not in self.beforewards.job_group:
                self.beforewards.job_group[exps_instance.commons.tags] = []
            self.beforewards.job_group[exps_instance.commons.tags].append(current_id)

    @classmethod
    def build(
        cls,
        config_list: list[dict[str, Any]],
        experiment_instance: type[_E],
        summoner_name: str | None = None,
        shots: int | None = None,
        backend: Backend = GeneralSimulator(),
        tags: tuple[str, ...] | None = None,
        manager_run_args: BaseRunArgs | dict[str, Any] | None = None,
        jobstype: PendingTargetProviderLiteral = "local",
        pending_strategy: PendingStrategyLiteral = "tags",
        # save parameters
        save_location: Path | str = Path("./"),
        skip_writing: bool = False,
        multiprocess_build: bool = False,
        multiprocess_write: bool = False,
    ) -> "MultiManager[_E]":
        """Build the multi-experiment.

        Args:
            config_list (list[dict[str, Any]]):
                The list of config of experiments.
                This config is used to build the experiments.
            experiment_instance (ExperimentPrototype):
                The instance of experiment.
            summoner_name (str | None, optional):
                Name of experiment of the :class:`MultiManager`. Defaults to None.
            shots (int | None, optional):
                The shots of experiments. Defaults to None.
            backend (Backend, optional):
                The backend of experiments. Defaults to GeneralSimulator().
            tags (tuple[str, ...] | None, optional):
                The tags of experiments. Defaults to None.
            manager_run_args (BaseRunArgs | dict[str, Any] | None, optional):
                The arguments of manager run. Defaults to None.
            jobstype (PendingTargetProviderLiteral, optional):
                The jobstype of experiments. Defaults to "local".
            pending_strategy (PendingStrategyLiteral, optional):
                The pending strategy of experiments. Defaults to "tags".
            save_location (Path | str, optional):
                Location of saving experiment. Defaults to Path("./").
            skip_writing (bool, optional):
                Whether skip writing. Defaults to False.
            multiprocess_build (bool, optional):
                Whether use multiprocess for building. Defaults to False.
            multiprocess_write (bool, optional):
                Whether use multiprocess for writing. Defaults to False.

        Returns:
            MultiManager: The container of experiments and multi-experiment.
        """

        if summoner_name is None:
            summoner_name = "multiexps"
        if tags is None:
            tags = ()
        if manager_run_args is None:
            manager_run_args = {}

        naming_complex = folder_naming(
            exp_or_summoner_name=summoner_name,
            save_location=save_location,
        )

        multicommons, outfields = MultiCommonparams.create(
            {
                "summoner_id": str(uuid4()),
                "summoner_name": naming_complex.summoner_name,
                "tags": tags,
                "shots": shots,
                "backend": backend,
                "save_location": naming_complex.save_location,
                "export_location": naming_complex.export_location,
                "files": {},
                "jobstype": jobstype,
                "pending_strategy": pending_strategy,
                "manager_run_args": manager_run_args,
                "filetype": "json",
                "datetimes": DatetimeDict(),
                "outfields": {},
            }
        )

        assert naming_complex.save_location == multicommons.save_location, (
            "| save_location is not consistent with namingCpx.save_location."
        )

        current_multimanager = cls(
            naming_complex=naming_complex,
            multicommons=multicommons,
            beforewards=Before(
                exps_config={},
                circuits_map={},
                pending_pool={},
                job_group={},
            ),
            quantity_info=MutltiQuantityInfo(),
            outfields=outfields,
        )

        initial_config_list: list[dict[str, Any]] = []
        for serial, config in enumerate(config_list):
            config.pop("export", None)
            config.pop("pbar", None)
            config.pop("multiprocess", None)
            initial_config_list.append(
                {
                    **config,
                    "shots": config.get("shots", shots),
                    "backend": backend,
                    "exp_name": current_multimanager.multicommons.summoner_name,
                    "save_location": current_multimanager.multicommons.save_location,
                    "serial": serial,
                    "summoner_id": current_multimanager.multicommons.summoner_id,
                    "summoner_name": current_multimanager.multicommons.summoner_name,
                }
            )

        if multiprocess_build:
            chunks_num = very_easy_chunk_size(
                tasks_num=len(initial_config_list),
                num_process=DEFAULT_POOL_SIZE,
                max_chunk_size=min(max(1, len(initial_config_list) // DEFAULT_POOL_SIZE), 20),
            )

            with make_multiprocess_pool(maxtasksperchild=4) as p:
                exps_iterable = qurry_progressbar(
                    p.imap_unordered(
                        experiment_instance.build_for_multiprocess,
                        initial_config_list,
                        chunksize=chunks_num,
                    ),
                    total=len(initial_config_list),
                    desc="MultiManager building...",
                )
                exps_iterable.set_description_str(
                    f"Loading {len(initial_config_list)} experiments..."
                )
                for new_exps, config in exps_iterable:
                    current_multimanager.register(
                        current_id=new_exps.commons.exp_id,
                        config=config,
                        exps_instance=new_exps,
                    )
                exps_iterable.set_description_str(
                    f"Loading {len(initial_config_list)} experiments done"
                )

        else:
            exps_iterable = qurry_progressbar(
                (
                    (experiment_instance.build(multiprocess=True, **config), config)
                    for config in initial_config_list
                ),
                total=len(initial_config_list),
                desc="MultiManager building...",
            )
            for new_exps, config in exps_iterable:
                current_multimanager.register(
                    current_id=new_exps.commons.exp_id,
                    config=config,
                    exps_instance=new_exps,
                )

        if not skip_writing:
            current_multimanager.write(multiprocess=multiprocess_write)

        return current_multimanager

    @classmethod
    def read(
        cls,
        summoner_name: str,
        experiment_instance: type[_E],
        save_location: Path | str = Path("./"),
        is_read_or_retrieve: bool = False,
        multiprocess: bool = True,
    ) -> "MultiManager[_E]":
        """Read the multi-experiment.

        Args:
            experiment_instance (type[ExperimentPrototype]):
                The instance of experiment.
            summoner_name (str | None, optional):
                Name of experiment of the :class:`MultiManager`. Defaults to None.
            save_location (Path | str, optional):
                Location of saving experiment. Defaults to Path("./").
            is_read_or_retrieve (bool, optional):
                Whether read or retrieve. Defaults to False.
            multiprocess (bool, optional):
                Whether use multiprocess for reading. Defaults to True.

        Returns:
            MultiManager: The container of experiments and multi-experiment.
        """
        naming_complex = folder_naming(
            is_read=is_read_or_retrieve,
            exp_or_summoner_name=summoner_name,
            save_location=save_location,
        )
        gitignore = GitSyncControl()
        gitignore.load(naming_complex.export_location)

        multicommons, outfields = MultiCommonparams.read(
            file_index={"multi.config": "multi.config.json"},
            save_location=naming_complex.save_location,
            export_location=naming_complex.export_location,
        )
        assert naming_complex.save_location == multicommons.save_location, (
            "| save_location is not consistent with namingCpx.save_location."
        )
        beforewards = Before.read(file_index=multicommons.files)
        quantity_info = MutltiQuantityInfo.read(file_index=multicommons.files)

        current_multimanager = cls(
            naming_complex=naming_complex,
            multicommons=multicommons,
            beforewards=beforewards,
            quantity_info=quantity_info,
            outfields=outfields,
            gitignore=gitignore,
        )

        reading_results: list[_E] = experiment_instance.read(
            save_location=current_multimanager.multicommons.save_location,
            exp_or_summoner_name=current_multimanager.multicommons.summoner_name,
            multiprocess=multiprocess,
        )
        current_multimanager.exps.update({exp.commons.exp_id: exp for exp in reading_results})
        current_multimanager.qurryinfo.update_qurryinfo(
            QurryInfo.read(
                save_location=current_multimanager.multicommons.export_location,
            )
        )

        return current_multimanager

    def update_save_location(self, save_location: Path | str, without_serial: bool = True):
        """Update the save location of the multi-experiment.

        Args:
            save_location (Path | str): Location of saving experiment.
            without_serial (bool, optional): Whether without serial number. Defaults to True.
        """
        save_location = Path(save_location)
        self.naming_complex = folder_naming(
            without_serial=without_serial,
            exp_or_summoner_name=self.multicommons.summoner_name,
            save_location=save_location,
        )
        self.multicommons = replace(
            self.multicommons,
            save_location=self.naming_complex.save_location,
            export_location=self.naming_complex.export_location,
        )

    def write(
        self,
        save_location: Path | str | None = None,
        export_transpiled_circuit: bool = False,
        skip_exps: bool = False,
        skip_quantities: bool = False,
        multiprocess: bool = False,
    ) -> dict[str, Any]:
        """Export the multi-experiment.

        Args:
            save_location (Path | str | None, optional): Location of saving experiment.
                Defaults to None.
            skip_manager_info (bool, optional):
                Skip the multimanager info. Defaults to False.
            skip_exps (bool, optional):
                Skip the experiments. Defaults to False.
            skip_quantities (bool, optional):
                Skip the quantities container. Defaults to False.
            multiprocess (bool, optional):
                Whether to use multiprocess for exporting. Defaults to False.

        Returns:
            dict[str, Any]: The dict of multiConfig.
        """
        if save_location is not None:
            self.update_save_location(save_location=save_location)
        save_location = self.multicommons.save_location

        self.gitignore.ignore("*.json")
        self.gitignore.sync("qurryinfo.json")
        if not os.path.exists(save_location):
            os.makedirs(save_location)
        if not os.path.exists(self.multicommons.export_location):
            os.makedirs(self.multicommons.export_location)
        self.gitignore.export(self.multicommons.export_location)

        # beforewards
        beforewards_index = self.beforewards.write(
            save_location=self.multicommons.export_location,
        )
        self.multicommons.files.update(beforewards_index)
        for file in STANDARD_FILE_INDEX.values():
            self.gitignore.sync(file)

        # quantities
        if not skip_quantities:
            quantities_index = self.quantity_info.write(
                save_location=self.multicommons.export_location
            )
            self.multicommons.files.update(quantities_index)
            self.gitignore.sync("multiquantity.json")

        # multiConfig
        multiconfig = self.multicommons.write(self.outfields)
        self.gitignore.sync("multi.config.json")

        # gitignore
        self.gitignore.export(self.multicommons.export_location)

        # experiments
        if not skip_exps:
            self.qurryinfo.update_qurryinfo(
                experiment_writer(
                    experiment_container=self.exps,
                    beforewards=self.beforewards,
                    multicommons=self.multicommons,
                    export_transpiled_circuit=export_transpiled_circuit,
                    multiprocess=multiprocess,
                )
            )

        return multiconfig

    def analyze(
        self,
        analysis_name: str = "report",
        no_serialize: bool = False,
        specific_analysis_args: SpecificAnalyzeArgs[_RA] = None,
        **analysis_args: dict[str, Any] | AnalyzeArgs,
    ) -> str:
        """Analyze the experiments.

        Args:
            exps_container (ExperimentContainer[_ExpInst]):
                The container of experiments.
            analysis_name (str, optional):
                The name of analysis. Defaults to "report".
            no_serialize (bool, optional):
                Whether serialize the analysis. Defaults to False.
            specific_analysis_args (SpecificAnalyzeArgs, optional):
                The specific analysis arguments. Defaults to None.
            **analysis_args (dict[str, Any] | AnalyzeArgs):
            The arguments of analysis.

        Returns:
            str: The name of analysis.
        """

        counts_check = [
            exp_id for exp_id, exp in self.exps.items() if len(exp.afterwards.counts) == 0
        ]
        if len(counts_check) > 0:
            raise ValueError(
                f"Counts of {len(counts_check)} experiments are empty, "
                + f"please check them before analysis: {counts_check}."
            )

        if specific_analysis_args is None:
            specific_analysis_args = {}
        if set(specific_analysis_args.keys()) - set(self.exps.keys()):
            raise KeyError("The specific_analysis_args keys must be in the experiments' keys.")
        specific_analysis_args_check = [
            exp_id
            for exp_id, args in specific_analysis_args.items()
            if not (isinstance(args, (bool, dict)))
        ]
        if len(specific_analysis_args_check) > 0:
            raise TypeError(
                "The specific_analysis_args values must be dict or bool, "
                + f"please check them: {specific_analysis_args_check}."
            )

        all_exps_progress = qurry_progressbar(
            self.exps.keys(),
            bar_format=("| {n_fmt}/{total_fmt} - Analysis: {desc} - {elapsed} < {remaining}"),
        )

        analysis_source_info: list[tuple[tuple[str, ...], str, int]] = []
        for k in all_exps_progress:
            if k not in specific_analysis_args:
                report: AnalysisPrototype = self.exps[k].analyze(**analysis_args)
                analysis_source_info.append((self.exps[k].commons.tags, k, report.serial))
                continue

            v_args = specific_analysis_args[k]
            if v_args is False:
                all_exps_progress.set_description_str(f"Skipped {k} in {self.summoner_id}.")
                continue
            if v_args is True:
                report: AnalysisPrototype = self.exps[k].analyze(**analysis_args)
                analysis_source_info.append((self.exps[k].commons.tags, k, report.serial))
                continue
            report: AnalysisPrototype = self.exps[k].analyze(**v_args)
            analysis_source_info.append((self.exps[k].commons.tags, k, report.serial))

        report_name = self.quantity_info.register(analysis_source_info, analysis_name, no_serialize)

        self.multicommons.datetimes.add_only(report_name)

        return report_name

    def all_reports(self, report_name: str):
        """Get the reports of the multi-experiment.

        Args:
            report_name (str): The name of report.

        Returns:
            dict[tuple[str, ...], list[AnalysisPrototype]]:
                The dict of tags to list of reports.
        """
        if report_name not in self.quantity_info:
            raise KeyError(f"{report_name} is not in the quantity_info reports.")

        return {
            tags: [
                self.exps[exp_id].reports[quantity_index]
                for exp_id, quantity_index in exp_id_quantity_index_list
            ]
            for tags, exp_id_quantity_index_list in self.quantity_info[report_name].items()
        }

    def all_quantities(self, report_name: str):
        """Get the quantities of the reports of the multi-experiment.

        Args:
            report_name (str): The name of report.

        Returns:
            dict[tuple[str, ...], list[dict[str, Any]]]:
                The dict of tags to list of quantities items.
        """

        current_all_reports: dict[tuple[str, ...], list[AnalysisPrototype]] = self.all_reports(
            report_name
        )
        return {
            tags: [dict(report.results_items()) for report in reports_list]
            for tags, reports_list in current_all_reports.items()
        }

    def write_all_quantities(self, report_name: str) -> None:
        """Export the quantities of the reports of the multi-experiment as JSON file.

        Args:
            report_name (str): The name of report.
        """

        current_all_reports: dict[tuple[str, ...], list[AnalysisPrototype]] = self.all_reports(
            report_name
        )
        quick_json_write(
            content={
                tags: [dict(report.results_items(serialized=True)) for report in reports_list]
                for tags, reports_list in current_all_reports.items()
            },
            filename=Path(self.multicommons.export_location) / f"{report_name}.all_quantities.json",
            mode=DEFAULT_MODE,
            encoding=DEFAULT_ENCODING,
            jsonable=True,
        )
