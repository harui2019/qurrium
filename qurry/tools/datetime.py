"""Datetime (:mod:`qurry.tools.datetime`)"""

from datetime import datetime

from ..capsule import CustomDict

DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
"""Default datetime format for the tools in this module.

The default format is `"%Y-%m-%d %H:%M:%S"`.
For example, it will return a string like "2019-10-01 12:34:56".
"""


def current_time(time_format: str = DEFAULT_DATETIME_FORMAT) -> str:
    """Returns the current time in the specified format.

    Args:
        time_format (str): The format of the time. Defaults to `DEFAULT_DATETIME_FORMAT`.

    Returns:
        str: The current time formatted as a string.
    """
    if not isinstance(time_format, str):
        raise TypeError(f"Expected a string for time_format, got {type(time_format).__name__}")
    return datetime.now().strftime(time_format)


class DatetimeDict(CustomDict[str, str]):
    """A dictionary that records the time when a key is added."""

    def add_only(self, eventname: str) -> tuple[str, str]:
        """Adds a key with the current time no matter the key does not exist.

        Args:
            eventname (str): The name of the event.

        Returns:
            tuple[str, str]: The name of the event and the time.
        """
        self[eventname] = current_time()
        return eventname, self[eventname]

    def add_serial(self, eventname: str) -> tuple[str, str]:
        """Adds a key with the current time and a serial number if the key exists.

        Args:
            eventname (str): The name of the event.

        Returns:
            tuple[str, str]: The name of the event and the time.
        """
        repeat_times_plus_one = 1
        for d in self:
            if d.startswith(eventname):
                repeat_times_plus_one += 1
        eventname_with_times = f"{eventname}." + f"{repeat_times_plus_one}".rjust(3, "0")
        self[eventname_with_times] = current_time()
        return eventname_with_times, self[eventname_with_times]

    def loads(self, datetimes: dict[str, str]):
        """Loads a dictionary of datetimes.

        Args:
            datetimes (dict[str, str]): A dictionary of datetimes.
        """
        for k, v in datetimes.items():
            self[k] = v

    def last_events(self, number: int = 1) -> list[tuple[str, str]]:
        """Returns the last event and its time.

        Args:
            number (int): The number of the last event.

        Returns:
            list[tuple[str, str]]: The last event and its time.
        """
        return list(self.items())[-number:]
