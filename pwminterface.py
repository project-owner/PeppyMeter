# Copyright 2019-2023 PeppyMeter peppy.player@gmail.com
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
from configfileparser import PWM_INTERFACE, FREQUENCY, GPIO_PIN_LEFT, GPIO_PIN_RIGHT, UPDATE_PERIOD

class DummyPWM(object):
    """ Dummy PWM class used for development on Windows platform """
    
    def __init__(self):
        """ Initializer """
        
        pass
    
    def start(self, value):
        """ Dummy start """
        
        pass
        
    def ChangeDutyCycle(self, value):
        """ Dummy change duty cycle """
        
        pass
    
    def stop(self, value):
        """ Dummy stop """
        
        pass

class PWMInterface(object):
    """ PWM interface class. 

    Can be used with devices controlled by means of PWM signal e.g. LED, gas tubes etc.
    """    
    def __init__(self, config, data_source):
        """ Initializer """
        
        self.data_source = data_source
        
        self.frequency = config[PWM_INTERFACE][FREQUENCY]
        self.gpio_pin_left = config[PWM_INTERFACE][GPIO_PIN_LEFT]
        self.gpio_pin_right = config[PWM_INTERFACE][GPIO_PIN_RIGHT]        
        self.update_period = config[PWM_INTERFACE][UPDATE_PERIOD]
        
        if "win" in sys.platform:
            self.left = DummyPWM()
            self.right = DummyPWM() 
        else:
            import RPi.GPIO as gpio
            gpio.setmode(gpio.BCM)
            gpio.setwarnings(False)
            
            gpio.setup(self.gpio_pin_left, gpio.OUT)
            gpio.setup(self.gpio_pin_right, gpio.OUT)
            
            self.left = gpio.PWM(self.gpio_pin_left, self.frequency)
            self.right = gpio.PWM(self.gpio_pin_right, self.frequency) 
            
        self.logging_template = "PWM left: {0} right: {1}"           
        
    def start_writing(self):
        """ Start writing thread """
        
        self.running = True
        thread = Thread(target = self.write_data)
        thread.start()
        
    def write_data(self):
        """ Method of the writing thread """
        
        self.left.start(0)
        self.right.start(0)
        
        while self.running:
            time.sleep(self.update_period)
            
            v = self.data_source.get_current_data()
            
            if v == 0:
                continue
            
            logging.debug(v)
            left = float(int(v[0]))
            right = float(int(v[1]))
            
            logging.debug(self.logging_template.format(left, right))

            self.left.ChangeDutyCycle(left)
            self.right.ChangeDutyCycle(right)
                
    def stop_writing(self):
        """ Stop writing thread and stop PWM """
        
        self.running = False
        time.sleep(self.update_period)
        self.left.stop()
        self.right.stop()
    