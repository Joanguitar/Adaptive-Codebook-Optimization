from .nlvendorattrparser import nl_encode, nl_decode
from .sectorcodebook import SectorCodebook
from .helper import mac_addr_to_int
import json
import pkg_resources
from collections import OrderedDict
import numpy as np
import re
import struct
import logging

logger = logging.getLogger(__name__)

class SectorCommandInterface(object):

    RF_SECTOR_TYPE_RX = 0x00
    RF_SECTOR_TYPE_TX = 0x01

    QCA_NL80211_VENDOR_SUBCMD_DMG_RF_GET_SECTOR_CFG = "0x8b"
    QCA_NL80211_VENDOR_SUBCMD_DMG_RF_SET_SECTOR_CFG = "0x8c"
    QCA_NL80211_VENDOR_SUBCMD_DMG_RF_GET_SELECTED_SECTOR = "0x8d"
    QCA_NL80211_VENDOR_SUBCMD_DMG_RF_SET_SELECTED_SECTOR = "0x8e"

    def __init__(self, host, **kwargs):
#        loglevel = kwargs.get('loglevel', logging.DEBUG)
        loglevel = kwargs.get('loglevel', logging.CRITICAL)
        logger.setLevel(loglevel)

        self._host = host
        self._nl_policy = self._get_nl_attr_default_policy()

    def __del__(self):
        pass

    def _get_nl_attr_default_policy(self):
        policy = pkg_resources.resource_string(
            __name__, 'data/wil_rf_sector_policy.json')
        return json.loads(policy.decode())

    def call_nl_vendor_command(self, request, command_id, policy):
        """Call NL Vendor command.

        Provides access to NL Vendor commands.
        """
        # TODO: Check capability ...

        # Encode the request
        logger.debug('Invoking nl vendor command: %s' % json.dumps(request))
        nla_request = nl_encode(request, policy)
        nla_req_f = list(map(lambda x: '{:02x}'.format(int(x)), nla_request))
        nla_req_f = '\\x' + '\\x'.join(nla_req_f)

        cmd = "echo -n -e \'%s\' | iw dev wlan2 vendor recv 0x001374 %s \
              - " % (nla_req_f, command_id)
        pid = self._host.execute_cmd(cmd)
        response = pid.decode()

        nla_stream_bytes = re.findall('[0-9a-fA-F]{2}', response)
        nla_stream_bytes = bytearray.fromhex(''.join(nla_stream_bytes))

        # Decode the stream
        data = nl_decode(nla_stream_bytes, policy)
        logger.debug('Response: %s' % json.dumps(response))
        return data

    def get_vendor_selected_sector(self, sector_type, peer_addr):
        """Get selected sector from NL vendor commands.

        Provides access to low level API
        """
        # Create the request
        request = OrderedDict()
        request['QCA_ATTR_DMG_RF_SECTOR_TYPE'] = sector_type
        request['QCA_ATTR_MAC_ADDR'] = mac_addr_to_int(peer_addr)

        # Call the vendor cmd
        vendor_cmd = self.QCA_NL80211_VENDOR_SUBCMD_DMG_RF_GET_SELECTED_SECTOR
        response = self.call_nl_vendor_command(request, vendor_cmd, self._nl_policy)

        # Shorten the results
        results = OrderedDict()
        try:
            results['QCA_ATTR_TSF'] = response['QCA_ATTR_TSF']['value_raw']
            results['QCA_ATTR_DMG_RF_SECTOR_INDEX'] =\
                response['QCA_ATTR_DMG_RF_SECTOR_INDEX']['value']
            results['QCA_ATTR_DMG_RF_SECTOR_TYPE'] =\
                request['QCA_ATTR_DMG_RF_SECTOR_TYPE']
            results['QCA_ATTR_MAC_ADDR'] = request['QCA_ATTR_MAC_ADDR']
        except KeyError:
            print('Key error in get_vendor_selected_sector, aborting')
        return results

    def set_vendor_selected_sector(self, sector_type, peer_addr, sector_index):
        """Get selected sector from NL vendor commands.

        Provides access to low level API
        """
        # Create the request
        request = OrderedDict()
        request['QCA_ATTR_DMG_RF_SECTOR_TYPE'] = sector_type
        request['QCA_ATTR_MAC_ADDR'] = self._mac_addr_to_int(peer_addr)
        request['QCA_ATTR_DMG_RF_SECTOR_INDEX'] = sector_index

        # Call the vendor cmd
        vendor_cmd = self.QCA_NL80211_VENDOR_SUBCMD_DMG_RF_SET_SELECTED_SECTOR
        self.call_nl_vendor_command(request, vendor_cmd, self._nl_policy)

    def get_vendor_sector_cfg(self, sector_type, sector_index):
        """Get sector config from NL vendor commands.

        Provides access to low level API
        """
        # Create the request
        request = OrderedDict()
        request['QCA_ATTR_DMG_RF_SECTOR_INDEX'] = sector_index
        request['QCA_ATTR_DMG_RF_SECTOR_TYPE'] = sector_type
        request['QCA_ATTR_DMG_RF_MODULE_MASK'] = 0x01

        # Call the vendor cmd
        vendor_cmd = self.QCA_NL80211_VENDOR_SUBCMD_DMG_RF_GET_SECTOR_CFG
        response = self.call_nl_vendor_command(request, vendor_cmd, self._nl_policy)

        # Shorten the results
        shortresp = response['QCA_ATTR_DMG_RF_SECTOR_CFG']['value']
        shortresp = shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_0']['value']

        results = OrderedDict()
        try:
            results['QCA_ATTR_TSF'] = response['QCA_ATTR_TSF']['value_raw']
            results['QCA_ATTR_DMG_RF_SECTOR_INDEX'] =\
                request['QCA_ATTR_DMG_RF_SECTOR_INDEX']
            results['QCA_ATTR_DMG_RF_SECTOR_TYPE'] =\
                request['QCA_ATTR_DMG_RF_SECTOR_TYPE']
            results['QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_INDEX'] =\
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_INDEX']['value']
            results['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE0'] =\
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE0']['value_raw']
            results['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE1'] =\
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE1']['value_raw']
            results['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE2'] =\
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE2']['value_raw']
            results['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_HI'] =\
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_HI']['value_raw']
            results['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_LO'] =\
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_LO']['value_raw']
            results['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16'] =\
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16']['value_raw']
        except KeyError:
            print('Key error in get_vendor_sector_cfg, aborting')
        return results

    def set_vendor_sector_cfg(self, sector_type, sector_index, sector_cfg):
        """Set sector config with NL vendor commands.

        Provides access to low level API
        """
        # Create the request
        request = OrderedDict()
        request['QCA_ATTR_DMG_RF_SECTOR_INDEX'] = sector_index
        request['QCA_ATTR_DMG_RF_SECTOR_TYPE'] = sector_type

        cfg_request = OrderedDict()
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_INDEX'] =\
            sector_cfg['QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_INDEX']
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE0'] =\
            int(sector_cfg['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE0'], 16)
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE1'] =\
            int(sector_cfg['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE1'], 16)
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE2'] =\
            int(sector_cfg['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE2'], 16)
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_HI'] =\
            int(sector_cfg['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_HI'], 16)
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_LO'] =\
            int(sector_cfg['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_LO'], 16)
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16'] =\
            int(sector_cfg['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16'], 16)

        cfg_module_request = OrderedDict()
        cfg_module_request['QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_0'] = \
            cfg_request

        request['QCA_ATTR_DMG_RF_SECTOR_CFG'] = OrderedDict()
        request['QCA_ATTR_DMG_RF_SECTOR_CFG'] =\
            cfg_module_request

        # Call the vendor cmd
        vendor_cmd = self.QCA_NL80211_VENDOR_SUBCMD_DMG_RF_SET_SECTOR_CFG
        self.call_nl_vendor_command(request, vendor_cmd, self._nl_policy)

    def get_sector_codebook(self, sectortype, sectors=[n for n in range(0, 64)]):

        if not type(sectors) == list:
            raise AttributeError('Sectors should be list')

        codebook = list()
        for s in sectors:
            sector = self.get_vendor_sector_cfg(sectortype, s)
            codebook.append(sector)
        return SectorCodebook(codebook)

    def set_sector_codebook(self, sectortype, codebook, sectors=[n for n in range(0, 64)]):
        if not type(sectors) == list:
            raise AttributeError('Sectors should be list')
        if not len(sectors) == codebook.num_sectors():
            raise AttributeError(
                'Invalid Codebook length (is %d should be %s)'
                % (codebook.num_sectors(), len(sectors)))

        for s in range(0, len(sectors)):
            self.set_vendor_sector_cfg(
                sectortype, sectors[s], codebook.get_sector(s))
