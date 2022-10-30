from typing import Optional, Hashable, NamedTuple

"""

- Before:
        
>>> print(" ### Qiskit version outdated warning")
>>> print("Please keep mind on your qiskit version, an very outdated version may cause some problems.")
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
        ('txt', "Please keep mind on your qiskit version, an very outdated version may cause some problems."),
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
        
------------------------------------------------------------
 ### Qiskit version outdated warning
 Please keep mind on your qiskit version, an very outdated version may cause some problems.
 - Local Qiskit version ------------------- 0.39.0
 - Latest Qiskit version ------------------ 0.39.0
```

Hoshi - A process content printer ?

## Why this name?
    I made it when I was listening the songs made by Hoshimachi Suisei, a VTuber in Hololive. I was inspired by her songs, and I made this tool. I named it Hoshi, which means star in Japanese. I hope this tool can help you to make your code more beautiful.

    (Hint: The last sentence is auto-complete by Github Copilot from 'Hoshimachi' to the end. That's meaning that Github Copilot knows VTuber, Hololive, even Suisei, who trains it with such content and how. "Does Skynet subscribe to Virtual Youtuber?")
"""


def hnprint(title, heading=3):
    """Print a title.

    Args:
        title (str): tilte of the section.
        heading (int, optional): Heading level. Defaults to 3.

    Returns:
        _type_: _description_
    """
    content = " "+"#"*heading+" {}".format(title)

    return content


def divider(length: int = 60):
    """Print a divider.

    Args:
        length (int, optional): Length of the divider. Defaults to 60.
    """
    content = "-"*length

    return content


def _ljustFilling(
    previous: str,
    length: Optional[int] = None,
    filler: str = '-'
) -> tuple[str, int]:

    previous = str(previous)
    if length is None or length == 0:
        length = len(previous)
        length = 5*(int(length/5)+2)

    return (previous+' ').ljust(length, filler)+' ', length


def itemize(
    description: str,
    value: Optional[any] = None,
    hint: str = '',
    listing_level: int = 1,

    listing_itemize: str = '-',
    ljust_description_len: int = 0,
    ljust_description_filler: str = '-',
    ljust_value_len: int = 0,
    ljust_value_filler: str = '.',
    hint_itemize: str = '#',

    export_len: bool = False,
):
    """_summary_

    Args:
        subscribe (str): _description_
        value (any): _description_
        hint (str, optional): _description_. Defaults to ''.
    """
    description = str(description)

    content = ''
    if not value is None:
        value = str(value)
        subscribe_str, ljust_description_len = _ljustFilling(
            previous=description,
            length=ljust_description_len,
            filler=ljust_description_filler
        )
        content += (" "*(2*listing_level-1) +
                    "{} {}".format(listing_itemize, subscribe_str))
    else:
        content += (" "*(2*listing_level-1) +
                    "{} {}".format(listing_itemize, description))

    hint = str(hint)
    if len(hint) != 0:
        value_str, ljust_value_len = _ljustFilling(
            previous=value,
            length=ljust_value_len,
            filler=ljust_value_filler
        )
        content += value_str+' '+hint_itemize+' '+hint
    else:
        content += value

    if export_len:
        return content, ljust_description_len, ljust_value_len
    else:
        return content


