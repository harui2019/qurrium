"""The Utils of Qurrium Arguments (:mod:`qurry.qurrium.arguments.utils`)"""

from typing import Any
from abc import ABC
from dataclasses import dataclass, fields
from uuid import UUID

from ...tools.datetime import DatetimeDict, current_time


def wave_key_to_target_keys(wave_key: str) -> list[str]:
    """Convert the wave key to target keys.

    Args:
        wave_key (str): The wave key.

    Returns:
        list[str]: The target keys.
    """
    return [wave_key]


def v7_to_v9_field_transpose(data_args: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """The field name of v7 to v9.

    Args:
        data_args (dict[str, dict[str, Any]]): The arguments of experiment.

    Returns:
        dict[str, dict[str, Any]]: The arguments of experiment with new field name
    """
    if "wave_key" in data_args["commonparams"]:
        data_args["commonparams"]["target_keys"] = wave_key_to_target_keys(
            data_args["commonparams"].pop("wave_key")
        )

    return data_args


def filter_deprecated_args(
    arguments_or_commons_input: dict[str, Any],
    container_fields: tuple[str, ...] | set[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Filter deprecated arguments from the given arguments or commons.

    Args:
        arguments_or_commons_input (dict[str, Any]): The arguments or commons to be filtered.
        container_fields (tuple[str, ...] | set[str]): The fields to be kept.

    Returns:
        tuple[dict[str, Any], dict[str, Any]]: A tuple containing the filtered arguments or commons
            and a dictionary of deprecated fields.

    Raises:
        TypeError: If the arguments_or_commons_input is not a dictionary.
    """
    arguments_deprecated = {}
    arguments_parsed = {}
    for k, v in arguments_or_commons_input.items():
        if k in container_fields:
            arguments_parsed[k] = v
            continue
        if any([isinstance(v, (int, bool)), bool(v), v is None]):
            # Some deprecated arguments are empty, so we only add non-empty ones.
            arguments_deprecated[k] = v

    return arguments_parsed, arguments_deprecated


def check_tags(tags: tuple[str, ...] | list[str] | None = None) -> tuple[str, ...]:
    """Check tags and return formatted tags.

    Args:
        tags (tuple[str, ...] | list[str] | None): Tags for the experiment.

    Returns:
        tuple[str, ...]: Formatted tags for the experiment.
    """
    if tags is None:
        tags = ()
    elif isinstance(tags, list):
        tags = tuple(tags)
    elif not isinstance(tags, tuple):
        raise TypeError("Tags must be a tuple of strings.")

    if not all(isinstance(tag, (str, int)) for tag in tags):
        raise TypeError(
            f"Tags must be a tuple of 'str' or 'int', other types are not allowed. tags: {tags}"
        )

    return tags


def check_datetimes(datetimes: DatetimeDict | dict[str, str] | None) -> DatetimeDict:
    """Check and format the datetimes dictionary.

    Args:
        datetimes (DatetimeDict | dict[str, str] | None): The datetimes dictionary.
    Returns:
        DatetimeDict: The formatted datetimes dictionary.
    """
    if datetimes is None:
        datetimes = DatetimeDict()
    elif not isinstance(datetimes, (DatetimeDict, dict)):
        raise TypeError("Datetimes must be a DatetimeDict or a dictionary.")
    for key, value in datetimes.items():
        if not isinstance(value, str):
            raise TypeError(
                f"All values in datetimes must be strings. Found {value} for key {key}."
            )

    return DatetimeDict(datetimes)


def raw_commons_process(commons_dict: dict[str, Any]) -> dict[str, Any]:
    """Process the raw common parameters of the experiment.

    Args:
        commons_dict (dict[str, Any]): The common parameters of the experiment.

    Returns:
        dict[str, Any]: The dealt common parameters of the experiment.
    """
    commons_dict["datetimes"] = check_datetimes(
        (commons_dict["datetimes"] if "datetimes" in commons_dict else {"bulid": current_time()})
    )
    commons_dict["tags"] = check_tags((commons_dict["tags"] if "tags" in commons_dict else ()))

    return commons_dict


def create_exp_outfields(outfields: dict[str, Any] | None) -> dict[str, Any]:
    """Create experiment outfields from the given outfields.

    Args:
        outfields (dict[str, Any] | None): The outfields to be parsed.

    Raises:
        TypeError: If the outfields is not a dictionary or None.

    Returns:
        The parsed outfields.
    """

    if outfields is None:
        return {}
    if isinstance(outfields, dict):
        return outfields

    raise TypeError(f"outfields should be dict or None, not {type(outfields)}")


@dataclass(frozen=True)
class DataClassEssential(ABC):
    """The abstract base class for the essential methods of data classes,
    which is used for both
    :class:`qurry.qurrium.arguments.arguments.ArgumentsPrototype` and
    :class:`qurry.qurrium.arguments.commonparams.Commonparams`."""

    @property
    def fields(self) -> tuple[str, ...]:
        """The fields of arguments."""
        return tuple(self.__dict__.keys())

    def asdict(self) -> dict[str, Any]:
        """The arguments as dictionary."""
        return dict(self.__dict__)

    @classmethod
    def dataclass_fields(cls) -> tuple[str, ...]:
        """The fields of arguments."""
        return tuple(f.name for f in fields(cls))


def isvalid_exp_id(exp_id: str | None) -> bool:
    """Check whether the exp_id is valid or not.

    Args:
        exp_id (str | None): The exp_id to be checked.
    """
    if exp_id is None:
        return False
    if not isinstance(exp_id, str):
        return False

    try:
        UUID(exp_id, version=4)
    except ValueError:
        return False

    return True
