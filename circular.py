# Copyright 2016-2020 PeppyMeter peppy.player@gmail.com
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
import logging

from threading import Thread

class CircularAnimator(Thread):
    """ Provides needle circular animation in a separate thread """
    
    def __init__(self, data_source, component, base, ui_refresh_period, needle_rects, get_data_method):
        """ Initializer
        
        :param data_source: data source
        :param channel: number of channels
        :param component: UI component
        :param base: meter base
        :param ui_refresh_period: animation interval 
        :param needle_rects: list of sprite rectangles
        :param get_data_method: method to get data
        """
        Thread.__init__(self)             
        self.data_source = data_source
        self.component = component
        self.run_flag = True
        self.base = base
        self.ui_refresh_period = ui_refresh_period
        self.previous_index = 0
        self.needle_rects = needle_rects
        self.get_data = get_data_method
        
    def run(self):
        """ Thread method. Converts volume value into the needle angle and displays corresponding sprite. """
        
        self.set_sprite(None, True)
        while self.run_flag:
            volume = self.get_data()
            n = self.set_sprite(volume)
            time.sleep(self.ui_refresh_period)
            self.previous_index = int(n)

    def set_sprite(self, volume, init=False):
        if volume == None:
                volume = 0.0            

        n = (volume * self.base.max_volume * self.base.incr) / 100.0
        if n >= len(self.base.needle_sprites):
            n = len(self.base.needle_sprites) - 1
            
        if self.previous_index == int(n) and not init:
            return n
            
        diff = n - self.previous_index
        sub_steps = range(int(abs(diff)) * self.base.steps_per_degree)
        sign = int(math.copysign(1, diff))
        if len(sub_steps) > 0:
            m = sub_steps[-1]
        else:
            m = 0

        previous_rect = self.component.bounding_box
        self.base.draw_bgr_fgr(previous_rect, self.base.bgr)
        next_index = (self.previous_index * self.base.steps_per_degree) + (m * sign)
        if next_index >= len(self.base.needle_sprites):
            next_index = len(self.base.needle_sprites) - 1

        sprite = self.base.needle_sprites[next_index]
        self.component.content = ("", sprite)
        r = self.needle_rects[next_index]
        self.component.content_x = r.x
        self.component.content_y = r.y
        r.x = 0
        r.y = 0
        self.component.bounding_box = r
        self.component.draw()
        r.x = self.component.content_x
        r.y = self.component.content_y

        a = previous_rect.union(r)
        if self.base.fgr:
            self.base.draw_bgr_fgr(a, self.base.fgr)

        self.base.update_rectangle(a)
        return n