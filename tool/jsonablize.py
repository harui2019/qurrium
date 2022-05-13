import json


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


def keyTupleLoads(o: dict) -> dict:
    """If a dictionary with string keys which read from json may originally be a python tuple, then transplies as a tuple.

    Args:
        o (dict): A dictionary with string keys which read from json.

    Returns:
        dict: Result which turns every possible string keys returning to 'tuple'.
    """

    if isinstance(o, dict):
        ks = list(o.keys())
        for k in ks:
            if isinstance(k, str):
                if k[0] == '(' and k[-1] == ')':
                    kt = tuple([tr[1:-1] for tr in k[1:-1].split(", ")])
                    o[kt] = o[k]
                    del o[k]
                else:
                    ...
                    # print(f"'{k}' may be not a tuple, parsing unactive.")
    else:
        ...
    return o
