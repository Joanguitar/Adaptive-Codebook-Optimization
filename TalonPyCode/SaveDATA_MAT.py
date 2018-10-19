import numpy as np
import json
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib._png import read_png
import scipy.misc
import scipy.io

# Experiments name
Names=['ExpO1_0', 'ExpO2_0', 'ExpO3_0', 'ExpO4_0', 'ExpO5_0', 'ExpO6_0',
       'ExpA_0', 'ExpB_0', 'ExpC_0', 'ExpD_0', 'ExpE_0', 'ExpF_0',
       'ExpG_0', 'ExpH_0', 'ExpI_0', 'ExpJ_0', 'ExpK_0', 'ExpL_0',
       'ExpE1_0', 'ExpE2_0', 'ExpE3_0', 'ExpE4_0', 'ExpE6_0',
       'ExpR1_0', 'ExpR2_0', 'ExpR3_0', 'ExpER_0', 'ExpR6_0', 'ExpR7_0',
       'ExpU31_0', 'ExpU41_0', 'ExpU51_0', 'ExpU61_0']

# Define extract methods
def getRSSI(json_data):
    Connected=json_data['Setup_info']['Connected']
    MACs=json_data['Setup_info']['MACs']
    MAC_ind={MACs[ii]: ii for ii in range(len(MACs))}
    RSSI={MAC_STA: [json_data['RSSIs_COM_val'][ii][Connected[MAC_ind[MAC_STA]]][MAC_STA] for ii in range(len(json_data['RSSIs_COM_val']))] for MAC_STA in MACs if Connected[MAC_ind[MAC_STA]] is not None}
    RSSI={key: [np.max(rssi) for rssi in RSSI[key]] for key in RSSI.keys()}
    return RSSI
def getSNR(json_data):
    Connected=json_data['Setup_info']['Connected']
    MACs=json_data['Setup_info']['MACs']
    MAC_ind={MACs[ii]: ii for ii in range(len(MACs))}
    RSSI={MAC_STA: [json_data['SNRs_COM_val'][ii][Connected[MAC_ind[MAC_STA]]][MAC_STA] for ii in range(len(json_data['SNRs_COM_val']))] for MAC_STA in MACs if Connected[MAC_ind[MAC_STA]] is not None}
    RSSI={key: [np.max(rssi) for rssi in RSSI[key]] for key in RSSI.keys()}
    return RSSI

