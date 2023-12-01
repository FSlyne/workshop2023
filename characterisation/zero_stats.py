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

tf = tflex("10.10.10.92")

voas=voa_maker('10.10.10.90').make() 

# Read out available line_ports

line_port = '1/1/n2' # 'ADVA_1_TF1_p2'

logical_interface = 'ot200'
modulation = 'dp-qpsk'
target_power = -5.
central_frequency_ghz = 193950 # Ghz
sleep_counter=15

# channel_num = 90 # 195000 [GHz], 74

#voas['CH-1-2-N2'].set_atten(20)
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

# sleep_counter = tf.change_configuration(line_port=line_port, logical_interface=logical_interface,
#                                           modulation=modulation, target_power=target_power,
#                                           central_frequency=central_frequency_ghz * 1000)
# 
# 
# time.sleep(sleep_counter)

#tf.get_params(line_port)
#exit()
config = tf.return_current_config()

tf.reset_pm_counters(line_port)

exit()

perf_dict = tf.read_pm_data(sleep_counter, line_port, DEBUG=True)


print(perf_dict)

print(config[line_port])
print(config[line_port]['symbolrate'])

print("Optical Receive Power, Q-Factor, SNR, OSNR, FEC ber")
print(perf_dict['CarrierTF_indefinite_opt-rcv-pwr'],
perf_dict['QualityTF_indefinite_q-factor'],
perf_dict['QualityTF200gQpsk_indefinite_signal-to-noise-ratio'],
perf_dict['QualityTF200gQpsk_indefinite_optical-signal-to-noise-ratio'],
'{:.2e}'.format(float( perf_dict['FEC:indefinite:fec-ber'])),
perf_dict['FEC:15min:fec-uncorrected-blocks'])


