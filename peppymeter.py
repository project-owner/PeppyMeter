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

import pygame
import os
import sys

from util import Util
from pygame.time import Clock
from vumeter import Vumeter
from keys import CURRENT, KEY_SCREENSAVER, SCREEN_RECT, PYGAME_SCREEN

class PeppyMeter(object):
    """ Peppy Meter class containing main method """
    
    def __init__(self, util):
        """ Initializer
        
        :param util: utility object
        """
        self.util = util
        self.util.config = {}
        self.screen_w = 480
        self.screen_h = 320
        
        os.environ["SDL_FBDEV"] = "/dev/fb1"
        os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
        os.environ["SDL_MOUSEDRV"] = "TSLIB"
        
        if "win" not in sys.platform:
            pygame.display.init()
            pygame.mouse.set_visible(False)
        else:            
            pygame.init()
            pygame.display.set_caption("Peppy Meter")
        self.util.config[PYGAME_SCREEN] = pygame.display.set_mode((self.screen_w, self.screen_h), pygame.DOUBLEBUF, 32)
        
        d = {KEY_SCREENSAVER : "vumeter"}
        self.util.config[CURRENT] = d
        self.util.config[SCREEN_RECT] = pygame.Rect(0, 0, self.screen_w, self.screen_h)
        self.config = self.util.config            
        self.meter = Vumeter(self.util)         
        self.current_image = None
        self.update_period = self.meter.get_update_period()
        self.frame_rate = 30
        self.one_cycle_period = 1000 / self.frame_rate
        self.counter = 0
    
    def start(self):
        """ Start meter """
        pygame.event.clear()
        clock = Clock()
        self.meter.start()        
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()
                elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                    keys = pygame.key.get_pressed() 
                    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and event.key == pygame.K_c: 
                        self.exit()                               
            self.refresh()
            clock.tick(self.frame_rate)
    
    def refresh(self):
        """ Refresh meter. Used to switch from one random meter to another. """
        self.counter = self.counter + 1
        if int(self.counter * self.one_cycle_period) == self.update_period * 1000:
            self.meter.refresh()
            self.counter = 0
    
    def exit(self):
        """ Exit program """
        pygame.quit()            
        os._exit(0) 
       
if __name__ == "__main__":
    util = Util(False)
    meter = PeppyMeter(util)    
    meter.start()
          
