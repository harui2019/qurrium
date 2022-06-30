from typing import Optional, Iterable
import warnings
from collections import defaultdict


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
            if isinstance(k, (str)):
                if k[0] == '(' and k[-1] == ')':

                    kt = [tr for tr in k[1:-1].split(", ")]
                    kt2 = []
                    for ktsub in kt:
                        if ktsub[0] == '\'':
                            kt2.append(ktsub[1:-1])
                        elif ktsub[0] == '\"':
                            kt2.append(ktsub[1:-1])
                        elif k.isdigit():
                            kt2.append(int(ktsub))
                        else:
                            kt2.append(ktsub)
                    kt2 = tuple(kt2)
                    o[kt2] = o[k]
                    del o[k]
                else:
                    ...
                    # print(f"'{k}' may be not a tuple, parsing unactive.")
    else:
        ...
    return o


class TagMap(defaultdict):
    """Specific data structures of :module:`qurry` like `dict[str, list[any]]`.

    >>> bla = TagMap()

    >>> bla.guider('strTag1', [...])
    >>> bla.guider(('tupleTag1', ), [...])
    >>> # other adding of key and value via `.guider()`
    >>> bla
    ... {
    ...     'noTags': [...], # something which does not specify tags.
    ...     'strTag1': [...], # something
    ...     ('tupleTag1', ): [...], 
    ...     ... # other hashable as key in python
    ... }

    """
    protect_keys = ['all', 'noTags']

    def __init__(
        self,
        o: dict[str, list] = {},
        tupleStrTransplie: bool = True,
    ) -> None:

        if not isinstance(o, dict):
            raise ValueError(
                "Input needs to be a dict with all values are iterable.")
        super().__init__(list)

        o = keyTupleLoads(o) if tupleStrTransplie else o
        not_list_v = []
        for k, v in o.items():
            if isinstance(v, Iterable):
                self[k] = [vv for vv in v]
            else:
                not_list_v.append(k)

        self._noTags = self['noTags']
        self._all_tags_value = []

        if len(not_list_v) > 0:
            warnings.warn(
                f"The following keys '{not_list_v}' with the values are not list won't be added.")

    def all(self) -> list:
        if len(self._all_tags_value) == 0:
            d = []
            for k, v in self.items():
                if isinstance(v, list):
                    d += v
            self._all_tags_value = d
        return self._all_tags_value

    def with_all(self) -> dict[list]:
        return {
            **self,
            'all': self.all()
        }

    def guider(
        self,
        legacyTag: Optional[any] = None,
        v: any = None,
    ) -> None:
        """

        Args:
            legacyTag (any): The tag for legacy as key.
            v (any): The value for legacy.

        Returns:
            dict: _description_
        """
        for k in self.protect_keys:
            if legacyTag == k:
                legacyTag == None
                warnings.warn(f"'{k}' is a reserved key for export data.")

        self._all_tags_value = []
        if legacyTag == None:
            self._noTags.append(v)
            super().__setitem__('noTags', self._noTags)
        elif legacyTag in self:
            self[legacyTag].append(v)
        else:
            self[legacyTag] = [v]

    # def tupleStrKey2tuple(self) -> None:
    #     self = keyTupleLoads(self)
