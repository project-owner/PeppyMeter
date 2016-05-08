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

import sys
import os
import logging

from configparser import ConfigParser
from keys import *

FILE_CONFIG = "config.txt"
AUDIO = "audio"
SERVER_FOLDER = "server.folder"
SERVER_COMMAND = "server.command"
CLIENT_NAME = "client.name"
HOST = "host"
PORT = "port"
USAGE = "usage"
USE_TOUCHSCREEN = "use.touchscreen"
USE_LIRC = "use.lirc"
USE_ROTARY_ENCODERS = "use.rotary.encoders"
USE_WEB = "use.web"
USE_LOGGING = "use.logging"
FONT_SECTION = "font"

class Config(object):
    """ Read the configuration file config.txt and prepare dictionary from it """
    
    def __init__(self):
        """ Initializer """
        self.config = self.load_config()
        self.init_lcd()
        self.config[PYGAME_SCREEN] = self.get_pygame_screen()
        
    def load_config(self):
        """ Loads and parses configuration file config.txt.
        Creates dictionary entry for each property in file.
        :return: dictionary containing all properties from config.txt file
        """
        config = {}
        
        linux_platform = True
        if "win" in sys.platform:
            linux_platform = False
        config[LINUX_PLATFORM] = linux_platform
        
        config_file = ConfigParser()
        config_file.read(FILE_CONFIG)
    
        c = {WIDTH : config_file.getint(SCREEN_INFO, WIDTH)}
        c[HEIGHT] = config_file.getint(SCREEN_INFO, HEIGHT)
        c[DEPTH] = config_file.getint(SCREEN_INFO, DEPTH)
        c[FRAME_RATE] = config_file.getint(SCREEN_INFO, FRAME_RATE)
        config[SCREEN_INFO] = c
        
        folder_name = "medium"
        if c[WIDTH] < 350:
            folder_name = "small"
        elif c[WIDTH] > 700:
            folder_name = "large"
        config[ICON_SIZE_FOLDER] = folder_name                        
        config[SCREEN_RECT] = pygame.Rect(0, 0, c[WIDTH], c[HEIGHT])

        c = {SERVER_FOLDER : config_file.get(AUDIO, SERVER_FOLDER)}
        c[SERVER_COMMAND] = config_file.get(AUDIO, SERVER_COMMAND)
        c[CLIENT_NAME] = config_file.get(AUDIO, CLIENT_NAME)
        config[AUDIO] = c
            
        c = {USE_LIRC : config_file.getboolean(USAGE, USE_LIRC)}
        c[USE_TOUCHSCREEN] = config_file.getboolean(USAGE, USE_TOUCHSCREEN)
        c[USE_ROTARY_ENCODERS] = config_file.getboolean(USAGE, USE_ROTARY_ENCODERS)
        c[USE_WEB] = config_file.getboolean(USAGE, USE_WEB)
        c[USE_LOGGING] = config_file.getboolean(USAGE, USE_LOGGING)
        if c[USE_LOGGING]:
            logging.basicConfig(level=logging.NOTSET)            
        else:
            logging.disable(logging.CRITICAL)
        config[USAGE] = c
        
        c = {HTTP_PORT : config_file.get(WEB_SERVER, HTTP_PORT)}
        config[WEB_SERVER] = c

        c = {COLOR_WEB_BGR : self.get_color_tuple(config_file.get(COLORS, COLOR_WEB_BGR))}
        c[COLOR_DARK] = self.get_color_tuple(config_file.get(COLORS, COLOR_DARK))
        c[COLOR_MEDIUM] = self.get_color_tuple(config_file.get(COLORS, COLOR_MEDIUM))
        c[COLOR_BRIGHT] = self.get_color_tuple(config_file.get(COLORS, COLOR_BRIGHT))
        c[COLOR_CONTRAST] = self.get_color_tuple(config_file.get(COLORS, COLOR_CONTRAST))
        c[COLOR_LOGO] = self.get_color_tuple(config_file.get(COLORS, COLOR_LOGO))
        config[COLORS] = c
            
        config[FONT_KEY] = config_file.get(FONT_SECTION, FONT_KEY)
            
        c = {MODE : config_file.get(CURRENT, MODE)}
        c[LANGUAGE] = config_file.get(CURRENT, LANGUAGE)
        c[PLAYLIST] = config_file.get(CURRENT, PLAYLIST)
        c[STATION] = config_file.getint(CURRENT, STATION)
        c[KEY_SCREENSAVER] = config_file.get(CURRENT, KEY_SCREENSAVER)
        c[KEY_SCREENSAVER_DELAY] = config_file.get(CURRENT, KEY_SCREENSAVER_DELAY)
        c[VOLUME] = config_file.getint(CURRENT, VOLUME)
        config[CURRENT] = c
            
        config[ORDER_HOME_MENU] = self.get_section(config_file, ORDER_HOME_MENU)
        config[ORDER_LANGUAGE_MENU] = self.get_section(config_file, ORDER_LANGUAGE_MENU)
        config[ORDER_GENRE_MENU] = self.get_section(config_file, ORDER_GENRE_MENU)
        config[ORDER_SCREENSAVER_MENU] = self.get_section(config_file, ORDER_SCREENSAVER_MENU)
        config[ORDER_SCREENSAVER_DELAY_MENU] = self.get_section(config_file, ORDER_SCREENSAVER_DELAY_MENU)
        config[PREVIOUS] = self.get_section(config_file, PREVIOUS)
        
        return config

    def get_section(self, config_file, section_name):
        """ Return property file section specified by name
        
        :param config_file: parsed config file
        :section_name: sction name in config file (string enclosed between [])
        
        :return: dictionary with properties from specified section 
        """
        c = config_file[section_name]
        d = r = {}
        for i in c.items():
            k = i[0]
            d[k] = int(i[1])
        return r

    def get_color_tuple(self, s):
        """ Convert string with comma separated colors into tuple with integer number for each color
        
        :param s: input string (e.g. "10, 20, 30" for RGB)
        
        :return: tuple with colors (e.g. (10, 20, 30))
        """
        a = s.split(",")
        return tuple(int(e) for e in a)
    
    def save_config(self):
        """ Save current configuration object (self.config) into config.txt file """       
        config_parser = ConfigParser()
        config_parser.read(FILE_CONFIG)
            
        current = None
        previous = None
            
        try:
            current = self.config[CURRENT]
        except KeyError:
            pass
            
        try:
            previous = self.config[PREVIOUS]
        except KeyError:
            pass
            
        if current:
            for t in current.items():
                config_parser.set(CURRENT, t[0], str(t[1]))
            
        if previous:    
            for t in previous.items():
                config_parser.set(PREVIOUS, t[0], str(t[1]))
            
        if current or previous:
            with open(FILE_CONFIG, 'w') as file:
                config_parser.write(file) 
    
    def get_pygame_screen(self):
        """ Initialize Pygame screen and place it in config object
        
        :return: pygame screen object which is used as drawing context
        """               
        if self.config[LINUX_PLATFORM]:
            pygame.display.init()
            pygame.font.init()
            pygame.mouse.set_visible(False)
        else:            
            pygame.init()
            pygame.display.set_caption("Peppy")
        w = self.config[SCREEN_INFO][WIDTH]
        h = self.config[SCREEN_INFO][HEIGHT]
        d = self.config[SCREEN_INFO][DEPTH]
        return pygame.display.set_mode((w, h), pygame.DOUBLEBUF, d)

    def init_lcd(self):
        """ Initialize touch-screen """
        if not self.config[USAGE][USE_TOUCHSCREEN]:
            return   
        os.environ["SDL_FBDEV"] = "/dev/fb1"
        os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
        os.environ["SDL_MOUSEDRV"] = "TSLIB"
    
        