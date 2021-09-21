from functools import wraps


def catch_exceptions(func):
    """
    When applied on a function, prevent it from throwing exceptions, if argument 'fail_silently' is set to True (False by default)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs.get("fail_silently") is True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return
        else:
            return func(*args, **kwargs)

    return wrapper


def return_str_or_datetime(func):
    """
    This decorator will be applied to the parse_datetime function,
    so that it returns strings in isoformat format whenever the
    return_string argument is set to True.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs.get("return_string") is True:
            return func(*args, **kwargs).isoformat()
        else:
            return func(*args, **kwargs)

    return wrapper
