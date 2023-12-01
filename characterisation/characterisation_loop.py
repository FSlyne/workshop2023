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
import re

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
target_power = -5.
central_frequency_ghz = 193950 # Ghz

# channel_num = 90 # 195000 [GHz], 74

voas['CH-1-2-N2'].set_atten(0)

settings_list=[('ot300', 'dp-16qam'),
    ('ot300', 'dp-32qam'), ('ot300', 'dp-64qam'),
    ('ot400', 'dp-16qam'), ('ot400', 'dp-32qam'),
    ('ot400', 'dp-64qam'), ('ot500', 'dp-32qam'),
    ('ot500', 'dp-64qam'), ('ot600', 'dp-64qam'),
    ('ot200', 'dp-qpsk'),  ('ot200', 'dp-16qam'),
    ('ot100', 'dp-qpsk'), ('ot200', 'dp-p-16qam'), ('ot300', 'dp-p-16qam')]

# settings_list=[ ('ot200', 'dp-p-16qam'), ('ot300', 'dp-p-16qam'), ('ot100', 'dp-qpsk')]

settings_list=[('ot100', 'dp-qpsk'), ('ot200', 'dp-p-16qam'), ('ot200', 'dp-qpsk'),
                ('ot200', 'dp-16qam'), ('ot300', 'dp-16qam')]

settings_list=[('ot300', 'dp-16qam')]

csv_file = 'teraflex_readings.txt'  
fcsv = open(os.path.join(path, csv_file), mode='w')
writer = csv.writer(fcsv)

header = ['Time','Line Port', 'Interface', 'Modulation', 'Atten',
          'Symbol Rate', 'FEC', 'Optical Receive Power',
          'Q-Factor', 'SNR', 'OSNR', 'FEC ber']

fec_rolloff = [('sdfec-acacia15-7iterations', 0.19), ('sdfec-acacia27-7iterations', 0.19)]
fec_rolloff = [('sdfec-acacia27-7iterations', 0.19)]
writer.writerow(header)

for logical_interface, modulation in settings_list:
    for sdfec, rolloff in fec_rolloff:
        sleep_counter = tf.change_configuration(line_port=line_port, logical_interface=logical_interface,
                          modulation=modulation, target_power=target_power,
                          central_frequency=central_frequency_ghz * 1000,
                          fec=sdfec, rolloff=rolloff)
        time.sleep(sleep_counter)
        for atten in range(30,-1, -1):
            atten=atten*10
            voas['CH-1-2-N1'].set_atten(atten) # 1/10 dB. set from 0 to 30 dB
            tf.reset_fec(line_port)
            time.sleep(10)
            for state in [1, 0]:
                if state == 1:
                    # resetting counters etc.
                    tf.set_interface_on(line_port)
                    time.sleep(50)
                    symbolrate = 0
                    perf_dict = tf.read_pm_data(15, line_port, DEBUG=False)
                    
                    #print(perf_dict)
                    
                    # Read out available line_ports
                    config = tf.return_current_config()
                    
                    #print(config[line_port])
        
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
                    
                    sdfec_pattern = r'\d+-\d+'
                    sdfec_match = re.search(sdfec_pattern, config[line_port]['fec'])
                    sdfec_extracted = '0-0'
                    if sdfec_match:
                        sdfec_extracted = sdfec_match.group()
   
                    result = [line_port, logical_interface, modulation, atten/10,
                              config[line_port]['symbolrate'], sdfec_extracted,
                              perf_dict['CarrierTF_indefinite_opt-rcv-pwr'],
                                perf_dict['QualityTF_indefinite_q-factor'],
                                perf_dict[indefinite_snr],
                                perf_dict[indefinite_osnr], fec, fub, time.time()]
                    print(result)
                    writer.writerow(result)
                else:
                    tf.set_interface_off(line_port)
        
                power_array=osa.get_wavelength_power_array()
                #print(power_array)
                #print(osa.read_freqency_power_from_power_array(power_array, central_frequency_ghz))
            
                file_name = 'osa_'+str(logical_interface)+'_'+str(modulation)+'_fec_' + str(sdfec_extracted) +'_atten_' + str(atten) +'_state_' + str(state)  + '_res.txt'
            
                with open(os.path.join(path, file_name), mode='w') as f:
                   f.write('\n'.join('%s %s' % x for x in power_array))

fcsv.close()

    



