"""
================================================================
Datetime Module for Qurry (:mod:`qurry.qurrium.utils.datetime`)
================================================================

"""

from datetime import datetime


def current_time():
    """Returns the current time in the format of ``YYYY-MM-DD HH:MM:SS``."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class DatetimeDict(dict[str, str]):
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
