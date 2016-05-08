# Copyright 2016 Peppy Player peppy.player@gmail.com
# 
# This file is part of Peppy Player.
# 
# Peppy Player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Peppy Player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Peppy Player. If not, see <http://www.gnu.org/licenses/>.

import time
from threading import Thread

class LinearAnimator(Thread):
    """ Provides linear animation in a separate thread """
    
    def __init__(self, channel, component, base, ui_refresh_period):
        """ Initializer
        
        :param channel: number of channels
        :param component: UI component
        :param base: meter base
        :param ui_refresh_period: animation interval 
        """
        Thread.__init__(self)
        self.indicator_height = 30 
        self.index = 0
        self.channel = channel
        self.component = component
        self.run_flag = True
        self.base = base
        self.ui_refresh_period = ui_refresh_period
        self.bgr = self.base.bgr
        self.fgr = self.base.fgr
        self.previous_volume = 0.0
    
    def run(self):
        """ Thread method. Converts volume value into the mask width and displays corresponding mask. """        
        previous_rect = self.component.bounding_box.copy()
        while self.run_flag:
            volume = self.channel.get()            
            self.channel.task_done()            
            if self.previous_volume == volume:
                time.sleep(self.ui_refresh_period)
                continue 
                       
            self.base.draw_bgr_fgr(previous_rect, self.base.bgr)
                          
            n = int((volume * self.base.max_volume) / (self.base.step * 100))
            if n >= len(self.base.masks): n = len(self.base.masks) - 1            
            w = self.base.masks[n]
            if w == 0: w = 1
                
            self.component.bounding_box.w = w
            self.component.bounding_box.x = 0          
            self.component.bounding_box.y = 0
            self.component.draw()
            
            r = self.component.bounding_box.copy()
            r.x = self.component.content_x
            r.y = self.component.content_y 
            u = previous_rect.union(r)
            if self.base.fgr:
                self.base.draw_bgr_fgr(u.copy(), self.base.fgr)
            
            self.base.update_rectangle(u)
            previous_rect = r.copy()
            self.previous_volume = volume
            time.sleep(self.ui_refresh_period)
