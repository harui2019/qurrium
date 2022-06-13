from .jsonablize import Parse as jsonablize
import warnings

class argdict(dict):
    __name__ = 'argdict'
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
        blacklist = dir({})
        
        for k in paramsKey:
            if k in blacklist:
                warnings.warn(
                    f"'{k}' will be not added as attribution "+
                    "due to this attribution is used for class working.")
            else:
                self.__setattr__(k , None)
        for k in params:
            if k in blacklist:
                warnings.warn(
                    f"'{k}' will be not added as attribution "+
                    "due to this attribution is used for class working.")
            else:
                self.__setattr__(k, params[k])

    def __getitem__(self, key) -> any:
        return self.__dict__[key]
    
    def __setitem__(self, key, value) -> None: ...

    def to_dict(self) -> dict[str: any]:
        return self.__dict__
    
    def __iter__(self):
        for k, v in self.__dict__.items():
            yield 'k', v

    def jsonize(self) -> dict[str: str]:
        return jsonablize(self.__dict__)

    def __repr__(self) -> str:
        return f'{self.__name__}({self.__dict__})'


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



