from tflex_params import *
from tcdona2.MS9710C import *
from tcdona2.lumentum2 import *
from experiment3_lib import *
from tcdona2.adva_voa_lib import *
import time
import pyvisa
from time import sleep
import xmltodict
import numpy as np
import os
import datetime
import csv

topology = 'topology1'
run = "00"
save_dir = topology + '_'+str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
path = os.path.join('/tmp/measurements', save_dir)
if not os.path.isdir(path):
    os.mkdir(path)
    
rm = pyvisa.ResourceManager()
osa=MS9710C(rm, 'GPIB0::8::INSTR')
voas=voa_maker('10.10.10.90').make()

tf = tflex("10.10.10.92")

# Read out available line_ports
config = tf.return_current_config()
line_ports = config.keys()

line_port = '1/1/n2' # 'ADVA_1_TF1_p2'

logical_interface = 'ot200'
modulation = 'dp-qpsk'
target_power = -2.
central_frequency_ghz = 193950 # Ghz

# channel_num = 90 # 195000 [GHz], 74

voas['CH-1-2-N2'].set_atten(0)

sleep_counter = tf.change_configuration(line_port=line_port, logical_interface=logical_interface,
                                      modulation=modulation, target_power=target_power,
                                      central_frequency=central_frequency_ghz * 1000)
time.sleep(sleep_counter)

csv_file = 'teraflex_readings.txt'  
fcsv = open(os.path.join(path, csv_file), mode='w')
writer = csv.writer(fcsv)

header = ['Line Port', 'Interface', 'Modulation',
          'Symbol Rate', 'FEC', 'Optical Receive Power',
          'Q-Factor', 'SNR', 'OSNR', 'FEC ber']
writer.writerow(result)

for atten in range(1):
    atten=atten*10
    voas['CH-1-2-N1'].set_atten(atten) # 1/10 dB. set from 0 to 30 dB
    time.sleep(5)
    
    for state in [0, 1]:
        if state == 0:
            tf.set_interface_on(line_port)
            symbolrate = 0
            perf_dict = tf.read_pm_data(5, line_port, DEBUG=True)
            
            # Read out available line_ports
            config = tf.return_current_config()

            if 'FEC:indefinite:fec-ber' in perf_dict and perf_dict['FEC:indefinite:fec-ber'] is not None:
                fec = '{:.2e}'.format(float( perf_dict['FEC:indefinite:fec-ber']))
            else:
                fec = "N/A"
            if 'FEC:15min:fec-uncorrected-blocks' in perf_dict and perf_dict['FEC:15min:fec-uncorrected-blocks'] is not None:
                fub = perf_dict['FEC:15min:fec-uncorrected-blocks']
            else:
                fub = "N/A"
                
            result = [line_port, logical_interface, modulation,
                      config[line_port]['symbolrate'], config[line_port]['fec'],
                      perf_dict['CarrierTF_indefinite_opt-rcv-pwr'],
                        perf_dict['QualityTF_indefinite_q-factor'],
                        perf_dict['QualityTF200gQpsk_indefinite_signal-to-noise-ratio'],
                        perf_dict['QualityTF200gQpsk_indefinite_optical-signal-to-noise-ratio'], fec, fub]
            
            writer.writerow(result)
        else:
            tf.set_interface_off(line_port)

        power_array=osa.get_wavelength_power_array()
        #print(power_array)
        #print(osa.read_freqency_power_from_power_array(power_array, central_frequency_ghz))
    
        file_name = 'osa_atten_'+str(atten) +'_state' + str(state)  + '_res.txt'
    
        with open(os.path.join(path, file_name), mode='w') as f:
           f.write('\n'.join('%s %s' % x for x in power_array))

fcsv.close()

    



