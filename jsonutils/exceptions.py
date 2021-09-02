class JSONQueryException(Exception):
    """Base class for JSON Query exceptions"""

    pass


class JSONSingletonException(Exception):
    pass


class JSONDecodeException(Exception):
    pass

class JSONQueryMultipleValues(JSONQueryException):
    pass
