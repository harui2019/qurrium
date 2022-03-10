from .jsonablize import Parse as jsonablize


class argdict(dict):
    def __init__(
        self,
        params: dict[str: any],
        paramsKey: list[str] = [],
    ) -> None:
        """This class is a container to keep the parameters for each experiment.
        And it's also am inherition of `dict`.

        ## example:

        >>> A = argset({'a': 22})

        - call

        >>> A['a'], A.a
        `('22', '22')`

        - iterations

        >>> [k for k in A]
        `['a']`

        - keys

        >>> ('a' in A)
        `True`

        - iterable unpacking

        >>> {**A}
        `{'a': 22}`

        Args:
            params (dict[str: any]): The parameters of the experiment.
            paramsKey (list[str]): The necessary parameters of the experiment.
        """

        super().__init__(params)
        for k in paramsKey:
            self.__setattr__(k, None)
        for k in params:
            self.__setattr__(k, params[k])

    def __getitem__(self, key) -> any:
        return self.__dict__[key]

    def to_dict(self) -> dict[str: any]:
        return self.__dict__

    def jsonize(self) -> dict[str: str]:
        return jsonablize(self.__dict__)

    def __repr__(self) -> str:
        return f'argsKeep({self.__dict__})'


def overNested(
    targetDict: dict = {},
    keys: list[any] = [],
    value: any = {},
) -> dict:
    k = keys[0]
    if k in targetDict:
        ...
    else:
        targetDict[k] = {}
    
    if isinstance(keys, list) and len(keys) > 1:
        targetDict[k] = overNested(
            targetDict=targetDict[k],
            keys=keys[1:],
            value=value
        )
    else:
        targetDict[k] = value

    return targetDict



