"""
================================================================
Runner Utils
(:mod:`qurry.qurrium.runner.utils`)
================================================================

"""

from typing import Hashable, Union, Iterable, Literal, overload


@overload
def pending_tags_decider(pk: Literal["_onetime"]) -> list[str]:
    ...


@overload
def pending_tags_decider(pk: Union[list[str], tuple[str]]) -> list[str]:
    ...


@overload
def pending_tags_decider(pk: str) -> list[str]:
    ...


@overload
def pending_tags_decider(pk: Hashable) -> list[Hashable]:
    ...


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
def pk_from_list_to_tuple(pk: str) -> str:
    ...


@overload
def pk_from_list_to_tuple(pk: Hashable) -> Hashable:
    ...


@overload
def pk_from_list_to_tuple(pk: Iterable[Hashable]) -> tuple[Hashable, ...]:
    ...


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