# Load
mean_RSSI_UP_low=[None]*len(Names)
mean_RSSI_UP_0=[None]*len(Names)
mean_SNR_UP_low=[None]*len(Names)
mean_SNR_UP_0=[None]*len(Names)
mean_Throughput_UP_low=[None]*len(Names)
mean_Throughput_UP_0=[None]*len(Names)
mean_RSSI_DOWN_low=[None]*len(Names)
mean_RSSI_DOWN_0=[None]*len(Names)
mean_SNR_DOWN_low=[None]*len(Names)
mean_SNR_DOWN_0=[None]*len(Names)
mean_Throughput_DOWN_low=[None]*len(Names)
mean_Throughput_DOWN_0=[None]*len(Names)
dump_RSSI_UP_low=[None]*len(Names)
dump_RSSI_UP_0=[None]*len(Names)
dump_SNR_UP_low=[None]*len(Names)
dump_SNR_UP_0=[None]*len(Names)
dump_Throughput_UP_low=[None]*len(Names)
dump_Throughput_UP_0=[None]*len(Names)
dump_Tx_mcs_UP_low=[None]*len(Names)
dump_Tx_mcs_UP_0=[None]*len(Names)
dump_Rx_mcs_UP_low=[None]*len(Names)
dump_Rx_mcs_UP_0=[None]*len(Names)
dump_SQ_UP_low=[None]*len(Names)
dump_SQ_UP_0=[None]*len(Names)
dump_RSSI_DOWN_low=[None]*len(Names)
dump_RSSI_DOWN_0=[None]*len(Names)
dump_SNR_DOWN_low=[None]*len(Names)
dump_SNR_DOWN_0=[None]*len(Names)
dump_Throughput_DOWN_low=[None]*len(Names)
dump_Throughput_DOWN_0=[None]*len(Names)
dump_Tx_mcs_DOWN_low=[None]*len(Names)
dump_Tx_mcs_DOWN_0=[None]*len(Names)
dump_Rx_mcs_DOWN_low=[None]*len(Names)
dump_Rx_mcs_DOWN_0=[None]*len(Names)
dump_SQ_DOWN_low=[None]*len(Names)
dump_SQ_DOWN_0=[None]*len(Names)
for ii_Name in np.arange(len(Names)):
    Name=Names[ii_Name]
    with open('Experiments_v2/%s_low.json'%(Name)) as fp:
        json_data_low=json.load(fp)
        fp.close()
    with open('Experiments_v2/%s_0.json'%(Name)) as fp:
        json_data_0=json.load(fp)
        fp.close()
    
    # Correct empty measures by extending last
    for key in json_data_low['DATA_DOWN_val'].keys():
        for data in json_data_low['DATA_DOWN_val'][key]:
            data['Rx_mcs'].extend([data['Rx_mcs'][-1]]*(10-len(data['Rx_mcs'])))
            data['SQ'].extend([data['SQ'][-1]]*(10-len(data['SQ'])))
            data['Tx_mcs'].extend([data['Tx_mcs'][-1]]*(10-len(data['Tx_mcs'])))
        for data in json_data_0['DATA_DOWN_val'][key]:
            data['Rx_mcs'].extend([data['Rx_mcs'][-1]]*(10-len(data['Rx_mcs'])))
            data['SQ'].extend([data['SQ'][-1]]*(10-len(data['SQ'])))
            data['Tx_mcs'].extend([data['Tx_mcs'][-1]]*(10-len(data['Tx_mcs'])))
    for key in json_data_low['DATA_UP_val'].keys():
        for data in json_data_low['DATA_UP_val'][key]:
            data['Rx_mcs'].extend([data['Rx_mcs'][-1]]*(10-len(data['Rx_mcs'])))
            data['SQ'].extend([data['SQ'][-1]]*(10-len(data['SQ'])))
            data['Tx_mcs'].extend([data['Tx_mcs'][-1]]*(10-len(data['Tx_mcs'])))
        for data in json_data_0['DATA_UP_val'][key]:
            data['Rx_mcs'].extend([data['Rx_mcs'][-1]]*(10-len(data['Rx_mcs'])))
            data['SQ'].extend([data['SQ'][-1]]*(10-len(data['SQ'])))
            data['Tx_mcs'].extend([data['Tx_mcs'][-1]]*(10-len(data['Tx_mcs'])))
    
    def getDATA_DOWN(json_data):
        DATA={key: {keyy: [] for keyy in json_data['DATA_DOWN_val'][key][0].keys()} for key in json_data['DATA_DOWN_val'].keys()}
        for key in json_data['DATA_DOWN_val'].keys():
            for keylist in json_data['DATA_DOWN_val'][key]:
                for keyy in ['Bandwidth']:
                    keylist[keyy].extend([keylist[keyy][-1]]*(100-len(keylist[keyy])))
                    DATA[key][keyy].extend(keylist[keyy])
                for keyy in ['Tx_mcs', 'Rx_mcs', 'SQ']:
                    keylist[keyy].extend([keylist[keyy][-1]]*(10-len(keylist[keyy])))
                    DATA[key][keyy].extend(keylist[keyy])
        return DATA
    def getDATA_UP(json_data):
        DATA={key: {keyy: [] for keyy in json_data['DATA_UP_val'][key][0].keys()} for key in json_data['DATA_UP_val'].keys()}
        for key in json_data['DATA_UP_val'].keys():
            for keylist in json_data['DATA_UP_val'][key]:
                for keyy in ['Bandwidth', 'Cwnd', 'Retr']:
                    keylist[keyy].extend([keylist[keyy][-1]]*(100-len(keylist[keyy])))
                    DATA[key][keyy].extend(keylist[keyy])
                for keyy in ['Tx_mcs', 'Rx_mcs', 'SQ']:
                    keylist[keyy].extend([keylist[keyy][-1]]*(10-len(keylist[keyy])))
                    DATA[key][keyy].extend(keylist[keyy])
        return DATA
    
    # Extract data
    DATA_DOWN_low=getDATA_DOWN(json_data_low)
    DATA_UP_low=getDATA_UP(json_data_low)
    RSSI_low=getRSSI(json_data_low)
    SNR_low=getSNR(json_data_low)
    DATA_DOWN_0=getDATA_DOWN(json_data_0)
    DATA_UP_0=getDATA_UP(json_data_0)
    RSSI_0=getRSSI(json_data_0)
    SNR_0=getSNR(json_data_0)
    STAs_ID=list(DATA_DOWN_low.keys())
    STAs_MAC=[json_data_low['Setup_info']['MACs'][ii] for ii in range(len(json_data_low['Setup_info']['MACs'])) if json_data_low['Setup_info']['Connected'][ii] is not None]
    
    # Dump data
    Connected=json_data_low['Setup_info']['Connected']
    mean_RSSI_UP_low[ii_Name]=np.mean(RSSI_low[STAs_MAC[0]])
    mean_RSSI_UP_0[ii_Name]=np.mean(RSSI_0[STAs_MAC[0]])
    mean_SNR_UP_low[ii_Name]=np.mean(np.power(10, [a/10 for a in SNR_low[STAs_MAC[0]]]))
    mean_SNR_UP_0[ii_Name]=np.mean(np.power(10, [a/10 for a in SNR_0[STAs_MAC[0]]]))
    mean_Throughput_UP_low[ii_Name]=np.mean(DATA_UP_low[STAs_ID[0]]['Bandwidth'])
    mean_Throughput_UP_0[ii_Name]=np.mean(DATA_UP_0[STAs_ID[0]]['Bandwidth'])
    mean_RSSI_DOWN_low[ii_Name]=np.mean(RSSI_low[STAs_MAC[Connected[0]]])
    mean_RSSI_DOWN_0[ii_Name]=np.mean(RSSI_0[STAs_MAC[Connected[0]]])
    mean_SNR_DOWN_low[ii_Name]=np.mean(np.power(10, [a/10 for a in SNR_low[STAs_MAC[Connected[0]]]]))
    mean_SNR_DOWN_0[ii_Name]=np.mean(np.power(10, [a/10 for a in SNR_0[STAs_MAC[Connected[0]]]]))
    mean_Throughput_DOWN_low[ii_Name]=np.mean(DATA_DOWN_low[STAs_ID[0]]['Bandwidth'])
    mean_Throughput_DOWN_0[ii_Name]=np.mean(DATA_DOWN_0[STAs_ID[0]]['Bandwidth'])
    dump_RSSI_UP_low[ii_Name]=RSSI_low[STAs_MAC[0]]
    dump_RSSI_UP_0[ii_Name]=RSSI_0[STAs_MAC[0]]
    dump_SNR_UP_low[ii_Name]=np.power(10, [a/10 for a in SNR_low[STAs_MAC[0]]])
    dump_SNR_UP_0[ii_Name]=np.power(10, [a/10 for a in SNR_0[STAs_MAC[0]]])
    dump_Throughput_UP_low[ii_Name]=DATA_UP_low[STAs_ID[0]]['Bandwidth']
    dump_Throughput_UP_0[ii_Name]=DATA_UP_0[STAs_ID[0]]['Bandwidth']
    dump_Tx_mcs_UP_low[ii_Name]=[int(a) for a in DATA_UP_low[STAs_ID[0]]['Tx_mcs']]
    dump_Tx_mcs_UP_0[ii_Name]=[int(a) for a in DATA_UP_0[STAs_ID[0]]['Tx_mcs']]
    dump_Rx_mcs_UP_low[ii_Name]=[int(a) for a in DATA_UP_low[STAs_ID[0]]['Rx_mcs']]
    dump_Rx_mcs_UP_0[ii_Name]=[int(a) for a in DATA_UP_0[STAs_ID[0]]['Rx_mcs']]
    dump_SQ_UP_low[ii_Name]=[int(a) for a in DATA_UP_low[STAs_ID[0]]['SQ']]
    dump_SQ_UP_0[ii_Name]=[int(a) for a in DATA_UP_0[STAs_ID[0]]['SQ']]
    dump_RSSI_DOWN_low[ii_Name]=RSSI_low[STAs_MAC[Connected[0]]]
    dump_RSSI_DOWN_0[ii_Name]=RSSI_0[STAs_MAC[Connected[0]]]
    dump_SNR_DOWN_low[ii_Name]=np.power(10, [a/10 for a in SNR_low[STAs_MAC[Connected[0]]]])
    dump_SNR_DOWN_0[ii_Name]=np.power(10, [a/10 for a in SNR_0[STAs_MAC[Connected[0]]]])
    dump_Throughput_DOWN_low[ii_Name]=DATA_DOWN_low[STAs_ID[0]]['Bandwidth']
    dump_Throughput_DOWN_0[ii_Name]=DATA_DOWN_0[STAs_ID[0]]['Bandwidth']
    dump_Tx_mcs_DOWN_low[ii_Name]=[int(a) for a in DATA_DOWN_low[STAs_ID[0]]['Tx_mcs']]
    dump_Tx_mcs_DOWN_0[ii_Name]=[int(a) for a in DATA_DOWN_0[STAs_ID[0]]['Tx_mcs']]
    dump_Rx_mcs_DOWN_low[ii_Name]=[int(a) for a in DATA_DOWN_low[STAs_ID[0]]['Rx_mcs']]
    dump_Rx_mcs_DOWN_0[ii_Name]=[int(a) for a in DATA_DOWN_0[STAs_ID[0]]['Rx_mcs']]
    dump_SQ_DOWN_low[ii_Name]=[int(a) for a in DATA_DOWN_low[STAs_ID[0]]['SQ']]
    dump_SQ_DOWN_0[ii_Name]=[int(a) for a in DATA_DOWN_0[STAs_ID[0]]['SQ']]

