from ..mori.jsonablize import Parse as jsonablize
from typing import NamedTuple, Iterable, overload
from collections import namedtuple
from collections.abc import Mapping
import warnings


class argdict(dict):
    __name__ = 'argdict'
    __version__ = (0, 2, 0)

    def __init__(
        self,
        params: dict[any],
        paramsKey: list[str] = [],
    ) -> None:
        """This class is a container to keep the parameters for each experiment.
        And it's also an inherition of `dict`.

        In future, with the rebuilding of :meth:`multiOuput`, :meth:`powerOutput`
        :cls:`argdict` will replace by :cls:`attributedDict`, a better data structure made by :cls:`namedtuple`.

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
            yield k, v

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
    Deprecated.

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


class attributedDict(object):
    __name__ = "attributedDict"
    __version__ = (0, 3, 0)

    def __init__(
        self,
        field: dict[str, any] = {},
        name: str = "attributedDict",
        field_names: Iterable[str] = [],
        **otherArgs,
    ) -> None:
        """This class is a container to keep the parameters for each experiment.
        And it's also an inherition of `dict`.

        A replacement of :cls:`argdict`.

        - :cls:`NameTuple` of :module:`typing` can be the type hint for this class.

        ## example:

        >>> A = attributedDict({'a': 22})

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
            field (dict[str, any]): The parameters of the experiment.
            field_names (Iterable[str]): The necessary parameters of the experiment.

        Welcome to Yona Yona Journey
        Wake up, we're gonna gonna party        
        """

        object.__setattr__(self, '__name__', name)
        object.__setattr__(self, '_saveDict', {})

        # downward compatibility for :cls:argdict
        if 'paramsKey' in otherArgs and len(field_names) == 0:
            field_names = otherArgs['paramsKey']

        if 'params' in otherArgs and len(field) == 0:
            field = otherArgs['params']

        for k in field_names:
            self._set_process(k, None)

        for k in field:
            self._set_process(k, field[k])

        for k in dir(self._saveDict):
            if k[:2] != '__':
                object.__setattr__(
                    self, '_'+k, self._saveDict.__getattribute__(k))

    # get option
    def __getitem__(self, __name: any) -> any:
        return self._saveDict[__name]

    # set option
    def _set_process(self, key, value) -> None:
        if key.startswith('_'):
            raise ValueError(
                f"Field names cannot start with an underscore: '{key!r}'")
        self._saveDict[key] = value
        object.__setattr__(self, key, self._saveDict[key])

    def __setitem__(self, key, value) -> None:
        self._set_process(key, value)

    def __setattr__(self, key, value) -> None:
        self._set_process(key, value)

    # del option
    def _del_process(self, __name) -> None:
        if not __name in self._saveDict:
            raise KeyError(f"Such key '{__name}' does not exist.")
        object.__delattr__(self, __name)
        del self._saveDict[__name]

    def __delattr__(self, __name) -> None:
        self._del_process(__name)

    def __delitem__(self, __name) -> None:
        self._del_process(__name)

    # iter option
    def __iter__(self):
        for k in self._saveDict:
            yield k

    def __len__(self):
        return len(self._saveDict)

    def _asdict(self) -> dict[str, any]:
        return self._saveDict

    def _jsonize(self) -> dict[str, any]:
        return jsonablize(self._saveDict)

    # def keys(self):
    #     return self._saveDict.keys()

    def __repr__(self) -> str:
        return f'{self.__name__}({self._saveDict})'


class attridict(dict):
    __name__ = 'attridict'
    __version__ = (0, 4, 1)

    @property
    def at(self) -> property:
        class At(object):
            def __getattr__(inner_self, key: str) -> any:
                return self[key]

            def __setattr__(inner_self, key: str, value: any) -> None:
                self[key] = value

            def __delattr__(inner_self, key: str) -> None:
                del self[key]

            def __repr__(inner_self) -> str:
                return self.__repr__()

        return At()

    def __init__(
        self,
        field: dict[str, any] = {},
        name: str = "attributedDict",
        field_names: Iterable[str] = [],
        **otherArgs,
    ) -> None:
        """This class is a container to keep the parameters for each experiment.
        And it's also an inherition of `dict`.

        A replacement of :cls:`argdict`.

        - :cls:`NameTuple` of :module:`typing` can be the type hint for this class.

        ## example:

        >>> A = attributedDict({'a': 22})

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
            field (dict[str, any]): The parameters of the experiment.
            field_names (Iterable[str]): The necessary parameters of the experiment.

        Welcome to Yona Yona Journey
        Wake up, we're gonna gonna party        
        """

        self.name = name

        # downward compatibility for :cls:argdict
        if 'paramsKey' in otherArgs and len(field_names) == 0:
            field_names = otherArgs['paramsKey']

        if 'params' in otherArgs and len(field) == 0:
            field = otherArgs['params']

        for k in field_names:
            self[k] = None

        for k in field:
            self[k] = field[k]
