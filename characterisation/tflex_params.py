from ncclient import manager
from ncclient.xml_ import *
import xmltodict
import logging
import time


class tflex:
    def __init__(self, ip_address):
        self.conn = manager.connect(host=ip_address,
                           port=830,
                           username="admin",
                           password="CHGME.1a",
                           timeout=60,
                           hostkey_verify=False)
        self.conn.raise_mode = 0  # on RPCError, do not throw any exceptions
        self._config = {}
        self._get_config()

    def read_pm_data(self,sleep_counter, line_port, DEBUG=False):
        offline = True
        stable = False
        localtime = time.localtime()
        result = time.strftime("%I:%M:%S %p", localtime)
        time.sleep(sleep_counter)
        localtime = time.localtime()
        result = time.strftime("%I:%M:%S %p", localtime)
        while offline:
            response = self.get_operational_state(line_port)
            response_details = xmltodict.parse(response.xml)
            status = response_details['rpc-reply']['data']['components']['component']['state']['oper-status']
            if DEBUG:
                print(status)
            offline = None if status == 'ACTIVE' else True
            time.sleep(5)
    
        while not stable:
            pm_data = self.get_params(line_port=line_port)
            if pm_data['QualityTF_indefinite_q-factor']:
                Q_factor = float(pm_data['QualityTF_indefinite_q-factor'])
                time.sleep(5)
                pm_data_verification = self.get_params(line_port=line_port)
                stable = abs(Q_factor - float(pm_data_verification['QualityTF_indefinite_q-factor'])) < 0.05
                if DEBUG:
                    print(Q_factor, float(pm_data_verification['QualityTF_indefinite_q-factor']))
            else:
                time.sleep(15)
        pm_data = self.get_params(line_port=line_port)
        if DEBUG:
            print(pm_data['QualityTF_indefinite_q-factor'])
        return pm_data

    def change_configuration(self, line_port, logical_interface, modulation, target_power, central_frequency,
                             fec='sdfec-acacia15-7iterations', rolloff=0.19):
        sleep_counter = 30
        if self._config[line_port]['admin_state'] != "acor-stt:is":
            self.set_interface_on(line_port)
        if self._config[line_port]['logical_interface'] != logical_interface:
            if self._config[line_port]['logical_interface']:
                self.delete_logical_interface(line_port)
            self.create_logical_interface(line_port, logical_interface)
            sleep_counter = 150
        if self._config[line_port]['modulation'] != modulation:
            self.set_admin_maintenance(line_port + '/' + logical_interface)
            self.set_interface_modulation(line_port, modulation)
            self.remove_admin_maintenance(line_port + '/' + logical_interface)
            sleep_counter = 150
        if self._config[line_port]['fec'] != fec:
            self.set_fec_algorithm(line_port, fec)
        if self._config[line_port]['filter-roll-off'] != rolloff and logical_interface != 'ot100':
            self.set_filterrolloff(line_port, rolloff)
        self.set_power_and_frequency(line_port=line_port, power=target_power, frequency=central_frequency)
        return sleep_counter


    def return_current_config(self):
        self._get_config()
        return self._config

    def _get_config(self):
        response = self.get_interface()
        response_details = xmltodict.parse(response.xml)     
        config = response_details['rpc-reply']['data']['terminal-device']['logical-channels']['channel']

        # get line_ports and logical interfaces
        for config_details in config:
            if 'odu4' not in config_details['config']['description']:
                line_port = config_details['config']['description'].split('/ot')[0]
                self._config[line_port] = {}
                self._config[line_port]['line_port'] = line_port
                self._config[line_port]['logical_interface'] = config_details['config']['description'].split(line_port +
                                                                                                             '/')[1]
                self._config[line_port]['index'] = config_details['config']['index']
        for line_port in self._config.keys():
            # get admin state
            response = self.get_port_admin_state(line_port)
            response_details = xmltodict.parse(response.xml)
            self._config[line_port]['admin_state'] = response_details['rpc-reply']['data']['managed-element']['interface']['physical-interface']['state']['admin-state']

            # get modulation
            response = self.get_interface_modulation(line_port)
            response_details = xmltodict.parse(response.xml)
            self._config[line_port]['modulation'] = response_details['rpc-reply']['data']['managed-element']['interface']['logical-interface']['otsia']['otsi']['optical-channel-configuration']['modulation']

            # get rolloff
            response = self.get_filterrolloff(line_port)
            response_details = xmltodict.parse(response.xml)
            try:
                self._config[line_port]['filter-roll-off'] = \
                    response_details['rpc-reply']['data']['managed-element']['interface']['logical-interface']['otsia']['otsi']['optical-channel-configuration']['filter-roll-off']
            except:
                self._config[line_port]['filter-roll-off'] = '0'

            # read power and frequency
            response = self.get_power_and_frequency(line_port)
            response_details = xmltodict.parse(response.xml)
            for component_details in response_details['rpc-reply']['data']['components']['component']:
                if 'config' in component_details.keys():
                    assert component_details['config']['name'] == 'optch ' + line_port
                    try:
                        self._config[line_port]['frequency'] = component_details['optical-channel']['config']['frequency']
                        self._config[line_port]['target-output-power'] = component_details['optical-channel']['config']['target-output-power']
                    except:
                        self._config[line_port]['frequency'] = '0'
                        self._config[line_port]['target-output-power'] = '0'

            #read fec
            response = self.get_fec_algorithm(line_port)
            response_details = xmltodict.parse(response.xml)
            for component_details in response_details['rpc-reply']['data']['components']['component']:
                if 'config' in component_details.keys():
                    assert component_details['config']['name'] == 'optch ' + line_port
                    try:
                        self._config[line_port]['fec'] = component_details['optical-channel']['config']['optical-channel-config']['fec']
                    except:
                        self._config[line_port]['fec'] = '0'

            # read symbolrate
            response = self.get_symbolrate(line_port)
            response_details = xmltodict.parse(response.xml)

            for component_details in response_details['rpc-reply']['data']['components']['component']:
                if 'config' in component_details.keys():
                    assert component_details['config']['name'] == 'optch ' + line_port
                    try:
                        self._config[line_port]['symbolrate'] = component_details['optical-channel']['state']['optical-channel-config']['symbol-rate']
                    except:
                        self._config[line_port]['symbolrate'] = '0'

    def get_operational_state(self, line_port):
        request = f'''
                <components xmlns="http://openconfig.net/yang/platform">
                <component>
                <name>port {line_port}</name>
                <state>
                <oper-status/>
                </state>
                </component>
                </components>
                '''
        flt = ("subtree", request)
        return self.conn.get(filter=flt)

    def get_interface(self):
        request = '''
        <terminal-device xmlns="http://openconfig.net/yang/terminal-device">
        <logical-channels>
        <channel>
        <config>
        <index/>
        <description/>
        </config>
        </channel>
        </logical-channels>
        </terminal-device>
        '''

        flt = ("subtree", request)

        return self.conn.get_config(source="running", filter=flt)

    def delete_logical_interface(self, line_port):
        request = f'''
                <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
                <terminal-device xmlns="http://openconfig.net/yang/terminal-device">
                    <logical-channels>
                        <channel nc:operation="delete">
                            <config>
                                <index>{self._config[line_port]['index']}</index>
                                <description>{line_port}</description>
                            </config>
                        </channel>
                    </logical-channels>
                </terminal-device>
                </nc:config>
                '''
        response = self.conn.edit_config(target="running", config=request)
        assert 'ok' in xmltodict.parse(response.xml)['rpc-reply'].keys(), print(response)
        self._config[line_port]['logical_interface'] = None
        return response

    def create_logical_interface(self, line_port, logical_interface):
        request = f'''
                     <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
                          <managed-element xmlns="http://www.advaoptical.com/aos/netconf/aos-core-managed-element">
                              <entity-name>1</entity-name>
                              <interface xmlns="http://www.advaoptical.com/aos/netconf/aos-core-facility">
                              <name>{self._config[line_port]['line_port'] + '/' + logical_interface}</name>
                                  <logical-interface/>
                              </interface>
                          </managed-element>
                     </nc:config>
                     '''
        response = self.conn.edit_config(target="running", config=request)
        assert 'ok' in xmltodict.parse(response.xml)['rpc-reply'].keys(), print(response)
        self._config[line_port]['logical_interface'] = logical_interface
        self._config[line_port]['modulation'] = self.get_interface_modulation(line_port)
        return response

    def get_interface_modulation(self, line_port):
        request = f'''<managed-element xmlns="http://www.advaoptical.com/aos/netconf/aos-core-managed-element"
                               xmlns:f8-ne="http://www.advaoptical.com/aos/netconf/adva-f8-ne"
                               xmlns:acor-me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element">
                                <entity-name>1</entity-name>
                                  <interface xmlns="http://www.advaoptical.com/aos/netconf/aos-core-facility">
                                    <name>{self._config[line_port]['line_port'] + '/' + self._config[line_port]['logical_interface']}</name>
                                    <logical-interface>
                                      <entity-name>{self._config[line_port]['logical_interface']}</entity-name>
                                      <otsia xmlns="http://www.advaoptical.com/aos/netconf/aos-domain-otn">
                                        <otsi>
                                          <id>1</id>
                                          <optical-channel-configuration>
                                            <modulation/>
                                          </optical-channel-configuration>
                                        </otsi>
                                      </otsia>
                                    </logical-interface>
                                  </interface>
                                </managed-element>
                                '''
        flt = ("subtree", request)
        return self.conn.get_config(source="running", filter=flt)

    def set_interface_modulation(self, line_port, modulation):
        request = f'''
                    <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
                        <managed-element xmlns="http://www.advaoptical.com/aos/netconf/aos-core-managed-element"
                               xmlns:f8-ne="http://www.advaoptical.com/aos/netconf/adva-f8-ne"
                               xmlns:acor-me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element">
                                <entity-name>1</entity-name>
                                  <interface xmlns="http://www.advaoptical.com/aos/netconf/aos-core-facility">
                                    <name>{self._config[line_port]['line_port'] + '/' + self._config[line_port]['logical_interface']}</name>
                                    <logical-interface>
                                      <entity-name>{self._config[line_port]['logical_interface']}</entity-name>
                                      <otsia xmlns="http://www.advaoptical.com/aos/netconf/aos-domain-otn">
                                        <otsi>
                                          <id>1</id>
                                          <optical-channel-configuration>
                                            <modulation>{modulation}</modulation>
                                            <state-of-polarization-tracking>normal-tracking</state-of-polarization-tracking>
                                          </optical-channel-configuration>
                                        </otsi>
                                      </otsia>
                                    </logical-interface>
                                  </interface>
                                </managed-element>
                              </nc:config>
                                '''
        response = self.conn.edit_config(target="running", config=request)
        assert 'ok' in xmltodict.parse(response.xml)['rpc-reply'].keys(), print(response)
        self._config[line_port]['modulation'] = modulation
        return response

    def get_power_and_frequency(self, line_port):
        request = f'''
        <oc-platform:components xmlns:oc-platform="http://openconfig.net/yang/platform">
        <oc-platform:component>
        <oc-platform:config>
        <oc-platform:name>optch {line_port}</oc-platform:name>
        </oc-platform:config>
        <oc-opt-term:optical-channel xmlns:oc-opt-term="http://openconfig.net/yang/terminal-device">
        <oc-opt-term:config>
        <oc-opt-term:frequency/>
        <oc-opt-term:target-output-power/>
        </oc-opt-term:config>
        </oc-opt-term:optical-channel>
        </oc-platform:component>
        </oc-platform:components>
        '''
        flt = ("subtree", request)

        return self.conn.get_config(source="running", filter=flt)

    def set_power_and_frequency(self, line_port, power, frequency):
        request = f'''
        <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <oc-platform:components xmlns:oc-platform="http://openconfig.net/yang/platform">
        <oc-platform:component>
        <oc-platform:config>
        <oc-platform:name>optch {line_port}</oc-platform:name>
        </oc-platform:config>
        <oc-opt-term:optical-channel xmlns:oc-opt-term="http://openconfig.net/yang/terminal-device">
        <oc-opt-term:config>
        <oc-opt-term:frequency>{frequency}</oc-opt-term:frequency>
        <oc-opt-term:target-output-power>{power:.1f}</oc-opt-term:target-output-power>
        </oc-opt-term:config>
        </oc-opt-term:optical-channel>
        </oc-platform:component>
        </oc-platform:components>
        </nc:config>
        '''
        response = self.conn.edit_config(target="running", config=request)
        assert 'ok' in xmltodict.parse(response.xml)['rpc-reply'].keys(), print(response)
        self._config[line_port]['frequency'] = frequency
        self._config[line_port]['target-output-power'] = power
        return response

    def set_interface_on(self, line_port):
        return self.set_interface_state(1, line_port)
    
    def set_interface_off(self, line_port):
        return self.set_interface_state(0, line_port)

    def set_interface_state(self, state, line_port):
        if state == 0:
            adva_state = "acor-stt:oos"
        else:
            adva_state = "acor-stt:is"
            
        request = f'''
        <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <managed-element xmlns="http://www.advaoptical.com/aos/netconf/aos-core-managed-element">
        <entity-name>1</entity-name>
        <interface xmlns="http://www.advaoptical.com/aos/netconf/aos-core-facility">   
        <name>{self._config[line_port]['line_port'] + '/' + self._config[line_port]['logical_interface']}</name>
        <physical-interface>
        <state xmlns:acor-stt="http://www.advaoptical.com/aos/netconf/aos-core-state-types">
        <admin-state>{adva_state}</admin-state>
        </state>
        </physical-interface>
        </interface>
        </managed-element>
        </nc:config>
        '''
        response = self.conn.edit_config(target="running", config=request)
        assert 'ok' in xmltodict.parse(response.xml)['rpc-reply'].keys(), print(response)
        return response
    
    def get_interface_state(self, line_port):
        request = f'''
        <managed-element xmlns="http://www.advaoptical.com/aos/netconf/aos-core-managed-element">
        <entity-name>1</entity-name>
        <interface xmlns="http://www.advaoptical.com/aos/netconf/aos-core-facility">   
        <name>{line_port}</name>
        <physical-interface>
        <state xmlns:acor-stt="http://www.advaoptical.com/aos/netconf/aos-core-state-types">
        </state>
        </physical-interface>
        </interface>
        </managed-element>
        '''

        flt=("subtree", request)
        return self.conn.get_config(source="running", filter=flt)


    def set_admin_maintenance(self, element):
        """

        :param element: line_port or logical interface e.g. 1/2/n1 or 1/2/n1/ot200
        :return:
        """
        request = f'''
     <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
     <managed-element xmlns="http://www.advaoptical.com/aos/netconf/aos-core-managed-element"
                   xmlns:f8-ne="http://www.advaoptical.com/aos/netconf/adva-f8-ne"
                   xmlns:acor-me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element">
        <entity-name>1</entity-name>
        <interface xmlns="http://www.advaoptical.com/aos/netconf/aos-core-facility">
          <name>{element}</name>
          <physical-interface xmlns:acor-factt="http://www.advaoptical.com/aos/netconf/aos-core-facility-types">
            <state xmlns:acor-stt="http://www.advaoptical.com/aos/netconf/aos-core-state-types">
              <admin-is-sub-states>acor-stt:mt</admin-is-sub-states>
            </state>
          </physical-interface>
        </interface>
      </managed-element>
      </nc:config>
        '''
        
        return self.conn.edit_config(target="running", config=request)  

    def remove_admin_maintenance(self, element):
        """

        :param element: line_port or logical interface e.g. 1/2/n1 or 1/2/n1/ot200
        :return:
        """
        request = f'''
        <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <managed-element xmlns="http://www.advaoptical.com/aos/netconf/aos-core-managed-element"
                       xmlns:f8-ne="http://www.advaoptical.com/aos/netconf/adva-f8-ne"
                       xmlns:acor-me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element">
            <entity-name>1</entity-name>
            <interface xmlns="http://www.advaoptical.com/aos/netconf/aos-core-facility">
              <name>{element}</name>
              <physical-interface xmlns:acor-factt="http://www.advaoptical.com/aos/netconf/aos-core-facility-types">
                <state xmlns:acor-stt="http://www.advaoptical.com/aos/netconf/aos-core-state-types">
                  <admin-is-sub-states nc:operation="delete">acor-stt:mt</admin-is-sub-states>
                </state>
              </physical-interface>
            </interface>
          </managed-element>
           </nc:config>
        '''
        
        return self.conn.edit_config(target="running", config=request)
    
    def get_port_admin_state(self, line_port):
        request = f'''
      <managed-element xmlns="http://www.advaoptical.com/aos/netconf/aos-core-managed-element">
            <entity-name>1</entity-name>
            <interface xmlns="http://www.advaoptical.com/aos/netconf/aos-core-facility">
                <name>{line_port}</name>
                <physical-interface>
                    <state xmlns:acor-stt="http://www.advaoptical.com/aos/netconf/aos-core-state-types">
                        <admin-state/>
                    </state>
                </physical-interface>
            </interface>
        </managed-element>
        '''

        flt=("subtree", request)
        return self.conn.get_config(source="running", filter=flt)


    def get_params(self, line_port, DEBUG=False):
        perf_dict = {}
    
        request_pm_data = f'''
        <get-pm-data xmlns="http://www.advaoptical.com/aos/netconf/aos-core-pm"
                     xmlns:fac="http://www.advaoptical.com/aos/netconf/aos-core-facility"
                     xmlns:me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element"
                     xmlns:otn="http://www.advaoptical.com/aos/netconf/aos-domain-otn">
          <target-entity>/me:managed-element[me:entity-name="1"]/fac:interface[fac:name="{self._config[line_port]['line_port'] + '/' + self._config[line_port]['logical_interface']}"]/fac:logical-interface/otn:otsia/otn:otsi[id="1"]</target-entity>
          <pm-data>
            <pm-current-data/>
          </pm-data>
        </get-pm-data>
        '''
    
        reply_pm_data = self.conn.dispatch(to_ele(request_pm_data))
        perf_details = xmltodict.parse(reply_pm_data.xml)
        
        perf_categories = perf_details['rpc-reply']['pm-data']['pm-current-data']
    
        for perf_cat in perf_categories:
            name=perf_cat['name']
            interval=perf_cat['bin-interval'].split("-")[2]
            montypemonval=perf_cat['montype-monval']
            if isinstance(montypemonval, list):
                for mtmv in montypemonval:
                    mt=mtmv['mon-type'].split(":")[1]
                    mv=mtmv['mon-val']
                    perf_dict["_".join([name,interval,mt])] = mv
                    # print(name,interval,mt,mv)
            else:
                mt=montypemonval['mon-type'].split(":")[1]
                mv=montypemonval['mon-val']
                perf_dict["_".join([name,interval,mt])] = mv
                #print(name,interval,mt)

        logical_interface = self._config[line_port]['logical_interface']
        
        if logical_interface == "ot200":
            otu_type = 'otu-c2pa'
        elif logical_interface == "ot300":
            otu_type = 'otu-c3pa'
        elif logical_interface == "ot400":
            otu_type = 'otu-c4pa'
        elif logical_interface == "ot500":
            otu_type = 'otu-c5pa'
        elif logical_interface == "ot600":
            otu_type = 'otu-c6pa'

        #otu_type = 'otu-c2pa'
        response = self.get_otu_type(line_port)
        response_details = xmltodict.parse(response.xml)

        if 'otu4' in response_details['rpc-reply']['data']['managed-element']['interface']['logical-interface'].keys():
            otu_type = 'otu4'

        request_fec_ber = f'''
        <get-pm-data xmlns="http://www.advaoptical.com/aos/netconf/aos-core-pm"
                     xmlns:me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element"
                     xmlns:fac="http://www.advaoptical.com/aos/netconf/aos-core-facility"
                     xmlns:adom-oduckpa="http://www.advaoptical.com/aos/netconf/aos-domain-otn-oduckpa"
                     xmlns:otn="http://www.advaoptical.com/aos/netconf/aos-domain-otn">
          <target-entity>/me:managed-element[me:entity-name="1"]/fac:interface[fac:name="{self._config[line_port]['line_port'] + '/' + self._config[line_port]['logical_interface']}"]/fac:logical-interface/adom-oduckpa:{otu_type}</target-entity>
          <pm-data>
            <pm-current-data/>
          </pm-data>
        </get-pm-data>
        '''
        reply_fec_ber = self.conn.dispatch(to_ele(request_fec_ber))
    
        perf_details = xmltodict.parse(reply_fec_ber.xml)
        if 'pm-data' in perf_details['rpc-reply'].keys():
            perf_categories=perf_details['rpc-reply']['pm-data']['pm-current-data']
            for perf_cat in perf_categories:
                name = perf_cat['name']
                interval = perf_cat['bin-interval'].split("-")[2]
                montypemonval = perf_cat['montype-monval']
                if isinstance(montypemonval, list):
                    for mtmv in montypemonval:
                        mt = mtmv['mon-type'].split(":")[1]
                        mv = mtmv['mon-val']
                        perf_dict[":".join([name, interval, mt])] = mv
                else:
                    mt=montypemonval['mon-type'].split(":")[1]
                    mv=montypemonval['mon-val']
                    perf_dict[":".join([name, interval, mt])] = mv
        else:
            if DEBUG:
                print('No BER reading available!')
        return perf_dict
    
    
    def reset_fec(self, line_port):
        logical_interface = self._config[line_port]['logical_interface']
        
        if logical_interface == "ot200":
            otu_type = 'otu-c2pa'
        elif logical_interface == "ot300":
            otu_type = 'otu-c3pa'
        elif logical_interface == "ot400":
            otu_type = 'otu-c4pa'
        elif logical_interface == "ot500":
            otu_type = 'otu-c5pa'
        elif logical_interface == "ot600":
            otu_type = 'otu-c6pa'

        #otu_type = 'otu-c2pa'
        response = self.get_otu_type(line_port)
        response_details = xmltodict.parse(response.xml)
        if 'otu4' in response_details['rpc-reply']['data']['managed-element']['interface']['logical-interface'].keys():
            otu_type = 'otu4'

        for interval in ["acor-pmt:interval-indefinite","acor-pmt:interval-15min"]:
            if otu_type == 'otu4':
                reset_stats = f'''
                    <acor-pm:reset-pm-stats xmlns:acor-pm="http://www.advaoptical.com/aos/netconf/aos-core-pm">
                    <acor-pm:target-entity xmlns:acor-fac="http://www.advaoptical.com/aos/netconf/aos-core-facility" xmlns:acor-me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element" xmlns:adom-oduckpa="http://www.advaoptical.com/aos/netconf/aos-domain-otn-oduckpa">/acor-me:managed-element[acor-me:entity-name="1"]/acor-fac:interface[acor-fac:name="{self._config[line_port]['line_port'] + '/' + self._config[line_port]['logical_interface']}"]/acor-fac:logical-interface/otn:otu4/otn:pm-monitored-entity</acor-pm:target-entity> 
                    <acor-pm:profile-name>FEC</acor-pm:profile-name> 
                    <acor-pm:bin-interval xmlns:acor-pmt="http://www.advaoptical.com/aos/netconf/aos-core-pm-types">{interval}</acor-pm:bin-interval>
                    </acor-pm:reset-pm-stats>
                    '''
            else:
                reset_stats = f'''
                    <acor-pm:reset-pm-stats xmlns:acor-pm="http://www.advaoptical.com/aos/netconf/aos-core-pm">
                    <acor-pm:target-entity xmlns:acor-fac="http://www.advaoptical.com/aos/netconf/aos-core-facility" xmlns:acor-me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element" xmlns:adom-oduckpa="http://www.advaoptical.com/aos/netconf/aos-domain-otn-oduckpa">/acor-me:managed-element[acor-me:entity-name="1"]/acor-fac:interface[acor-fac:name="{self._config[line_port]['line_port'] + '/' + self._config[line_port]['logical_interface']}"]/acor-fac:logical-interface/adom-oduckpa:{otu_type}/adom-oduckpa:pm-monitored-entity</acor-pm:target-entity> 
                    <acor-pm:profile-name>FEC</acor-pm:profile-name> 
                    <acor-pm:bin-interval xmlns:acor-pmt="http://www.advaoptical.com/aos/netconf/aos-core-pm-types">{interval}</acor-pm:bin-interval>
                    </acor-pm:reset-pm-stats>
                    '''
            #print(reset_stats)
            reset_stats_resp = self.conn.dispatch(to_ele(reset_stats))
            #print(reset_stats_resp)
            
    def reset_pm_counters(self, line_port):
        logical_interface = self._config[line_port]['logical_interface']
        
        if logical_interface == "ot200":
            otu_type = 'otu-c2pa'
        elif logical_interface == "ot300":
            otu_type = 'otu-c3pa'
        elif logical_interface == "ot400":
            otu_type = 'otu-c4pa'
        elif logical_interface == "ot500":
            otu_type = 'otu-c5pa'
        elif logical_interface == "ot600":
            otu_type = 'otu-c6pa'

        #otu_type = 'otu-c2pa'
        response = self.get_otu_type(line_port)
        response_details = xmltodict.parse(response.xml)
        if 'otu4' in response_details['rpc-reply']['data']['managed-element']['interface']['logical-interface'].keys():
            otu_type = 'otu4'
        
        imp_tf_ranges = [
            "ImpTF16QCdcRange1", "ImpTF16QCdcRange2", "ImpTF16QCdcRange3", "ImpTF16QCdcRange4",
            "ImpTF32QCdcRange1", "ImpTF32QCdcRange2", "ImpTF32QCdcRange3", "ImpTF32QCdcRange4",
            "ImpTF64QCdcRange1", "ImpTF64QCdcRange2", "ImpTF64QCdcRange3", "ImpTF64QCdcRange4",
            "ImpTFP16QCdcRange1", "ImpTFP16QCdcRange2", "ImpTFP16QCdcRange3", "ImpTFP16QCdcRange4",
            "ImpTFQpskCdcRange1", "ImpTFQpskCdcRange2", "ImpTFQpskCdcRange3", "ImpTFQpskCdcRange4"
        ]
        imp_tf_ranges = ['ImpTF200gQpskNorm', 'ImpTFQpskCdcRange2']
        for profile in imp_tf_ranges:
            for interval in ["acor-pmt:interval-indefinite","acor-pmt:interval-15min"]:
                reset_stats = f'''
                    <acor-pm:reset-pm-stats xmlns:acor-pm="http://www.advaoptical.com/aos/netconf/aos-core-pm">
                    <acor-pm:target-entity xmlns:acor-fac="http://www.advaoptical.com/aos/netconf/aos-core-facility" 
                    xmlns:acor-me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element" 
                    xmlns:adom-otn="http://www.advaoptical.com/aos/netconf/aos-domain-otn">/acor-me:managed-element[acor-me:entity-name="1"]/acor-fac:interface[acor-fac:name="{self._config[line_port]['line_port'] + '/' + self._config[line_port]['logical_interface']}"]/acor-fac:logical-interface/adom-otn:otsia/adom-otn:otsi[adom-otn:id="1"]/adom-otn:pm-monitored-entity</acor-pm:target-entity>
                    <acor-pm:profile-name>ImpTF16QCdcRange2</acor-pm:profile-name>
                    <acor-pm:bin-interval xmlns:acor-pmt="http://www.advaoptical.com/aos/netconf/aos-core-pm-types">acor-pmt:interval-indefinite</acor-pm:bin-interval>
                    <acor-pm:profile-name>{profile}</acor-pm:profile-name>
                    <acor-pm:bin-interval xmlns:acor-pmt="http://www.advaoptical.com/aos/netconf/aos-core-pm-types">{interval}</acor-pm:bin-interval>
                    </acor-pm:reset-pm-stats>
                    '''
                print(reset_stats)
                reset_stats_resp = self.conn.dispatch(to_ele(reset_stats))
                print(reset_stats_resp)
        

    def get_otu_type(self, line_port):
        request = f'''
                <managed-element xmlns:acor-me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element">
                    <interface xmlns="http://www.advaoptical.com/aos/netconf/aos-core-facility">
                    <name>{self._config[line_port]['line_port'] + '/' + self._config[line_port]['logical_interface']}</name>
                    <logical-interface/>
                    </interface>
                </managed-element>
                        '''
        flt = ("subtree", request)
        return self.conn.get_config(source="running", filter=flt)

    def get_symbolrate(self, line_port):
        request = f'''<components xmlns="http://openconfig.net/yang/platform">
                        <component>
                        <config>
                          <name>optch {line_port}</name>
                        </config>
                        <optical-channel xmlns="http://openconfig.net/yang/terminal-device">
                          <state>
                            <optical-channel-config xmlns="http://www.advaoptical.com/openconfig/terminal-device-dev">
                              <symbol-rate/>
                            </optical-channel-config>
                          </state>
                        </optical-channel>
                      </component>
                      </components>
                   '''
        flt = ("subtree", request)
        return self.conn.get(filter=flt)

    def set_filterrolloff(self, line_port, rolloff):
        request = f'''
                            <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
                                <managed-element xmlns="http://www.advaoptical.com/aos/netconf/aos-core-managed-element"
                                       xmlns:f8-ne="http://www.advaoptical.com/aos/netconf/adva-f8-ne"
                                       xmlns:acor-me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element">
                                        <entity-name>1</entity-name>
                                          <interface xmlns="http://www.advaoptical.com/aos/netconf/aos-core-facility">
                                            <name>{self._config[line_port]['line_port'] + '/' + self._config[line_port]['logical_interface']}</name>
                                            <logical-interface>
                                              <entity-name>{self._config[line_port]['logical_interface']}</entity-name>
                                              <otsia xmlns="http://www.advaoptical.com/aos/netconf/aos-domain-otn">
                                                <otsi>
                                                  <id>1</id>
                                                  <optical-channel-configuration>
                                                    <filter-roll-off>{rolloff:.2f}</filter-roll-off>
                                                    <state-of-polarization-tracking>normal-tracking</state-of-polarization-tracking>
                                                  </optical-channel-configuration>
                                                </otsi>
                                              </otsia>
                                            </logical-interface>
                                          </interface>
                                        </managed-element>
                                      </nc:config>
                                        '''
        response = self.conn.edit_config(target="running", config=request)
        assert 'ok' in xmltodict.parse(response.xml)['rpc-reply'].keys(), print(response)
        self._config[line_port]['filter-roll-off'] = rolloff
        return response

    def get_filterrolloff(self, line_port):
        request = f'''<managed-element xmlns="http://www.advaoptical.com/aos/netconf/aos-core-managed-element"
                               xmlns:f8-ne="http://www.advaoptical.com/aos/netconf/adva-f8-ne"
                               xmlns:acor-me="http://www.advaoptical.com/aos/netconf/aos-core-managed-element">
                                <entity-name>1</entity-name>
                                  <interface xmlns="http://www.advaoptical.com/aos/netconf/aos-core-facility">
                                    <name>{self._config[line_port]['line_port'] + '/' + self._config[line_port]['logical_interface']}</name>
                                    <logical-interface>
                                      <entity-name>{self._config[line_port]['logical_interface']}</entity-name>
                                      <otsia xmlns="http://www.advaoptical.com/aos/netconf/aos-domain-otn">
                                        <otsi>
                                          <id>1</id>
                                          <optical-channel-configuration>
                                            <filter-roll-off/>
                                          </optical-channel-configuration>
                                        </otsi>
                                      </otsia>
                                    </logical-interface>
                                  </interface>
                                </managed-element>
                                '''
        flt = ("subtree", request)
        return self.conn.get_config(source="running", filter=flt)


    def get_fec_algorithm(self, line_port):
        request = f'''<components xmlns="http://openconfig.net/yang/platform">
                      <component>
                        <config>
                          <name>optch {line_port}</name>
                        </config>
                        <optical-channel xmlns="http://openconfig.net/yang/terminal-device">
                          <config>
                            <optical-channel-config xmlns="http://www.advaoptical.com/openconfig/terminal-device-dev">
                              <fec/>
                            </optical-channel-config>
                          </config>
                        </optical-channel>
                      </component>
                    </components>
                    '''
        flt=("subtree", request)
        return self.conn.get_config(source="running", filter=flt)
    


    def set_fec_algorithm(self, line_port, fec):
        request = f'''<nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <components xmlns="http://openconfig.net/yang/platform">
                      <component>
                        <config>
                          <name>optch {line_port}</name>
                        </config>
                        <optical-channel xmlns="http://openconfig.net/yang/terminal-device">
                          <config>
                            <optical-channel-config xmlns="http://www.advaoptical.com/openconfig/terminal-device-dev">
                              <fec>{fec}</fec>
                            </optical-channel-config>
                          </config>
                        </optical-channel>
                      </component>
                    </components>
                    </nc:config>
                    '''
        response = self.conn.edit_config(target="running", config=request)
        assert 'ok' in xmltodict.parse(response.xml)['rpc-reply'].keys(), print(response)
        self._config[line_port]['fec'] = fec
        return response
