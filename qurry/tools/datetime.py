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

    def __repr__(self):
        return f"{type(self).__name__}({super().__repr__()})"

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(f"{type(self).__name__}" + "({...})")
        else:
            original_repr = super().__repr__()
            original_repr_split = original_repr[1:-1].split(", ")
            length = len(original_repr_split)
            with p.group(2, f"{type(self).__name__}(" + "{", "})"):
                for i, item in enumerate(original_repr_split):
                    p.breakable()
                    p.text(item)
                    if i < length - 1:
                        p.text(",")

    def __str__(self):
        return super().__repr__()
