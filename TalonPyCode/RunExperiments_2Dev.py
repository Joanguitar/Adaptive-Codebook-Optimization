from TalonPy import Talon, SectorCodebook, BoardFile, MethodIndependent, MethodIndependent_low
import numpy as np
import time
import json

# CONFIGURE ENVIRONMENT
APs_ID=[1]                               # ID of the access point
STAs_ID=[2]                              # ID of the station
Connected=[1, 0]                         # To which AP index is each STA connected
CFG_PASSWORD = '12345'                   # root password of the devices
dump_wait_time = 0.2                     # Time to wait for the sweep dump to be collected
ITER=20                                  # Number of iterations (-1 for infinite)
communication_redundancy=16              # Times the communication beam-pattern appears in the codebook to be measured
iperf_redundancy=2                       # Times the iperf is measured
Repetitions=16                           # Experiment repetitions
bool_reception=False                     # Whether to modify the reception beam-pattern or not
exp_name='Exp2Dev_Test'                  # Name of the experiment (used for the file name)

# HYPER-PARAMETERS
max_active_antennas=18                   # Maximum number of active antennas
gain_val=1                               # On antenna gain value
ampl_val=1                               # On antenna amplifier value

# Derivated parameters
APs_IP = ['192.168.2.%i'%(a+1) for a in APs_ID]                # APs IPs
STAs_IP = ['192.168.2.%i'%(a+1) for a in STAs_ID]              # STAs IPs
IDs=APs_ID+STAs_ID                                             # combine IDs sets
IPs=APs_IP+STAs_IP                                             # combine IPs sets
N_devices=len(IPs)                                             # Number of devices
IP_ind={IPs[ii]: ii for ii in range(N_devices)}                # Ennumerate IPs
Roles=['ap' if IP in APs_IP else 'sta' for IP in IPs]          # Get roles ('ap' or 'sta')
talons=[Talon(IP, password=CFG_PASSWORD) for IP in IPs]        # Establish connections

# ESTABLISH CONNECTION TO REMOTE HOST AND OBTAIN CODEBOOK
codebook_comm=SectorCodebook()
codebook_comm.initialize_default(communication_redundancy)

# Define connected stations
for ii in [ii for ii in range(N_devices) if Roles[ii]=='sta']:
    talons[ii]._host.execute_cmd('echo 10.0.0.%i > /joanscripts/variables/APIP'%(IDs[Connected[ii]])) # This line may change with the IP selected for the 60GHz interface

# Reload driver if not reloaded
for talon in talons:
    talon._host.execute_cmd('bash /joanscripts/initialization')
time.sleep(dump_wait_time)

# Get MACs
MACs=[talon.get_wlan2_mac_address().casefold() for talon in talons] # get MACs without CAPs
MAC_ind={MACs[ii]: ii for ii in range(N_devices)} # ennumerate MACs

# Condensate connection info
Setup_info={'IDs': IDs, 'Connected': Connected, 'MACs': MACs}

