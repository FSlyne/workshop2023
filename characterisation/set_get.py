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


tf = tflex("10.10.10.92")

tf.set_fec_algorithm('1/1/n2', 'sdfec-acacia15-7iterations')
print(tf.get_fec_algorithm('1/1/n2'))
print(tf.get_filterrolloff('1/1/n2'))

exit()

voas=voa_maker('10.10.10.90').make() 

# Read out available line_ports
config = tf.return_current_config()
config['1/1/n2']
line_ports = config.keys()

line_port = '1/1/n2' # 'ADVA_1_TF1_p2'

logical_interface = 'ot300'
modulation = 'dp-p-16qam'
target_power = -5.
central_frequency_ghz = 193950 # Ghz

# channel_num = 90 # 195000 [GHz], 74

voas['CH-1-2-N2'].set_atten(0)
# settings_list=[('ot200', 'dp-qpsk'),
#     ('ot200', 'dp-16qam'),
#     ('ot300', 'dp-16qam'),
#     ('ot300', 'dp-32qam'), ('ot300', 'dp-64qam'),
#     ('ot400', 'dp-16qam'), ('ot400', 'dp-32qam'),
#     ('ot400', 'dp-64qam'), ('ot500', 'dp-32qam'),
#     ('ot500', 'dp-64qam'), ('ot600', 'dp-64qam'), ('ot100', 'dp-qpsk'), ('ot200', 'dp-p-16qam'), ('ot300', 'dp-p-16qam')]
# 
# settings_list=[('ot200','dp-qpsk')]
# settings_list=[('ot300','dp-32qam')]
# settings_list=[('ot300','dp-p-h16qam')]

sleep_counter = tf.change_configuration(line_port=line_port, logical_interface=logical_interface,
                                          modulation=modulation, target_power=target_power,
                                          central_frequency=central_frequency_ghz * 1000)


time.sleep(sleep_counter)
atten =30
voas['CH-1-2-N1'].set_atten(atten) # 1/10 dB. set from 0 to 30 dB
time.sleep(5)

tf.set_interface_on(line_port)
perf_dict = tf.read_pm_data(5, line_port, DEBUG=True)
                
#                print(perf_dict)
                
                # Read out available line_ports
config = tf.return_current_config()
    
print(perf_dict)
print(config[line_port])

if 'FEC:indefinite:fec-ber' in perf_dict:
    if perf_dict['FEC:indefinite:fec-ber'] is not None:
        fec = '{:.2e}'.format(float( perf_dict['FEC:indefinite:fec-ber']))
    else:
        fec = "None"
else:
    fec = "N/A"
if 'FEC:15min:fec-uncorrected-blocks' in perf_dict:
    if perf_dict['FEC:15min:fec-uncorrected-blocks'] is not None:
        fub = perf_dict['FEC:15min:fec-uncorrected-blocks']
    else:
        fub = "None"
else:
    fub = "N/A"

indefinite_snr='QualityTF200gQpsk_indefinite_signal-to-noise-ratio'
indefinite_osnr='QualityTF200gQpsk_indefinite_optical-signal-to-noise-ratio'

for key, value in perf_dict.items():
    if key.endswith('_indefinite_signal-to-noise-ratio'):
        indefinite_snr = key
    if key.endswith('_indefinite_optical-signal-to-noise-ratio'):
        indefinite_osnr = key
        
print(indefinite_snr, indefinite_osnr)
    
result = [line_port, logical_interface, modulation,
          config[line_port]['symbolrate'], config[line_port]['fec'],
          perf_dict['CarrierTF_indefinite_opt-rcv-pwr'],
            perf_dict['QualityTF_indefinite_q-factor'],
            perf_dict[indefinite_snr],
            perf_dict[indefinite_osnr], fec, fub]
print(result)

    



