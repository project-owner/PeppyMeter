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

import os

from component import Component
from container import Container
from keys import SCREEN_RECT
from configfileparser import TYPE_LINEAR, TYPE_CIRCULAR
from linear import LinearAnimator
from circular import CircularAnimator

class Meter(Container):
    """ The base class for all meters """
    
    def __init__(self, util, meter_type, ui_refresh_period, left_channel_queue=None, right_channel_queue=None, mono_channel_queue=None):
        """ Initializer
        
        :param util: utility class
        :param meter_type: the type of the meter - linear or circular
        :param ui_refresh_period: refresh interval for animation
        :param left_channel_queue: left channel queue
        :param right_channel_queue: right channel queue
        :param mono_channel_queue: right channel queue
        """
        self.util = util
        self.config = util.config
        self.meter_type = meter_type
        self.ui_refresh_period = ui_refresh_period
        self.left_channel_queue = left_channel_queue
        self.right_channel_queue = right_channel_queue
        self.mono_channel_queue = mono_channel_queue
        self.rect = self.config[SCREEN_RECT]
        Container.__init__(self, util, self.rect, (0, 0, 0))
        self.max_volume = 100.0
        self.total_steps = 100
        self.origin_x = self.origin_y = 0
        self.meter_bounding_box = None
        self.bgr = None
        self.fgr = None
        self.left_sprites = None
        self.right_sprites = None
        self.needle_sprites = None
        self.mono_needle_rects = None
        self.left_needle_rects = None
        self.right_needle_rects = None
        self.masks = None
        self.channels = 1

    def add_background(self, image_name):
        """ Position and add background image.
        
        :param image_name: the name of the background image
        """
        img = self.load_image(image_name)
        self.origin_x = (self.rect.w - img[1].get_size()[0])/2
        self.origin_y = (self.rect.h - img[1].get_size()[1])/2
        self.meter_bounding_box = img[1].get_rect()
        self.meter_bounding_box.x = self.origin_x
        self.meter_bounding_box.y = self.origin_y
        self.bgr = self.add_image(img, self.origin_x, self.origin_y, self.meter_bounding_box)
        
    def add_foreground(self, image_name):
        """ Position and add foreground image.
        
        :param image_name: the name of the foreground image
        """
        if not image_name: return
        img = self.load_image(image_name)     
        self.fgr = self.add_image(img, self.origin_x, self.origin_y, self.meter_bounding_box)
        
    def add_channel(self, image_name, x, y):
        """ Position and add channel indicator image.
        
        :param image_name: the name of the indicator image
        """
        img = self.load_image(image_name)
        r = img[1].get_rect()
        r.x = self.origin_x + x
        r.y = self.origin_y + y
        r.w = 100
        self.add_image(img, self.origin_x + x, self.origin_y + y, r)
    
    def load_image(self, image_name):
        """ Load image
        
        :param image_name: the image name
        """
        path = os.path.join("images",  image_name)        
        return self.util.load_pygame_image(path)
    
    def add_image(self, image, x, y, rect=None):
        """ Creates new UI component from provided image and adds it to the UI container.
        
        :param image: the image object
        :param x: x coordinate of the image top left corner
        :param y: y coordinate of the image top left corner
        :param rect: bounding rectangle of the image
        """               
        c = Component(self.util)
        c.content = image
        c.content_x = x
        c.content_y = y
        if rect: c.bounding_box = rect
        self.add_component(c)
        return c

    def set_volume(self, volume):
        """ Set volume level """
        
        self.max_volume = volume
    
    def draw_bgr_fgr(self, rect, comp):
        """ Draw either background or foreground component """
        
        if not rect: return
        comp.content_x = rect.x
        comp.content_y = rect.y
        comp.bounding_box = rect
        comp.draw()
            
    def start(self):
        """ Initialize meter and start meter animation. """
        
        self.reset_bgr_fgr(self.bgr)
        
        if self.needle_sprites:            
            if self.channels == 1:
                self.components[1].content = self.needle_sprites[0]
                self.components[1].bounding_box = self.mono_needle_rects[0]
            elif self.channels == 2:
                self.components[1].content = self.needle_sprites[0]
                self.components[1].bounding_box = self.left_needle_rects[0]
                self.components[2].content = self.needle_sprites[0]
                self.components[2].bounding_box = self.right_needle_rects[0]
        
        if self.masks:
            self.reset_mask(self.components[1])
            self.reset_mask(self.components[2])
        
        if self.fgr: self.reset_bgr_fgr(self.fgr)
        
        super(Meter, self).draw()
        self.update()
        
        if self.left_channel_queue:
            self.left = self.start_animator(self.left_channel_queue, self.components[1], self.left_needle_rects) 
        
        if self.right_channel_queue:
            self.right = self.start_animator(self.right_channel_queue, self.components[2], self.right_needle_rects) 
            
        if self.mono_channel_queue:
            self.mono = self.start_animator(self.mono_channel_queue, self.components[1], self.mono_needle_rects) 

    def reset_bgr_fgr(self, comp):
        """ Reset background or foreground bounding box  
        
        :param comp: component to reset
        """
        comp.bounding_box = comp.content[1].get_rect()
        comp.content_x = self.origin_x
        comp.content_y = self.origin_y

    def reset_mask(self, comp):
        """ Initialize linear mask. """
        comp.bounding_box.x = comp.content_x
        comp.bounding_box.y = comp.content_y
        comp.bounding_box.w = 1

    def start_animator(self, queue, component, needle_rects=None):
        """ Start meter animation
        
        :param queue: data provider queue 
        :param component: component to animate
        :param needle_rects: list of needle bounding boxes
        """
        a = None
        if self.meter_type == TYPE_LINEAR:
            a = LinearAnimator(queue, component, self, self.ui_refresh_period)
        elif self.meter_type == TYPE_CIRCULAR:
            a = CircularAnimator(queue, component, self, self.ui_refresh_period, needle_rects)            
        a.setDaemon(True)
        a.start()        
        return a
    
    def stop(self):
        """ Stop meter animation """
        if self.left_channel_queue: self.left.run_flag = False
        if self.right_channel_queue: self.right.run_flag = False
        if self.mono_channel_queue: self.mono.run_flag = False

    
