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
            except Exception:
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


def return_false_on_exception(exception):
    """
    When applied on a function, it will return Flase if selected exception is raised
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if kwargs.get("only_check") is True:
                try:
                    return func(*args, **kwargs)
                except exception:
                    return False
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator
