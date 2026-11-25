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
        self.timed_random_enabled = False
        self.random_meter_names = copy.copy(self.meter_names)
        self.current_meter_name = None
        self.forced_meter_name = None

        if self.util.meter_config[METER] == "random":
            self.random_meter = True
        elif "," in self.util.meter_config[METER]:
            self.list_meter = True
        self.timed_random_enabled = bool(
            timer_controlled_random_meter and (self.random_meter or self.list_meter)
        )
            
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

        if self.forced_meter_name is not None:
            meter_name = self.forced_meter_name
            self.forced_meter_name = None
        elif self.random_meter:
            meter_name = self.get_next_random_meter_name()
        elif self.list_meter:
            if self.list_meter_index == len(self.meter_names):
                self.list_meter_index = 0
            meter_name = self.meter_names[self.list_meter_index]
            self.list_meter_index += 1
        else:
            meter_name = self.util.meter_config[METER]

        if self.meter and self.current_meter_name == meter_name:
            return self.meter

        self.util.meter_config[METER] = meter_name

        factory = MeterFactory(self.util, self.util.meter_config, self.data_source, self.mono_needle_cache, self.mono_rect_cache, self.left_needle_cache, self.left_rect_cache, self.right_needle_cache, self.right_rect_cache)
        m = factory.create_meter()
        self.current_meter_name = meter_name

        return m

    def get_next_random_meter_name(self):
        """从当前分辨率皮肤列表中抽取一个，尽量避免连续重复。"""
        if not self.random_meter_names:
            self.random_meter_names = [
                name for name in self.meter_names if name != self.current_meter_name
            ] or copy.copy(self.meter_names)
        if not self.random_meter_names:
            return self.current_meter_name
        index = randrange(0, len(self.random_meter_names))
        return self.random_meter_names.pop(index)

    def set_timed_random_enabled(self, enabled):
        """开启或关闭定时随机模式，不在切换状态时立即更换皮肤。"""
        self.timed_random_enabled = bool(enabled)
        self.timer_controlled_random_meter = self.timed_random_enabled
        self.frames = 0
        self.list_meter = False
        self.random_meter = self.timed_random_enabled
        if self.random_meter:
            self.random_meter_names = [
                name for name in self.meter_names if name != self.current_meter_name
            ] or copy.copy(self.meter_names)
        elif self.current_meter_name is not None:
            self.util.meter_config[METER] = self.current_meter_name

    def switch_to_random_meter(self):
        """立即随机切换一次，并保留定时随机模式状态。"""
        if not self.meter_names:
            return
        self.forced_meter_name = self.get_next_random_meter_name()
        self.restart()

    def next_manual_meter(self):
        """切到当前分辨率的下一款皮肤，末尾循环到开头。"""
        self.switch_manual_meter(1)

    def previous_manual_meter(self):
        """切到当前分辨率的上一款皮肤，开头循环到末尾。"""
        self.switch_manual_meter(-1)

    def switch_manual_meter(self, direction):
        """手动切换会关闭定时随机，并在当前皮肤列表内循环。"""
        if not self.meter_names:
            return
        self.set_timed_random_enabled(False)
        try:
            current_index = self.meter_names.index(self.current_meter_name)
        except ValueError:
            current_index = -1 if direction > 0 else 0
        next_index = (current_index + direction) % len(self.meter_names)
        self.forced_meter_name = self.meter_names[next_index]
        self.restart()
    
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

        if not self.timed_random_enabled:
            return
               
        if (self.random_meter or self.list_meter) and self.frames == self.frames_before_switch:
            self.frames = 0
            self.restart()
        self.frames += 1
