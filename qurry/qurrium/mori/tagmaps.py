from typing import Optional
import warnings

class TagMap(dict[list[any]]):
    def __init__(self) -> None:
        super().__init__({ 'noTags': [] })
        self._noTags = self['noTags']
        self._all_tags = []
        
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
        """Migarate from :func:`Qurry()._legacyTagGuider`.

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
            
