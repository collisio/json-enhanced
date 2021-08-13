class UUIDdict(dict):
    """
    This objects represents a normal dict, but overwrites the way a new child item is set, asserting its UUID4 id is unique.
    """

    def __setitem__(self, key, child):

        while key in self.keys():
            key = child._set_new_uuid()

        return super().__setitem__(key, child)


class TranslationDict(dict):
    """
    This objects represents a normal dict, but with a default value when trying to get a missing key.
    """

    class Key:
        pass

    def __init__(self, *args, default_=Key, **kwargs):
        super().__init__(*args, **kwargs)
        self._default = default_

    def __getitem__(self, k):
        try:
            return super().__getitem__(k)
        except KeyError:
            return k if self._default == self.Key else self._default
