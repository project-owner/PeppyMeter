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

import math
import pygame as pg
from configfileparser import *

class NeedleFactory(object):
    """ Factory to prepare needle sprites for circular animator """
    
    def __init__(self, image, config):
        """ Initializer
        
        :param image: base needle image
        :param config: configuration dictionary
        """
        self.image = image
        self.config = config
        self.needle_sprites = None
        self.mono_needle_rects = None
        self.left_needle_rects = None
        self.right_needle_rects = None
        self.needle_sprites = list()
        self.angle_range = abs(self.config[STOP_ANGLE] - self.config[START_ANGLE])
        
        if config[CHANNELS] == 1:
            self.mono_needle_rects = list()
            self.create_needle_sprites(self.needle_sprites, self.mono_needle_rects, self.config[DISTANCE], self.config[MONO_ORIGIN_X], self.config[MONO_ORIGIN_Y])
        elif config[CHANNELS] == 2:
            self.left_needle_rects = list()
            self.create_needle_sprites(self.needle_sprites, self.left_needle_rects, self.config[DISTANCE], self.config[LEFT_ORIGIN_X], self.config[LEFT_ORIGIN_Y])
            self.right_needle_rects = list()
            self.create_needle_sprites(None, self.right_needle_rects, self.config[DISTANCE], self.config[RIGHT_ORIGIN_X], self.config[RIGHT_ORIGIN_Y])

    def create_needle_sprites(self, needle_sprites, needle_rects, d, o_x, o_y):
        """ Create needle sprites
        
        :param needle_sprites: list for image sprites
        :param needle_rects: list for sprite bounding boxes
        :param d: the distance beteen image center and rotation origin
        :param o_x: x coordinate of the rotation origin
        :param o_y: y coordinate of the rotation origin 
        """
        img = pg.transform.rotozoom(self.image, self.config[START_ANGLE], 1)
        self.initial_angle = self.config[START_ANGLE]
        start_angle = math.atan2(img.get_rect().h/2, -img.get_rect().w/2) - math.radians(self.config[START_ANGLE])
 
        for _ in range(self.angle_range * self.config[STEPS_PER_DEGREE]):
            self.initial_angle = (self.initial_angle - 1/self.config[STEPS_PER_DEGREE]) % 360
            new_angle = math.radians(self.initial_angle) + start_angle
            new_center = (o_x + d * math.cos(new_angle), o_y - d * math.sin(new_angle))            
            img = pg.transform.rotozoom(self.image, self.initial_angle, 1)
            r = img.get_rect()
            img = img.subsurface((r.x, r.y, r.w, r.h))
            rect = img.get_rect(center=new_center)
            if needle_sprites != None:
                needle_sprites.append(img)
            needle_rects.append(rect)     
