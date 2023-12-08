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

    def add_only(self, eventname: str):
        """Adds a key with the current time if the key does not exist."""
        self[eventname] = current_time()

    def add_serial(self, eventname: str):
        """Adds a key with the current time and a serial number if the key exists."""
        repeat_times_plus_one = 1
        for d in self:
            if d.startswith(eventname):
                repeat_times_plus_one += 1
        eventname_with_times = f"{eventname}." + f"{repeat_times_plus_one}".rjust(
            3, "0"
        )
        self[eventname_with_times] = current_time()
