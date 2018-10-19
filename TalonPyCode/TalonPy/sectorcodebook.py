"""SectorCodebook.

Implements a codebook of sector definitions
"""

from tabulate import tabulate
from collections import OrderedDict
import json


class SectorCodebook(object):
    """Sector Codebook.

    Implements a codebook of Sectors with methods to adjust
    """

    RF_SECTOR_TYPE_RX = 0x00
    RF_SECTOR_TYPE_TX = 0x01

    _max_sectors = 64

    # The default sector, is the original sector 63
    default_sector = {
        'QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_INDEX': 0,
        'QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE0': '00200000',
        'QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE1': '8c80a002',
        'QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE2': '8ca0a002',
        'QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_HI': '639c00e3',
        'QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_LO': 'eaa21160',
        'QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16': '30db0c06'
    }

    null_sector = {
        'QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_INDEX': 0,
        'QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE0': '0x00000000',
        'QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE1': '0x00000000',
        'QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE2': '0x00000000',
        'QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_HI': '0x00000000',
        'QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_LO': '0x00000000',
        'QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16': '0x00000000'
    }

    def __init__(self, definitions=None):
        if not definitions:
            self._sectors = list()
        else:
            self._sectors = definitions

    def initialize_default(self, number):
        self._sectors = list()
        for n in range(0, number):
            self.add_sector(self.default_sector.copy())

    def get_sector(self, idx):
        return self._sectors[idx]

    def set_sector(self, idx, sector):
        self._sectors[idx] = sector

    def add_sector(self, sector):
        self._sectors.append(sector.copy())

    def add_sectors(self, sectors):
        for s in sectors:
            self.add_sector(s)

    def rem_sector(self, idx):
        sector = self._sectors[idx]
        self._sectors[idx] = []
        return sector

    def get_psh_reg(self, idx):
        data = self._sectors[idx]
        # Phase values for RF Chains[15-0] (2bits per RF chain)
        psh_lo = int(data['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_LO'], 16)
        # Phase values for RF Chains[31-16] (2bits per RF chain) */
        psh_hi = int(data['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_HI'], 16)

        psh = [0] * 32
        for n in range(0, 32):
            if n >= 16:
                psh[n] = (psh_hi & (0x3 << ((n-16) * 2))) >> ((n-16) * 2)
            else:
                psh[n] = (psh_lo & (0x3 << (n * 2))) >> (n * 2)
        return psh

    def set_psh_reg(self, idx, value):
        if not (type(value) is list and len(value) == 32):
            raise AttributeError('Value should be list of 32 elements')

        psh_lo = 0x00
        psh_hi = 0x00

        for n in range(0, 32):
            v = value[n] & 0x3
            if n >= 16:
                psh_hi |= v << (2 * (n-16))
            else:
                psh_lo |= v << (2 * n)

        scfg = self._sectors[idx]
        scfg['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_LO'] = '%08x' % (psh_lo % 0x100000000) 
        scfg['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_HI'] = '%08x' % (psh_hi % 0x100000000) 
        self._sectors[idx] = scfg

    def get_etype_reg(self, idx):
        data = self._sectors[idx]

        # ETYPE Bit0 for all RF chains[31-0] - bit0 of Edge amplifier gain
        etype0 = int(data['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE0'], 16)
        # ETYPE Bit1 for all RF chains[31-0] - bit1 of Edge amplifier gain
        etype1 = int(data['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE1'], 16)
        # ETYPE Bit2 for all RF chains[31-0] - bit2 of Edge amplifier gain
        etype2 = int(data['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE2'], 16)

        etype = [0] * 32
        for n in range(0, 32):
            etype[n] |= (etype0 >> n) % 2
            etype[n] |= ((etype1 >> n) % 2) << 1
            etype[n] |= ((etype2 >> n) % 2) << 2
        return etype

    def set_etype_reg(self, idx, value):
        if not (type(value) is list and len(value) == 32):
            raise AttributeError('Value should be list of 32 elements')

        etype0 = 0x00
        etype1 = 0x00
        etype2 = 0x00

        for n in range(0, 32):
            v = value[n]
            etype0 |= ((v >> 0) % 2) << n
            etype1 |= ((v >> 1) % 2) << n
            etype2 |= ((v >> 2) % 2) << n

        scfg = self._sectors[idx]
        scfg['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE0'] = '%08x' % (etype0 % 0x100000000) 
        scfg['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE1'] = '%08x' % (etype1 % 0x100000000) 
        scfg['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE2'] = '%08x' % (etype2 % 0x100000000) 
        self._sectors[idx] = scfg

    def get_dtype_reg(self, idx):
        data = self._sectors[idx]
        # D-Type values (3bits) for 8 Distribution amplifiers + X16 switch bits
        dt_x16 = int(data['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16'], 16)

        dtypes = [0] * 8
        for n in range(0, 8):
            dtypes[n] = (dt_x16 & (0x7 << (n * 3))) >> (n * 3)
        return dtypes

    def set_dtype_reg(self, idx, value):
        if not (type(value) is list and len(value) == 8):
            raise AttributeError('Value should be list of 8 elements')

        scfg = self._sectors[idx]
        dt_x16 = int(scfg['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16'], 16)
        dt_x16 = (dt_x16 & 0xff000000)

        for n in range(0, 8):
            v = value[n] & 0x7
            dt_x16 |= v << (n*3)

        scfg['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16'] = '%08x' % (dt_x16 % 0x100000000) 
        self._sectors[idx] = scfg

    def get_x16_reg(self, idx):
        data = self._sectors[idx]

        # D-Type values (3bits) for 8 Distribution amplifiers + X16 switch bits
        dt_x16 = int(data['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16'], 16)

        x16 = (dt_x16 & 0xff000000) >> 24
        return x16

    def set_x16_reg(self, idx, value):
        if not (type(value) is int):
            raise AttributeError('Value should be integer')

        scfg = self._sectors[idx]
        dt_x16 = int(scfg['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16'], 16)
        dt_x16 = (dt_x16 & 0x00ffffff)
        dt_x16 |= (value & 0xff) << 24

        scfg['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16'] = '%08x' % (dt_x16 % 0x100000000) 
        self._sectors[idx] = scfg

    def get_sector_id(self, idx):
        data = self._sectors[idx]
        if 'QCA_ATTR_DMG_RF_SECTOR_INDEX' in data:
            return data['QCA_ATTR_DMG_RF_SECTOR_INDEX']
        else:
            return None

    def num_sectors(self):
        return len(self._sectors)

    def get_params(self, idx):
        params = OrderedDict()
        params['idx'] = idx
        params['sid'] = self.get_sector_id(idx)
        params['psh'] = self.get_psh_reg(idx)
        params['etype'] = self.get_etype_reg(idx)
        params['dtype'] = self.get_dtype_reg(idx)
        params['x16'] = self.get_x16_reg(idx)
        return params

    def print_overview(self):

        paramlist = list()

        # Iterate over all sectors
        for idx in range(0, len(self._sectors)):
            params = OrderedDict()
            params['idx'] = idx
            params['sid'] = self.get_sector_id(idx)
            params['psh'] = self.get_psh_reg(idx)
            params['etype'] = self.get_etype_reg(idx)
            params['dtype'] = self.get_dtype_reg(idx)
            params['x16'] = self.get_x16_reg(idx)
            paramlist.append(params)

        print(tabulate(paramlist, headers='keys'))

    def dump(self):
        return json.dumps(self._sectors, indent=4)

    # def split(self, max_size):
    #     n_groups = int(np.ceil(self.num_sectors() / max_size))

    #     groups = list()
    #     for n in range(0, n_groups):
    #         group = self._sectors[n * max_size:(n+1) * max_size]
    #         groups.append(SectorCodebook(group))
    #     return groups

    def get_raw(self):
        return self._sectors
