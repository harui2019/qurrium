

class TagMap(dict):
    def __init__(self, *args, **kwargs):
        super().__init__({ 'noTags': [] })
        self.__dict__ = self
        
    def all(self):
        d = {'all': []}
        for k, v in self.__dict__.iteritems():
            if isinstance(v, list):
                d['all'] += v
        return d