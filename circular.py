# Copyright 2016-2022 PeppyMeter peppy.player@gmail.com
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
import pygame

from configfileparser import METER_X, METER_Y, UI_REFRESH_PERIOD, NEEDLE_WIDTH, NEEDLE_HEIGHT
from threading import Thread

class CircularAnimator(Thread):
    """ Provides needle circular animation in a separate thread """
    
    def __init__(self, data_source, component, base, meter_parameters, needles, needle_rects, get_data_method, origin_x, origin_y):
        """ Initializer
        
        :param data_source: data source
        :param component: UI component
        :param base: meter base
        :param meter_parameters: meter configuration parameters
        :param needles: list of sprite images
        :param needle_rects: list of sprite rectangles
        :param get_data_method: method to get data
        :param origin_x: rotation X origin
        :param origin_y: rotation Y origin
        """
        Thread.__init__(self)             
        self.data_source = data_source
        self.component = component
        self.run_flag = True
        self.base = base
        self.ui_refresh_period = meter_parameters[UI_REFRESH_PERIOD]
        self.previous_index = 0
        self.needles = needles
        self.needle_rects = needle_rects
        self.get_data = get_data_method
        self.meter_parameters = meter_parameters
        self.origin_x = origin_x + meter_parameters[METER_X]
        self.origin_y = origin_y + meter_parameters[METER_Y]
        
    def run(self):
        """ Thread method. Converts volume value into the needle angle and displays corresponding sprite. """
        
        self.set_sprite(None, True)
        while self.run_flag:
            volume = self.get_data()
            n = self.set_sprite(volume)
            time.sleep(self.ui_refresh_period)
            self.previous_index = int(n)

    def stop_thread(self):
        """ Stop thread """

        self.run_flag = False
        time.sleep(self.ui_refresh_period * 2)

    def set_sprite(self, volume, init=False):
        """ Set current sprite for new volume level

        :param volume: new volume level
        :param init: True - init stage

        :return: index of the current sprite
        """
        if volume == None:
                volume = 0.0            

        n = (volume * self.base.max_volume * self.base.incr) / 100.0
        if n >= len(self.needles):
            n = len(self.needles) - 1
            
        if self.previous_index == int(n) and not init:
            return n
            
        diff = n - self.previous_index
        sub_steps = range(int(abs(diff)) * self.base.steps_per_degree)
        sign = int(math.copysign(1, diff))
        if len(sub_steps) > 0:
            m = sub_steps[-1]
        else:
            m = 0

        previous_rect = self.component.bounding_box.copy()
        gap = 4
        previous_rect.x -= gap
        previous_rect.y -= gap
        previous_rect.w += gap * 2
        previous_rect.h += gap * 2
        self.base.draw_bgr_fgr(previous_rect, self.base.bgr)
        next_index = (self.previous_index * self.base.steps_per_degree) + (m * sign)
        if next_index >= len(self.needles):
            next_index = len(self.needles) - 1

        sprite = self.needles[next_index]
        self.component.content = sprite
        r = self.needle_rects[next_index]
        rc = r.copy()
        rc.x += self.origin_x - self.meter_parameters[NEEDLE_WIDTH]/2
        rc.y += self.origin_y - self.meter_parameters[NEEDLE_HEIGHT]
        self.component.bounding_box = rc
        self.component.draw()

        a = previous_rect.union(rc)
        if self.base.fgr:
            self.base.draw_bgr_fgr(a, self.base.fgr)

        self.base.update_rectangle(a)
        return n
