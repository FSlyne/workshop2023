from tcdona2.lumentum2 import *
import random
import time

def convert_dbm_to_watt(value):
    return (10**(value/10)/1000)

class timer:
    def __init__(self, show=True):
        self.now = time.time()
        self.show=show
        
    def disp(self,message, reset=False):
        if self.show:
            print("%s\t: %d sec" % (message, time.time()-self.now))
        if reset==True:
            self.now=time.time()

class solo_equalise():
    def __init__(self):
        roadm3=Lumentum('10.10.10.33') # roadm3
        #roadm4=Lumentum('10.10.10.32') # roadm4
        #roadm5=Lumentum('10.10.10.31') # roadm4
        #roadm7=Lumentum('10.10.10.29') # roadm7
        
        internal_roadm_loss=4 # dbm
    
        power=roadm3.get_demux_connection_input_power()      
        flatten_value = get_flatten_value(power)
        power2=flatten_setpoint(power,-6 + internal_roadm_loss)
        roadm3.set_demux_atten(power2)
        
        
class just_equalise():
    def __init__(self):
        roadm3=Lumentum('10.10.10.33') # roadm3
        roadm4=Lumentum('10.10.10.32') # roadm4
        roadm5=Lumentum('10.10.10.31') # roadm4
        roadm7=Lumentum('10.10.10.29') # roadm7
        
        internal_roadm_loss=4 # dbm
        
        # Follow the light !!!
        power=roadm3.get_mux_connection_input_power()      
        flatten_value = get_flatten_value(power)
        power2=flatten_setpoint(power,-13.1 + internal_roadm_loss)
        roadm3.set_mux_atten(power2)
        
        time.sleep(5)
        
        power=roadm7.get_demux_connection_input_power()      
        flatten_value = get_flatten_value(power)
        power2=flatten_setpoint(power,-10 + internal_roadm_loss)
        roadm7.set_demux_atten(power2)
        
        time.sleep(5)
 
        power=roadm5.get_mux_connection_input_power()      
        flatten_value = get_flatten_value(power)
        power2=flatten_setpoint(power,-21 + internal_roadm_loss)
        roadm5.set_mux_atten(power2)
        
        time.sleep(5)
        
        power=roadm4.get_demux_connection_input_power()      
        flatten_value = get_flatten_value(power)
        power2=flatten_setpoint(power,-10 + internal_roadm_loss)
        roadm4.set_demux_atten(power2)
        
        time.sleep(5)
        
        power=roadm4.get_mux_connection_input_power()      
        flatten_value = get_flatten_value(power)
        power2=flatten_setpoint(power,-21 + internal_roadm_loss)
        roadm4.set_mux_atten(power2)

        time.sleep(5)

        power=roadm5.get_demux_connection_input_power()      
        flatten_value = get_flatten_value(power)
        power2=flatten_setpoint(power,-10 + internal_roadm_loss)
        roadm5.set_demux_atten(power2)
        
        time.sleep(5)
        
        power=roadm7.get_mux_connection_input_power()      
        flatten_value = get_flatten_value(power)
        power2=flatten_setpoint(power,-21 + internal_roadm_loss)
        roadm7.set_mux_atten(power2)
        
        time.sleep(5)
        
        power=roadm3.get_demux_connection_input_power()      
        flatten_value = get_flatten_value(power)
        power2=flatten_setpoint(power,-6 + internal_roadm_loss)
        roadm3.set_demux_atten(power2)
        
        time.sleep(5)

class roadm_network:
    def __init__(self):
        self.settle_time=5
        self.channel_list=list(range(1,96))
        roadm_ip_list=['10.10.10.29', '10.10.10.31'] # roadm3, roadm4, roadm7
        self.roadm_list=[]
        for roadm_ip in roadm_ip_list:
            roadm=Lumentum(roadm_ip)
            roadm.make_grid(open_channels=self.channel_list)
            roadm.set_mux_online()
            roadm.set_demux_online()
            self.roadm_list.append(roadm)
        
    def equalise(self):
        for roadm in self.roadm_list:
            power=roadm.get_demux_connection_input_power()
            flatten_value = get_flatten_value(power)
            power2=flatten(power)
            roadm.set_demux_atten(power2)

class comb_source:
    def __init__(self):
        self.roadm1=Lumentum('10.10.10.38')
        self.roadm2=Lumentum('10.10.10.37')
        self.channel_list=list(range(1,96))
        self.settle_time=5
        
        self.roadm1.make_grid(open_channels=self.channel_list)
        self.roadm2.make_grid(open_channels=self.channel_list)
        time.sleep(self.settle_time)
        power=self.roadm1.get_demux_connection_input_power()
        self.flatten_value = get_flatten_value(power)
        power2=flatten(power)
        self.roadm1.set_demux_atten(power2)
        power2=level_atten(self.channel_list) # set to zero attenuation
        self.roadm2.set_mux_atten(power2)
        self.roadm1.set_mux_online()
        self.roadm1.set_demux_online()
        self.roadm2.set_mux_online()
        self.roadm2.set_demux_online()
        
    def randomise(self, channels_to_remove, channel_number):
        channel_sample=random.sample(self.channel_list,channel_number)
        channel_sample=[e for  e in channel_sample if e not in channels_to_remove]
        channel_sample.sort()
        self.roadm2.make_grid(open_channels=channel_sample)
        time.sleep(self.settle_time)
        power2=level_atten(self.channel_list) # set to zero attenuation
        self.roadm2.set_mux_atten(power2)
        output_power = self.roadm2.get_mux_connection_output_power()
        p = []
        for tuple in output_power:
            if tuple[0] in channel_sample:
                p.append(tuple[1])
        if len(p) == 0:
            self.flatten_value_dbm = 0
            self.flatten_value_watt = 0
        else:
            self.flatten_value_dbm = sum(p) / len(p)
            self.flatten_value_watt = convert_dbm_to_watt(self.flatten_value_dbm)
        self.roadm1.disable_als(1, duration=600)
        self.roadm2.disable_als(1, duration=600)
        return channel_sample
    
    def debug(self):
        print("Roadm1 Demux target power: ", self.roadm1.get_demux_target_power())
        print("Roadm2 Mux target gain: ", self.roadm2.get_mux_target_gain())
    
    
    
        
        
