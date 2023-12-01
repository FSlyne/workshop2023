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
line_port='1/1/n2'

tf = tflex("10.10.10.92")
tf.reset_stats(line_port)

exit()

print(config[line_port])
print(config[line_port]['fec'], config[line_port]['symbolrate'], config[line_port]['filter-roll-off'])
