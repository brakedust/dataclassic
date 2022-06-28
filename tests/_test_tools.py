class ExceptionNotRaised(Exception):
    """
    An exception raised when an expected exception is not raised.  This should generally
    only be used in the context of unit testing
    """

    pass


class Raises:
    """
    This is a decorator on test methods that should raise an exception.
    It catches and swallows exceptions of certain types.  If the exception is not thrown, then
    a new exception is thrown
    """

    def __init__(self, *exception_types):
        self.exception_types = exception_types
        self.raised_exceptions = []

    def __call__(self, func):
        """
        Makes the class callable.  This wraps the property setter.
        """
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            try:
                func(*args, **kwargs)
            except self.exception_types as ex:
                self.raised_exceptions.append(ex)
            except:  # nopep8
                raise ExceptionNotRaised(
                    "The expected exception type was not raised {0}".format(
                        self.exception_types
                    )
                )

        return wrapper

    def __enter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type in self.exception_types:
            self.raised_exceptions.append(exc_value)
            return True
        raise ExceptionNotRaised(
            "The expected exception type was not raised {0}".format(
                self.exception_types
            )
        )
