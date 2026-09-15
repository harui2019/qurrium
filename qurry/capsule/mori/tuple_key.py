"""Tuple Key Parser (:mod:`qurry.capsule.mori.tuple_key`)"""

from typing import TypeVar

_T = TypeVar("_T")


def tuple_str_parse(kstring: str) -> tuple[str, ...] | str:
    r"""Convert tuple strings to real tuple.

    >>> tuple_str_parse("hello_world")
    'hello_world'

    >>> tuple_str_parse("(1, 2, 3)")
    (1, 2, 3)

    >>> tuple_str_parse("('a', 'b', 'c')")
    ('a', 'b', 'c')

    >>> tuple_str_parse("('delay', '1.60e+01_ns', 'excited')")
    ('delay', '1.60e+01_ns', 'excited')

    >>> tuple_str_parse(
        '(\'normalstr\', \'alsostr\', \'"power"str\', "p\'aw\'a", 42, \'114514\', \'\')'
    )
    ('normalstr', 'alsostr', '"power"str', "p'aw'a", 42, '114514', '')

    Args:
        kstring (str): Tuplizing available string.

    Returns:
        tuple[str, ...] | str: Result of tuplizing.
    """
    if not isinstance(kstring, str):
        raise ValueError("Input must be a string")

    if kstring[0] != "(" or kstring[-1] != ")":
        return kstring

    kt = list(kstring[1:-1].split(", "))
    # ", " is the acutal divider of the tuple elements
    # Not just comma alone
    # Otherwise it will make some really bad result...
    kt2 = []
    for ktelt in kt:
        if len(ktelt) <= 0:
            continue
        if ktelt[0] == "'" or ktelt[0] == '"':
            kt2.append(ktelt[1:-1].strip())
        elif ktelt.isdigit():
            kt2.append(int(ktelt))
        else:
            kt2.append(ktelt)

    return tuple(kt2)


def tuple_str_parse_ensured(kstring: str) -> tuple[str, ...]:
    r"""Convert tuple strings to real tuple, ensured.
    So it will raise ValueError if the input string is not a tuple string.

    >>> tuple_str_parse_ensured("(1, 2, 3)")
    (1, 2, 3)

    >>> tuple_str_parse_ensured("('a', 'b', 'c')")
    ('a', 'b', 'c')

    Args:
        kstring (str): Tuplizing available string.

    Raises:
        ValueError: If the input string is not a tuple string.

    Returns:
        tuple[str, ...]: Result of tuplizing.
    """
    kt = tuple_str_parse(kstring)
    if not isinstance(kt, tuple):
        raise ValueError("Input string is not a tuple string.")
    return kt


def key_tuple_loads(o: _T) -> _T:
    """If a dictionary with string keys
    which read from json may originally be a python tuple,
    then transplies as a tuple.

    Args:
        o (dict): A dictionary with string keys which read from json.

    Returns:
        dict: Result which turns every possible string keys returning to 'tuple'.
    """

    if not isinstance(o, dict):
        return o

    ks = list(o.keys())
    for k in ks:
        if isinstance(k, str):
            kt2 = tuple_str_parse(k)
            if kt2 != k:
                o[kt2] = o.pop(k)
    return o
