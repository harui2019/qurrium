import json
from typing import Hashable
from collections import OrderedDict


def valueParse(v: any) -> any:
    """Make value json-allowable. If a value is not allowed by json, them return its '__str__'.

    Args:
        v (any): Value.

    Returns:
        any: Json-allowable value.
    """

    try:
        parsed = json.dumps(v)
        return v
    except TypeError as e:
        return str(v)


def keyParse(k: any) -> any:
    """Make key json-allowable. If a value is not allowed by json, them return its '__str__'.

    str, int, float, bool or None

    Args:
        o (any): Key.

    Returns:
        any: Json-allowable key.
    """

    if isinstance(k, (str, int, float, bool)):
        parsed = k
    elif k == None:
        parsed = k
    else:
        parsed = str(k)

    return parsed


def Parse(o: any) -> any:
    """Make a python object json-allowable.

    Args:
        o (any): Python object.

    Returns:
        any: Json-allowable python object.
    """

    if isinstance(o, list):
        parsed = [Parse(v) for v in o]
    elif isinstance(o, tuple):
        parsed = [Parse(v) for v in o]
    elif isinstance(o, dict):
        parsed = {keyParse(k): Parse(v) for k, v in o.items()}
    else:
        parsed = valueParse(o)

    return parsed


def sortHashableAhead(o: dict) -> dict:
    """Make hashable values be the ahead in dictionary."

    Args:
        o (dict): Unsorted dictionary.

    Returns:
        dict: Sorted dictionary.
    """
    sort_o = OrderedDict()
    for k, v in o.items():
        if isinstance(v, Hashable):
            sort_o[k] = v
    
    for k, v in o.items():
        if not k in sort_o:
            sort_o[k] = v
            
    return sort_o
    


def quickJSONExport(
    content: any,
    filename: str,
    mode: str,
    indent: int = 2,
    encoding: str = 'utf-8',
    jsonablize: bool = False,
) -> None:
    ...
    with open(filename, mode, encoding=encoding) as File:
        if jsonablize:
            json.dump(Parse(content), File, indent=indent, ensure_ascii=False)
        else:
            json.dump(content, File, indent=indent, ensure_ascii=False)
        print(f"'{filename}' exported successfully.")
