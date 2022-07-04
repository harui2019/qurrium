from .jsonablize import Parse as jsonablize
from typing import NamedTuple
from collections import namedtuple
import warnings


class argdict(dict):
    __name__ = 'argdict'
    __version__ = (0, 3, 0)
    def __init__(
        self,
        params: dict[any],
        paramsKey: list[str] = [],
    ) -> None:
        """This class is a container to keep the parameters for each experiment.
        And it's also an inherition of `dict`.
        
        In future, with the rebuilding of :meth:`multiOuput`, :meth:`powerOutput`
        :cls:`argdict` will replace by :cls:`argTuple`, a better data structure made by :cls:`namedtuple`.

        - :cls:`NameTuple` of :module:`typing` can be the type hint for this class.

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
            params (dict[str, any]): The parameters of the experiment.
            paramsKey (list[str]): The necessary parameters of the experiment.
        """

        super().__init__(params)
        blacklist = dir({})

        for k in paramsKey:
            if k in blacklist:
                warnings.warn(
                    f"'{k}' will be not added as attribution but can be called by subscript" +
                    "due to this attribution is used for class working.")
            else:
                self.__setattr__(k, None)
        for k in params:
            if k in blacklist:
                warnings.warn(
                    f"'{k}' will be not added as attribution but can be called by subscript" +
                    "due to this attribution is used for class working.")
            else:
                self.__setattr__(k, params[k])

    def __getitem__(self, key) -> any:
        return self.__dict__[key]

    def __setitem__(self, key, value) -> None: ...

    def to_dict(self) -> dict[str, any]:
        return self.__dict__

    def __iter__(self):
        for k, v in self.__dict__.items():
            yield 'k', v

    def jsonize(self) -> dict[str, str]:
        return jsonablize(self.__dict__)

    def __repr__(self) -> str:
        return f'{self.__name__}({self.__dict__})'


def argTuple(
    params: dict[str, any],
    paramsKey: list[str] = [],
    name: str = 'argTuple',
) -> NamedTuple:
    """This class is a container to keep the parameters for each experiment powered by :cls:`NamedTuple`.

    - :cls:`NameTuple` of :module:`typing` can be the type hint for this class.

    ## example:

    >>> A = argset({'a': 22})

    - call

    >>> A['a'], A.a
    `('22', '22')`

    - iterations

    >>> [k for k in A]
    `['22']`

    - keys

    >>> ('a' in A)
    `True`

    - iterable unpacking

    >>> {**A}
    `{'a': 22}`

    Args:
        params (dict[str, any]): The parameters of the experiment.
        paramsKey (list[str]): The necessary parameters of the experiment.
    """

    f = {
        **{k: None for k in paramsKey},
        **{k: v for k, v in params.items()},
    }
    prototype = namedtuple(field_names=f.keys(), typename=name)

    class argTuple(prototype):
        def __getitem__(self, key) -> any:
            try:
                return self.__getattribute__(key)
            except AttributeError as e:
                raise KeyError(e, ', so this key is not in the argTuple.')
            
        def keys(self) -> list:
            return self._fields

        def jsonize(self) -> dict[str, str]:
            return jsonablize(self._asdict())

    return argTuple(**f)
