# Adaptive-Codebook-Optimization
This code is intended for replicating the results of the paper presented in Mobicom 2018:

["Joan Palacios, Daniel Steinmetzer, Adrian Loch, Matthias Hollick, and Joerg Widmer. 2018. Adaptive Codebook Optimization for Beam Training on Off-The-Shelf IEEE 802.11ad Devices. In Proceedings of the 24th ACM Annual International Conference on Mobile Computing and Networking."](http://eprints.networks.imdea.org/1880/)

## Requirements
1.	Two TALON7200AD routers (one will act as AP and the other as STA)
2.	A PC with ssh, scp and Python installed

## Routers configuration
1.	Routers must be flashed with the firmware modification made by Daniel Steinmetzer that you can find in this [link](https://github.com/seemoo-lab/lede-ad7200).
2.	Then, you should copy the folders Router_AP and Router_STA in each router’s main folder. This will configure them to act as AP and STA and to create a Wi-Fi Network with SSID “ACOTalon” and password “TalonACO”, so you can access the AP with IP “192.168.4.2” and the STA with IP “192.168.4.3”. Please, remember to configure a static IP in your PC that doesn’t create a conflict with your router’s ones.
3.	You must set a password for the root user in the routers using command “passwd root”.
Step 1 allows you to read the per sector RSSI and SNR measured by the routers
Step 2 configures the routers
Step 3 sets the password used for the ssh connection in the Python script

## Python scripts
The main python script for measuring is “RunExperiments_v2Dev.py”. In this script you can find the parameters to modify in the beginning of the file under the title “CONFIGURE ENVIRONMENT”. This will reproduce a measurement for the experiments done in our Mobicom paper “ACO”.
Then you can find two other scripts to show results “VisualizeData_v2.py” and “VisualizeSimpleData.py”.
There’s another script “SaveDATA_MAT.py” that translates the experiments measures to a MatLab file so you can analyze the results using MatLab.

## Warning:
This code is designed for a very specific version of a Talon7200 firmware patch and it may not work properly under other versions due to parsing problems.
That's why I created a more flexible interface with an intuitive measurement pipeline where you can plug your device measurements.
You can find it in the following repository:
[ACO](https://github.com/Joanguitar/ACO)

## Contact
[Joan Palacios](https://scholar.google.es/citations?user=tTH1m20AAAAJ) [joan.palacios@imdea.org]
