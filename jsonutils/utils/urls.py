def join_paths(*args, sep="/"):
    """
    Joins different elements within the same path, using a single separator
    and making sure that it is not repeated as a connecting link.
    """
    # TODO add test
    def _format(s, idx):
        if idx == 0:
            return s.rstrip(sep)
        return s.lstrip(sep).rstrip(sep)

    return sep.join([_format(item, idx) for idx, item in enumerate(args)])
