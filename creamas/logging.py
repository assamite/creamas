'''
.. py:module:: logging
    :platform: Unix

Logging module holds utilities that help with logging and analyzing the
creative system's behavior.
'''
from functools import wraps
import logging
import os
import sys

__all__ = ['log_before', 'log_after', 'ObjectLogger']


def log_before(attr, level=logging.DEBUG):
    '''Decorator to log attribute's value(s) before function call.

    Implementation allows usage only for methods belonging to class. The class
    instance needs to have **logger** attribute that is subclass of
    :py:class:`~creamas.logging.ObjectLogger`.

    :param int level: logging level
    :param str attr: name of the class instance's parameter to be logged
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


def log_after(attr, level=logging.DEBUG):
    '''Decorator to log attribute's value(s) after function call.

    Implementation allows usage only for methods belonging to class. The class
    instance needs to have **logger** variable set.

    :param int level: logging level
    :param str attr: name of the class instance's parameter to be logged
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


class ObjectLogger():
    '''Base logger for objects. *Not* a subclass of base logger.

    Generates one file for each attribute to be logged.
    '''
    def __init__(self, obj, folder, add_name=False, init=True,
                 log_level=logging.DEBUG):
        '''Create new logger instance for *obj* in *folder*. If *add_name*
        is True, creates subfolder carrying :py:attr:`obj.name` to *folder*.
        If *init* is true, sets logger's level to *log_level* and adds basic
        *StreamHandler* to the logger.
        '''
        self._obj = obj
        self._folder = folder

        if add_name:
            import re
            a = re.split("[:/]", self._obj.name)
            fold = "_".join([i for i in a if len(i) > 0])
            obj_folder = os.path.join(self._folder, fold)
            if not os.path.exists(obj_folder):
                os.makedirs(obj_folder)
            self._folder = obj_folder

        self.logger = logging.getLogger("creamas.{}".format(self._obj.name))
        if len(self.logger.handlers) == 0:
            self.logger.addHandler(logging.NullHandler())
            if init:
                self.logger.setLevel(log_level)
                ch = logging.StreamHandler()
                ch.setLevel(log_level)
                self.logger.addHandler(ch)

        self.DEBUG = logging.DEBUG
        self.INFO = logging.INFO
        self.ERROR = logging.ERROR
        self.CRITICAL = logging.CRITICAL
        self.WARNING = logging.WARNING

    @property
    def obj(self):
        '''Object this logger belongs to. Object has to have **name**
        attribute.'''
        return self._obj

    @property
    def folder(self):
        '''Root logging folder for this logger.'''
        return self._folder

    def add_handler(self, handler):
        '''Add handler to the logger.
        '''
        self.logger.addHandler(handler)

    def get_file(self, attr_name):
        '''Return absolute path to logging file for obj's attribute.'''
        return os.path.abspath(os.path.join(self.folder, "{}.log"
                                            .format(attr_name)))

    def log_attr(self, level, attr_name):
        '''Log attribute to file and pass the message to underlying logger.

        :param int level: logging level
        :param str attr_name: attribute's name to be logged
        '''
        msg = self.write(attr_name)
        self.log(level, msg)

    def log(self, level, msg):
        self.logger.log(level, "{}: {}".format(self.obj.name, msg))
        sys.stdout.flush()

    def write(self, attr_name, prefix='age'):
        '''Write attribute's value to file.

        :param str attr_name:
            attribute's name to be logged

        :param str prefix:
            attribute's name that is prefixed to logging message, defaults to
            *age*.

        :returns: message written to file
        :rtype: str
        '''
        separator = "\t"
        attr = getattr(self.obj, attr_name)
        if hasattr(attr, '__iter__'):
            msg = separator.join([str(e) for e in attr])
        else:
            msg = str(attr)

        if prefix is not None:
            msg = "{}\t{}".format(getattr(self.obj, prefix), msg)

        path = self.get_file(attr_name)
        with open(path, 'a') as f:
            f.write("{}\n".format(msg))

        return msg
