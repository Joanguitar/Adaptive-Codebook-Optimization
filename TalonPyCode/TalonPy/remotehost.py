"""Summary

Attributes:
    logger (TYPE): Description
"""

from .host import Host
import logging
import os
import paramiko
import scp

logger = logging.getLogger(__name__)

class RemoteHostException(Exception):

    """Summary
    """
    
    pass


class RemoteHost(Host):

    """Summary
    """

    def __init__(self, host, **kwargs):
        """Summary
        
        Args:
            host (TYPE): Description
            **kwargs: Description
        """
        super().__init__()
        self._host = host
        self._username = kwargs.get('username', 'root')
        self._password = kwargs.get('password')
        loglevel = kwargs.get('loglevel', logging.INFO)
        logger.setLevel(loglevel)

        logger.debug('Remote Host Object instantiated')

    def __del__(self):
        self.disconnect()

    def read_file(self, filename, mode):
        """Summary
        
        Args:
            filename (TYPE): Description
            mode (TYPE): Description
        
        Raises:
            NotImplementedError: Description
        """


        #         if self.is_connected():
#             lpath = self.pull(filepath)
#             print('Copied to %s' % lpath)
#             flag = 'rb' if binary else 'r'

#             with open(lpath, flag) as f:
#                 data = f.read()
#             return bytearray(data) if binary else data
#         else:
#             raise Exception('Remote Node not connected')
        raise NotImplementedError()

    def write_file(self, filename, data, mode):
        """Summary
        
        Args:
            filename (TYPE): Description
            data (TYPE): Description
            mode (TYPE): Description
        
        Raises:
            NotImplementedError: Description
        """

        #         if self.is_connected():
#             flag = 'wb' if binary else 'w'

#             # Write local file
#             lpath = self._tmp_dir + os.sep + os.path.basename(filepath)
#             os.makedirs(os.path.dirname(lpath), exist_ok=True)
#             with open(lpath, flag) as f:
#                 f.write(data)

#             # Push file to remote
#             self.put(lpath, filepath)

#         else:
#             raise Exception('Remote Node not connected')

        raise NotImplementedError()

    def execute_cmd(self, cmd, timeout=10):
        """Summary
        
        Args:
            cmd (TYPE): Description
        
        Raises:
            NotImplementedError: Description
        """

        if self.check_connection():
            logger.debug('Executing command %s at %s ...' % (cmd, self._host))

            try:
                # Invoke command
                stdin, stdout, stderr = self._ssh.exec_command(cmd, timeout=timeout)
                # Wait for command to complete
                stdout.channel.recv_exit_status()
            except Exception:
                logger.error('Executing command failed ...')

            for line in stderr.readlines():
                logger.error(line)

            # TODO: Push STDERR to log ...
            result = stdout.read()
            return result
        else:
            raise RemoteHostException('Could not execute command, remote host not connected')


    def invoke_process(self, cmd):
        """Summary
        
        Args:
            cmd (TYPE): Description
        
        Raises:
            NotImplementedError: Description
        """
        raise NotImplementedError()

    def connect(self, timeout=2):
        """Summary
        
        Args:
            timeout (int, optional): timeout (in seconds) for the TCP connection
        
        Returns:
            TYPE: Description
        """

        logger.info('Connecting to remote host at %s ...' % self._host)

        if hasattr(self, '_ssh') and self._ssh:
            self._ssh.disconnect()
            logger.info('Remote Host already connected, disconnecting')

        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self._ssh.connect(
                self._host,
                username=self._username,
                password=self._password,
                timeout=timeout)
        except paramiko.AuthenticationException:
            logger.critical("Authentication Error for Host %s,\
                please check your credentials" % self._host)
            self._ssh = None
            return
        except paramiko.SSHException:
            logger.critical("Could not connect to %s,\
                please check your network" % self._host)
            self._ssh = None
            return

        # TODO: catch: pramiko.BadHostKeyException
        # TODO: catch: pramiko.socket.error

        logger.debug('Connection established')

    def disconnect(self):
        """Summary
        """
        if hasattr(self, '_ssh') and self._ssh:
            logger.debug('Disconnecting from remote host at %s ...' % self._host)
            self._ssh.close()
            self._ssh = None
            self.del_tmp_dir()

    def check_connection(self):
        """Summary
        
        Returns:
            TYPE: Description
        """
        if self._ssh and self._ssh.get_transport().is_active():
            return True
        return False

    def get_remote_tmp_dir(self):
        """Summary
        
        Raises:
            NotImplementedError: Description
        """
        raise NotImplementedError()

    def put(self, lfile, rfile):
        """Push file to remote host.

        Decription goes here.
        """
        logger.debug('Putting file %s to %s at %s ...' % (lfile, rfile, self._host))
        if self.check_connection():
            myscp = scp.SCPClient(self._ssh.get_transport())
            myscp.put(lfile, rfile)

    def pull(self, rpath):
        """Pull file from remote Node and return local temporary file name

        Decription goes here.
        """

        # Create temporary file 
        tmp_dir = self.get_tmp_dir()
        lpath = tmp_dir + os.sep + os.path.basename(rpath)

        if self.check_connection():
            myscp = scp.SCPClient(self._ssh.get_transport())
            myscp.get(remote_path=rpath, local_path=lpath)

            logger.debug('Pulling file %s from %s at %s ...' % (lpath, rpath, self._host))
            return lpath
        else:
            raise Exception('Remote Node not connected')



#     def execute(self, cmd, blocking=True):
#         """Invoke remote command.

#         Description goes here
#         """
#         if self.is_connected():
#             stdin, stdout, stderr = self._ssh.exec_command(cmd)

#             if blocking:
#                 stdout.channel.recv_exit_status()
#             return stdout
#         else:
#             raise Exception('Remote Node not connected')

#     def call_process(self, cmd):
#         """Invoke call.

#         Description goes here
#         """
#         transport = self._ssh.get_transport()
#         transport.set_keepalive(1)
#         channel = transport.open_session()
#         channel.exec_command(cmd)
#         return channel