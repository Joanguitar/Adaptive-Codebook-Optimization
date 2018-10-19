import numpy as np
import json
import matplotlib.pyplot as plt
import scipy.signal

# Experiments' names
Names=['Exp2_1', 'Exp3_1', 'Exp4_1', 'Exp5_1', 'Exp6_1', 'Exp7_1']

RSSI=[]
Bandwidth=[]
Cwnd=[]
Tx_mcs=[]
Rx_mcs=[]
SQ=[]
for Name in Names:
    # Load
    with open('Experiments/%s_low.json'%(Name)) as fp:
        json_data_low=json.load(fp)
        fp.close()
    with open('Experiments/%s_0.json'%(Name)) as fp:
        json_data_0=json.load(fp)
        fp.close()
    
    # Correct empty measures by extending last
    for key in json_data_low['DATA_val'].keys():
        for data in json_data_low['DATA_val'][key]:
            data['Rx_mcs'].extend([data['Rx_mcs'][-1]]*(100-len(data['Rx_mcs'])))
            data['SQ'].extend([data['SQ'][-1]]*(100-len(data['SQ'])))
            data['Tx_mcs'].extend([data['Tx_mcs'][-1]]*(100-len(data['Tx_mcs'])))
        for data in json_data_0['DATA_val'][key]:
            data['Rx_mcs'].extend([data['Rx_mcs'][-1]]*(100-len(data['Rx_mcs'])))
            data['SQ'].extend([data['SQ'][-1]]*(100-len(data['SQ'])))
            data['Tx_mcs'].extend([data['Tx_mcs'][-1]]*(100-len(data['Tx_mcs'])))
    
    # Define extract methods
    def getRSSI(json_data):
        Connected=json_data['Setup_info']['Connected']
        MACs=json_data['Setup_info']['MACs']
        MAC_ind={MACs[ii]: ii for ii in range(len(MACs))}
        RSSI={MAC_STA: [json_data['RSSIs_COM_val'][ii][Connected[MAC_ind[MAC_STA]]][MAC_STA] for ii in range(len(json_data['RSSIs_COM_val']))] for MAC_STA in MACs if Connected[MAC_ind[MAC_STA]] is not None}
        RSSI={key: [np.max(rssi) for rssi in RSSI[key]] for key in RSSI.keys()}
        return RSSI
    
    def getDATA(json_data):
        DATA={key: {keyy: [] for keyy in json_data['DATA_val'][key][0].keys()} for key in json_data['DATA_val'].keys()}
        for key in json_data['DATA_val'].keys():
            for keylist in json_data['DATA_val'][key]:
                for keyy in keylist.keys():
                    DATA[key][keyy].extend(keylist[keyy])
        return DATA
    
    # Extract data
    DATA_low=getDATA(json_data_low)
    RSSI_low=getRSSI(json_data_low)
    DATA_0=getDATA(json_data_0)
    RSSI_0=getRSSI(json_data_0)
    STAs_ID=list(DATA_low.keys())
    STAs_MAC=[json_data_low['Setup_info']['MACs'][ii] for ii in range(len(json_data_low['Setup_info']['MACs'])) if json_data_low['Setup_info']['Connected'][ii] is not None]
    
    # Append data
    for ii in range(len(STAs_ID)):
        RSSI.append([np.mean(RSSI_low[STAs_MAC[ii]]), np.mean(RSSI_0[STAs_MAC[ii]])])
        Bandwidth.append([np.mean(DATA_low[STAs_ID[ii]]['Bandwidth']), np.mean(DATA_0[STAs_ID[ii]]['Bandwidth'])])
        Cwnd.append([np.mean(DATA_low[STAs_ID[ii]]['Cwnd']), np.mean(DATA_0[STAs_ID[ii]]['Cwnd'])])
        Tx_mcs.append([np.mean([int(a) for a in DATA_low[STAs_ID[ii]]['Tx_mcs']]), np.mean([int(a) for a in DATA_0[STAs_ID[ii]]['Tx_mcs']])])
        Rx_mcs.append([np.mean([int(a) for a in DATA_low[STAs_ID[ii]]['Rx_mcs']]), np.mean([int(a) for a in DATA_0[STAs_ID[ii]]['Rx_mcs']])])
        SQ.append([np.mean([int(a) for a in DATA_low[STAs_ID[ii]]['SQ']]), np.mean([int(a) for a in DATA_0[STAs_ID[ii]]['SQ']])])

# Matrix parameters
RSSI=np.array(RSSI)
Bandwidth=np.array(Bandwidth)
Cwnd=np.array(Cwnd)
Tx_mcs=np.array(Tx_mcs)
Rx_mcs=np.array(Rx_mcs)
SQ=np.array(SQ)

PARAMS=[RSSI, Bandwidth, Cwnd, Tx_mcs, Rx_mcs, SQ]
PARAM_NAMES=['RSSI', 'Bandwidth', 'Cwnd', 'Tx_mcs', 'Rx_mcs', 'SQ']
PARAM_UNITS=['', '[Mbps]', '[Mb]', '', '', '']

# Create figures
fig_a=plt.figure('Absolute plots')
ax_a=[None]*6
xx=np.arange(RSSI.shape[0])
for ii in range(6):
    ax_a[ii]=fig_a.add_subplot(611+ii)
    ax_a[ii].bar(xx-0.2, PARAMS[ii][:, 0], width=0.4, color='r', label='method low')
    ax_a[ii].bar(xx+0.2, PARAMS[ii][:, 1], width=0.4, color='b', label='no method')
    ax_a[ii].set_xlabel('Index')
    ax_a[ii].set_ylabel('%s %s'%(PARAM_NAMES[ii], PARAM_UNITS[ii]))
    ax_a[ii].legend()

# Create relative figures
fig_r=plt.figure('Relative plots')
ax_r=[None]*6
for ii in range(6):
    ax_r[ii]=fig_r.add_subplot(611+ii)
    ax_r[ii].bar(xx-0.2, (PARAMS[ii][:, 0]/PARAMS[ii][:, 1]-1)*100, width=0.4, color='k', label='gain %%')
    ax_r[ii].set_xlabel('Index')
    ax_r[ii].set_ylabel('%s gain [%%]'%(PARAM_NAMES[ii]))
    ax_r[ii].legend()
plt.show()