# Repetitions
for rep in range(Repetitions):
    for method_num in range(2):
		# Choose method
        if method_num==0:        # Standard IEEE 802.11ad
            method_name='0'
            bool_update=False
            bool_low=False
        elif method_num==1:      # ACO
            method_name='low'
            bool_update=True
            bool_low=True
		# Define when to consider a measurement as outage
        if bool_low:
            active_TH=[0.1, 0.1, 0.9]
        else:
            active_TH=[0.8, 0.2, 0.2, 0.9]
        # Define methods and first iteration (custom BP)
        if bool_low:
            methods=[MethodIndependent_low() for ii in range(N_devices)]
            for method in methods:
                method._max_active_antennas=max_active_antennas
                method._gain_val=gain_val
                method._ampl_val=ampl_val
        else:
            methods=[MethodIndependent() for ii in range(N_devices)]
        for method in methods:
            method.iterate()
        
        # Define Board file, create it and upload it
        BRD=BoardFile()
        BRD.define_BP(methods[0]._codebook, np.arange(0, 64))
        BRD.update_BPInfo2BRD('wil6210.brd')
        for talon in talons:
            talon._host.put('wil6210.brd', '/lib/firmware/wil6210.brd')
        
        # Define how to measure
        def Measure(ite=1):
            RSSIs=[None]*N_devices
            SNRs=[None]*N_devices
            for talon in [talons[ii] for ii in range(N_devices) if Roles[ii]=='sta']:
                talon._host.execute_cmd('bash /joanscripts/reassociate')                                    # Reassociate to load BRD file
            time.sleep(dump_wait_time)
            for talon in talons:
                talon._host.execute_cmd('bash /joanscripts/startsweepdump')                                 # Start dump
                talon._host.execute_cmd('bash /joanscripts/clearsweepdump')                                 # Clear dump
            time.sleep(dump_wait_time)
            for it in range(ite):
                for talon in [talons[ii] for ii in range(N_devices) if Roles[ii]=='sta']:
                    talon._host.execute_cmd('bash /joanscripts/stopsweepdump')                              # Stop dump
                    time.sleep(dump_wait_time)
                    talon._host.execute_cmd('bash /joanscripts/reassociate')                                # Reassociate to load BRD file
                    time.sleep(10*dump_wait_time)
                    talon._host.execute_cmd('bash /joanscripts/startsweepdump')                             # Start dump
                time.sleep(dump_wait_time)
                for ii in [ii for ii in range(N_devices) if Roles[ii]=='sta']:
                    talon=talons[ii]
                    cmdout=talon._host.execute_cmd('bash /joanscripts/connectedstations').decode()[:-1]
                    if len(cmdout)==0:
                        time.sleep(dump_wait_time)
                        cmdout=talon._host.execute_cmd('bash /joanscripts/connectedstations').decode()[:-1]
                        while len(cmdout)==0:
                            talon._host.execute_cmd('bash /joanscripts/defibrilate')
                            talons[Connected[ii]]._host.execute_cmd('bash /joanscripts/defibrilate')
                            time.sleep(100*dump_wait_time)
                            cmdout=talon._host.execute_cmd('bash /joanscripts/connectedstations').decode()[:-1]
                time.sleep(dump_wait_time)
            for talon in talons:
                talon._host.execute_cmd('bash /joanscripts/stopsweepdump')                                  # Stop dump
            time.sleep(dump_wait_time) # wait
            for ii in range(N_devices):
                cmdout=talons[ii]._host.execute_cmd('cat /joanscripts/variables/sweepdump').decode()[:-1]   # Read dump
                RSSIs[ii]=methods[ii].getRSSI_multiple(cmdout)                                              # Get RSSI
                SNRs[ii]=methods[ii].getSNR_multiple(cmdout)                                                # Get SNR
            return RSSIs, SNRs
        
        # Define how to set the codebook
        def SetBPs(ii_talon):
            talon=talons[ii]
            talon._host.execute_cmd('bash /joanscripts/reassociate')                                        # Reassociate to load BRD file
            cmdout=talon._host.execute_cmd('bash /joanscripts/connectedstations').decode()[:-1]             # Check if the connection is working
            t=0
            while len(cmdout)==0:                                                                           # If the connection is dead, wait
                t+=1
                cmdout=talon._host.execute_cmd('bash /joanscripts/connectedstations').decode()[:-1]
                if t==20:
                    talon._host.execute_cmd('bash /joanscripts/defibrilate')                                # Try to revive the connection
                elif t==30:
                    talons[Connected[ii_talon]]._host.execute_cmd('bash /joanscripts/defibrilate')          # Try to revive the connection
                elif t==40:
                    talon._host.execute_cmd('bash /joanscripts/restorewil')                                 # Assume it, connection is dead
                    return False
                time.sleep(1)              # Wait
            time.sleep(dump_wait_time)     # Wait
            return True
        
        # Define how to defibrilate
        def Defibrilate():
            for talon in talons:
                talon._host.execute_cmd('bash /joanscripts/defibrilate &> /dev/null &')                     # Reassociate to load BRD file
            for talon in [talons[ii] for ii in range(N_devices) if Roles[ii]=='sta']:
                talon._host.execute_cmd('bash /joanscripts/waitforconnection')                              # Wait to connect
            time.sleep(2)
        
        # Define how to collect data
        def CollectData(mytalon):
            for talon in [talons[ii] for ii in range(N_devices) if Roles[ii]=='ap']:
                talon._host.execute_cmd('killall iperf3 2> /dev/null')                                      # Kill iperf on the AP side
                talon._host.execute_cmd('iperf3 -s &>/dev/null &')                                          # Start iperf on the AP side
            mytalon._host.execute_cmd('killall iperf3 2> /dev/null')                                        # Kill iperf on the STA side
            cmdout=mytalon._host.execute_cmd('bash /joanscripts/collectdata').decode()[:-1]                 # Collect the data
            while cmdout[-4:]=='able':                                                                      # Insist to collect data untill you're able to
                mytalon._host.execute_cmd('killall iperf3 2> /dev/null')
                mytalon._host.execute_cmd('bash /joanscripts/defibrilate')
                time.sleep(dump_wait_time)
                cmdout=mytalon._host.execute_cmd('bash /joanscripts/collectdata').decode()[:-1]
            return cmdout
            
        # Initialization
        DATA_val={ID: [] for ID in STAs_ID}
        FILES_val={ID: [] for ID in IDs}
        RSSIs_TRAIN_val=[]
        RSSIs_COM_val=[]
        SNRs_TRAIN_val=[]
        SNRs_COM_val=[]
        # Iterate algorithm
        iteration=0
        while not iteration==ITER:
            iteration+=1
            print('-----         Iteration: %3i         -----' % iteration)
            RSSIs, SNRs=Measure(2) # Measure
            RSSIs_TRAIN_val.append([{key: list(RSSI[key]) for key in RSSI.keys()} for RSSI in RSSIs])
            SNRs_TRAIN_val.append([{key: list(SNR[key]) for key in SNR.keys()} for SNR in SNRs])
            # Iterate algorithm and set links for communication
            for jj in [jj for jj in range(N_devices) if Roles[jj]=='sta']:
                ii=Connected[jj]                                                                    # Check to which device it's connected
                if MACs[jj] in RSSIs[ii].keys():
                    RSSI=RSSIs[ii][MACs[jj]]
                    proportionoffoundBPs=np.sum(RSSI>0)/methods[jj]._nBPs                           # Check if the measurement is valid to continue
                    if proportionoffoundBPs>active_TH[methods[jj]._stage] or not bool_update:
                        methods[jj].iterate(RSSI)                                                   # Decide new BPs configuration
                        print('Iterate ID %2i with %2i active antennas (%i%%)'%(IDs[jj], methods[jj]._active_antennas, 100*proportionoffoundBPs))
                    else:
                        print('No Iterate ID %2i (%i%%)'%(IDs[jj], 100*proportionoffoundBPs))
                codebook_comm._sectors=[methods[jj]._winnerBP._sectors[0]]*communication_redundancy # Set transmission beam-patterns for the communication
                if bool_reception:
					# Set the receiving beam-pattern for the communication
                    codebook_comm.add_sector(codebook_comm.null_sector)
                    codebook_comm.set_psh_reg(communication_redundancy, codebook_comm.get_psh_reg(0))
                    codebook_comm.set_etype_reg(communication_redundancy, [6*a for a in codebook_comm.get_etype_reg(0)])
                    codebook_comm.set_dtype_reg(communication_redundancy, [6*a for a in codebook_comm.get_dtype_reg(0)])
                    BRD.define_BP(codebook_comm, np.concatenate((np.arange(communication_redundancy), [64])))                        # Load the BP configuration into the BRD file
                else:
                    BRD.default_BP()
                    BRD.define_BP(codebook_comm, np.arange(communication_redundancy))                                                # Load the BP configuration into the BRD file
                BRD.update_BPInfo2BRD('wil6210.brd')                                                                                 # Create BRD file
                talons[jj]._host.put('wil6210.brd', '/lib/firmware/wil6210.brd')                                                     # Upload BRD file
            # Check how communication is going
            Transmitting={jj: SetBPs(jj) for jj in [jj for jj in range(N_devices) if Roles[jj]=='sta']}
            RSSIs, SNRs=Measure(2) # Measure
            RSSIs_COM_val.append([{key: list(RSSI[key]) for key in RSSI.keys()} for RSSI in RSSIs])
            SNRs_COM_val.append([{key: list(SNR[key]) for key in SNR.keys()} for SNR in SNRs])
            for ii in range(N_devices):
                print('-----Received signals at ID %2i (RSSI)-----' % IDs[ii])
                for MAC in set(RSSIs[ii].keys()).intersection(MACs):
                    if Roles[MAC_ind[MAC]]=='sta' and not Transmitting[MAC_ind[MAC]]:
                        RSSIs[ii][MAC]=np.zeros(64)
                    print('ID %i: %i' % (IDs[MAC_ind[MAC]], np.max(RSSIs[ii][MAC])))
            print('-----            Bitrate             -----')
			# Measure Iperf
            for jj in [jj for jj in range(N_devices) if Roles[jj]=='sta']:
                if Transmitting[jj]:
                    iperf_mean=-1
                    for iiii in range(iperf_redundancy):
                        cmdout=CollectData(talons[jj])
                        channel_data_candidate=methods[jj].ParseData(cmdout)
                        iperf_mean_candidate=np.mean(channel_data_candidate['Bandwidth'])
                        if iperf_mean_candidate>iperf_mean:
                            iperf_mean=iperf_mean_candidate
                            channel_data=channel_data_candidate
                else:
                    iperf_mean=0
                    channel_data={'Tx_mcs': [0]*100, 'Rx_mcs': [0]*100, 'SQ': [0]*100, 'Bandwidth': [0]*100, 'Retr': [0]*100, 'Cwnd': [0]*100}
                    methods[jj]._stage=0
                    methods[jj].iterate()
                if not bool_update:
                    methods[jj]._stage=0
                    methods[jj].iterate()
                print('Bitrate ID %2i: %iMbits/s'%(IDs[jj], np.mean(channel_data['Bandwidth'])))
                codebook_train=methods[jj]._codebook
				# Set beam-patterns for training
                if bool_reception:
                    codebook_comm._sectors=[methods[jj]._winnerBP._sectors[0]]*communication_redundancy
                    codebook_train.add_sector(codebook_comm.null_sector)
                    codebook_train.set_psh_reg(64, codebook_comm.get_psh_reg(0))
                    codebook_train.set_etype_reg(64, [6*a for a in codebook_comm.get_etype_reg(0)])
                    codebook_train.set_dtype_reg(64, [6*a for a in codebook_comm.get_dtype_reg(0)])
                    BRD.define_BP(codebook_train, np.arange(0, 65))                     # load the BP configuration into the BRD file
                else:
                    BRD.default_BP()
                    BRD.define_BP(codebook_train, np.arange(0, 64))                     # load the BP configuration into the BRD file
                BRD.update_BPInfo2BRD('wil6210.brd')                                    # create BRD file
                talons[jj]._host.put('wil6210.brd', '/lib/firmware/wil6210.brd')        # upload BRD file
                DATA_val[IDs[jj]].append({key: list(channel_data[key]) for key in channel_data.keys()})
            for ii in range(N_devices):
                cmdout=talons[ii]._host.execute_cmd('bash /joanscripts/openstations').decode()[:-1]
                FILES_val[IDs[ii]].append(cmdout)
        
        # Encode into json
        Data2save={'DATA_val': DATA_val, 'FILES_val': FILES_val, 'RSSIs_COM_val': RSSIs_COM_val, 'RSSIs_TRAIN_val': RSSIs_TRAIN_val, 'SNRs_COM_val': SNRs_COM_val, 'SNRs_TRAIN_val': SNRs_TRAIN_val, 'Setup_info': Setup_info}
        class MyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                else:
                    return super(MyEncoder, self).default(obj)
        with open('%s_%i_%s.json'%(exp_name, rep, method_name), 'w') as fp:
            json.dump(Data2save, fp, cls=MyEncoder)