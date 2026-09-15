"""ExperimentContainer (:mod:`qurry.qurrium.multimanager.exps_container`)"""

from typing import TypeVar, Any
from pathlib import Path

from .arguments import MultiCommonparams
from .beforewards import Before
from ..experiment import ExperimentPrototype, Export, QurryInfo
from ...tools import (
    qurry_progressbar,
    DEFAULT_POOL_SIZE,
    very_easy_chunk_distribution,
    make_multiprocess_pool,
)
from ...capsule import CustomDict, DEFAULT_INDENT

_E = TypeVar("_E", bound=ExperimentPrototype)


def multiprocess_exporter(id_exec: str, exps_export: Export) -> tuple[str, dict[str, Any]]:
    """Multiprocess exporter and writer for experiment.

    Args:
        id_exec (str): ID of experiment.
        exps_export (Export): The export of experiment.
        mode (str, optional): The mode of writing. Defaults to "w+".
        indent (int, optional): The indent of writing. Defaults to 2.
        encoding (str, optional): The encoding of writing. Defaults to "utf-8".
        jsonable (bool, optional): The jsonable of writing. Defaults to False.

    Returns:
        tuple[str, dict[str, Any]]: The ID of experiment and the files of experiment.
    """
    qurryinfo_exp_id, qurryinfo_files = exps_export.write()
    assert id_exec == qurryinfo_exp_id, (
        f"{id_exec} is not equal to {qurryinfo_exp_id}" + " which is not supported."
    )
    del exps_export

    return qurryinfo_exp_id, qurryinfo_files


def multiprocess_exporter_wrapper(all_arguments: tuple[str, Export]) -> tuple[str, dict[str, str]]:
    """Multiprocess wrapper for exporter.

    Args:
        all_arguments (tuple[str, Export, str, int, str, bool]):
            The arguments for exporter.

            - id_exec (str): ID of experiment.
            - exps_export (Export): The export of experiment.

    Returns:
        tuple[str, dict[str, str]]: The ID of experiment and the files of experiment.
    """
    return multiprocess_exporter(*all_arguments)


