from .sectorcommandinterface import SectorCommandInterface
from .debugfsinterface import DebugFSInterface
from .sweepstatistics import SweepStatistics
from .remotehost import RemoteHost
from .localhost import LocalHost
import logging
import re
import time

logger = logging.getLogger(__name__)

class Talon(object):

    SECTOR_TYPE_RX = SectorCommandInterface.RF_SECTOR_TYPE_RX
    SECTOR_TYPE_TX = SectorCommandInterface.RF_SECTOR_TYPE_TX

    _valid_sectors = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                      17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 
                      31, 59, 60, 61, 62, 63]

    def __init__(self, address=None, **kwargs):

#        loglevel = kwargs.get('loglevel', logging.DEBUG)
        loglevel = kwargs.get('loglevel', logging.CRITICAL)
        logger.setLevel(loglevel)

        if not address:
            self._host = LocalHost()
        else:
            self._host = RemoteHost(address, **kwargs)
            self._host.connect()

        self._sectorcmdiface = SectorCommandInterface(self._host)
        self._debugfsiface = DebugFSInterface(self._host)

    def get_sector_codebook(self, sectortype, sectors=None):
        sectors = self._valid_sectors if not sectors else sectors
        return self._sectorcmdiface.get_sector_codebook(sectortype, sectors)

    def set_sector_codebook(self, sectortype, codebook, sectors=None):
        sectors = self._valid_sectors if not sectors else sectors
        return self._sectorcmdiface.set_sector_codebook(sectortype, codebook, sectors)

    def get_sweep_statistics(self):
        dump = self._debugfsiface.get_sweep_dump()
        stats = SweepStatistics(dump)
        # TODO: Extend this to filter for specific data
        stats.get_summary('0')
        return stats

    def collect_sweep_statistics(self, num_sweeps, timeout, force_reassoc=False):
        dump = self._debugfsiface.get_sweep_dump()
        swpstats = SweepStatistics(dump)
        swpstats.trigger_measurement_start()

        addr_src = self.get_wlan2_mac_address()
        addr_dst = self._debugfsiface.get_stations()[0]['MAC']

        logger.info('Collecting sweeps at %s for station %s' % (addr_src, addr_dst) )

        tic = time.time()
        while time.time() < (tic + timeout):

            # Send reassociation frame to force reconnections
            if force_reassoc:
                self.send_debug_association_frame(addr_dst, addr_src, addr_dst)
                self.wait_for_sta_connected(addr_dst)
                time.sleep(0.01)

            # Collect new dump and update
            dump = self._debugfsiface.get_sweep_dump()
            swpstats.update(dump)

            if swpstats.get_num_sweeps() >= num_sweeps:
                time_consumed = int(time.time() - tic)
                logger.info('Collecting %d sweeps completed after %d seconds.' 
                            % (num_sweeps, time_consumed))
                return swpstats.get_current()

        logger.info('Timeout Found %d sweep durations' % swpstats.get_num_sweeps())
        raise TimeoutError('Taking Sweep Measurements took to long')

    def reassociate(self):
        addr_src = self.get_wlan2_mac_address()
        addr_dst = self._debugfsiface.get_stations()[0]['MAC']
        self.send_debug_association_frame(addr_dst, addr_src, addr_dst)
        self.wait_for_sta_connected(addr_dst)
        time.sleep(0.01)

    def send_debug_association_frame(self, dst, src, bss):
        fcf = 0x00
        payload = bytearray.fromhex('100005006400000854414c4f4e5f41442e010c3' +
                                    'b02b4b4941104ce140aae180011d1b706000040' +
                                    '100000dd0f506f9a170109000704ce140aae1800')
        return self._debugfsiface.send_debug_mgmt_frame(fcf, dst, src, bss, payload)

    def send_debug_disassociation_frame(self, dst, src, bss):
        fcf = 0x0A
        payload = bytearray.fromhex("0100")
        return self._debugfsiface.send_debug_mgmt_frame(fcf, dst, src, bss, payload)

    def get_station_info(self):
        sta_info = self._debugfsiface.get_stations()
        bf_info = self._debugfsiface.get_bf()

        for bf in bf_info:
            sta = [sta for sta in sta_info if sta['CID'] == bf['CID']][0]
            bf.update(sta)
        return bf_info

    def get_wlan2_mac_address(self):
        # Todo: Move this to external interface
        rx = re.compile('HWaddr\s+([0-9a-fA-F:]{17})')
        cmd = 'ifconfig wlan2'
        response = self._host.execute_cmd(cmd).decode()
        return rx.findall(response)[0]

    def check_sta_connected(self, host):
        for sta in self.get_station_info():
            if sta['MAC'].lower() == host.lower() and\
               sta['StatusType'] == 'OK':
                return True
        return False

    def wait_for_sta_connected(self, host, timeout=5):
        tic = time.time()

        while(time.time() < (tic + timeout)):
            if self.check_sta_connected(host):
                return True
            time.sleep(0.01)
        raise TimeoutError('STA not connected after %d s' % timeout)

    def wait_for_fw_ready(self, timeout=5):
        """Wait for Firmware to report OK
        """
        tic = time.time()
        while(time.time() < tic + timeout):
            if self._debugfsiface.get_status() == 0x75:
                return True
            time.sleep(0.01)
        raise TimeoutError(
            'Firmware not ready after timeout of %d seconds.' % timeout)

