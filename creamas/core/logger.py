'''
.. py:module:: logger
    :platform: Unix

'''
import logging
import os


__all__ = ['ObjectLogger']


class ObjectLogger():
    '''Base logger for objects.

    Generates one file for each attribute to be logged.
    '''
    def __init__(self, obj, folder, add_name=False, init=True):
        '''Create new logger instance for *obj* in *folder*. If *add_name*
        is true, then creates subfolder carrying ``obj.name`` to *folder*.
        '''
        self._obj = obj
        self._folder = folder

        if add_name:
            obj_folder = os.path.join(self._folder, self._obj.name)
            if not os.path.exists(obj_folder):
                os.makedirs(obj_folder)
            self._folder = obj_folder

        self.logger = logging.getLogger("creamas.{}".format(self.obj.name))
        self.logger.addHandler(logging.NullHandler())
        if init:
            self.logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            self.logger.addHandler(ch)

    @property
    def obj(self):
        '''Object this logger belongs to. Object has to have **name**
        attribute.'''
        return self._obj

    @property
    def folder(self):
        '''Root logging folder for this logger.'''
        return self._folder

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
        self.logger.log(level, "{}:{}".format(self.obj.name, msg))

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
