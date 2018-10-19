import numpy as np
import json
import matplotlib.pyplot as plt
import scipy.signal

# Experiment's name
Name='Exp2Dev_Test'

# Load
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

# Define extract methods
Connected=json_data_low['Setup_info']['Connected']
def getRSSI(json_data):
    MACs=json_data['Setup_info']['MACs']
    MAC_ind={MACs[ii]: ii for ii in range(len(MACs))}
    RSSI={MAC_STA: [json_data['RSSIs_COM_val'][ii][Connected[MAC_ind[MAC_STA]]][MAC_STA] for ii in range(len(json_data['RSSIs_COM_val']))] for MAC_STA in MACs if Connected[MAC_ind[MAC_STA]] is not None}
    RSSI={key: [np.max(rssi) for rssi in RSSI[key]] for key in RSSI.keys()}
    return RSSI
def getSNR(json_data):
    MACs=json_data['Setup_info']['MACs']
    MAC_ind={MACs[ii]: ii for ii in range(len(MACs))}
    RSSI={MAC_STA: [json_data['SNRs_COM_val'][ii][Connected[MAC_ind[MAC_STA]]][MAC_STA] for ii in range(len(json_data['SNRs_COM_val']))] for MAC_STA in MACs if Connected[MAC_ind[MAC_STA]] is not None}
    RSSI={key: [np.max(rssi) for rssi in RSSI[key]] for key in RSSI.keys()}
    return RSSI

def getDATA_DOWN(json_data):
    DATA={key: {keyy: [] for keyy in json_data['DATA_DOWN_val'][key][0].keys()} for key in json_data['DATA_DOWN_val'].keys()}
    for key in json_data['DATA_DOWN_val'].keys():
        for keylist in json_data['DATA_DOWN_val'][key]:
            for keyy in keylist.keys():
                keylist[keyy].extend([keylist[keyy][-1]]*(100-len(keylist[keyy])))
                DATA[key][keyy].extend(keylist[keyy])
    return DATA
def getDATA_UP(json_data):
    DATA={key: {keyy: [] for keyy in json_data['DATA_UP_val'][key][0].keys()} for key in json_data['DATA_UP_val'].keys()}
    for key in json_data['DATA_UP_val'].keys():
        for keylist in json_data['DATA_UP_val'][key]:
            for keyy in keylist.keys():
                keylist[keyy].extend([keylist[keyy][-1]]*(100-len(keylist[keyy])))
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

