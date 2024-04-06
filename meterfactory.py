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

import logging

from meter import Meter
from maskfactory import MaskFactory
from needlefactory import NeedleFactory
from configfileparser import *

class MeterFactory(object):
    """ Meter creation factory """
    
    def __init__(self, util, meter_config, data_source, mono_needle_cache, mono_rect_cache, left_needle_cache, left_rect_cache, right_needle_cache, right_rect_cache):
        """ Initializer
        
        :param util: utility class
        :param meter_config: configuration dictionary
        :param data_source: the source of audio data
        :param needle_cache: dictionary where key - meter name, value - list of needle sprites
        :param mono_rect_cache: dictionary where key - meter name, value - list of mono needle sprite rectangles
        :param left_rect_cache: dictionary where key - meter name, value - list of left needle sprite rectangles
        :param right_rect_cache: dictionary where key - meter name, value - list of right needle sprite rectangles
        """
        self.util = util
        self.meter_config = meter_config
        self.data_source = data_source
        self.mono_needle_cache = mono_needle_cache
        self.mono_rect_cache = mono_rect_cache
        self.left_needle_cache = left_needle_cache
        self.left_rect_cache = left_rect_cache
        self.right_needle_cache = right_needle_cache
        self.right_rect_cache = right_rect_cache
        
    def create_meter(self):
        """ Dispatcher method """ 
               
        meter_name = self.meter_config[METER]
        try:
            meter_config_section = self.meter_config[meter_name]
        except:
            logging.debug("Meter " + meter_name + " not found for size " + self.meter_config[SCREEN_INFO][METER_SIZE])
            self.util.exit_function()

        if meter_config_section[METER_TYPE] == TYPE_LINEAR:
            return self.create_linear_meter(meter_name)
        elif meter_config_section[METER_TYPE] == TYPE_CIRCULAR:
            return self.create_circular_meter(meter_name)
        
    def create_linear_meter(self, name):
        """ Create linear method
        
        :param name: meter name
        """
        config = self.meter_config[name]
        
        if config[CHANNELS] == 2:
            meter = Meter(self.util, TYPE_LINEAR, config, self.data_source)
            meter.channels = 2
            meter.left_x = config[LEFT_X]
            meter.left_y = config[LEFT_Y]
            meter.right_x = config[RIGHT_X]
            meter.right_y = config[RIGHT_Y]            
        else:
            meter = Meter(self.util, TYPE_LINEAR, config, self.data_source)
            meter.x = config[MONO_X]
            meter.y = config[MONO_Y]
        
        meter.positions_regular = config[POSITION_REGULAR]
        meter.step_width_regular = config[STEP_WIDTH_REGULAR]
        if POSITION_OVERLOAD in config:
            meter.positions_overload = config[POSITION_OVERLOAD]
            meter.step_width_overload = config[STEP_WIDTH_OVERLOAD]
        else:
            meter.positions_overload = 0
            meter.step_width_overload = 0
        meter.total_steps = meter.positions_regular + meter.positions_overload + 1
        meter.step = 100/meter.total_steps
        
        meter.add_background(config[BGR_FILENAME], config[METER_X], config[METER_Y])
        
        if config[CHANNELS] == 2:
            meter.add_channel(config[INDICATOR_FILENAME], meter.left_x, meter.left_y)
            meter.add_channel(config[INDICATOR_FILENAME], meter.right_x, meter.right_y)
        else:
            meter.add_channel(config[INDICATOR_FILENAME], meter.x, meter.y)
        
        meter.add_foreground(config[FGR_FILENAME])
        
        factory = MaskFactory()
        meter.masks = factory.create_masks(meter.positions_regular, meter.positions_overload, meter.step_width_regular, meter.step_width_overload)
        
        return meter

    def create_circular_meter(self, name):
        """ Create circular method
        
        :param name: meter name
        """
        config = self.meter_config[name]
        
        if config[CHANNELS] == 2:
            meter = Meter(self.util, TYPE_CIRCULAR, config, self.data_source)
            meter.channels = 2
        else:
            meter = Meter(self.util, TYPE_CIRCULAR, config, self.data_source)

        try:
            start_angle = config[START_ANGLE]
            stop_angle = config[STOP_ANGLE]
        except:
            pass
			
        if start_angle == None:
            start_angle = config[LEFT_START_ANGLE]
			
        if stop_angle == None:
            stop_angle = config[LEFT_STOP_ANGLE]

        meter.steps_per_degree = config[STEPS_PER_DEGREE]
        if start_angle > stop_angle:
            meter.incr = abs(start_angle - stop_angle) / 100
        elif start_angle < stop_angle:
            meter.incr = abs(stop_angle - start_angle) / 100
        else:
            meter.incr = (abs(start_angle) + abs(stop_angle)) / 100
        meter.add_background(config[BGR_FILENAME], config[METER_X], config[METER_Y])
        needle = meter.load_image(config[INDICATOR_FILENAME])[1]
        w, h = needle.get_size()
        config[NEEDLE_WIDTH] = w
        config[NEEDLE_HEIGHT] = h
        
        if self.meter_config[USE_CACHE] and len(self.mono_needle_cache) + len(self.left_needle_cache) < self.meter_config[CACHE_SIZE]:
            config[USE_CACHE] = True
        else:
            config[USE_CACHE] = False

        factory = NeedleFactory(name, needle, config, self.mono_needle_cache, self.mono_rect_cache, self.left_needle_cache, self.left_rect_cache, self.right_needle_cache, self.right_rect_cache)
        
        if config[CHANNELS] == 2:
            meter.left_needle_sprites = factory.left_needle_sprites
            meter.right_needle_sprites = factory.right_needle_sprites
            meter.left_needle_rects = factory.left_needle_rects
            meter.right_needle_rects = factory.right_needle_rects
            meter.left_needle_rects = factory.left_needle_rects

            sprites_left = meter.left_needle_sprites[0]
            rect_left = meter.left_needle_rects[0]
            rc = rect_left.copy()
            rc.x += config[LEFT_ORIGIN_X] - w/2
            rc.y += config[LEFT_ORIGIN_Y] - h
            meter.add_image(sprites_left, 0, 0, rc)

            sprites_right = meter.right_needle_sprites[0]
            rect_right = meter.right_needle_rects[0]
            rc = rect_right.copy()
            rc.x += config[RIGHT_ORIGIN_X] - w/2
            rc.y += config[RIGHT_ORIGIN_Y] - h
            meter.add_image(sprites_right, 0, 0, rc)
        else:
            meter.mono_needle_sprites = factory.mono_needle_sprites
            meter.mono_needle_rects = factory.mono_needle_rects     
            s = meter.mono_needle_sprites[0]
            r = meter.mono_needle_rects[0]
            rc = r.copy()
            rc.x += config[MONO_ORIGIN_X] - w/2
            rc.y += config[MONO_ORIGIN_Y] - h
            meter.add_image(s, 0, 0, rc)
        
        if config[FGR_FILENAME]:
            meter.add_foreground(config[FGR_FILENAME])
        
        return meter      
        
        