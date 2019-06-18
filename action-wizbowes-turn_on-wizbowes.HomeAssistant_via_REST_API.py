#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import ConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ffi.utils import MqttOptions
from hermes_python.ontology import *
import io

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

class SnipsConfigParser(ConfigParser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, ConfigParser.Error) as e:
        return dict()

def subscribe_intent_callback(hermes, intentMessage):
    conf = read_configuration_file(CONFIG_INI)
    action_wrapper(hermes, intentMessage, conf)


def action_wrapper(hermes, intentMessage, conf):
    from requests import post, get
    import json
    
    current_session_id = intentMessage.session_id
    try:
     if len(intentMessage.slots.state) > 0:
        myState = intentMessage.slots.state.first().value 
     if len(intentMessage.slots.device_name) > 0:
        myDeviceId = intentMessage.slots.device_name.first().value 
#        myDeviceName = intentMessage.slots.device_name.first().value
        myDeviceName = intentMessage.slots.device_name[0].raw_value 
# put this line back one once the bug is resolved: https://github.com/snipsco/snips-issues/issues/68
#        myDeviceName = intentMessage.slots.device_name.first().raw_value
     auth = conf['secret']['ha-apikey']
     myip = conf['secret']['ha-ipaddress']
     myport = conf['secret']['ha-port']
     header = {'Authorization': auth.encode("utf-8"), 'Content-Type': 'application/json'}
     print header
     if myState != "query":
       payload = json.dumps({"entity_id": myDeviceId.encode("utf-8")})
       url = 'http://'+ myip.encode("utf-8") + ':' + myport.encode("utf-8") + '/api/services/homeassistant/turn_' + myState.encode("utf-8")
       response = post(url, headers=header, data=payload)
       hermes.publish_end_session(current_session_id, "Turning " + myState.encode("utf-8") + " " + myDeviceName.encode("utf-8"))
     else:
       url = 'http://'+ myip.encode("utf-8") + ':' + myport.encode("utf-8") + '/api/states/' + myDeviceId.encode("utf-8")
       response = get(url, headers=header)
       hermes.publish_end_session(current_session_id, myDeviceName.encode("utf-8") + " is " + response.json()['state'])
    except:
       print 'http://'+ myip.encode("utf-8") + ':' + myport.encode("utf-8") + '/api/states/' + myDeviceId.encode("utf-8")
       print myDeviceName.encode("utf-8")
       print myDeviceId.encode("utf-8")
       hermes.publish_end_session(current_session_id, "Sorry, something went wrong again")

 


if __name__ == "__main__":
    mqtt_opts = MqttOptions()
    with Hermes(mqtt_options=mqtt_opts) as h:
#    with Hermes("localhost:1883") as h:
        h.subscribe_intent("hooray4me:turn_on", subscribe_intent_callback) \
         .start()

