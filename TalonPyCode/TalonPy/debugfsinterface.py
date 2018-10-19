"""Summary

Attributes:
    logger (TYPE): Description
"""
from .helper import mac_addr_to_bytearray
import json
from collections import OrderedDict
import numpy as np
import re
import struct
import logging

logger = logging.getLogger(__name__)


class DebugFSException(Exception):
    pass


class DebugFSInterface(object):

    """Summary
    """

    def __init__(self, host, **kwargs):
        """Summary

        Args:
            host (TYPE): Description
            **kwargs: Description
        """
        loglevel = kwargs.get('loglevel', logging.INFO)
        logger.setLevel(loglevel)

        self._host = host
        self._dbgfs_dir = self._get_wil6210_debugfs_dir()

    def __del__(self):
        """Summary
        """
    pass

    def _get_wil6210_debugfs_dir(self):
        """Get wil6210 debugfs directory.
        """
        cmd = 'echo /sys/kernel/debug/ieee80211/'\
              '$(ls /sys/kernel/debug/ieee80211/| tail -1)/wil6210'
        dbgfs_dir = self._host.execute_cmd(cmd).decode()[:-1]
        logger.debug('Found DebugFS in %s' % dbgfs_dir)
        return dbgfs_dir

    def _read_debugfs_file(self, debugfsfile):
        """Get wil6210 debugfs file.
        """
        cmd = 'cat %s/%s' % (self._dbgfs_dir, debugfsfile)
        filecontent = self._host.execute_cmd(cmd).decode()[:-1]
        logger.debug('Getting DebugFS %s content (size %d)'
                     % (debugfsfile, len(filecontent)))
        return filecontent

    def get_bf(self):
        data = self._read_debugfs_file('bf')

        results = list()
        rx1 = re.compile(
            'CID\s+(\d+)\s+\{\n\s+TSF\s+=\s+(0x[0-9a-fA-F]+)\n' +
            '\s+TxMCS\s+=\s+(\d+)\s+TxTpt\s+=\s+(\d+)\n' +
            '\s+SQI\s+=\s+(\d+)\n' +
            '\s+Status\s+=\s+(0x[0-9a-fA-F]+)\s(\w+)\n' +
            '\s+Sectors\(rx\:tx\)\s+my\s+(\d+)\:\s*(\d+)' +
            '\s+peer\s+(\d+)\:\s*(\d+)\n' +
            '\s+Goodput\(rx\:tx\)\s+(\d+)\:\s*(\d+)\n}')
        rx2 = re.compile(
            'CID\s+(\d+)\s+\{\n\s+TSF\s+=\s+(0x[0-9a-fA-F]+)\n' +
            '\s+TxMCS\s+=\s+(\d+)\s+TxTpt\s+=\s+(\d+)\n' +
            '\s+SQI\s+=\s+(\d+)\n' +
            '\s+RSSI\s+=\s+\d+\n' +
            '\s+Status\s+=\s+(0x[0-9a-fA-F]+)\s(\w+)\n' +
            '\s+Sectors\(rx\:tx\)\s+my\s+(\d+)\:\s*(\d+)' +
            '\s+peer\s+(\d+)\:\s*(\d+)\n' +
            '\s+Goodput\(rx\:tx\)\s+(\d+)\:\s*(\d+)\n}')

        if len(data) == 0:
            return results
        elif rx1.match(data):
            bf_dump = rx1.findall(data)
        elif rx2.match(data):
            bf_dump = rx2.findall(data)
        else:
            raise AttributeError('Invalid DebugFS Content')

        for bf in bf_dump:

            r = OrderedDict([
                ('CID', bf[0]),
                ('TSF', bf[1]),
                ('TxMCS', bf[2]),
                ('TxTpt', bf[3]),
                ('SQI', bf[4]),
                ('StatusID', bf[5]),
                ('StatusType', bf[6]),
                ('RxSector', bf[7]),
                ('TxSector', bf[8]),
                ('RxSectorPeer', bf[9]),
                ('TxSectorPeer', bf[10]),
                ('RxGoodput', bf[11]),
                ('TxGoodput', bf[12])
                ])

            results.append(r)
        return results

    def get_fw_version(self):
        """Get wil6210 firmware version.
        """
        rx = re.compile('(\d+)\.(\d+)\.(\d+)\.(\d+)')
        v = self._read_debugfs_file('fw_version')
        if not rx.match(v):
            raise DebugFSException('Invalid DebugFS Response, ' +
                                   'check if firmware is running.')
        if returnformat == 'str':
            return v
        elif returnformat == 'num':
            r = rx.findall(v)
            return list(map(int, r[0]))
        else:
            raise AttributeError('Wrong Return Format: %s' % returnformat)

    def get_hw_version(self):
        """Get QCA9500 Hardware Version.
        """
        return int(self._read_debugfs_file('hw_version'), 0)

    def get_stations(self):
        data = self._read_debugfs_file('stations')

        results = list()
        rx = re.compile('\[(\d)\]\s+([0-9a-fA-F:]{17})\s+([a-zA-Z]+)\s+AID' +
                        '\s+(\d)(\n[^\[].*)?(\n[^\[].*)?(\n[^\[].*)?',
                        re.MULTILINE)
        rx2 = re.compile('.*?total\s+(\d+)\s+drop\s+(\d+)\s+\(dup\s+(\d+).+?' +
                         'old\s+(\d+)')
        rx3 = re.compile('Rx\sinvalid\sframe\:\s+non-data\s(\d+).*(\d+).*' +
                         '(\d+).+replay\s+(\d+)')
        rx4 = re.compile('Rx\/MCS\:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)' +
                         '\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)' +
                         '\s+(\d+)\s+(\d+)')
        mcs_zero = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        stations_dump = rx.findall(data)

        for sta in stations_dump:
            dump2 = rx2.findall(sta[4])
            dump3 = rx3.findall(sta[5])
            dump4 = rx4.findall(sta[6])

            r = OrderedDict([
                ('CID', sta[0]),
                ('MAC', sta[1]),
                ('Status', sta[2]),
                ('AID', sta[3]),
                ('PktsTotal', dump2[0][0] if len(dump2) > 0 else -1),
                ('PktsDrop', dump2[0][1] if len(dump2) > 0 else -1),
                ('PktsDup', dump2[0][2] if len(dump2) > 0 else -1),
                ('PktsOld', dump2[0][3] if len(dump2) > 0 else -1),
                ('InvNondata', dump3[0][0] if len(dump3) > 0 else -1),
                ('InvShort', dump3[0][1] if len(dump3) > 0 else -1),
                ('InvLarge', dump3[0][2] if len(dump3) > 0 else -1),
                ('InvReplay', dump3[0][3] if len(dump3) > 0 else -1),
                ('RxMCS', list(map(int, dump4[0])) if len(dump4) > 0 else
                    mcs_zero)])
            results.append(r)
        return results

    def get_status(self):
        """Parse Status DebugFS File.
        """
        status = self._read_debugfs_file('status[0]')
        if len(status) == 0:
            return 0
        return int(status, 16)

    def get_sweep_dump(self, to_be_updated=list()):
        """Summary
        """
        data = self._read_debugfs_file('sweep_dump')

        # Parse information to list
        sweepinfo = list()

        # Load the sweep counter
        swpctr = int(re.findall('Counter:\s+(\d+)\s+swps', data)[0])

        if swpctr == 0:
            logger.error('No sweeps found to be parsed')

        else:
            # Load the sweeps from table
            sweeps = re.findall(
                '\[sec:\s+(\d+)\srssi:\s+(\d+)\s+snr:\s+(-?\d+)\s+qdB',
                data)

            # Append sweep number to data
            last_id = int(sweeps[-1][0])
            cur_ctr = swpctr

            # Iterate backwards over all sweeps
            for n in range(len(sweeps) - 1, -1, -1):
                cur_sector_id = int(sweeps[n][0])
                # Check if current ID is greater then the last one
                # This is to check if this is a different sweep
                if cur_sector_id > last_id:
                    cur_ctr = cur_ctr - 1

                # Append results
                if cur_ctr > 0:
                    # TODO: FIX MAC String
                    sweepinfo.append({
                        'sweep': cur_ctr,
                        'sector': cur_sector_id,
                        'rssi': int(sweeps[n][1]),
                        'snr': int(sweeps[n][2]) / 4,
                        'mac': str(0)})
                last_id = cur_sector_id

            sweepinfo.reverse()

        # Combine results with to_be_updated from last call
        mysweepids = set([s['sweep'] for s in to_be_updated])
        sweepinfo = [s for s in sweepinfo if
                     s['sweep'] not in mysweepids]

        to_be_updated.extend(sweepinfo)
        return to_be_updated

    def get_temp(self):
        pass

    def send_debug_mgmt_frame_raw(self, framedata):
        fb_arr = list(map(lambda x: '{:02x}'.format(int(x)), framedata))
        fb = '\\x' + '\\x'.join(fb_arr)
        cmd = 'echo -n -e \'%s\' > %s/tx_mgmt'\
            % (fb, self._dbgfs_dir)
        logger.debug('Injecting mgmt frame: %s' % cmd)
        out = self._host.execute_cmd(cmd)
        return out

    def send_debug_mgmt_frame(self, frame_type, dst, src, bss, payload):    
        fcf = bytearray(struct.pack('H', frame_type))
        dur = bytearray.fromhex('b907')
        src_b = mac_addr_to_bytearray(src)
        dst_b = mac_addr_to_bytearray(dst)
        bss_b = mac_addr_to_bytearray(bss)
        seq_id = bytearray(2)

        frame = fcf + dur + dst_b + src_b + bss_b + seq_id + payload
        return self.send_debug_mgmt_frame_raw(frame)
