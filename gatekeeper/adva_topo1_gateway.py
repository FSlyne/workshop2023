import sys
import time
from tcdona2.polatis3 import *

option=1
if len(sys.argv) == 1:
    option=1
else: 
    option=0

# Setting up Polatis
print ("Setting up the Polatis ...")
plts = Polatis('10.10.10.28','3082')
plts.login()

patch_list = [
('ADVA_1_TF1_p1', 'ADVA_1_8PSM_p1', 'ADVA_1_TF1_p1'),
('ADVA_1_TF1_p2', 'ADVA_1_8PSM_p2', 'ADVA_1_TF1_p2'),
('ADVA_2_TF1_p1', 'ADVA_1_8PSM_p3', 'ADVA_2_TF1_p1'),
('ADVA_2_TF1_p2', 'ADVA_1_8PSM_p4', 'ADVA_2_TF1_p2'),

('ADVA_1_8PSM_line','ADVA_1_D20'),
#('ADVA_1_D20', 'ADVA_1_voa2'),

('ADVA_1_D20', 'Lumentum_3_p1'),

('Lumentum_3_line', 'ADVA_1_voa2'),
('ADVA_1_voa2', 'Reel_Corning_25220'),

('Reel_Corning_25220', 'Lumentum_4_line'),
('Lumentum_4_p1','Lumentum_4_p1'),

('Lumentum_4_line', 'Reel_Lycom_25028'),
('Reel_Lycom_25028','Lumentum_3_line'),
('Lumentum_3_p1', 'ADVA_1_8PSM_line'),

#('ADVA_1_voa2', 'ADVA_1_8PSM_line'),

('Lumentum_1_p1', 'Lumentum_2_p1'),
('Lumentum_2_line', 'ADVA_1_voa1', 'ADVA_1_8PSM_p5'),
('Laser_N7711A_1', 'Lumentum_2_line'),

('ADVA_1_8PSM_p6','OSA_MS9710C_1')
]

if option == 0:
    plts.clearallconn()
    print("Patching ...")
    for patch in patch_list:
        plts.patching2(*patch)
    time.sleep(3)
    print("Monitoring ...")
    for patch in patch_list:
        plts.get_patch_power(*patch)
    time.sleep(3)
else:
    print("Monitoring ...")
    for patch in patch_list:
        plts.get_patch_power(*patch)

