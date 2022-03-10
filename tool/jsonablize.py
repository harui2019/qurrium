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
        parsed = {k: Parse(v) for k, v in o.items()}
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
