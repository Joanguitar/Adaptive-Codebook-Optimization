from TalonPy import SectorCodebook
from collections import OrderedDict
import numpy as np
import re

class Method(object):
    
    def __init__(self, active_antennas=10, search_antennas=15):
        self._stage=0 # stage the method is in
        self._active_antennas=active_antennas # number of active antennas
        self._search_antennas=search_antennas # number of search antennas
        self._winner=0 # winner beam-pattern location
        self._amplitude_X=np.arange(active_antennas+search_antennas) # indices of the amplitude beam-patterns
        self._amplitude_Y=np.arange(active_antennas+search_antennas) # antenna indices corresponding to the amplitude beam-patterns
        self._phase_X=np.arange(4*(active_antennas-1)) # indices of the phase beam-patterns
        self._codebook = SectorCodebook()
        self._codebook.initialize_default(64)
    
    def __del__(self):
        pass
    
    def ParseDump(self, data):
        data

        # Parse information to list
        sweepinfo = list()

        # Load the sweep counter
        swpctr = int(re.findall('Counter:\s+(\d+)\s+swps', data)[0])

        if swpctr == 0:
            print('No sweeps found to be parsed')
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
        to_be_updated=list()
        mysweepids = set([s['sweep'] for s in to_be_updated])
        sweepinfo = [s for s in sweepinfo if
                     s['sweep'] not in mysweepids]

        to_be_updated.extend(sweepinfo)
        return to_be_updated
    
    def ParseIperf(self, data):
        data
        
        # Parse information
        number_str="(\d*\.\d+|\d+)"
        information=re.findall(
                number_str+"\s+sec\s+"+number_str+"\s+\w+\s+"+number_str+"\s+(\w)",
                data)
        return information
    
    def get_amplitude_and_phase(self, data):
        output=OrderedDict()
        Dump=self.ParseDump(data)
        RSSI=np.zeros(64)
        for dump in Dump:
            RSSI[dump['sector']]=dump['rssi']
        output['amplitude']=np.sqrt(RSSI[self._amplitude_X])
        output['phase']=np.concatenate((np.arange(1), np.angle(np.fft.fft(RSSI[self._phase_X].reshape(self._active_antennas-1, 4), axis=1)[:, 1])))
        return output
    
    def update_data2(self, selected, winnerBP, AmplitudeAndPhase):
        available_I=np.arange(64)
        available_I=np.delete(available_I, selected)
        for ii in np.arange(64-(self._active_antennas*5-4+self._search_antennas+1)):
            self._codebook._sectors[available_I[0]]=winnerBP
            available_I=np.delete(available_I, 0)
        Powerful_Antennas=self._amplitude_Y[np.argsort(AmplitudeAndPhase['amplitude'])[np.arange(self._active_antennas+self._search_antennas-1, -1, -1)]]
        self._amplitude_Y=Powerful_Antennas[np.arange(self._active_antennas)]
        searching_antennas=np.delete(np.arange(32), self._amplitude_Y)[np.random.permutation(32-self._active_antennas)[np.arange(self._search_antennas)]]
        self._amplitude_Y=np.concatenate((self._amplitude_Y, searching_antennas))
        self._amplitude_X=available_I[np.arange(self._active_antennas+self._search_antennas)]
        self._phase_X=np.delete(available_I, np.arange(self._active_antennas+self._search_antennas))
        for ii in np.arange(self._active_antennas+self._search_antennas):
            Phase=[0]*32
            Gain=[0]*32
            Gain[self._amplitude_Y[ii]]=1
            Amplitude=[0]*8
            Amplitude[int(np.floor(self._amplitude_Y[ii]/4))]=1
            self._codebook.set_psh_reg(self._amplitude_X[ii], Phase)
            self._codebook.set_etype_reg(self._amplitude_X[ii], Gain)
            self._codebook.set_dtype_reg(self._amplitude_X[ii], Amplitude)
        index=0
        for ii in np.arange(self._active_antennas-1)+1:
            Phase=[0]*32
            Gain=[0]*32
            Gain[self._amplitude_Y[0]]=1
            Gain[self._amplitude_Y[ii]]=1
            Amplitude=[0]*8
            Amplitude[int(np.floor(self._amplitude_Y[0]/4))]=1
            Amplitude[int(np.floor(self._amplitude_Y[ii]/4))]=1
            for jj in np.arange(4):
                Phase[self._amplitude_Y[ii]]=jj
                self._codebook.set_psh_reg(self._phase_X[index], Phase)
                self._codebook.set_etype_reg(self._phase_X[index], Gain)
                self._codebook.set_dtype_reg(self._phase_X[index], Amplitude)
                index=index+1
    
    def update_data1(self, selected, winnerBP, RSSI):
        available_I=np.arange(64)
        available_I=np.delete(available_I, selected)
        for ii in np.arange(64-(self._active_antennas*5-4+self._search_antennas+1)):
            self._codebook._sectors[available_I[0]]=winnerBP
            available_I=np.delete(available_I, 0)
        Powerful_Antennas=np.argsort(RSSI)[np.arange(32-1, -1, -1)]
        self._amplitude_Y=Powerful_Antennas[np.arange(self._active_antennas)]
        searching_antennas=np.delete(np.arange(32), self._amplitude_Y)[np.random.permutation(32-self._active_antennas)[np.arange(self._search_antennas)]]
        self._amplitude_Y=np.concatenate((self._amplitude_Y, searching_antennas))
        self._amplitude_X=available_I[np.arange(self._active_antennas+self._search_antennas)]
        self._phase_X=np.delete(available_I, np.arange(self._active_antennas+self._search_antennas))
        for ii in np.arange(self._active_antennas+self._search_antennas):
            self._codebook.set_psh_reg(self._amplitude_X[ii], [0]*32)
            Gain=[0]*32
            Gain[self._amplitude_Y[ii]]=1
            Amplitude=[0]*8
            Amplitude[int(np.floor(self._amplitude_Y[ii]/4))]=1
            self._codebook.set_etype_reg(self._amplitude_X[ii], Gain)
            self._codebook.set_dtype_reg(self._amplitude_X[ii], Amplitude)
        index=0
        for ii in np.arange(self._active_antennas-1)+1:
            Phase=[0]*32
            Gain=[0]*32
            Gain[self._amplitude_Y[0]]=1
            Gain[self._amplitude_Y[ii]]=1
            Amplitude=[0]*8
            Amplitude[int(np.floor(self._amplitude_Y[0]/4))]=1
            Amplitude[int(np.floor(self._amplitude_Y[ii]/4))]=1
            for jj in np.arange(4):
                Phase[self._amplitude_Y[ii]]=jj
                self._codebook.set_psh_reg(self._phase_X[index], Phase)
                self._codebook.set_etype_reg(self._phase_X[index], Gain)
                self._codebook.set_dtype_reg(self._phase_X[index], Amplitude)
                index=index+1
    def getRSSI(self, data):
        Dump=self.ParseDump(data)
        RSSI=np.zeros(64)
        for dump in Dump:
            RSSI[dump['sector']]=dump['rssi']
        return RSSI
    def iterate(self, data):
        Dump=self.ParseDump(data)
        RSSI=np.zeros(64)
        for dump in Dump:
            RSSI[dump['sector']]=dump['rssi']
        Powerful_BPs=np.argsort(RSSI)[np.arange(64-1, -1, -1)]
        if self._stage==2:
            AmplitudeAndPhase=self.get_amplitude_and_phase(data)
            winner_codebook=SectorCodebook()
            winner_codebook.initialize_default(1)
            Phase=[0]*32
            Gain=[0]*32
            Amplitude=[0]*8
            for ii_antenna in np.arange(self._active_antennas):
                antenna=self._amplitude_Y[ii_antenna]
                Phase[antenna]=int(np.mod(np.round(-AmplitudeAndPhase['phase'][ii_antenna]*2/np.pi)+4, 4))
                Gain[antenna]=1
                Amplitude[int(np.floor(antenna/4))]=1
            winner_codebook.set_psh_reg(0, Phase)
            winner_codebook.set_etype_reg(0, Gain)
            winner_codebook.set_dtype_reg(0, Amplitude)
            self.update_data2(Powerful_BPs[0], winner_codebook._sectors[0], AmplitudeAndPhase)
        elif self._stage==1:
            self.update_data1(Powerful_BPs[0], self._codebook._sectors[Powerful_BPs[0]], RSSI[np.arange(32, 64)])
            self._stage=2
        elif self._stage==0:
            self._codebook._sectors=[self._codebook._sectors[i] for i in Powerful_BPs]
            for ii in np.arange(32):
                Gain=[0]*32
                Gain[ii]=1
                Amplitude=[0]*8
                Amplitude[int(np.floor(ii/4))]=1
                self._codebook.set_psh_reg(ii+32, [0]*32)
                self._codebook.set_etype_reg(ii+32, Gain)
                self._codebook.set_dtype_reg(ii+32, Amplitude)
            self._stage=1
        return RSSI