import numpy as np
import scipy
import zlib

class BoardFile(object):
    
    def __init__(self):
        BoardInfo=scipy.io.loadmat('BoardInfo.mat')
        FileOrigin=BoardInfo['FileOrigin'][:, 0].reshape(3588, 8)[:, 7-np.arange(0, 8)].reshape(28704)
        self._MemorI=BoardInfo['MemorI'].T-1
        self._File8=np.packbits(FileOrigin)
        self._BPInfo=FileOrigin[self._MemorI]
        self._MemorI=np.int16((self._MemorI[:, np.arange(0, 192, 8)])/8).reshape(1560)
    
    def __del__(self):
        pass
    
    def build_File8(self):
        self._File8[self._MemorI]=np.packbits(self._BPInfo.reshape(12480))
    
    def insert_crc32(self):
        self._File8[16:20]=0
        CRC32=np.binary_repr(zlib.crc32(self._File8), 32)
        self._File8[16:20]=[int(CRC32[24:32], 2), int(CRC32[16:24], 2), int(CRC32[8:16], 2), int(CRC32[0:8], 2)]
    
    def save_File8(self, filename):
        self._File8.tofile(filename)
    
    def update_BPInfo2BRD(self, filename):
        self.build_File8()
        self.insert_crc32()
        self.save_File8(filename)
    
    def default_BP(self):
        BoardInfo=scipy.io.loadmat('BoardInfo.mat')
        FileOrigin=BoardInfo['FileOrigin'][:, 0].reshape(3588, 8)[:, 7-np.arange(0, 8)].reshape(28704)
        self._BPInfo=FileOrigin[BoardInfo['MemorI'].T-1]
    
    def define_BP(self, codebook, index):
        self._BPInfo[0:64, :]=0
        myone=np.uint8(1)
        InvertbitsI=np.arange(192).reshape(24, 8)[:, np.arange(7, -1, -1)].reshape(192)
        for ii_BP in np.arange(len(index)):
            BP_ind=index[ii_BP]
            # get BP
            BP=codebook.get_params(ii_BP)
            Phases=np.array(BP['psh'])
            Gains=np.array(BP['etype'])
            Amplifiers=np.array(BP['dtype'])
            # Transform to binary
            miniBPInfo=self._BPInfo[BP_ind, :]
            miniBPInfo[32:64]=(Phases>1)*myone
            Phases=np.mod(Phases, 2)
            miniBPInfo[0:32]=(Phases>0)*myone
            miniBPInfo[128:160]=(Gains>3)*myone
            Gains=np.mod(Gains, 4)
            miniBPInfo[96:128]=(Gains>1)*myone
            Gains=np.mod(Gains, 2)
            miniBPInfo[64:96]=(Gains>0)*myone
            miniBPInfo[176:184]=(Amplifiers>3)*myone
            Amplifiers=np.mod(Amplifiers, 4)
            miniBPInfo[168:176]=(Amplifiers>1)*myone
            Amplifiers=np.mod(Amplifiers, 2)
            miniBPInfo[160:168]=(Amplifiers>0)*myone
            miniBPInfo[184:192]=[0, 0, 0, 0, 1, 1, 0, 0]
            # 1-2 bits changed between Joan code and Daniel code
            miniBPInfo[np.concatenate((np.arange(96, 128), np.arange(64, 96)))]=miniBPInfo[np.arange(64, 128)]
            # shuffle
            np.set_printoptions(threshold=np.nan)
            miniBPInfo[np.concatenate((np.arange(0, 64, 2), np.arange(1, 64, 2)))]=miniBPInfo[np.arange(0, 64)]
            miniBPInfo[np.concatenate((np.arange(160, 182, 3), np.arange(161, 183, 3), np.arange(162, 184, 3)))]=miniBPInfo[np.arange(160, 184)]
            miniBPInfo[np.arange(128, 192)]=miniBPInfo[np.concatenate((np.arange(160, 192), np.arange(128, 160)))]
            miniBPInfo[np.arange(0, 64)]=miniBPInfo[np.concatenate((np.arange(32, 64), np.arange(0, 32)))]
            self._BPInfo[BP_ind, :]=miniBPInfo[InvertbitsI]