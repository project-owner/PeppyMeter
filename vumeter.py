# Copyright 2016-2024 PeppyMeter peppy.player@gmail.com
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
import copy
import pygame

from random import randrange
from meterfactory import MeterFactory
from screensavermeter import ScreensaverMeter
from configfileparser import METER, METER_NAMES, RANDOM_METER_INTERVAL, USE_CACHE, SCREEN_RECT, FRAME_RATE

class Vumeter(ScreensaverMeter):
    """ VU Meter plug-in. """
    
    def __init__(self, util, data_source, timer_controlled_random_meter=True):
        """ Initializer
        
        :param util: utility class
        """
        self.util = util
        self.update_period = 1
        self.meter = None
        
        self.meter_names = self.util.meter_config[METER_NAMES]
        random_meter_interval = self.util.meter_config[RANDOM_METER_INTERVAL]
        frame_rate = self.util.meter_config[FRAME_RATE]
        self.frames_before_switch = random_meter_interval * frame_rate
        self.data_source = data_source
        self.timer_controlled_random_meter = timer_controlled_random_meter
        self.random_meter = False
        self.list_meter = False
        self.list_meter_index = 0
        
        if self.util.meter_config[METER] == "random":
            self.random_meter = True
            self.random_meter_names = copy.copy(self.meter_names)
        elif "," in self.util.meter_config[METER]:
            self.list_meter = True
            
        self.meter = None
        self.current_volume = 100.0
        self.frames = 0

        self.mono_needle_cache = {}
        self.mono_rect_cache = {}
        self.left_needle_cache = {}
        self.left_rect_cache = {}
        self.right_needle_cache = {}
        self.right_rect_cache = {}
    
    def get_meter(self):
        """ Creates meter using meter factory. """  
              
        if self.meter and not (self.random_meter or self.list_meter):
            return self.meter
        
        if self.random_meter:
            if len(self.random_meter_names) == 0:
                self.random_meter_names = copy.copy(self.meter_names)
            i = randrange(0, len(self.random_meter_names))     
            self.util.meter_config[METER] = self.random_meter_names[i]
            del self.random_meter_names[i]
        elif self.list_meter:
            if self.list_meter_index == len(self.meter_names):
                self.list_meter_index = 0
            self.util.meter_config[METER] = self.meter_names[self.list_meter_index]
            self.list_meter_index += 1

        factory = MeterFactory(self.util, self.util.meter_config, self.data_source, self.mono_needle_cache, self.mono_rect_cache, self.left_needle_cache, self.left_rect_cache, self.right_needle_cache, self.right_rect_cache)
        m = factory.create_meter()

        return m
    
    def set_volume(self, volume):
        """ Set volume level 
        
        :param volume: new volume level
        """
        self.current_volume = volume        
    
    def start(self):
        """ Start data source and meter animation. """ 
               
        self.meter = self.get_meter()
        self.meter.set_volume(self.current_volume)
        self.meter.start()

        if hasattr(self, "callback_start"):
            self.callback_start(self.meter)

    def run(self):
        """ Run meter  
        
        :return: list of rectangles for update
        """
        if getattr(self, "meter", None) != None:
            return self.meter.run()
        return None
    
    def stop(self):
        """ Stop meter animation. """ 
        
        self.frames = 0
        self.meter.stop()

        if hasattr(self, "callback_stop"):
            self.callback_stop(self.meter)

        if not self.util.meter_config[USE_CACHE]:
            del self.mono_needle_cache
            del self.mono_rect_cache
            del self.left_needle_cache
            del self.left_rect_cache
            del self.right_needle_cache
            del self.right_rect_cache
            del self.meter

            if hasattr(self, "malloc_trim"):
                self.malloc_trim()

            self.mono_needle_cache = {}
            self.mono_rect_cache = {}
            self.left_needle_cache = {}
            self.left_rect_cache = {}
            self.right_needle_cache = {}
            self.right_rect_cache = {}
            self.meter = None

    def restart(self):
        """ Restart random meter """

        self.stop()
        time.sleep(0.2) # let threads stop
        self.start()
        pygame.display.update(self.util.meter_config[SCREEN_RECT])
    
    def refresh(self):
        """ Refresh meter. Used to update random meter. """

        if not self.timer_controlled_random_meter:
            return
               
        if (self.random_meter or self.list_meter) and self.frames == self.frames_before_switch:
            self.frames = 0
            self.restart()
        self.frames += 1
