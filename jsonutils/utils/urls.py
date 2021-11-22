import os


def join_paths(*args, sep=None):
    """
    Joins different elements within the same path, using a single separator
    and making sure that it is not repeated as a connecting link.
    """
    # TODO add test
    if sep is None:
        sep = os.path.sep

    if not isinstance(sep, str):
        raise TypeError(f"Argument 'sep' must be a str instance, not {type(sep)}")

    length = len(args)

    def _format(s, idx):
        if isinstance(s, os.PathLike):
            s = os.fspath(s)
        if idx == 0:
            return s.rstrip(sep)
        if idx == length - 1:
            return s.lstrip(sep)
        return s.lstrip(sep).rstrip(sep)

    return sep.join([_format(item, idx) for idx, item in enumerate(args)])
