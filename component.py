# Copyright 2016-2024 Peppy Player peppy.player@gmail.com
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

class Component(object):
    """ Represent the lowest UI component level.    
    This is the only class which knows how to draw on Pygame Screen.
    """
    
    def __init__(self, util, c=None, x=0, y=0, bb=None, fgr=(0, 0, 0), bgr=(0, 0, 0), v=True):
        """ Initializer
        
        :param util: utility object
        :param c: component content
        :param x: component coordinate X on Pygame Screen
        :param y: component coordinate Y on Pygame Screen
        :param bb: component bounding box
        :param fgr: component foreground
        :param bgr: component background
        :param v: visibility flag, True - visible, False - invisible 
        """
        self.screen = None
        self.screen = util.PYGAME_SCREEN
        self.content = c
        self.content_x = x
        self.content_y = y
        if bb: 
            self.bounding_box = pygame.Rect(bb.x, bb.y, bb.w, bb.h)
        else:
            self.bounding_box = None
        self.fgr = fgr       
        self.bgr = bgr
        self.visible = v
        self.text = None
        self.text_size = None
        self.image_filename = None

    def clean(self):
        """ Clean component by filling its bounding box by background color """
        
        if not self.visible: return
        self.draw_rect(self.bgr, self.bounding_box)
    
    def draw(self):
        """ Dispatcher drawing method.        
        Distinguishes between Rectangle and Image components.
        Doesn't draw invisible component. 
        """
        if not self.visible: return
        
        if isinstance(self.content, pygame.Rect):
            self.draw_rect(self.bgr, r=self.content)
        else:
            self.draw_image(self.content, self.content_x, self.content_y)
    
    def draw_rect(self, f, r, t=0):
        """ Draw Rectangle on Pygame Screen
        
        :param f: outline color
        :param r: rectangle object
        :param t: outline thickness
        """
        if not self.visible: return
        if self.screen:
            pygame.draw.rect(self.screen, f, r, t)
    
    def draw_image(self, c, x, y):
        """ Draw Image on Pygame Screen
        
        :param c: image
        :param x: coordinate X of the image top-left corner on Pygame Screen
        :param y: coordinate Y of the image top-left corner on Pygame Screen
        """
        comp = c
        if isinstance(c, tuple):        
            comp = c[1]
        if comp and self.screen:
            try:
                if self.bounding_box:
                    if isinstance(self.content, tuple):
                        self.screen.blit(self.content[1], (self.content_x, self.content_y), self.bounding_box)
                    else:
                        self.screen.blit(self.content, self.bounding_box)
                else:
                    self.screen.blit(comp, (x, y))
            except:
                pass
 
    def set_visible(self, flag):
        """ Set component visibility 
        
        :param flag: True - component visible, False - component invisible
        """
        self.visible = flag
        
    def refresh(self):
        """ Refresh component. Used for periodical updates  animation. """
        
        pass

        