# Save as .mat
scipy.io.savemat('MapStatistics', {'mean_RSSI_UP_low': mean_RSSI_UP_low, 'mean_RSSI_UP_0': mean_RSSI_UP_0, 'mean_RSSI_DOWN_low': mean_RSSI_DOWN_low, 'mean_RSSI_DOWN_0': mean_RSSI_DOWN_0,
                                   'mean_SNR_UP_low': mean_SNR_UP_low, 'mean_SNR_UP_0': mean_SNR_UP_0, 'mean_SNR_DOWN_low': mean_SNR_DOWN_low, 'mean_SNR_DOWN_0': mean_SNR_DOWN_0,
                                   'mean_Throughput_UP_low': mean_Throughput_UP_low, 'mean_Throughput_UP_0': mean_Throughput_UP_0, 'mean_Throughput_DOWN_low': mean_Throughput_DOWN_low, 'mean_Throughput_DOWN_0': mean_Throughput_DOWN_0})
scipy.io.savemat('FullStatistics', {'dump_RSSI_UP_low': dump_RSSI_UP_low, 'dump_RSSI_UP_0': dump_RSSI_UP_0, 'dump_RSSI_DOWN_low': dump_RSSI_DOWN_low, 'dump_RSSI_DOWN_0': dump_RSSI_DOWN_0,
                                   'dump_SNR_UP_low': dump_SNR_UP_low, 'dump_SNR_UP_0': dump_SNR_UP_0, 'dump_SNR_DOWN_low': dump_SNR_DOWN_low, 'dump_SNR_DOWN_0': dump_SNR_DOWN_0,
                                   'dump_Throughput_UP_low': dump_Throughput_UP_low, 'dump_Throughput_UP_0': dump_Throughput_UP_0, 'dump_Throughput_DOWN_low': dump_Throughput_DOWN_low, 'dump_Throughput_DOWN_0': dump_Throughput_DOWN_0,
                                   'dump_Tx_mcs_UP_low': dump_Tx_mcs_UP_low, 'dump_Tx_mcs_UP_0': dump_Tx_mcs_UP_0, 'dump_Tx_mcs_DOWN_low': dump_Tx_mcs_DOWN_low, 'dump_Tx_mcs_DOWN_0': dump_Tx_mcs_DOWN_0,
                                   'dump_Rx_mcs_UP_low': dump_Rx_mcs_UP_low, 'dump_Rx_mcs_UP_0': dump_Rx_mcs_UP_0, 'dump_Rx_mcs_DOWN_low': dump_Rx_mcs_DOWN_low, 'dump_Rx_mcs_DOWN_0': dump_Rx_mcs_DOWN_0,
                                   'dump_SQ_UP_low': dump_SQ_UP_low, 'dump_SQ_UP_0': dump_Rx_mcs_UP_0, 'dump_SQ_DOWN_low': dump_SQ_DOWN_low, 'dump_SQ_DOWN_0': dump_SQ_DOWN_0})
