"""Summary

Attributes:
    logger (TYPE): Description
"""

from .host import Host
import logging
import os
import subprocess

logger = logging.getLogger(__name__)

class LocalHost(Host):

    def __init__(self):
        super().__init__()
        self._address = '127.0.0.1'

    def __del__(self):
        pass

    def read_file(self, filename, mode):
        raise NotImplementedError()

    def write_file(self, filename, data, mode):
        raise NotImplementedError()

    def whoami(self):
        name = self.execute_cmd('whoami').decode('utf-8')[:-1]
        return name

    def execute_cmd(self, cmd, timeout=10):
        process = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE)
        process.check_returncode()

        return process.stdout

    def invoke_process(self, cmd):
        raise NotImplementedError()

    def get_info(self):
        if not hasattr(self, '_username') or not self._username:
            self._username = self.whoami()
        return super(LocalHost, self).get_info()
