"""
# Hoshi - A process content printer ?

- Before:

>>> print(" ### Qiskit version outdated warning")
>>> print("Please keep mind on your qiskit version, 
an very outdated version may cause some problems.")
>>> print(" - Local Qiskit version ".ljust(40, '-')+f" {__qiskit_version__['qiskit']}")
>>> print(" - Latest Qiskit version ".ljust(40, '-')+f" {latest_version}")
```     
### Qiskit version outdated warning
Please keep mind on your qiskit version, an very outdated version may cause some problems.
- Local Qiskit version ---------------- 0.39.0
- Latest Qiskit version --------------- 0.39.0
```

- After:

>>> check_msg = Hoshi(
        [
            ("divider", 60),
            ("h3", "Qiskit version outdated warning"),
            (
                "txt",
                "Please keep mind on your qiskit version,"
                + " an very outdated version may cause some problems.",
            ),
            ("itemize", "Local Qiskit version", 3),
            {
                "type": "itemize",
                "description": "Latest Qiskit version",
                "value": 3,
            },
        ],
        ljust_description_len=40,
    )
>>> print(check_msg)

```

------------------------------------------------------------
 ### Qiskit version outdated warning
 Please keep mind on your qiskit version, an very outdated version may cause some problems.
 - Local Qiskit version ------------------- 0.39.0
 - Latest Qiskit version ------------------ 0.39.0
```

Hoshi - A process content printer ?

## Why this name?
    I made it when I was listening the songs made by Hoshimachi Suisei, 
    a VTuber in Hololive. I was inspired by her songs, and I made this tool. 
    I named it Hoshi, which means star in Japanese. 
    I hope this tool can help you to make your code more beautiful.

    (Hint: The last sentence is auto-complete by Github Copilot from 'Hoshimachi' to the end. 
    That's meaning that Github Copilot knows VTuber, Hololive, even Suisei, 
    who trains it with such content and how. 
    "Does Skynet subscribe to Virtual Youtuber?")
"""

from typing import Optional, Union, NamedTuple, Literal, Any, overload
import pprint


def hnprint(title, heading=3, raw_input=False) -> Union[str, dict[str, Any]]:
    """Print a title.

    Args:
        title (str): tilte of the section.
        heading (int, optional): Heading level. Defaults to 3.
        raw_input (bool, optional): If True, return a dict. Defaults to False.

    Returns:
        Union[str, dict[str, Any]]: Content to print.
    """

    if raw_input:
        return {
            "type": "h" + str(heading),
            "heading": heading,
            "title": title,
        }
    content = " " + "#" * heading + f" {title}"
    return content


def divider(length: int = 60, raw_input=False) -> Union[str, dict[str, Any]]:
    """Print a divider.

    Args:
        length (int, optional): Length of the divider. Defaults to 60.
        raw_input (bool, optional): If True, return a dict. Defaults to False.

    Returns:
        Union[str, dict[str, Any]]: Content to print.
    """

    if raw_input:
        return {
            "type": "divider",
            "length": length,
        }
    content = "-" * length
    return content


def txt(text: str, listing_level: int = 1, raw_input=False) -> Union[str, dict[str, Any]]:
    """Print a text.

    Args:
        text (str): Text to print.
        listing_level (int, optional): Listing level. Defaults to 1.
        raw_input (bool, optional): If True, return a dict. Defaults to False.

    Returns:
        Union[str, dict[str, Any]]: Content to print.
    """

    if raw_input:
        return {
            "type": "txt",
            "listing_level": listing_level,
            "text": text,
        }
    return (" " * (2 * listing_level - 1)) + str(text)


def _ljust_filling(
    previous: str,
    length: Optional[int] = None,
    filler: str = "-",
) -> tuple[str, int]:
    """Ljust filling.

    Args:
        previous (str): The previous string.
        length (Optional[int], optional): Filling length. Defaults to None.
        filler (str, optional): Filling character. Defaults to '-'.

    Returns:
        tuple[str, int]: Filled string and the length of the filled string.
    """

    previous = str(previous)
    if length is None or length == 0:
        length = len(previous)
        length = 5 * (int(length / 5) + 2)

    new_str = (previous + " ").ljust(length, filler)
    if len(new_str) > length:
        length = len(new_str)

    return new_str + " ", length