# Create figures
fig_vec=[plt.figure('STA %s'%ID) for ID in STAs_ID]
ax_vec=[[None]*6 for ID in STAs_ID]
for ii in range(len(fig_vec)):
    plt.figure('STA %s'%STAs_ID[ii])
    fig_vec[ii].clf()
    ax_vec[ii][0]=fig_vec[ii].add_subplot(611)
    plt.xticks(np.arange(0, 22, 2))
    ax_vec[ii][1]=fig_vec[ii].add_subplot(612)
    plt.xticks(np.arange(0, 22, 2))
    ax_vec[ii][2]=fig_vec[ii].add_subplot(613)
    plt.xticks(np.arange(0, 22, 2))
    ax_vec[ii][3]=fig_vec[ii].add_subplot(614)
    plt.xticks(np.arange(0, 22, 2))
    ax_vec[ii][4]=fig_vec[ii].add_subplot(615)
    plt.xticks(np.arange(0, 22, 2))
    ax_vec[ii][5]=fig_vec[ii].add_subplot(616)
    plt.xticks(np.arange(0, 22, 2))
    ax_vec[ii][0].plot(np.arange(0, 20, 1), 10*np.log10(RSSI_low[STAs_MAC[Connected[ii]]]), color='red', label='method low')
    ax_vec[ii][0].plot(np.arange(0, 20, 1), 10*np.log10(RSSI_0[STAs_MAC[Connected[ii]]]), color='blue', label='no method')
    ax_vec[ii][0].set_ylabel('RSSI\nDOWN\n(dB)')
    ax_vec[ii][0].set_xlim(0, 20)
    ax_vec[ii][1].plot(np.arange(0, 20, 0.01), scipy.signal.savgol_filter(DATA_DOWN_low[STAs_ID[ii]]['Bandwidth'], 101, 1), color='red', label='method low')
    ax_vec[ii][1].plot(np.arange(0, 20, 0.01), scipy.signal.savgol_filter(DATA_DOWN_0[STAs_ID[ii]]['Bandwidth'], 101, 1), color='blue', label='no method')
    ax_vec[ii][1].set_ylabel('Bandwidth\nDOWN\n(Mbps)')
    ax_vec[ii][1].set_xlim(0, 20)
    ax_vec[ii][2].plot(np.arange(0, 20, 1), SNR_low[STAs_MAC[Connected[ii]]], color='red', label='method low')
    ax_vec[ii][2].plot(np.arange(0, 20, 1), SNR_0[STAs_MAC[Connected[ii]]], color='blue', label='no method')
    ax_vec[ii][2].set_ylabel('SNR\nDOWN\n(dB)')
    ax_vec[ii][2].set_xlim(0, 20)
    ax_vec[ii][3].plot(np.arange(0, 20, 1), 10*np.log10(RSSI_low[STAs_MAC[ii]]), color='red', label='method low')
    ax_vec[ii][3].plot(np.arange(0, 20, 1), 10*np.log10(RSSI_0[STAs_MAC[ii]]), color='blue', label='no method')
    ax_vec[ii][3].set_ylabel('RSSI\nUP\n(dB)')
    ax_vec[ii][3].set_xlim(0, 20)
    ax_vec[ii][4].plot(np.arange(0, 20, 0.01), scipy.signal.savgol_filter(DATA_UP_low[STAs_ID[ii]]['Bandwidth'], 101, 1), color='red', label='method low')
    ax_vec[ii][4].plot(np.arange(0, 20, 0.01), scipy.signal.savgol_filter(DATA_UP_0[STAs_ID[ii]]['Bandwidth'], 101, 1), color='blue', label='no method')
    ax_vec[ii][4].set_ylabel('Bandwidth\nUP\n(Mbps)')
    ax_vec[ii][4].set_xlim(0, 20)
    ax_vec[ii][5].plot(np.arange(0, 20, 1), SNR_low[STAs_MAC[ii]], color='red', label='method low')
    ax_vec[ii][5].plot(np.arange(0, 20, 1), SNR_0[STAs_MAC[ii]], color='blue', label='no method')
    ax_vec[ii][5].set_ylabel('SNR\nUP\n(dB)')
    ax_vec[ii][5].set_xlabel('Time (s)')
    ax_vec[ii][5].set_xlim(0, 20)
#    ax_vec[ii][3].plot(np.arange(0, 200, 1), np.array(DATA_low[STAs_ID[ii]]['Tx_mcs']), color='red', label='method low')
#    ax_vec[ii][3].plot(np.arange(0, 200, 1), np.array(DATA_0[STAs_ID[ii]]['Tx_mcs']), color='blue', label='no method')
#    ax_vec[ii][3].set_xlabel('Time (s)')
#    ax_vec[ii][3].set_ylabel('Tx_mcs')
#    ax_vec[ii][3].set_xlim(0, 200)
#    ax_vec[ii][4].plot(np.arange(0, 200, 1), np.array(DATA_low[STAs_ID[ii]]['Rx_mcs']), color='red', label='method low')
#    ax_vec[ii][4].plot(np.arange(0, 200, 1), np.array(DATA_0[STAs_ID[ii]]['Rx_mcs']), color='blue', label='no method')
#    ax_vec[ii][4].set_xlabel('Time (s)')
#    ax_vec[ii][4].set_ylabel('Rx_mcs')
#    ax_vec[ii][4].set_xlim(0, 200)
#    ax_vec[ii][5].plot(np.arange(0, 200, 1), np.array(DATA_low[STAs_ID[ii]]['SQ']), color='red', label='method low')
#    ax_vec[ii][5].plot(np.arange(0, 200, 1), np.array(DATA_0[STAs_ID[ii]]['SQ']), color='blue', label='no method')
#    ax_vec[ii][5].set_xlabel('Time (s)')
#    ax_vec[ii][5].set_ylabel('SQ')
#    ax_vec[ii][5].set_xlim(0, 200)
    ax_vec[ii][0].legend(bbox_to_anchor=(0.9, 0.975))
    for ii_ax in range(6):
#        ax_vec[ii][ii_ax].legend()
        ax_vec[ii][ii_ax].yaxis.set_label_position("right")
plt.show()