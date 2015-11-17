'''
.. py:module:: util
    :platform: Unix

Various utility functions for logging, etc.
'''
from functools import wraps
import logging


__all__ = ['log_before', 'log_after']


def log_before(attr, level=logging.INFO, sep="\t"):
    '''Decorator to log attribute's value(s) before function call.

    Implementation allows usage only for methods belonging to class. The class
    instance needs to have **logger** attribute that is subclass of
    :py:class:`creamas.core.logger.ObjectLogger`.

    :param int level: logging level
    :param str attr: name of the class instance's parameter to be logged
    :param str sep: if **attr** is iterable, separate its elements with **sep**
    '''
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = getattr(args[0], 'logger', None)
            if logger is not None:
                logger.log_attr(level, attr)
            return func(*args, **kwargs)
        return wrapper
    return deco


def log_after(attr, level=logging.INFO, sep="\t"):
    '''Decorator to log attribute's value(s) after function call.

    Implementation allows usage only for methods belonging to class. The class
    instance needs to have **logger** variable set.

    :param int level: logging level
    :param str attr: name of the class instance's parameter to be logged
    :param str sep: if **attr** is iterable, separate its elements with **sep**
    '''
    def deco(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ret = await func(*args, **kwargs)
            logger = getattr(args[0], 'logger', None)
            if logger is not None:
                logger.log_attr(level, attr)
            return ret
        return wrapper
    return deco
