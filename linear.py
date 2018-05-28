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

import time
from threading import Thread

class LinearAnimator(Thread):
    """ Provides linear animation in a separate thread """
    
    def __init__(self, data_source, components, base, ui_refresh_period):
        """ Initializer
        
        :param data_source: data source
        :param components: UI component
        :param base: meter base
        :param ui_refresh_period: animation interval 
        """
        Thread.__init__(self)
        self.indicator_height = 30 
        self.index = 0
        self.data_source = data_source
        self.components = components
        self.run_flag = True
        self.base = base
        self.ui_refresh_period = ui_refresh_period
        self.bgr = self.base.bgr
        self.fgr = self.base.fgr
    
    def run(self):
        """ Thread method. Converts volume value into the mask width and displays corresponding mask. """
                
        previous_rect_left = self.components[1].bounding_box.copy()
        previous_rect_right = self.components[2].bounding_box.copy()
        previous_volume_left = previous_volume_right = 0.0
        
        while self.run_flag:
            d = self.data_source.get_current_data() 
            
            try:
                previous_rect_left, previous_volume_left = self.update_channel(d[0], self.components[1], previous_rect_left, previous_volume_left)
                previous_rect_right, previous_volume_right = self.update_channel(d[1], self.components[2], previous_rect_right, previous_volume_right)
            except:
                pass
            
            time.sleep(self.ui_refresh_period)
            
    def update_channel(self, volume, component, previous_rect, previous_volume):
        """ Update channel
        
        :volume: new volume value
        :component: component to update
        :previous_rect: previous bounding rectangle
        :previous_volume: previous volume value
        """
        if previous_volume == volume:
            return (previous_rect, previous_volume) 
                       
        self.base.draw_bgr_fgr(previous_rect, self.base.bgr)
                          
        n = int((volume * self.base.max_volume) / (self.base.step * 100))
        if n >= len(self.base.masks): n = len(self.base.masks) - 1            
        w = self.base.masks[n]
        if w == 0: w = 1
                
        component.bounding_box.w = w
        component.bounding_box.x = 0          
        component.bounding_box.y = 0
        component.draw()
            
        r = component.bounding_box.copy()
        r.x = component.content_x
        r.y = component.content_y 
        u = previous_rect.union(r)
        if self.base.fgr:
            self.base.draw_bgr_fgr(u.copy(), self.base.fgr)
            
        self.base.update_rectangle(u)
        
        return (r.copy(), volume)
        
