# Copyright 2016-2018 PeppyMeter peppy.player@gmail.com
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

import pygame
import os
import sys
import logging

from meterutil import MeterUtil
from pygame.time import Clock
from vumeter import Vumeter
from datasource import DataSource, SOURCE_NOISE, SOURCE_PIPE
from serialinterface import SerialInterface
from i2cinterface import I2CInterface
from screensavermeter import ScreensaverMeter
from configfileparser import ConfigFileParser, SCREEN_RECT, SCREEN_INFO, WIDTH, HEIGHT, DEPTH, \
    OUTPUT_DISPLAY, OUTPUT_SERIAL, OUTPUT_I2C, DATA_SOURCE, TYPE, USE_LOGGING, USE_VU_METER

class Peppymeter(ScreensaverMeter):
    """ Peppy Meter class """
    
    def __init__(self, util=None, standalone=False):
        """ Initializer
        
        :param util: utility object
        :param standalone: True - standalone version, False - part of Peppy player
        """
        ScreensaverMeter.__init__(self)
        if util:
            self.util = util
        else:
            self.util = MeterUtil()
            
        use_vu_meter = getattr(self.util, USE_VU_METER, None)
        
        base_path = "."
        if __package__:
            pkg_parts = __package__.split(".")
            if len(pkg_parts) > 0:
                base_path = os.path.join(os.getcwd(), "screensaver", "peppymeter")
        
        parser = ConfigFileParser(base_path)
        self.util.meter_config = parser.meter_config
        self.outputs = {}
        
        if standalone:
            if self.util.meter_config[USE_LOGGING]:
                logging.basicConfig(level=logging.NOTSET)            
            else:
                logging.disable(logging.CRITICAL)
        
        # no VU Meter support for Windows
        if "win" in sys.platform or use_vu_meter == False:
            self.util.meter_config[DATA_SOURCE][TYPE] = SOURCE_NOISE
        
        self.data_source = DataSource(self.util.meter_config)
        if self.util.meter_config[DATA_SOURCE][TYPE] == SOURCE_PIPE or use_vu_meter == True:      
            self.data_source.start_data_source()
        
        if self.util.meter_config[OUTPUT_DISPLAY]:
            self.meter = self.output_display(self.data_source)
            
        if self.util.meter_config[OUTPUT_SERIAL]:
            self.outputs[OUTPUT_SERIAL] = SerialInterface(self.util.meter_config, self.data_source)
            
        if self.util.meter_config[OUTPUT_I2C]:
            self.outputs[OUTPUT_I2C] = I2CInterface(self.util.meter_config, self.data_source)

        self.start_interface_outputs()
    
    def output_display(self, data_source):
        """ Initialize display
        
        :data_source: data source
        :return: graphical VU Meter
        """
        meter = Vumeter(self.util, data_source)         
        self.current_image = None
        self.update_period = meter.get_update_period()
        
        return meter
    
    def init_display(self):
        screen_w = self.util.meter_config[SCREEN_INFO][WIDTH]
        screen_h = self.util.meter_config[SCREEN_INFO][HEIGHT]
        depth = self.util.meter_config[SCREEN_INFO][DEPTH]
        
        os.environ["SDL_FBDEV"] = "/dev/fb1"
        os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
        os.environ["SDL_MOUSEDRV"] = "TSLIB"
        
        if "win" not in sys.platform:
            pygame.display.init()
            pygame.mouse.set_visible(False)
        else:            
            pygame.init()
            pygame.display.set_caption("Peppy Meter")
            
        self.util.PYGAME_SCREEN = pygame.display.set_mode((screen_w, screen_h), pygame.DOUBLEBUF, depth)        
        self.util.meter_config[SCREEN_RECT] = pygame.Rect(0, 0, screen_w, screen_h) 
    
    def start_interface_outputs(self):
        """ Starts writing to Serial and I@C interfaces """
        
        if self.util.meter_config[OUTPUT_SERIAL]:
            self.serial_interface = self.outputs[OUTPUT_SERIAL]
            self.serial_interface.start_writing()
        
        if self.util.meter_config[OUTPUT_I2C]:
            self.i2c_interface = self.outputs[OUTPUT_I2C]
            self.i2c_interface.start_writing()
    
    def start(self):
        """ Start VU meter. This method called by Peppy Meter to start meter """
        
        pygame.event.clear()
        if self.util.meter_config[DATA_SOURCE][TYPE] != SOURCE_PIPE:      
            self.data_source.start_data_source()
        self.meter.start()
        
    def start_display_output(self):
        """ Start thread for graphical VU meter """
        
        pygame.event.clear()
        clock = Clock()
        self.meter.start()        
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()
                elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                    keys = pygame.key.get_pressed() 
                    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and event.key == pygame.K_c:
                        self.exit()                                                 
            self.refresh()
            clock.tick(1)
    
    def stop(self):
        """ Stop meter animation. """ 
        if self.util.meter_config[DATA_SOURCE][TYPE] != SOURCE_PIPE:      
            self.data_source.stop_data_source()
        self.meter.stop()
    
    def refresh(self):
        """ Refresh meter. Used to switch from one random meter to another. """
        
        self.meter.refresh()
    
    def exit(self):
        """ Exit program """
        
        if self.util.meter_config[OUTPUT_SERIAL]:
            self.serial_interface.stop_writing()
        if self.util.meter_config[OUTPUT_I2C]:
            self.i2c_interface.stop_writing()
        pygame.quit()            
        os._exit(0) 
       
if __name__ == "__main__":
    """ This is called by stand-alone PeppyMeter """
    pm = Peppymeter(standalone=True)
    if pm.util.meter_config[DATA_SOURCE][TYPE] != SOURCE_PIPE:      
        pm.data_source.start_data_source()
    if pm.util.meter_config[OUTPUT_DISPLAY]:
        pm.init_display()
        pm.start_display_output()    
          