class Hoshi(list):

    _availablePrint = ['h1', 'h2', 'h3', 'h4',
                       'h5', 'h6', 'txt', 'itemize', 'divider']

    class _config_container(NamedTuple):
        listing_level: int = 1
        listing_itemize: str = '-'
        ljust_description_len: Optional[int] = None
        ljust_description_filler: str = '-'
        ljust_value_len: Optional[int] = None
        ljust_value_filler: str = '.'
        hint_itemize: str = '#'

    def __init__(
        self,
        raw: list[tuple[str]],

        listing_level: int = 1,
        listing_itemize: str = '-',
        ljust_description_len: int = 0,
        ljust_description_filler: str = '-',
        ljust_value_len: int = 0,
        ljust_value_filler: str = '.',
        hint_itemize: str = '#',
        **kwargs
    ):
        """

        - Before:

        >>> print(" ### Qiskit version outdated warning")
        >>> print("Please keep mind on your qiskit version, an very outdated version may cause some problems.")
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
                ('txt', "Please keep mind on your qiskit version, an very outdated version may cause some problems."),
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

        ------------------------------------------------------------
         ### Qiskit version outdated warning
         Please keep mind on your qiskit version, an very outdated version may cause some problems.
         - Local Qiskit version ------------------- 0.39.0
         - Latest Qiskit version ------------------ 0.39.0
        ```
        Hoshi - A process content printer ?

        ## Why this name?
            I made it when I was listening the songs made by Hoshimachi Suisei, a VTuber in Hololive. I was inspired by her songs, and I made this tool. I named it Hoshi, which means star in Japanese. I hope this tool can help you to make your code more beautiful.

            (Hint: The last sentence is auto-complete by Github Copilot from 'Hoshimachi' to the end. That's meaning that Github Copilot knows VTuber, Hololive, even Suisei, who trains it with such content and how. "Does Skynet subscribe to Virtual Youtuber?")
        """

        for item in raw:
            if isinstance(item, (tuple, list)):
                if item[0] in self._availablePrint:
                    if len(item) > 1:
                        self.append(item)
                else:
                    self.append(('txt', item))
            elif isinstance(item, dict):
                if 'type' in item:
                    if item['type'] in self._availablePrint:
                        self.append(item)
            else:
                self.append(('txt', item))

        self._config = self._config_container(**{
            'listing_level': listing_level,
            'listing_itemize': listing_itemize,
            'ljust_description_len': ljust_description_len,
            'ljust_description_filler': ljust_description_filler,
            'ljust_value_len': ljust_value_len,
            'ljust_value_filler': ljust_value_filler,
            'hint_itemize': hint_itemize,
        })
        self._update()

    def _update(self):
        self._print_list = []
        # configuration update
        for item_raw in self:
            if isinstance(item_raw, dict):
                item = [item_raw['type']]
                if 'description' in item_raw:
                    item.append(item_raw['description'])
                    if 'value' in item_raw:
                        item.append(item_raw['value'])
                    if 'hint' in item_raw:
                        item.append(item_raw['hint'])
                    if 'listing_level' in item_raw:
                        item.append(item_raw['listing_level'])
                elif 'text' in item_raw:
                    item.append(item_raw['text'])
                elif 'length' in item_raw:
                    item.append(item_raw['length'])
                else:
                    ...
            else:
                item = item_raw

            if item[0] == 'itemize':
                if len(item) < 5:
                    item = list(item)
                    item.extend(['' for i in range(4-len(item))])
                    item.extend([1])
                content, ljust_description_len, ljust_value_len = itemize(
                    description=item[1],
                    value=item[2],
                    hint=item[3],
                    listing_level=item[4],

                    listing_itemize=self._config.listing_itemize,
                    ljust_description_len=0,
                    ljust_description_filler=self._config.ljust_description_filler,
                    ljust_value_len=0,
                    ljust_value_filler=self._config.ljust_value_filler,
                    hint_itemize=self._config.hint_itemize,
                    export_len=True
                )
                if ljust_description_len > self._config.ljust_description_len:
                    self._config = self._config._replace(
                        ljust_description_len=ljust_description_len)
                if ljust_value_len > self._config.ljust_value_len:
                    self._config = self._config._replace(
                        ljust_value_len=ljust_value_len)

        # string add
        for item_raw in self:
            if isinstance(item_raw, dict):
                item = [item_raw['type']]
                if 'description' in item_raw:
                    item.append(item_raw['description'])
                    if 'value' in item_raw:
                        item.append(item_raw['value'])
                    if 'hint' in item_raw:
                        item.append(item_raw['hint'])
                    if 'listing_level' in item_raw:
                        item.append(item_raw['listing_level'])
                elif 'text' in item_raw:
                    item.append(item_raw['text'])
                elif 'length' in item_raw:
                    item.append(item_raw['length'])
                else:
                    ...
            else:
                item = item_raw

            if item[0] == 'h1':
                self._print_list.append(hnprint(item[1], heading=1))
            elif item[0] == 'h2':
                self._print_list.append(hnprint(item[1], heading=2))
            elif item[0] == 'h3':
                self._print_list.append(hnprint(item[1], heading=3))
            elif item[0] == 'h4':
                self._print_list.append(hnprint(item[1], heading=4))
            elif item[0] == 'h5':
                self._print_list.append(hnprint(item[1], heading=5))
            elif item[0] == 'h6':
                self._print_list.append(hnprint(item[1], heading=6))
            elif item[0] == 'txt':
                self._print_list.append(' '+str(item[1]))
            elif item[0] == 'divider':
                self._print_list.append(divider())
            elif item[0] == 'itemize':
                if len(item) < 5:
                    item = list(item)
                    item.extend(['' for i in range(4-len(item))])
                    item.extend([1])

                content = itemize(
                    description=item[1],
                    value=item[2],
                    hint=item[3],
                    listing_level=item[4],

                    listing_itemize=self._config.listing_itemize,
                    ljust_description_len=self._config.ljust_description_len,
                    ljust_description_filler=self._config.ljust_description_filler,
                    ljust_value_len=self._config.ljust_value_len,
                    ljust_value_filler=self._config.ljust_value_filler,
                    hint_itemize=self._config.hint_itemize,
                )
                self._print_list.append(content)
            else:
                raise ValueError("Unknown print type.")

    def __str__(self):
        content = ''
        for item in self._print_list:
            content += item
            content += '\n'
        return content

    def __repr__(self):

        content = self.__str__()
        content += '\n'
        content += 'by <Hoshi>'
        return content

    def newline(self, item):
        super().append(item)
        self._update()

    def h1(self, text: str):
        return hnprint(text, heading=1)

    def h2(self, text: str):
        return hnprint(text, heading=2)

    def h3(self, text: str):
        return hnprint(text, heading=3)

    def h4(self, text: str):
        return hnprint(text, heading=4)

    def h5(self, text: str):
        return hnprint(text, heading=5)

    def h6(self, text: str):
        return hnprint(text, heading=6)

    def txt(self, text: str):
        return ' '+str(text)

    def divider(self, length: int = 60):
        return divider(length)

    def itemize(
        self,
        desc: str,
        value: Optional[any] = None,
        hint: str = '',
    ):
        return itemize(
            description=desc,
            value=value,
            hint=hint,
            **self._config._asdict(),
        )
