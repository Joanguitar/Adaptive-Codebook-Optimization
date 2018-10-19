from TalonPy import SectorCodebook
from collections import OrderedDict
import numpy as np
import re
import scipy.io

class MethodIndependent(object):
    
    def __init__(self, active_antennas=10, search_antennas=15):
        self._stage=0 # stage the method is in
        self._active_antennas=active_antennas # number of active antennas
        self._search_antennas=search_antennas # number of search antennas
        self._amplitude_X=np.arange(active_antennas+search_antennas) # indices of the amplitude beam-patterns
        self._amplitude_Y=np.arange(active_antennas+search_antennas) # antenna indices corresponding to the amplitude beam-patterns
        self._phase_X=np.arange(4*(active_antennas-1)) # indices of the phase beam-patterns
        self._codebook = SectorCodebook()
        self._codebook.initialize_default(64)
        self._winnerBP = SectorCodebook()
        self._winnerBP.initialize_default(1)
        self._nBPs=36
    
    def __del__(self):
        pass
    
    def ParseDump(self, data):
        sweeps = re.findall(
            '\[sec:\s+(\d+)\srssi:\s+(\d+)\s+snr:\s+(-?\d+)\s+qdB\s\(\s?(-?\d+)\sdB\)\ssrc:\s(\w+:\w+:\w+:\w+:\w+:\w+)\]',
            data)
        sweepinfo=[{'sector': int(sweep[0]), 'rssi': int(sweep[1]), 'snr': int(sweep[2])/4, 'mac': sweep[4]} for sweep in sweeps]
        return sweepinfo
    def getBPkind(self):
        kind=np.zeros(64, dtype='int')
        for ii in self._amplitude_X:
            kind[ii]=1
        for ii in self._phase_X:
            kind[ii]=2
        return kind
    def ParseData(self, data):
        # Parse information
        number_str="(\d*\.\d+|\d+)"
        information1=re.findall(
                "Tx_mcs:\s(\d+)\sRx_mcs:\s(\d+)\sSQ:\s(\d+)",
                data)
        information2=re.findall(
                number_str+"\s+sec\s+"+number_str+"\s+\w+\s+"+number_str+"\s+(\w)\w+/\w+\s+(\d+)\s+"+number_str+"\s(\w)",
                data)
        multiplier={'b': 0.000001, 'K': 0.001, 'M': 1, 'G': 1000}
        Channel=OrderedDict()
        Channel['Tx_mcs']=np.array([info[0] for info in information1])
        Channel['Rx_mcs']=np.array([info[1] for info in information1])
        Channel['SQ']=np.array([info[2] for info in information1])
        Channel['Bandwidth']=np.array([float(info[2])*multiplier[info[3]] for info in information2])
        Channel['Retr']=np.array([int(info[4]) for info in information2])
        Channel['Cwnd']=np.array([float(info[5])*multiplier[info[6]] for info in information2])
        return Channel
    def ParseData_Up(self, data):
        # Parse information
        number_str="(\d*\.\d+|\d+)"
        information1=re.findall(
                "Tx_mcs:\s(\d+)\sRx_mcs:\s(\d+)\sSQ:\s(\d+)",
                data)
        information2=re.findall(
                number_str+"\s+sec\s+"+number_str+"\s+\w+\s+"+number_str+"\s+(\w)\w+/\w+\s+(\d+)\s+"+number_str+"\s(\w)",
                data)
        multiplier={'b': 0.000001, 'K': 0.001, 'M': 1, 'G': 1000}
        Channel=OrderedDict()
        Channel['Tx_mcs']=np.array([info[0] for info in information1])
        Channel['Rx_mcs']=np.array([info[1] for info in information1])
        Channel['SQ']=np.array([info[2] for info in information1])
        Channel['Bandwidth']=np.array([float(info[2])*multiplier[info[3]] for info in information2])
        Channel['Retr']=np.array([int(info[4]) for info in information2])
        Channel['Cwnd']=np.array([float(info[5])*multiplier[info[6]] for info in information2])
        return Channel
    def ParseData_Down(self, data):
        # Parse information
        number_str="(\d*\.\d+|\d+)"
        information1=re.findall(
                "Tx_mcs:\s(\d+)\sRx_mcs:\s(\d+)\sSQ:\s(\d+)",
                data)
        information2=re.findall(
                number_str+"\s+sec\s+"+number_str+"\s+\w+\s+"+number_str+"\s+(\w)\w+/\w+\s+",
                data)[:-2]
        multiplier={'b': 0.000001, 'K': 0.001, 'M': 1, 'G': 1000}
        Channel=OrderedDict()
        Channel['Tx_mcs']=np.array([info[0] for info in information1])
        Channel['Rx_mcs']=np.array([info[1] for info in information1])
        Channel['SQ']=np.array([info[2] for info in information1])
        Channel['Bandwidth']=np.array([float(info[2])*multiplier[info[3]] for info in information2])
        return Channel
    def ParseIperf(self, data):
        # Parse information
        number_str="(\d*\.\d+|\d+)"
        information=re.findall(
                number_str+"\s+sec\s+"+number_str+"\s+\w+\s+"+number_str+"\s+(\w)",
                data)
        multiplier={'b': 0.000001, 'K': 0.001, 'M': 1, 'G': 1000}
        Iperf=np.array([float(info[2])*multiplier[info[3]] for info in information][:-2])
        return Iperf
    def getRSSI(self, data):
        Dump=self.ParseDump(data)
        RSSI=np.zeros(64)
        for dump in Dump:
            RSSI[dump['sector']]=dump['rssi']
        return RSSI
    def getRSSI_multiple(self, data, mac=None):
        Dump=self.ParseDump(data)
        if mac==None:
            MACS=np.unique([dump['mac'] for dump in Dump])
            RSSI={MAC: [[] for ii in range(64)] for MAC in MACS}
            for dump in Dump:
                if dump['rssi']>0:
                    RSSI[dump['mac']][dump['sector']].append([dump['rssi']])
            RSSI={MAC: np.array([np.mean(rssi) if len(rssi)>0 else 0 for rssi in RSSI[MAC]]) for MAC in MACS}
        else:
            mac=mac.casefold()
            RSSI=[[] for dump in range(64)]
            for dump in Dump:
                if dump['mac']==mac and dump['rssi']>0:
                    RSSI[dump['sector']].append([dump['rssi']])
            RSSI=np.array([np.median(rssi) if len(rssi)>0 else 0 for rssi in RSSI])
        return RSSI
    def getSNR_multiple(self, data, mac=None):
        Dump=self.ParseDump(data)
        if mac==None:
            MACS=np.unique([dump['mac'] for dump in Dump])
            RSSI={MAC: [[] for ii in range(64)] for MAC in MACS}
            for dump in Dump:
                if dump['rssi']>0:
                    RSSI[dump['mac']][dump['sector']].append([dump['snr']])
            RSSI={MAC: np.array([np.mean(rssi) if len(rssi)>0 else 0 for rssi in RSSI[MAC]]) for MAC in MACS}
        else:
            mac=mac.casefold()
            RSSI=[[] for dump in range(64)]
            for dump in Dump:
                if dump['mac']==mac and dump['rssi']>0:
                    RSSI[dump['sector']].append([dump['snr']])
            RSSI=np.array([np.median(rssi) if len(rssi)>0 else 0 for rssi in RSSI])
        return RSSI
    def get_amplitude_and_phase(self, RSSI):
        output=OrderedDict()
        output['amplitude']=np.sqrt(RSSI[self._amplitude_X])
        if self._active_antennas>1:
            output['phase']=np.concatenate((np.zeros(1), np.angle(np.fft.fft(RSSI[self._phase_X].reshape(self._active_antennas-1, 4), axis=1)[:, 1])))
        elif self._active_antennas==0:
            output['phase']=np.zeros(0)
        else:
            output['phase']=np.zeros(1)
        output['Y']=self._amplitude_Y
        return output
    def createmeasurecodebook(self, AmplitudeAndPhase):
        Powerful_Antennas=self._amplitude_Y[np.argsort(AmplitudeAndPhase['amplitude'])[np.arange(self._active_antennas+self._search_antennas-1, -1, -1)]]
        self._amplitude_Y=Powerful_Antennas[np.arange(self._active_antennas)]
        searching_antennas=np.delete(np.arange(32), self._amplitude_Y)[np.random.permutation(32-self._active_antennas)[np.arange(self._search_antennas)]]
        self._amplitude_Y=np.concatenate((self._amplitude_Y, searching_antennas))
        self._amplitude_X=np.arange(self._active_antennas+self._search_antennas-1, -1, -1) # Inverted to avoid invisible active antennas
        self._phase_X=np.arange(self._active_antennas+self._search_antennas, self._active_antennas+self._search_antennas+4*(self._active_antennas-1))
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
        for ii in np.arange(1, self._active_antennas):
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
        Phase=[0]*32
        Gain=[0]*32
        Amplitude=[0]*8
        for ii in np.arange(self._active_antennas+self._search_antennas+4*(self._active_antennas-1), 64):
            self._codebook.set_psh_reg(ii, Phase)
            self._codebook.set_etype_reg(ii, Gain)
            self._codebook.set_dtype_reg(ii, Amplitude)
    def createmeasurecodebook_selectedAntennas(self, selectedAntennas):
        self._amplitude_Y=selectedAntennas
        searching_antennas=np.delete(np.arange(32), self._amplitude_Y)[np.random.permutation(32-self._active_antennas)[np.arange(self._search_antennas)]]
        self._amplitude_Y=np.concatenate((self._amplitude_Y, searching_antennas))
        self._amplitude_X=np.arange(self._active_antennas+self._search_antennas-1, -1, -1) # Inverted to avoid invisible active antennas
        self._phase_X=np.arange(self._active_antennas+self._search_antennas, self._active_antennas+self._search_antennas+4*(self._active_antennas-1))
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
        for ii in np.arange(1, self._active_antennas):
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
        Phase=[0]*32
        Gain=[0]*32
        Amplitude=[0]*8
        for ii in np.arange(self._active_antennas+self._search_antennas+4*(self._active_antennas-1), 64):
            self._codebook.set_psh_reg(ii, Phase)
            self._codebook.set_etype_reg(ii, Gain)
            self._codebook.set_dtype_reg(ii, Amplitude)
    def createwinnerBP(self, AmplitudeAndPhase):
        Phase=[0]*32
        Gain=[0]*32
        Amplitude=[0]*8
        for ii_antenna in np.arange(self._active_antennas):
            antenna=self._amplitude_Y[ii_antenna]
            Phase[antenna]=int(np.mod(np.round(-AmplitudeAndPhase['phase'][ii_antenna]*2/np.pi)+4, 4))
            Gain[antenna]=1
            Amplitude[int(np.floor(antenna/4))]=1
        self._winnerBP.set_psh_reg(0, Phase)
        self._winnerBP.set_etype_reg(0, Gain)
        self._winnerBP.set_dtype_reg(0, Amplitude)
    def iterate(self, RSSI=None):
        if self._stage==3:
            AmplitudeAndPhase=self.get_amplitude_and_phase(RSSI)
            self.createwinnerBP(AmplitudeAndPhase)
            search_len=np.min((13, self._active_antennas+self._search_antennas))
            self._active_antennas=np.argmax(np.cumsum(np.sort(AmplitudeAndPhase['amplitude'])[::-1][0:search_len])/np.sqrt(np.arange(1, search_len+1)))+1 # Campute next number of active antennas
            self._search_antennas=np.min((64-5*self._active_antennas+4, 32-self._active_antennas))
            self.createmeasurecodebook(AmplitudeAndPhase)
            self._nBPs=self._active_antennas*5-4+self._search_antennas
        elif self._stage==2:
            AmplitudeAndPhase=self.get_amplitude_and_phase(RSSI)
            search_len=np.min((13, self._active_antennas+self._search_antennas))
            self._active_antennas=np.argmax(np.cumsum(np.sort(AmplitudeAndPhase['amplitude'])[::-1][0:search_len])/np.sqrt(np.arange(1, search_len+1)))+1 # Campute next number of active antennas
            self._search_antennas=np.min((64-5*self._active_antennas+4, 32-self._active_antennas))
            self.createmeasurecodebook(AmplitudeAndPhase)
            self._stage=3
            self._nBPs=self._active_antennas*5-4+self._search_antennas
        elif self._stage==1:
            ii_winner=np.argmax(RSSI)
            self._winnerBP.set_psh_reg(0, self._codebook.get_psh_reg(ii_winner)) # Select as winner the winner of past estimation stage
            self._winnerBP.set_etype_reg(0, self._codebook.get_etype_reg(ii_winner)) # Select as winner the winner of past estimation stage
            self._winnerBP.set_dtype_reg(0, self._codebook.get_dtype_reg(ii_winner)) # Select as winner the winner of past estimation stage
            AmplitudeAndPhase=OrderedDict() # Create 0 AmplitudeAndPhase estimation
            AmplitudeAndPhase['amplitude']=np.zeros(32)
            AmplitudeAndPhase['phase']=np.zeros(0)
            self._active_antennas=0 # No active antennas
            self._search_antennas=np.min((64-5*self._active_antennas+4, 32-self._active_antennas))
            self._amplitude_Y=np.arange(self._search_antennas)
            self.createmeasurecodebook(AmplitudeAndPhase)
            self._stage=2
            self._nBPs=self._active_antennas*5-4+self._search_antennas
        elif self._stage==0:
            ConnectionInfo=scipy.io.loadmat('ConnectionInfo.mat')
            for n in range(0, 64):
                psh = list(ConnectionInfo['DefaultPhase'][:, n])
                self._codebook.set_psh_reg(n, psh)
                etype = list(ConnectionInfo['DefaultGain'][:, n])
                self._codebook.set_etype_reg(n, etype)
                dtype = list(ConnectionInfo['DefaultAmplitude'][:, n])
                self._codebook.set_dtype_reg(n, dtype)
            self._stage=1
            self._amplitude_X=np.zeros(0)
            self._amplitude_Y=np.zeros(0)
            self._phase_X=np.zeros(0)
            self._active_antennas=0 # No active antennas
            self._search_antennas=0 # No search antennas
            self._nBPs=36