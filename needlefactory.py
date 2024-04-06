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

import pygame
from configfileparser import *

class NeedleFactory(object):
    """ Factory to prepare needle sprites for circular animator """
    
    def __init__(self, name, image, config, mono_needle_cache, mono_rect_cache, left_needle_cache, left_rect_cache, right_needle_cache, right_rect_cache):
        """ Initializer
        
        :param name: meter name
        :param image: base needle image
        :param config: configuration dictionary
        :param mono_needle_cache: dictionary where key - meter name, value - list of mono needle sprites
        :param mono_rect_cache: dictionary where key - meter name, value - list of mono needle sprite rectangles
        :param left_needle_cache: dictionary where key - meter name, value - list of left channel needle sprites
        :param left_rect_cache: dictionary where key - meter name, value - list of left channel needle sprite rectangles
        :param right_needle_cache: dictionary where key - meter name, value - list of right channel needle sprites
        :param right_rect_cache: dictionary where key - meter name, value - list of right channel needle sprite rectangles
        """
        self.image = image
        self.config = config
        
        if config[CHANNELS] == 1:
            self.mono_needle_sprites = self.get_cached_object(name, mono_needle_cache)
            self.mono_needle_rects = self.get_cached_object(name, mono_rect_cache)

            if len(self.mono_needle_sprites) != 0:
                return

            self.create_needle_sprites(self.mono_needle_sprites, self.mono_needle_rects, self.config[DISTANCE],
                self.config[START_ANGLE], self.config[STOP_ANGLE], False)

            if self.config[USE_CACHE]:
                mono_needle_cache[name] = self.mono_needle_sprites
                mono_rect_cache[name] = self.mono_needle_rects
        elif config[CHANNELS] == 2:
            self.left_needle_sprites = self.get_cached_object(name, left_needle_cache)
            self.right_needle_sprites = self.get_cached_object(name, right_needle_cache)
            self.left_needle_rects = self.get_cached_object(name, left_rect_cache)
            self.right_needle_rects = self.get_cached_object(name, right_rect_cache)

            if len(self.left_needle_sprites) != 0:
                return

            self.create_needle_sprites(self.left_needle_sprites, self.left_needle_rects, self.config[DISTANCE],
                self.config[LEFT_START_ANGLE], self.config[LEFT_STOP_ANGLE], self.config[LEFT_NEEDLE_FLIP])

            if config[LEFT_START_ANGLE] == config[RIGHT_START_ANGLE] and config[LEFT_STOP_ANGLE] == config[RIGHT_STOP_ANGLE]:
                self.right_needle_sprites = self.left_needle_sprites
                self.right_needle_rects = self.left_needle_rects
            else:
                self.create_needle_sprites(self.right_needle_sprites, self.right_needle_rects, self.config[DISTANCE],
                    self.config[RIGHT_START_ANGLE], self.config[RIGHT_STOP_ANGLE], self.config[RIGHT_NEEDLE_FLIP])

            if self.config[USE_CACHE]:
                left_needle_cache[name] = self.left_needle_sprites
                right_needle_cache[name] = self.right_needle_sprites
                left_rect_cache[name] = self.left_needle_rects
                right_rect_cache[name] = self.right_needle_rects

    def get_cached_object(self, name, cache):
        """ Get cached object

        :param name: object name
        :param cache: object cache

        :return: object from cache or empty list otherwise
        """
        cached_object = list()

        try:
            cached_object = cache[name]
        except:
            pass

        return cached_object

    def rotate_image(self, image, distance, angle):
        """ Rotate provided image by specified angle
        
        :param image: provided image
        :param distance: distance between rotation origin and image center
        :param angle: rotation angle

        :return: tuple with rotated image and rectangle
        """
        w, h = image.get_size()
        image_bottom = (w/2,  h)
        distance_to_origin = (w/2, h/2 + distance)
        image_rect = image.get_rect(topleft = (image_bottom [0] - distance_to_origin[0], image_bottom [1] - distance_to_origin[1]))
        offset_origin_to_center = pygame.math.Vector2(image_bottom ) - image_rect.center
        rotated_offset = offset_origin_to_center.rotate(-angle)
        rotated_image_center = (image_bottom [0] - rotated_offset.x, image_bottom [1] - rotated_offset.y)
        rotated_image = pygame.transform.rotozoom(image, angle, 1)
        rotated_image_rect = rotated_image.get_rect(center = rotated_image_center)

        return (rotated_image, rotated_image_rect)

    def create_needle_sprites(self, needle_sprites, needle_rects, distance, start_angle, stop_angle, flip):
        """ Create sprites for all angles

        :param needle_sprites: list of sprite images
        :param needle_rects: list of sprite rectangles
        :param distance: distance between rotation origin and image center
        :param start_angle: start angle
        :param stop_angle: stop angle
        :param flip: True - flip indicator image across X axis
        """
        images = []
        rects = []
        s = 1 / self.config[STEPS_PER_DEGREE]
        s *= 2 * ((stop_angle > start_angle) ^ (s < 0)) - 1
        angles = [start_angle + i * s for i in range(int((stop_angle - start_angle) / s + 1))]

        if flip:
            image = pygame.transform.flip(self.image, True, False)
        else:
            image = self.image

        for a in angles:
            i, r = self.rotate_image(image, distance, a)
            images.append(i)
            rects.append(r)

        sprites = (images, rects)
        needle_sprites.extend(sprites[0])
        needle_rects.extend(sprites[1])
