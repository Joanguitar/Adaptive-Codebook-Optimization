from TalonPy import SectorCodebook
from collections import OrderedDict
import numpy as np
import re
import scipy.io

class MethodIndependent_low(object):
    
    def __init__(self, active_antennas=10, search_antennas=15):
        self._stage=0 # stage the method is in
        self._active_antennas=active_antennas # number of active antennas
        self._search_antennas=search_antennas # number of search antennas
        self._active_Y=np.arange(active_antennas)
        self._search_Y=np.arange(search_antennas)
        self._fft_X=np.zeros(4*(active_antennas+search_antennas), dtype='int')
        self._codebook = SectorCodebook()
        self._codebook.initialize_default(64)
        self._winnerBP = SectorCodebook()
        self._winnerBP.initialize_default(1)
        self._nBPs=36
        self._max_active_antennas=18 # Can be set up to 18
        self._max_BP=62 # Can be set up to 62
        self._gain_val=1 # Value that is going to be set for the antenna gains
        self._ampl_val=1 # Value that is going to be set for the amplitude gains
    
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
            last_seen_sec=-1
            last_sec=-1
            for dump in Dump:
                if int(dump['sector'])==last_seen_sec:
                    last_sec+=1
                else:
                    last_seen_sec=int(dump['sector'])
                    last_sec=last_seen_sec
                if dump['rssi']>0 and last_sec<64:
                    RSSI[dump['mac']][last_sec].append([dump['rssi']])
            RSSI={MAC: np.array([np.mean(rssi) if len(rssi)>0 else 0 for rssi in RSSI[MAC]]) for MAC in MACS}
        else:
            mac=mac.casefold()
            RSSI=[[] for dump in range(64)]
            last_seen_sec=-1
            last_sec=-1
            for dump in Dump:
                if int(dump['sector'])==last_seen_sec:
                    last_sec+=1
                else:
                    last_seen_sec=int(dump['sector'])
                    last_sec=last_seen_sec
                if dump['mac']==mac and dump['rssi']>0 and last_sec<64:
                    RSSI[last_sec].append([dump['rssi']])
            RSSI=np.array([np.median(rssi) if len(rssi)>0 else 0 for rssi in RSSI])
        return RSSI
    def getSNR_multiple(self, data, mac=None):
        Dump=self.ParseDump(data)
        if mac==None:
            MACS=np.unique([dump['mac'] for dump in Dump])
            RSSI={MAC: [[] for ii in range(64)] for MAC in MACS}
            last_seen_sec=-1
            last_sec=-1
            for dump in Dump:
                if int(dump['sector'])==last_seen_sec:
                    last_sec+=1
                else:
                    last_seen_sec=int(dump['sector'])
                    last_sec=last_seen_sec
                if dump['rssi']>0 and last_sec<64:
                    RSSI[dump['mac']][last_sec].append([dump['snr']])
            RSSI={MAC: np.array([np.mean(rssi) if len(rssi)>0 else 0 for rssi in RSSI[MAC]]) for MAC in MACS}
        else:
            mac=mac.casefold()
            RSSI=[[] for dump in range(64)]
            last_seen_sec=-1
            last_sec=-1
            for dump in Dump:
                if int(dump['sector'])==last_seen_sec:
                    last_sec+=1
                else:
                    last_seen_sec=int(dump['sector'])
                    last_sec=last_seen_sec
                if dump['mac']==mac and dump['rssi']>0 and last_sec<64:
                    RSSI[last_sec].append([dump['snr']])
            RSSI=np.array([np.median(rssi) if len(rssi)>0 else 0 for rssi in RSSI])
        return RSSI
    def get_amplitude_and_phase(self, RSSI):
        output=OrderedDict()
        Mat=RSSI[self._fft_X].reshape(self._active_antennas+self._search_antennas, 4)
        Win_I=np.all(Mat>0, axis=1)
        fft_Mat=np.fft.fft(Mat, axis=1).T
        a=2*abs(fft_Mat[1, :])
        b=np.max((np.real(fft_Mat[0, :]), a), axis=0)
        top=np.sqrt(b+a)
        bot=np.sqrt(b-a)
        main=top+bot
        output['amplitude']=top-bot
        output['phase']=np.angle(fft_Mat[1, :])
        output['phase'][:self._active_antennas]=output['phase'][:self._active_antennas]-np.angle(output['amplitude'][:self._active_antennas]*np.exp((output['phase'][:self._active_antennas]+(np.pi/2)*np.array(self._winnerBP.get_psh_reg(0))[self._active_Y])*1j)+main[:self._active_antennas])
        output['Y']=np.concatenate((self._active_Y, self._search_Y))
        output['amplitude']=np.extract(Win_I, output['amplitude'])
        output['phase']=np.extract(Win_I, output['phase'])
        output['Y']=np.extract(Win_I, output['Y'])
        return output
    def createmeasurecodebook(self):
        self._search_Y=np.delete(np.arange(32), self._active_Y)[np.random.permutation(32-self._active_antennas)[:self._search_antennas]]
        win_Phase=self._winnerBP.get_psh_reg(0)
        win_Gain=self._winnerBP.get_etype_reg(0)
        win_Amplitude=self._winnerBP.get_dtype_reg(0)
        for ii_BP in range(64):
            self._codebook.set_psh_reg(ii_BP, [0]*32)
            self._codebook.set_etype_reg(ii_BP, [0]*32)
            self._codebook.set_dtype_reg(ii_BP, [0]*8)
        self._codebook.set_psh_reg(0, win_Phase)
        self._codebook.set_etype_reg(0, win_Gain)
        self._codebook.set_dtype_reg(0, win_Amplitude)
        self._fft_X=np.zeros(4*(self._active_antennas+self._search_antennas), dtype='int')
        ind_BP=63
        ind_fft=0
        for antenna in self._active_Y:
            Phase=list(win_Phase)
            Gain=list(win_Gain)
            Amplitude=list(win_Amplitude)
            for phase in np.arange(4):
                if phase==win_Phase[antenna]:
                    self._fft_X[ind_fft]=0
                else:
                    self._fft_X[ind_fft]=ind_BP
                    Phase[antenna]=phase
                    self._codebook.set_psh_reg(ind_BP, Phase)
                    self._codebook.set_etype_reg(ind_BP, Gain)
                    self._codebook.set_dtype_reg(ind_BP, Amplitude)
                    ind_BP-=1
                ind_fft+=1
        for antenna in self._search_Y:
            Phase=win_Phase
            Gain=win_Gain
            Amplitude=win_Amplitude
            Gain[antenna]=self._gain_val
            Amplitude[int(np.floor(antenna/4))]=self._ampl_val
            for phase in np.arange(4):
                self._fft_X[ind_fft]=ind_BP
                Phase[antenna]=phase
                self._codebook.set_psh_reg(ind_BP, Phase)
                self._codebook.set_etype_reg(ind_BP, Gain)
                self._codebook.set_dtype_reg(ind_BP, Amplitude)
                ind_fft+=1
                ind_BP-=1
    def createwinnerBP(self, AmplitudeAndPhase):
        Phase=[0]*32
        Gain=[0]*32
        Amplitude=[0]*8
        Antennas_I={AmplitudeAndPhase['Y'][ii]: ii for ii in np.arange(len(AmplitudeAndPhase['Y']))}
        for antenna in self._active_Y:
            ii_antenna=Antennas_I[antenna]
            Phase[antenna]=int(np.mod(np.round(-AmplitudeAndPhase['phase'][ii_antenna]*2/np.pi)+4, 4))
            Gain[antenna]=self._gain_val
            Amplitude[int(np.floor(antenna/4))]=self._ampl_val
        self._winnerBP.set_psh_reg(0, Phase)
        self._winnerBP.set_etype_reg(0, Gain)
        self._winnerBP.set_dtype_reg(0, Amplitude)
    def iterate(self, RSSI=None):
        if self._stage==2:
            AmplitudeAndPhase=self.get_amplitude_and_phase(RSSI)
            search_len=np.min((self._max_active_antennas, len(AmplitudeAndPhase['amplitude'])))
            self._active_antennas=np.argmax(np.cumsum(np.sort(AmplitudeAndPhase['amplitude'])[::-1][0:search_len])/np.sqrt(np.arange(1, search_len+1)))+1 # Campute next number of active antennas
            self._search_antennas=np.min((int(np.floor((self._max_BP-3*self._active_antennas)/4)), 32-self._active_antennas)) # No search antennas
            Y=AmplitudeAndPhase['Y']
            self._active_Y=Y[np.argsort(AmplitudeAndPhase['amplitude'])[::-1][0:self._active_antennas]]
            self.createwinnerBP(AmplitudeAndPhase)
            self.createmeasurecodebook()
            self._nBPs=1+3*self._active_antennas+4*self._search_antennas
        elif self._stage==1:
            ii_winner=np.argmax(RSSI)
            self._winnerBP.set_psh_reg(0, self._codebook.get_psh_reg(ii_winner)) # Select as winner the winner of past estimation stage
            self._winnerBP.set_etype_reg(0, [(a>0)*self._gain_val for a in self._codebook.get_etype_reg(ii_winner)]) # Select as winner the winner of past estimation stage
            self._winnerBP.set_dtype_reg(0, [(a>0)*self._ampl_val for a in self._codebook.get_dtype_reg(ii_winner)]) # Select as winner the winner of past estimation stage
            self._active_Y=np.where(self._winnerBP.get_etype_reg(0))[0]
            self._active_antennas=len(self._active_Y)
            self._search_antennas=np.min((int(np.floor((62-3*self._active_antennas)/4)), 32-self._active_antennas)) # No search antennas
            self.createmeasurecodebook()
            self._stage=2
            self._nBPs=1+3*self._active_antennas+4*self._search_antennas
        elif self._stage==0:
            ConnectionInfo=scipy.io.loadmat('ConnectionInfo.mat')
            for n in range(0, 64):
                psh = list(ConnectionInfo['DefaultPhase'][:, n])
                self._codebook.set_psh_reg(n, psh)
                etype = list(ConnectionInfo['DefaultGain'][:, n])
                self._codebook.set_etype_reg(n, [(a>0)*self._gain_val for a in etype])
                dtype = list(ConnectionInfo['DefaultAmplitude'][:, n])
                self._codebook.set_dtype_reg(n, [(a>0)*self._ampl_val for a in dtype])
            self._stage=1
            self._search_antennas=0 # No search antennas
            self._nBPs=36