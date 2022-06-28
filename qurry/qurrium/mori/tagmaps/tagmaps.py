from ..jsonablize import keyTupleLoads

from typing import Optional
import warnings


class TagMap(dict):
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

    def __init__(
        self,
        o: dict[str, list] = {},
        tupleStrTransplie: bool = True,
    ) -> None:
        if not isinstance(o, dict):
            raise ValueError(
                "Input needs to be a dict with all values are list.")

        o = keyTupleLoads(o) if tupleStrTransplie else o
        not_list_v = []
        next_o = {'noTags': []}
        for k, v in o.items():
            if isinstance(v, list):
                next_o[k] = v
            else:
                not_list_v.append(k)

        super().__init__(next_o)
        self._noTags = self['noTags']
        self._all_tags = []

        if len(not_list_v) > 0:
            warnings.warn(
                f"The following keys '{not_list_v}' with the values are not list won't be added.")

    def all(self) -> list:
        if len(self._all_tags) == 0:
            d = []
            for k, v in self.items():
                if isinstance(v, list):
                    d += v
            self._all_tags = d
        return self._all_tags

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
        for k in ['all', 'noTags']:
            if legacyTag == k:
                legacyTag == None
                warnings.warn(f"'{k}' is a reserved key for export data.")

        self._all_tags = []
        if legacyTag == None:
            self['noTags'].append(v)
        elif legacyTag in self:
            self[legacyTag].append(v)
        else:
            self[legacyTag] = [v]

    # def tupleStrKey2tuple(self) -> None:
    #     self = keyTupleLoads(self)