@overload
def itemize(
    description: str,
    *,
    export_len: Literal[True],
) -> tuple[str, int, int]: ...


@overload
def itemize(
    description: str,
    *,
    independent_newline: Literal[True],
) -> Union[tuple[str, str], str]: ...


@overload
def itemize(
    description: str,
    *,
    export_len: bool,
    independent_newline: bool,
) -> str: ...


def itemize(
    description: str,
    value: Optional[Any] = None,
    hint: Optional[str] = None,
    listing_level: int = 1,
    listing_itemize: str = "-",
    ljust_description_len: int = 0,
    ljust_description_filler: str = "-",
    ljust_value_len: int = 0,
    ljust_value_filler: str = ".",
    ljust_value_max_len: int = 40,
    max_value_len: int = 2000,
    hint_itemize: str = "#",
    export_len: bool = False,
    independent_newline: bool = False,
):
    """Print a listing item."""
    description = str(description)

    content = ""
    brokelinehint = ""
    if value is not None:
        value = pprint.pformat(value) if isinstance(value, (list, tuple, dict)) else str(value)

        if len(value) > max_value_len:
            value = value[:max_value_len] + "..."

        subscribe_str, ljust_description_len = _ljust_filling(
            previous=description,
            length=ljust_description_len,
            filler=ljust_description_filler,
        )
        content += " " * (2 * listing_level - 1) + f"{listing_itemize} {subscribe_str}"
    else:
        content += " " * (2 * listing_level - 1) + f"{listing_itemize} {description}"

    if (hint is not None) and (hint != ""):
        hint = str(hint)
        if value is not None:
            value_str, ljust_value_len = _ljust_filling(
                previous=value, length=ljust_value_len, filler=ljust_value_filler
            )
        else:
            value_str, ljust_value_len = _ljust_filling(
                previous="", length=ljust_value_len, filler=ljust_value_filler
            )
        if ljust_value_len > ljust_value_max_len:
            ljust_value_len = 0
            content += str(value)
            brokelinehint += " " + (" " * (2 * listing_level)) + hint
        else:
            content += value_str + " " + hint_itemize + " " + hint
    else:
        if value is not None:
            content += str(value)

    if export_len:
        return content, ljust_description_len, ljust_value_len
    if brokelinehint != "":
        if independent_newline:
            return content, brokelinehint
        return content + brokelinehint
    return content


