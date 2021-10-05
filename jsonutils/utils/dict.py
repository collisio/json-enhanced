from collections.abc import KeysView


class UUIDdict(dict):
    """
    This objects represents a normal dict, but overwrites the way a new child item is set, asserting its UUID4 id is unique.
    """

    def __setitem__(self, key, child):

        while key in self.keys():
            key = child._set_new_uuid()

        return super().__setitem__(key, child)

    def values_except(self, except_):

        if isinstance(except_, str):
            result = {k: v for k, v in self.items() if k != except_}
        elif isinstance(except_, (list, tuple, set, KeysView)):
            result = {k: v for k, v in self.items() if k not in except_}
        else:
            raise TypeError("except_ argument must be a str o sequence instance")

        return result.values()


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


class ValuesDict(dict):
    """An usual dict object, but accessing keys by attribute"""

    def __getattr__(self, name):

        try:
            return super().__getitem__(name)
        except KeyError:
            return


class FlagsDict:
    """
    A dict to combine bitflags

    Example
    -------

    >> FlagsDict("A", "B", "C").get_flags(3)
        ['A', 'B']
    """

    def __init__(self, *flags):
        self.dict = {2 ** i: v for i, v in enumerate(flags)}

    def get_flags(self, num, generator=False):
        if num:
            return (
                (self.dict[x] for x in self.dict if x & num)
                if generator
                else [self.dict[x] for x in self.dict if x & num]
            )
