from tcdona2.lumentum2 import *

roadm_ip_list=['10.10.10.33'] # roadm3, roadm4


roadm1 = Lumentum('10.10.10.38')
roadm2 = Lumentum('10.10.10.37')

r1_conn = roadm1.wss_get_connections()
r2_conn = roadm2.wss_get_connections()

chnum=86


for i in range(1,chnum): 
     print(i,  "\t", r1_conn['mux']['conn-%d' % i]['blocked'], r2_conn['mux']['conn-%d' % i]['blocked'], "\t",
          "%7.1f %7.1f %7.1f %7.1f"%(
          r1_conn['demux']['conn-%d' % i]['input-power'],
          r1_conn['demux']['conn-%d' % i]['output-power'],
          r2_conn['mux']['conn-%d' % i]['input-power'],
          r2_conn['mux']['conn-%d' % i]['output-power']
          ))
     
print()

for i in range(1,chnum): 
     print(i,  "\t", r1_conn['mux']['conn-%d' % i]['blocked'], r2_conn['mux']['conn-%d' % i]['blocked'], "\t",
          "%7.1f %7.1f %7.1f %7.1f"%(
          r1_conn['demux']['conn-%d' % i]['attenuation'],
          r1_conn['demux']['conn-%d' % i]['attenuation'],
          r2_conn['mux']['conn-%d' % i]['attenuation'],
          r2_conn['mux']['conn-%d' % i]['attenuation'])
          )
     
print(roadm1.edfa_get_info())
print(roadm2.edfa_get_info())
