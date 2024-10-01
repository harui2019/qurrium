"""
================================================================
Runner Utils
(:mod:`qurry.qurrium.runner.utils`)
================================================================

"""

import warnings
from typing import Union, Literal, Any, overload
from collections.abc import Iterable, Hashable
from qiskit import QuantumCircuit

from ..multimanager import MultiManager
from ..multimanager.arguments import PendingStrategyLiteral
from ..container import ExperimentContainer
from ..experiment import ExperimentPrototype
from ...tools import qurry_progressbar, DatetimeDict
from ...exceptions import QurryPendingTagTooMany


@overload
def pending_tags_decider(pk: Literal["_onetime"]) -> list[str]: ...
@overload
def pending_tags_decider(pk: Union[list[str], tuple[str]]) -> list[str]: ...
@overload
def pending_tags_decider(pk: str) -> list[str]: ...
@overload
def pending_tags_decider(pk: Hashable) -> list[Hashable]: ...


def pending_tags_decider(pk):
    """Decide the pending tags.

    Args:
        pk (str): The pending key.

    Returns:
        list[str]: The pending tags.
    """

    if pk == "_onetime":
        return []
    if isinstance(pk, (list, tuple)):
        return list(pk)
    return [pk]


@overload
def pk_from_list_to_tuple(pk: str) -> str: ...
@overload
def pk_from_list_to_tuple(pk: Hashable) -> Hashable: ...
@overload
def pk_from_list_to_tuple(pk: Iterable[Hashable]) -> tuple[Hashable, ...]: ...


def pk_from_list_to_tuple(pk):
    """Convert the pending key from list to tuple.

    Args:
        pk (Union[str, Hashable, Iterable[Hashable]]): The pending key.

    Returns:
        Union[str, Hashable, tuple[Hashable, ...]]: The pending key.
    """

    if isinstance(pk, str):
        return pk
    if isinstance(pk, Iterable) and not isinstance(pk, tuple):
        return tuple(pk)
    return pk


def retrieve_times_namer(retrieve_times: int) -> str:
    """Retrieve times namer.

    Args:
        retrieve_times (int): The retrieve times.

    Returns:
        str: The retrieve times namer.
    """
    return "retrieve." + f"{retrieve_times}".rjust(3, "0")


def retrieve_counter(datetimes_dict: DatetimeDict):
    """Count the number of retrieve jobs in the datetimes_dict.""

    Args:
        datetimes_dict (DatetimeDict): The datetimes_dict from Qurry instance.

    Returns:
        int: The number of retrieve jobs in the datetimes_dict.
    """
    return len([datetime_tag for datetime_tag in datetimes_dict if "retrieve" in datetime_tag])


def pending_pool_loading(
    pending_strategy: PendingStrategyLiteral,
    circ_with_serial_num: dict[int, QuantumCircuit],
    current_multimanager: MultiManager,
    experiment_container: ExperimentContainer,
):
    """Load the pending pool.

    Args:
        pending_strategy (PendingStrategyLiteral): The pending strategy.
        circ_with_serial_num (dict[int, QuantumCircuit]): The circuit with serial number.
        current_multimanager (MultiManager): The current multimanager.
        experiment_container (ExperimentContainer): The experiment container.

    """

    for id_exec in qurry_progressbar(
        current_multimanager.beforewards.exps_config,
        bar_format="| {n_fmt}/{total_fmt} - Preparing pending pool - {elapsed} < {remaining}",
        # leave=False,
    ):
        circ_serial_len = len(circ_with_serial_num)
        for idx, circ in enumerate(experiment_container[id_exec].beforewards.circuit):
            current_multimanager.beforewards.circuits_map[id_exec].append(idx + circ_serial_len)

            if pending_strategy == "each":
                current_multimanager.beforewards.pending_pool[id_exec].append(idx + circ_serial_len)

            elif pending_strategy == "tags":
                tags = experiment_container[id_exec].commons.tags
                current_multimanager.beforewards.pending_pool[tags].append(idx + circ_serial_len)

            else:
                if pending_strategy != "onetime":
                    warnings.warn(f"Unknown strategy '{pending_strategy}, use 'onetime'.")
                current_multimanager.beforewards.pending_pool["_onetime"].append(
                    idx + circ_serial_len
                )

            circ_with_serial_num[idx + circ_serial_len] = circ


