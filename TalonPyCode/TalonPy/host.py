"""Host.

Abstract Host class to control Node either remote or locally
"""

from abc import ABC, abstractmethod
import json
import logging
import tempfile
import shutil

logger = logging.getLogger(__name__)


class Host(ABC):

    """Summary
    """

    def __init__(self):
        self._address = None
        self._username = None

    def __del__(self):
        self.del_tmp_dir()

    @abstractmethod
    def read_file(self, filename, mode):
        raise NotImplementedError('This is an abstract method')

    @abstractmethod
    def write_file(self, filename, data, mode):
        raise NotImplementedError('This is an abstract method')

    @abstractmethod
    def execute_cmd(self, cmd, timeout):
        raise NotImplementedError('This is an abstract method')

    @abstractmethod
    def invoke_process(self, cmd):
        raise NotImplementedError('This is an abstract method')

    def get_tmp_dir(self):
        if not hasattr(self, '_tmp_dir') or not self._tmp_dir:
            logger.debug('Creating temporary file tree')
            self._tmp_dir = tempfile.mkdtemp()
        return self._tmp_dir

    def del_tmp_dir(self):
        if hasattr(self, '_tmp_dir') and self._tmp_dir:
            logger.debug('Deleting temporary file tree')
            shutil.rmtree(self._tmp_dir)
            self._tmp_dir = None

    def check_status(self):
        pass

    def find_process(self, rgx):
        pass

    def kill_process(self, rgx):
        pass

    def whoami(self):
        pass

    def get_kernel_version(self):
        system = self.execute_cmd('uname').decode('utf-8')[:-1]
        version = self.execute_cmd('uname -r').decode('utf-8')[:-1]
        return (system, version)

    def get_hostname(self):
        name = self.execute_cmd('hostname').decode('utf-8')[:-1]
        return name

    def get_info(self):
        info = {
            'kernel': self.get_kernel_version(),
            'user': self._username,
            'address': self._address,
            'hostname': self.get_hostname()
        }
        return info

    def print_info(self):
        print(json.dumps(self.get_info()))

