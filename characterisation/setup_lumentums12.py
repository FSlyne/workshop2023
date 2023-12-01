import json

from tcdona2.lumentum2 import *

roadm_ip_list=['10.10.10.38','10.10.10.37'] # roadm2

# chunk=[
# ('193284.375','193315.625',1),
# ('193584.375','193615.625',1),
# ('193784.375','193815.625',1),
# ('193884.375','193915.625',1),
# ('193984.375','194015.625',1),
# ('194084.375','194115.625',1)
# ]

unblock_list = [7,14,17,19,20,21,22];
# unblock_list = [14,17,19,20,21,22];

roadm_list=[]
for roadm_ip in roadm_ip_list:
    roadm=Lumentum(roadm_ip)
    roadm.wss_delete_connection(1,'all')
    roadm.wss_delete_connection(2,'all')
    # 
    roadm.make_n_channel_chunk_mux(191600.00, 50,50, max_f=195900.00, blocked=False)
    roadm.make_n_channel_chunk_demux(191600.00, 50,50, max_f=195900.00, blocked=False)
    print(roadm_ip)
    print("mux")
    #roadm.set_mux_unblock(unblock_list)
    print("demux")
    #roadm.set_demux_unblock(unblock_list)
    
    roadm.set_mux_offline()
    roadm.set_demux_offline()
    
    roadm.set_mux_high_gain_mode()
    roadm.set_demux_high_gain_mode()
    
    roadm.set_mux_constant_gain(20)
    roadm.set_demux_constant_power(23)
    
    roadm.set_mux_online()
    roadm.set_demux_online()
    
    roadm_list.append(roadm)


    