def multiprocess_writer(
    id_exec: str,
    exps: ExperimentPrototype,
    save_location: Path,
    export_transpiled_circuit: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Multiprocess exporter and writer for experiment.

    Args:
        id_exec (str): ID of experiment.
        exps (ExperimentPrototype): The export of experiment.
        save_location (Path): The location of saving.
        export_transpiled_circuit (bool, optional):
            Whether to export transpiled circuit. Defaults to False.

    Returns:
        tuple[str, dict[str, Any]]: The ID of experiment and the files of experiment.
    """
    export_instance = exps.export(
        save_location=save_location,
        export_transpiled_circuit=export_transpiled_circuit,
    )
    qurryinfo_exp_id, qurryinfo_files = export_instance.write()
    assert id_exec == qurryinfo_exp_id, (
        f"{id_exec} is not equal to {qurryinfo_exp_id}" + " which is not supported."
    )
    del export_instance

    return qurryinfo_exp_id, qurryinfo_files


def multiprocess_writer_wrapper(
    all_arguments: tuple[str, _E, Path, bool],
) -> tuple[str, dict[str, str]]:
    """Multiprocess wrapper for exporter.

    Args:
        all_arguments (tuple[str, ExperimentPrototype, Path, bool]):
            The arguments for exporter.

            - id_exec (str): ID of experiment.
            - exps (ExperimentPrototype): The export of experiment.
            - save_location (Path): The location of saving.
            - export_transpiled_circuit (bool): Whether to export transpiled circuit.

    Returns:
        tuple[str, dict[str, str]]: The ID of experiment and the files of experiment.
    """
    return multiprocess_writer(*all_arguments)


class ExperimentContainer(CustomDict[str, _E]):
    """A customized dictionary for storing
    :class:`~qurry.qurrium.experiment.experiment.ExperimentPrototype`."""

    def call(self, exp_id: str) -> _E:
        """Call an experiment by its id.

        Args:
            exp_id: The id of the experiment to be called.

        Returns:
            ExperimentPrototype: The experiment with the given id.
        """

        if exp_id in self:
            return self[exp_id]
        raise KeyError(f"Experiment id: '{exp_id}' not found.")

    def __call__(self, exp_id: str) -> _E:
        return self.call(exp_id=exp_id)

    def __repr__(self):
        original_repr = repr({k: v._repr_short() for k, v in self.items()})
        return f"{self.__class__.__name__}({original_repr}, num={len(self)})"

    def _repr_oneline(self):
        return f"{self.__class__.__name__}(" + "{...}" + f", num={len(self)})"

    def _repr_pretty_(self, p, cycle):
        length = len(self)
        if cycle:
            p.text(f"{self.__class__.__name__}(" + "{...}" + f", num={length})")
            return

        with p.group(DEFAULT_INDENT, f"{self.__class__.__name__}(num={length}" + ", {", "})"):
            for i, (k, v) in enumerate(self.items()):
                p.breakable()
                # pylint: disable=protected-access
                p.text(f"'{k}': {v._repr_short()}")
                # pylint: enable=protected-access
                if i < length - 1:
                    p.text(",")


def experiment_writer(
    experiment_container: ExperimentContainer[_E],
    beforewards: Before,
    multicommons: MultiCommonparams,
    export_transpiled_circuit: bool = False,
    multiprocess: bool = False,
) -> QurryInfo:
    """Write the experiment.

    Args:
        experiment_container (ExperimentContainer[_E]):
            The container of the experiment.
        beforewards (Before):
            The beforewards of the experiment.
        multicommons (MultiCommonparams):
            The common parameters of the experiment.
        export_transpiled_circuit (bool, optional):
            Whether to export the transpiled circuit. Defaults to False.
        multiprocess (bool, optional):
            Whether to use multiprocess. Defaults to False.

    Returns:
        The dictionary of the exported information of the experiment.
        The keys are the experiment IDs,
        and the values are the dictionaries of the exported information.
    """

    if multiprocess and len(beforewards.exps_config) > 1:
        respect_memory_array = [
            (id_exec, int(experiment_container[id_exec].memory_usage_factor))
            for id_exec in beforewards.exps_config.keys()
        ]
        respect_memory_array.sort(key=lambda x: x[1])
        exps_serial = {
            id_exec: default_order for default_order, id_exec in enumerate(beforewards.exps_config)
        }

        tmp_export_info = experiment_container[respect_memory_array[0][0]].write(
            save_location=multicommons.save_location,
            export_transpiled_circuit=export_transpiled_circuit,
            qurryinfo_lock=multicommons.summoner_id,
            pbar=None,
        )

        chunks_num, chunks_sorted_list, _ = very_easy_chunk_distribution(
            respect_memory_array=respect_memory_array[1:],
            num_process=DEFAULT_POOL_SIZE,
            max_chunk_size=min(max(1, len(respect_memory_array[1:]) // DEFAULT_POOL_SIZE), 40),
        )

        with make_multiprocess_pool(maxtasksperchild=4) as ep:
            export_imap_result = qurry_progressbar(
                ep.imap_unordered(
                    multiprocess_exporter_wrapper,
                    (
                        (
                            id_exec,
                            experiment_container[id_exec].export(
                                save_location=multicommons.save_location,
                                export_transpiled_circuit=export_transpiled_circuit,
                            ),
                        )
                        for id_exec, memory_usage in chunks_sorted_list
                    ),
                    chunksize=chunks_num,
                ),
                total=len(chunks_sorted_list),
                desc="Exporting experiments...",
                bar_format="qurry-barless",
            )
            qurryinfo_dict = dict(export_imap_result)

        qurryinfo_dict[tmp_export_info[0]] = tmp_export_info[1]
        qurryinfo_dict = dict(sorted(qurryinfo_dict.items(), key=lambda x: exps_serial[x[0]]))

    else:
        qurryinfo_dict = {}
        single_exporting_progress = qurry_progressbar(
            beforewards.exps_config,
            desc="Exporting experiments...",
            bar_format="qurry-barless",
        )
        for id_exec in single_exporting_progress:
            tmp_export_info = experiment_container[id_exec].write(
                save_location=multicommons.save_location,
                qurryinfo_lock=multicommons.summoner_id,
                export_transpiled_circuit=export_transpiled_circuit,
                pbar=single_exporting_progress,
            )
            assert id_exec == tmp_export_info[0], (
                f"ID is not consistent: {id_exec} != {tmp_export_info[0]}."
            )
            qurryinfo_dict[id_exec] = tmp_export_info[1]

    # for id_exec, files in all_qurryinfo_items:
    qurryinfo = QurryInfo.read(save_location=multicommons.export_location)
    qurryinfo.update_qurryinfo(qurryinfo_dict)
    qurryinfo.write(save_location=multicommons.export_location)

    return qurryinfo
