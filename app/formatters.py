import logging
import os


class HostnameFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super(HostnameFormatter, self).__init__(fmt=fmt, datefmt=datefmt)
        self.hostname = os.getenv('HOSTNAME', 'unknown')

    def format(self, record):
        record.hostname = self.hostname
        return super(HostnameFormatter, self).format(record)