class Hoshi:
    """Hoshi - A process content printer ?"""

    _availablePrint = ["h1", "h2", "h3", "h4", "h5", "h6", "txt", "itemize", "divider"]
    __name__ = "Hoshi"

    class ConfigContainer(NamedTuple):
        """Config container for Hoshi."""

        # itemize
        listing_level: int = 1
        listing_itemize: str = "-"
        ljust_description_len: int = 0
        ljust_description_filler: str = "-"
        ljust_value_len: int = 40
        ljust_value_filler: str = "."
        ljust_value_max_len: int = 40
        max_value_len: int = 2000
        hint_itemize: str = "#"

        # divider
        divider_length: int = 60

        @property
        def itemize_fields(self) -> tuple[str, ...]:
            """Return a list of itemize fields."""
            return (
                "listing_level",
                "listing_itemize",
                "ljust_description_len",
                "ljust_description_filler",
                "ljust_value_len",
                "ljust_value_filler",
                "ljust_value_max_len",
                "max_value_len",
                "hint_itemize",
            )

        @property
        def divider_fields(self) -> tuple[str, ...]:
            """Return a list of divider fields."""
            return ("divider_length",)

    def __init__(
        self,
        raw: Optional[list[Union[tuple[Any, ...], dict[str, Any]]]] = None,
        name: str = "Hoshi",
        **kwargs,
    ):
        """

        - Before:

        >>> print(" ### Qiskit version outdated warning")
        >>> print("Please keep mind on your qiskit version,
        an very outdated version may cause some problems.")
        >>> print(" - Local Qiskit version ".ljust(40, '-')+f" {__qiskit_version__['qiskit']}")
        >>> print(" - Latest Qiskit version ".ljust(40, '-')+f" {latest_version}")
        ```
        ### Qiskit version outdated warning
        Please keep mind on your qiskit version, an very outdated version may cause some problems.
        - Local Qiskit version ---------------- 0.39.0
        - Latest Qiskit version --------------- 0.39.0
        ```

        - After:

        >>> check_msg = Hoshi([
                ('divider', 60),
                ('h3', 'Qiskit version outdated warning'),
                ('txt', "Please keep mind on your qiskit version,
                an very outdated version may cause some problems."),
                ('itemize', 'Local Qiskit version', __qiskit_version__['qiskit']),
                {
                    'type': 'itemize',
                    'description': 'Latest Qiskit version',
                    'value': latest_version,
                }
                ],
                ljust_describe_len=40,
            )
        >>> print(check_msg)

        ```
        """

        self.__name__ = name
        self._raw = []
        if raw is None:
            raw = []
        for item in raw:
            if isinstance(item, (tuple, list)):
                if item[0] in self._availablePrint:
                    if len(item) > 1:
                        self._raw.append(item)
                else:
                    self._raw.append(("txt", item))
            elif isinstance(item, dict):
                if "type" in item:
                    if item["type"] in self._availablePrint:
                        self._raw.append(item)
            else:
                self._raw.append(("txt", item))

        self._config = self.ConfigContainer(
            **{
                "listing_level": 1,
                "listing_itemize": "-",
                "ljust_description_len": 0,
                "ljust_description_filler": "-",
                "ljust_value_len": 0,
                "ljust_value_filler": ".",
                "ljust_value_max_len": 40,
                "hint_itemize": "#",
                "max_value_len": 2000,
                "divider_length": 60,
                **kwargs,
            }
        )
        self._update()

    def _item_input_handler(
        self,
        item_type: Literal["itemize"],
        item_input: Optional[dict[str, Any]] = None,
        mode: Literal["add", "config"] = "add",
    ) -> dict[str, Any]:
        """Item input handler.

        Args:
            item_type (Literal['itemize']): Item type.
            item_input (Optional[dict[str, Any]], optional): Item input. Defaults to None.
            mode (Literal['add', 'config'], optional): Mode. Defaults to 'add'.

        Returns:
            dict[str, Any]: Item input.
        """

        if item_input is None:
            item_input = {}

        if item_type == "itemize":
            for k in self._config.itemize_fields:
                item_input[k] = getattr(self._config, k) if k not in item_input else item_input[k]
            if mode == "config":
                item_input["ljust_description_len"] = 0
                item_input["ljust_value_len"] = 0

        return item_input

    def _item_raw_handler(
        self,
        item_raw: Union[tuple[Any, ...], dict[str, Any]],
    ) -> dict[str, Any]:
        item = {}
        if isinstance(item_raw, dict):
            item = item_raw
        elif isinstance(item_raw, (tuple, list)):
            item["type"] = item_raw[0]
            if item["type"] == "itemize":
                item["description"] = str(item_raw[1])
                item["value"] = item_raw[2] if len(item_raw) > 2 else None
                item["hint"] = item_raw[3] if len(item_raw) > 3 else None
                item["listing_level"] = (
                    item_raw[4] if len(item_raw) > 4 else self._config.listing_level
                )
            elif item["type"] == "txt":
                item["text"] = item_raw[1]
                item["listing_level"] = (
                    item_raw[2] if len(item_raw) > 2 else self._config.listing_level
                )
            elif item["type"] == "divider":
                item["length"] = item_raw[1] if len(item_raw) > 1 else self._config.divider_length
            elif item["type"] in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                item["title"] = item_raw[1]
                item["heading"] = int(item["type"].replace("h", ""))
            else:
                raise ValueError(f"Unknown print type, '{item['type']}'.")
        else:
            raise TypeError(f"Unknown item type. '{item}', '{type(item)}'.")
        return item

    def _update(self):
        """Update the print lines."""

        self._print_lines = []
        _formated = []

        for item_raw in self._raw:
            item = self._item_raw_handler(item_raw)

            content = ""
            item_input = {k: v for k, v in item.items() if k != "type"}
            # config
            if item["type"] == "itemize":
                item_input = self._item_input_handler("itemize", item_input, mode="config")
                (content, ljust_description_len, ljust_value_len) = itemize(
                    **item_input, export_len=True
                )
                if ljust_description_len > self._config.ljust_description_len:
                    self._config = self._config._replace(
                        ljust_description_len=ljust_description_len
                    )
                if ljust_value_len > self._config.ljust_value_len:
                    self._config = self._config._replace(ljust_value_len=ljust_value_len)

            _formated.append(item)

        for item in _formated:
            item_input = {k: v for k, v in item.items() if k != "type"}

            # string add
            if item["type"] in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                self._print_lines.append(hnprint(**item_input))
            elif item["type"] == "txt":
                self._print_lines.append(txt(**item_input))
            elif item["type"] == "divider":
                self._print_lines.append(divider(**item_input))
            elif item["type"] == "itemize":
                item_input = self._item_input_handler("itemize", item_input)
                content = itemize(**item_input, independent_newline=True)
                if isinstance(content, str):
                    self._print_lines.append(content)
                else:
                    mainline, brokelinehint = content
                    self._print_lines.append(mainline)
                    self._print_lines.append(brokelinehint)
            else:
                raise TypeError(f"Unknown item type. '{item['type']}', '{type(item)}'.")

    def __str__(self):
        self._update()
        content = ""
        for item in self._print_lines:
            content += item
            content += "\n"
        return content

    def __repr__(self):
        content = self.__str__()
        content += f"by <{self.__name__}>"
        return content

    def print(self):
        """Print the content."""
        self._update()
        for item in self._print_lines:
            print(item)

    def newline(self, item: Union[dict[str, Any], tuple[Any, ...]]):
        """Add a new line.

        Args:
            item (Union[dict[str, Any], tuple[str]]): Item to add.
        """
        self._raw.append(item)

    @property
    def lines(self) -> list[str]:
        """Return the print lines."""
        self._update()
        return self._print_lines

    def h1(self, text: str):
        """Add a h1 title."""
        self._raw.append(hnprint(text, heading=1, raw_input=True))

    def h2(self, text: str):
        """Add a h2 title."""
        self._raw.append(hnprint(text, heading=2, raw_input=True))

    def h3(self, text: str):
        """Add a h3 title."""
        self._raw.append(hnprint(text, heading=3, raw_input=True))

    def h4(self, text: str):
        """Add a h4 title."""
        self._raw.append(hnprint(text, heading=4, raw_input=True))

    def h5(self, text: str):
        """Add a h5 title."""
        self._raw.append(hnprint(text, heading=5, raw_input=True))

    def h6(self, text: str):
        """Add a h6 title."""
        self._raw.append(hnprint(text, heading=6, raw_input=True))

    def txt(self, text: str, listing_level: int = 1):
        """Add a text.

        Args:
            text (str): Text to print.
            listing_level (int, optional): Listing level. Defaults to 1.
        """
        self._raw.append(txt(text, listing_level, raw_input=True))

    def divider(self, length: int = 60):
        """Add a divider.

        Args:
            length (int, optional): Length of the divider. Defaults to 60.
        """
        self._raw.append(divider(length, raw_input=True))

    def itemize(
        self,
        description: str,
        value: Optional[str] = None,
        hint: Optional[str] = None,
        listing_level: int = 1,
    ):
        """Add a listing item.

        Args:
            description (str): Description of the item.
            value (str, optional): Value of the item. Defaults to None.
            hint (str, optional): Hint of the item. Defaults to None.
            listing_level (int, optional): Listing level. Defaults to 1.
        """

        self._raw.append(
            {
                "type": "itemize",
                "description": description,
                "value": value,
                "hint": hint,
                "listing_level": listing_level,
            }
        )