def pending_tag_packings(
    pk: Union[str, tuple[str, ...], Hashable],
    current_multimanager: MultiManager,
):
    """Pack the pending tags.

    Args:
        pk (Union[str, tuple[str, ...], Hashable]): The key from pending pool.
        current_multimanager (MultiManager): The current multimanager.

    Returns:
        list[str]: The pending tags.
    """

    pending_tags = pending_tags_decider(pk)
    all_pending_tags = [
        str(s)
        for s in [
            current_multimanager.multicommons.summoner_name,
            current_multimanager.multicommons.summoner_id,
            *pending_tags,
            *current_multimanager.multicommons.tags,
        ]
    ]
    if len(all_pending_tags) > 8:
        all_pending_tags = all_pending_tags[:8]
        warnings.warn(
            "The max number of tags is 8, "
            + f"but the number of pending tags is {len(all_pending_tags)}, "
            + "the rest will be ignored.",
            category=QurryPendingTagTooMany,
        )

    return all_pending_tags


def is_not_overwrite_decider(
    datetimes: DatetimeDict,
    retrieve_times: int,
    overwrite: bool = False,
) -> bool:
    """Retrieve counter and overwrite.

    Args:
        datetimes (DatetimeDict): The datetimes.
        retrieve_times (int): The retrieve times.
        overwrite (bool, optional): The overwrite flag. Defaults to False.

    Returns:
        bool: The overwrite flag.
    """

    is_not_overwrite = retrieve_times > 0 and not overwrite

    if is_not_overwrite:
        print(f"| retrieve times: {retrieve_times}, overwrite: {overwrite}")
        last_time_date = datetimes[retrieve_times_namer(retrieve_times)]
        print(f"| Last retrieve by: {retrieve_times_namer(retrieve_times)} at {last_time_date}")
        print("| Seems to there are some retrieves before.")
        print("| You can use `overwrite=True` to overwrite the previous retrieve.")

    return is_not_overwrite


def circuits_map_distributer(
    current_multimanager: MultiManager,
    experiment_container: ExperimentContainer[ExperimentPrototype],
    counts_tmp_container: dict[int, dict[str, int]],
    retrieve_times_name: str,
):
    """Distribute the circuits map.

    Args:
        current_multimanager (MultiManager): The current multimanager.
        experiment_container (ExperimentContainer): The experiment container.
        counts_tmp_container (dict[int, dict[str, int]]): The counts temporary container.
        retrieve_times_name (str): The retrieve times name.
        current (str): The current time.
    """
    distributing_progressbar = qurry_progressbar(
        current_multimanager.beforewards.circuits_map.items(),
        bar_format=("| {n_fmt}/{total_fmt} - Distributing {desc} - {elapsed} < {remaining}"),
    )
    for current_id, idx_circs in distributing_progressbar:
        distributing_progressbar.set_description_str(
            f"{current_id} with {len(idx_circs)} circuits", refresh=True
        )
        experiment_container[current_id].reset_counts(summoner_id=current_multimanager.summoner_id)
        for idx in idx_circs:
            experiment_container[current_id].afterwards.counts.append(counts_tmp_container[idx])
        experiment_container[current_id].commons.datetimes.add_only(retrieve_times_name)
        current_multimanager.afterwards.allCounts[current_id] = experiment_container[
            current_id
        ].afterwards.counts


def retrieve_exceptions_loader(
    exceptions: dict[str, Union[Exception, Any]],
    current_multimanager_outfields: dict[str, Any],
):
    """Exceptions loader during retrieve.

    Args:
        exceptions (dict[str, Union[Exception, Any]]): The exceptions.
        current_multimanager_outfields (dict[str, Any]): The current multimanager outfields
    """
    if len(exceptions) > 0:
        if "exceptions" not in current_multimanager_outfields:
            current_multimanager_outfields["exceptions"] = {}
        for result_id, exception_item in exceptions.items():
            current_multimanager_outfields["exceptions"][result_id] = exception_item
