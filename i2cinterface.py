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
import math
import sys
import logging

from threading import Thread
from configfileparser import I2C_INTERFACE, PORT, LEFT_CHANNEL_ADDRESS, RIGHT_CHANNEL_ADDRESS, \
    OUTPUT_SIZE, UPDATE_PERIOD

class DummySMBus(object):
    """ Dummy SMBus class used for development on Windows platform """
    
    def __init__(self):
        """ Initializer """
        
        pass
    
    def write_byte_data(self, address, command, value):
        """ Dummy byte data writer """
        
        pass
        
    def write_word_data(self, address, command, value):
        """ Dummy word data writer """
        
        pass

class I2CInterface(object):
    """ I2C interface class. 
        It writes VU Meter stereo data into the I2C port defined in the configuration file.
        The I2C addresses for the left and right channel should be defined in config.txt. 
        Default values 0x21, 0x20. The property output.size defines the number of bits used
        for the I2C VU Meter. The default value is 10. For the smaller/larger numbers the
        bit_patterns array should be modified accordingly.
    """    
    def __init__(self, config, data_source):
        """ Initializer """
        
        self.data_source = data_source
        
        self.port = config[I2C_INTERFACE][PORT]
        self.left_channel_address = config[I2C_INTERFACE][LEFT_CHANNEL_ADDRESS]
        self.right_channel_address = config[I2C_INTERFACE][RIGHT_CHANNEL_ADDRESS]        
        self.output_size = config[I2C_INTERFACE][OUTPUT_SIZE]
        self.update_period = config[I2C_INTERFACE][UPDATE_PERIOD]
        
        self.step = int(100/self.output_size)
        
        if "win" in sys.platform:
            self.i2c_interface = DummySMBus()
        else:
            from smbus import SMBus
            self.i2c_interface = SMBus(self.port)
            
        self.i2c_interface.write_byte_data(self.left_channel_address, 0x00, 0x00)
        self.i2c_interface.write_byte_data(self.left_channel_address, 0x01, 0x00)
        self.i2c_interface.write_byte_data(self.right_channel_address, 0x00, 0x00)
        self.i2c_interface.write_byte_data(self.right_channel_address, 0x01, 0x00)
        
        self.bit_patterns = {}
        self.bit_patterns[10] = 0b10000000
        self.bit_patterns[20] = 0b11000000
        self.bit_patterns[30] = 0b11100000
        self.bit_patterns[40] = 0b11110000
        self.bit_patterns[50] = 0b11111000
        self.bit_patterns[60] = 0b11111100
        self.bit_patterns[70] = 0b11111110
        self.bit_patterns[80] = 0b11111111
        self.bit_patterns[90] = 0b111111111
        self.bit_patterns[100] = 0b1111111111
        
        f = "{:0" + str(self.output_size) + "b}"
        self.logging_template = "I2C left: " + f + " right: " + f
        
    def start_writing(self):
        """ Start writing thread """
        
        self.running = True
        thread = Thread(target = self.write_data)
        thread.start()
        
    def write_data(self):
        """ Method of the writing thread """
        
        while self.running:
            v = self.data_source.get_current_data()

            if v:
                left = self.get_bits(v[0])
                right = self.get_bits(v[1])

                logging.debug(self.logging_template.format(left, right))

                self.i2c_interface.write_word_data(self.left_channel_address, 0x12, left)
                self.i2c_interface.write_word_data(self.right_channel_address, 0x12, right)

            time.sleep(self.update_period)
    
    def stop_writing(self):
        """ Stop writing thread and nullify values in I2C """
        
        self.running = False
        time.sleep(self.update_period)
        self.i2c_interface.write_word_data(self.left_channel_address, 0x12, 0)
        self.i2c_interface.write_word_data(self.right_channel_address, 0x12, 0)
    
    def get_bits(self, n):
        """ Return bit pattern for the defined value in range 0-100
        
        :param n: data value
        :return: bit pattern
        """
        if n == 0:
            return 0
        else:
            k = int(math.ceil(n / self.step)) * self.step
            v = self.bit_patterns[k]
            return v
