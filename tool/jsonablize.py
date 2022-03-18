import json


def valueParse(v: any) -> any:
    """[summary]

    Args:
        v (any): [description]

    Returns:
        any: [description]
    """

    try:
        parsed = json.dumps(v)
        return v
    except TypeError as e:
        return str(v)


def keyParse(k: any) -> any:
    """_summary_

    str, int, float, bool or None

    Args:
        o (any): _description_

    Returns:
        any: _description_
    """

    if isinstance(k, (str, int, float, bool)):
        parsed = k
    elif k == None:
        parsed = k
    else:
        parsed = str(k)

    return parsed


def Parse(o: any) -> any:
    """[summary]

    Args:
        o (any): [description]

    Returns:
        any: [description]
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
    """_summary_

    Args:
        o (dict): _description_

    Returns:
        dict: _description_
    """

    if isinstance(o, dict):
        ks = list(o.keys())
        for k in ks:
            if isinstance(k, str):
                if k[0] == '(' and k[-1] == ')':
                    try:
                        kt = eval(k)
                        o[kt] = o[k]
                        del o[k]
                    except:
                        print(f"'{k}' may be not a tuple, parsing cancelled.")
                else:
                    print(f"'{k}' may be not a tuple, parsing unactive.")
    else:
        ...
    return o
