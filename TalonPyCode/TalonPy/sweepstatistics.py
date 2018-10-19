from collections import OrderedDict
from tabulate import tabulate
import logging
import re
import numpy as np

logger = logging.getLogger(__name__)

class EmptySweepDumpException(Exception):
    pass


class SweepStatistics(object):
    """Sweep Statistics.

    Provides basic statistics to handle Sweep results
    """

    ci_bounds = [2.5, 50, 97.5]  # 95% confidence bounds

    def __init__(self, sweepdump, **kwargs):
        """Initilaize.

        Initializes with optional argument
        """
        loglevel = kwargs.get('loglevel', logging.DEBUG)
        logger.setLevel(loglevel)

        self.purge()
        self.update(sweepdump)

    def update(self, sweepdump):
        cmax_swps = self.get_max_sweeps()

        if len(sweepdump) == 0:
            logger.error('Parsing empy sweep dump, omitting update')
            return False

        # Filter new dump for updated values
        myupdates = [s for s in sweepdump if s['sweep'] > cmax_swps]

        if len(myupdates) > 0:
            # Updating new sweep information
            max_update = max([0] + [s['sweep'] for s in myupdates])
            logger.debug('Updating Sweep Info with %d measurements (counter %d)'
                         % (len(myupdates), max_update))
            self.sweepinfo.extend(myupdates)
            return True

        # No updates found
        return False

    def trigger_measurement_start(self):
        self._start_new_scope()

    def purge(self):
        self.sweepinfo = list()
        self._set_min_sweep(0)

    def _start_new_scope(self):
        max_sweeps = self.get_max_sweeps()
        self._set_min_sweep(max_sweeps)

    def _set_min_sweep(self, min_sweep):
        logger.debug('Setting min sweep counter to %d' % min_sweep)
        self._min_sweep = min_sweep

    def get_max_sweeps(self):
        return max([0] + [s['sweep'] for s in self.sweepinfo])

    def get_num_sweeps(self):
        return len(set([s['sweep'] for s in self.sweepinfo
                       if s['sweep'] > self._min_sweep]))

    def get_num_sweeps_per_sector(self, sector):
        return len(set([s['sweep'] for s in self.sweepinfo
                        if s['sweep'] > self._min_sweep and
                        s['sector'] == sector]))

    def get_current(self):
        return [s for s in self.sweepinfo if s['sweep'] > self._min_sweep]

    def get_sectors(self):
        return list(set([s['sector'] for s in self.sweepinfo]))

    def get_sweep_ids(self):
        return list(set([s['sweep'] for s in self.sweepinfo]))

    def get_rssi_per_sector(self, host, sectors='all'):
        if sectors == 'all':
            sectors = self.get_sectors()
        elif type(sectors) is not list:
            sectors = [sectors]

        values = list()
        for sec in sectors:
            myrssi = [s['rssi'] for s in self.sweepinfo if
                      s['mac'] == host and s['sector'] == sec and
                      s['rssi'] != 0]
            values.append(myrssi)
        return values

    def get_rssi_mean(self, host, sectors='all'):
        values = list()
        for rssi in self.get_rssi_per_sector(host, sectors):
            if len(rssi) == 0:
                values.append(None)
            else:
                values.append(int(round(np.mean(rssi))))
        if sectors == 'all' or type(sectors) is list:
            return values
        return values[0]

    def get_rssi_percentiles(self, host, sectors='all'):
        values = list()
        ptiles = self.ci_bounds
        for rssi in self.get_rssi_per_sector(host, sectors):
            if len(rssi) == 0:
                values.append(None)
            else:
                values.append(
                    np.round(np.percentile(rssi, ptiles)))
        if sectors == 'all' or type(sectors) is list:
            return values
        return values[0]

    def get_rssi_std(self, host, sectors='all'):
        values = list()
        for rssi in self.get_rssi_per_sector(host, sectors):
            if len(rssi) == 0:
                values.append(None)
            else:
                values.append(
                    np.round(np.std(rssi)))
        if sectors == 'all' or type(sectors) is list:
            return values
        return values[0]

    def get_rssi_num(self, host, sectors='all'):
        values = list()
        for rssi in self.get_rssi_per_sector(host, sectors):
            if len(rssi) == 0:
                values.append(0)
            else:
                values.append(len(rssi))
        if sectors == 'all' or type(sectors) is list:
            return values
        return values[0]

    def get_snr_per_sector(self, host, sectors='all'):
        if sectors == 'all':
            sectors = self.get_sectors()
        elif type(sectors) is not list:
            sectors = [sectors]

        values = list()
        for sec in sectors:
            mysnr = [s['snr'] for s in self.sweepinfo if
                     s['mac'] == host and s['sector'] == sec and
                     s['rssi'] != 0]
            values.append(mysnr)
        return values

    def get_snr_mean(self, host, sectors='all'):
        values = list()
        for snr in self.get_snr_per_sector(host, sectors):
            if len(snr) == 0:
                values.append(None)
            else:
                values.append(round(np.mean(snr) * 100) / 100)
        if sectors == 'all' or type(sectors) is list:
            return values
        return values[0]

    def get_snr_percentiles(self, host, sectors='all'):
        values = list()
        ptiles = self.ci_bounds
        for snr in self.get_snr_per_sector(host, sectors):
            if len(snr) == 0:
                values.append(None)
            else:
                values.append(
                    np.round(np.percentile(snr, ptiles) * 100) / 100)
        if sectors == 'all' or type(sectors) is list:
            return values
        return values[0]

    def get_snr_std(self, host, sectors='all'):
        values = list()
        for snr in self.get_snr_per_sector(host, sectors):
            if len(snr) == 0:
                values.append(None)
            else:
                values.append(
                    np.round(np.std(snr) * 100) / 100)
        if sectors == 'all' or type(sectors) is list:
            return values
        return values[0]

    def get_sector_statistics(self, host, sectors='all'):
        r = OrderedDict()
        r['num'] = self.get_rssi_num(host, sectors)
        r['rssi_mean'] = self.get_rssi_mean(host, sectors)
        r['rssi_std'] = self.get_rssi_std(host, sectors)
        r['rssi_percentiles'] = self.get_rssi_percentiles(host, sectors)
        r['snr_mean'] = self.get_snr_mean(host, sectors)
        r['snr_std'] = self.get_snr_std(host, sectors)
        r['snr_percentiles'] = self.get_snr_percentiles(host, sectors)
        return r

    def get_summary(self, host):
        swp = self.sweepinfo
        sweeps = self.get_sweep_ids()
        sectors = self.get_sectors()
        ci_bounds = self.ci_bounds

        summary = list()

        for sw in sweeps:
            entry = OrderedDict([('sweep', sw)])
            for sec in sectors:
                swp_fil = [s for s in swp if s['sweep'] == sw and
                           s['mac'] == host and s['sector'] == sec]
                myrssi = swp_fil[0]['rssi'] if len(swp_fil) > 0 else None
                mysnr = swp_fil[0]['snr'] if len(swp_fil) > 0 else None
                entry['sector%02d_rssi' % sec] = myrssi
                entry['sector%02d_snr' % sec] = mysnr
            entry['num'] = len([s for s in swp if s['sweep'] == sw and
                                s['mac'] == host])
            entry['mean_rssi'] =\
                int(round(np.mean([s['rssi'] for s in swp if
                          s['sweep'] == sw and s['mac'] == host])))
            entry['mean_snr'] =\
                round(np.mean([s['snr'] for s in swp if
                      s['sweep'] == sw and s['mac'] == host]) * 100) / 100
            summary.append(entry)

        # Append the average
        entry = [
            OrderedDict([('sweep', 'mean')]),
            OrderedDict([('sweep', 'median')]),
            OrderedDict([('sweep', 'ci_hi')]),
            OrderedDict([('sweep', 'ci_lo')]),
            OrderedDict([('sweep', 'std')])]

        for sec in sectors:
            myrssi = [s['rssi'] for s in swp if
                      s['mac'] == host and s['sector'] == sec and
                      s['rssi'] != 0]
            mysnr = [s['snr'] for s in swp if
                     s['mac'] == host and s['sector'] == sec and
                     s['rssi'] != 0]
            entry[0]['sector%02d_rssi' % sec] =\
                int(round(np.mean(myrssi)))
            entry[0]['sector%02d_snr' % sec] =\
                round(np.mean(mysnr) * 100) / 100
            ci_rssi = np.round(np.percentile(myrssi, ci_bounds))
            ci_snr = np.round(np.percentile(mysnr, ci_bounds) * 100) / 100
            entry[1]['sector%02d_rssi' % sec] = ci_rssi[1]
            entry[1]['sector%02d_snr' % sec] = ci_snr[1]
            entry[2]['sector%02d_rssi' % sec] = ci_rssi[2]
            entry[2]['sector%02d_snr' % sec] = ci_snr[2]
            entry[3]['sector%02d_rssi' % sec] = ci_rssi[0]
            entry[3]['sector%02d_snr' % sec] = ci_snr[0]
            entry[4]['sector%02d_rssi' % sec] = np.round(np.std(myrssi))
            entry[4]['sector%02d_snr' % sec] =\
                np.round(np.std(mysnr) * 100) / 100

            for e in entry:
                e['num'] = None
                e['mean_snr'] = None
                e['mean_rssi'] = None
        summary.extend(entry)

        # Obtain the Headers for the SNR table
        header_snr = OrderedDict([('sweep', 'Sweep')])
        header_snr.update(
            [(k, re.findall('\d+', k)[0]) for k in summary[0].keys()
             if re.match('sector\d+_snr', k)])
        header_snr.update([('mean_snr', 'mean'), ('num', 'N')])
        data_snr = [OrderedDict((k, x[k]) for k in header_snr.keys())
                    for x in summary]

        # Obtain the Headers for the RSSI table
        header_rssi = OrderedDict([('sweep', 'Sweep')])
        header_rssi.update(
            [(k, re.findall('\d+', k)[0]) for k in summary[0].keys()
             if re.match('sector\d+_rssi', k)])
        header_rssi.update([('mean_rssi', 'mean'), ('num', 'N')])
        data_rssi = [OrderedDict((k, x[k]) for k in header_rssi.keys())
                     for x in summary]

        print('RSSI')
        print(tabulate(data_rssi, headers=header_rssi))
        print('SNR')
        print(tabulate(data_snr, headers=header_snr))
