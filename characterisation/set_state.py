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
import json

line_port = '1/1/n2' # 'ADVA_1_TF1_p2'

tf = tflex("10.10.10.92")

# Read out available line_ports

tf.set_interface_on(line_port)






