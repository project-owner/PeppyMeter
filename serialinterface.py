# Copyright 2016-2023 PeppyMeter peppy.player@gmail.com
# 
# This file is part of PeppyMeter.
# 
# PeppyMeter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PeppyMeter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with PeppyMeter. If not, see <http://www.gnu.org/licenses/>.

import time
import sys
import logging

from threading import Thread
from configfileparser import SERIAL_INTERFACE, DEVICE_NAME, BAUD_RATE, INCLUDE_TIME, UPDATE_PERIOD

class DummySerial(object):
    """ Dummy Serial class used for development on Windows platform """
    
    def __init__(self):
        """ Initializer """
        
        self.port = None
        self.baudrate = None
    
    def open(self):
        """ Dummy open method """
        
        pass
        
    def write(self, data):
        """ Dummy write method """
        
        pass

class SerialInterface():
    """ Serial Interface class. Provides writing data into serial interface """
    
    def __init__(self, config, data_source):
        """ Initializer
        
        :config: configuration settings
        :data_source: data source
        """
        self.data_source = data_source
        
        if "win" in sys.platform:
            self.serial_interface = DummySerial()
        else:
            from serial import Serial
            self.serial_interface = Serial()
        
        self.serial_interface.port = config[SERIAL_INTERFACE][DEVICE_NAME]
        self.serial_interface.baudrate  = config[SERIAL_INTERFACE][BAUD_RATE]        
        self.include_time = config[SERIAL_INTERFACE][INCLUDE_TIME]
        self.update_period = config[SERIAL_INTERFACE][UPDATE_PERIOD]
        self.serial_interface.open()
        
    def start_writing(self):
        """ Start writing thread """
        
        self.running = True
        thread = Thread(target = self.write_data)
        thread.start()
        
    def write_data(self):
        """ Write data into serial interface """
        
        while self.running:
            v = self.data_source.get_current_data()
            if v:
                data = self.get_data(v[0], v[1])
                logging.debug("Serial output: " + data.rstrip())

                self.serial_interface.write(data.encode("utf-8"))
            time.sleep(self.update_period)
    
    def get_data(self, left, right):
        """ Prepare data for writing. Include time if enabled.
        
        :left: data for left channel
        :right: data for right channel
        :return: string representing volume level and time
        """
        data = "l%03ir%03i\n" % (left, right) 
        if self.include_time:
            data =  time.strftime("%H:%M:%S") + data
        return data  
            
    def stop_writing(self):
        """ Stop writing thread and nullify values in serial interface """
        
        self.running = False
        time.sleep(self.update_period)
        data = self.get_data(0, 0)              
        self.serial_interface.write(data.encode("utf-8"))
            
