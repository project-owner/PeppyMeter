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
import codecs
import importlib
import logging

from state import State
from config import Config
from keys import *

IMAGE_VOLUME = "volume"
IMAGE_MUTE = "volume-mute"
IMAGE_SHADOW = "shadow"
IMAGE_SELECTION = "selection"
IMAGE_SELECTED_SUFFIX = "-on"
IMAGE_DISABLED_SUFFIX = "-off"
IMAGE_ABOUT = "about"
IMAGE_LANGUAGE = "language"
IMAGE_HARD_DRIVE = "hard.drive"
IMAGE_RADIO = "radio"
IMAGE_STREAM = "stream"
IMAGE_SCREENSAVER = "screensaver"
EXT_PROPERTIES = ".properties"
EXT_PNG = ".png"
EXT_M3U = ".m3u"
FOLDER_ICONS = "icons"
FOLDER_SLIDES = "slides"
FOLDER_STATIONS = "stations"
FOLDER_HOME = "home"
FOLDER_GENRES = "genres"
FOLDER_FONT = "font"
FOLDER_PLAYLIST = "playlist"
PACKAGE_SCREENSAVER = "screensaver"    
FILE_LABELS = "labels.txt"
FOLDER_SAVER = "saver"
FOLDER_SAVER_TYPE = "type"
FOLDER_SAVER_DELAY = "delay"
FOLDER_STATIONS = "stations"
PROPERTY_SEPARATOR = "="
PROPERTY_COMMENT_CHAR = "#"
CURRENT_PLAYLIST = "current playlist"
CURRENT_INDEX = "current index"
INDEX = "index"
KEY_HOME = "home"
KEY_LANGUAGE = "language"
KEY_GENRE = "genre"
KEY_BYE = "bye"
UTF_8 = "utf-8-sig"
HOME_ITEMS = [IMAGE_ABOUT, IMAGE_LANGUAGE, IMAGE_HARD_DRIVE, IMAGE_RADIO, IMAGE_STREAM, IMAGE_SCREENSAVER]
HOME_DISABLED_ITEMS = [IMAGE_HARD_DRIVE, IMAGE_STREAM]
GENRE_ITEMS = ["children", "classical", "contemporary", "culture", "jazz", "news", "pop", "retro", "rock"]
LANGUAGE_ITEMS = ["en_us", "de", "fr", "ru"]
SCREENSAVER_ITEMS = ["clock", "logo", "slideshow"]
FOLDER_BUNDLES = "bundles"

class Util(object):
    """ Utility class """
    
    def __init__(self, read_config=True):
        """ Initializer. Prepares Config object. """
        if read_config:      
            self.config_class = Config()
            self.config = self.config_class.config
            self.config[LABELS] = self.get_labels()        
        self.font_cache = {}
        self.image_cache = {}
        self.image_cache_base64 = {}
    
    def get_labels(self):
        """ Reads labels for current language
        
        :return: labels dictionary
        """        
        language = self.config[CURRENT][LANGUAGE]
        path = os.path.join(FOLDER_BUNDLES, language + EXT_PROPERTIES)
        labels = self.load_properties(path, UTF_8)
        return labels
    
    def load_image(self, path, base64=False):
        """ Load and return image
        
        :param path: image path 
        :param base64: True - encode image using base64 algorithm (for web), False - don't encode
        """
        if base64:
            return self.load_base64_image(path)
        else:
            return self.load_pygame_image(path)
    
    def load_pygame_image(self, path):
        """ Check if image is in the cache.
         
        If yes, return the image from the cache.
        If not load image file and place it in the cache.
        
        :param path: image path
        
        :return: pygame image
        """
        image = None
        try:
            i = self.image_cache[path]            
            return (path, i)
        except KeyError:
            pass
            
        try:            
            image = pygame.image.load(path).convert_alpha()
        except:
            pass
            
        if image:
            self.image_cache[path] = image
            return (path, image)
        else:
            return None
        
    def load_base64_image(self, path):
        """ Check if image is in the cache for encoded images. 
        
        If yes, return the image from the cache.
        If not load image file and place it in the cache.
        
        :param path: image path
        
        :return: base64 encoded image
        """
        try:
            i = self.image_cache_base64[path]            
            return (path, i)
        except KeyError:
            pass
            
        import base64  
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode()                
        
    def load_icon(self, filename, resizable=True):
        """ Load UI icon
        
        :param filename: icon name without extension
        :param resizable: True - load icon from small/medium/large folders, False - load from 'icons' folder
        
        :return: pygame image
        """
        filename += EXT_PNG
        path = os.path.join(FOLDER_ICONS, self.config[ICON_SIZE_FOLDER], filename)
        if not resizable:
            path = os.path.join(FOLDER_ICONS, filename)
        return self.load_image(path)
        
    def load_screensaver_images(self, saver_name, folder_name):
        """ Load screensaver images (e.g. for Slideshow plug-in)
        
        :param saver_name: defines the folder below screensaver folder (e.g. slideshow)
        :param folder_name: defines the images folder (e.g. slides)
        
        :return: list of images
        """
        slides = []        
        folder = os.path.join(PACKAGE_SCREENSAVER, saver_name, folder_name)   
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            slides.append(self.load_image(path))     
        return slides
        
    def load_station_icon(self, folder, index):
        """ Load station icon
        
        :param folder: image folder
        :param index: image filename without extension
        
        :return: station icon
        """
        path = os.path.join(folder, str(index) + EXT_PNG)  
        return self.load_image(path)
        
    def get_font(self, size):
        """ Return font from cache if not in cache load, place in cache and return.
        
        :param size: font size 
        """
        font_name = self.config[FONT_KEY]
        key = font_name + str(size)
        if key in self.font_cache:
            return self.font_cache[key]
        filename = os.path.join(FOLDER_FONT, font_name)
        font = pygame.font.Font(filename, size)
        self.font_cache[key] = font
        return font
        
    def scale_image(self, image, ratio):
        """ Scale image using specified ratio
        
        :param ratio: scaling ratio
        
        :return: scaled image
        """
        if image == None:
            return None
        a = pygame.Surface(ratio, flags=pygame.SRCALPHA)
        if isinstance(image, tuple):
            image = image[1]
        pygame.transform.smoothscale(image, ratio, a)
        return a
            
    def load_stations(self, language, genre, stations_per_page):
        """ Load stations for specified language and genre
        
        :param language: the language
        :param genre: the genre
        :param stations_per_page: stations per page used to assign indexes
        
        :return: list of button state objects. State contains station icons, index, genre, name etc.
        """
        stations = []
        folder = os.path.join(FOLDER_STATIONS, language, genre)
        path = os.path.join(folder, genre + EXT_M3U)
        lines = []
        try:
            lines = codecs.open(path, "r", UTF_8).read().split("\n")
        except Exception as e:
            logging.error(str(e))
            pass
        for i in range(0, len(lines), 3):
            if len(lines[i].rstrip()) == 0: 
                continue
            index = int(lines[i].rstrip()[1:])
            localized_name = lines[i + 1][1:]
            url = lines[i + 2]
            icon = self.load_station_icon(folder, index)
            state = State()
            state.index = index
            state.genre = genre
            state.url = url.rstrip()
            state.name = str(index)
            state.l_name = localized_name.rstrip()
            state.icon_base = icon
            state.comparator_item = INDEX
            state.index_in_page = index % stations_per_page
            stations.append(state)    
        return stations
        
    def load_properties(self, path, encoding=None):
        """ Load properties file
        
        :param path: file path
        :param encoding: file encoding
        
        :return: dictioanry with properties
        """
        properties = {}
        file = codecs.open(path, "r", encoding)
        for line in file:
            l = line.rstrip()
            if l and not l.startswith(PROPERTY_COMMENT_CHAR):
                pair = l.split(PROPERTY_SEPARATOR)
                properties[pair[0].rstrip()] = pair[1].rstrip()
        return properties
        
    def load_menu(self, names, comparator, disabled_items=None):
        """ Load menu items
        
        :param names: list of menu item names (should have corresponding filename)
        :param comparator: string used to sort items
        :param disabled_items: list of items which should be disabled
        
        :return: dictionary with menu items
        """
        items = {}
        f = self.config[ICON_SIZE_FOLDER]
            
        for name in names:
            filename = name + EXT_PNG
            path = os.path.join(FOLDER_ICONS, f, filename)
            icon = self.load_image(path)
                
            filename = name + IMAGE_SELECTED_SUFFIX + EXT_PNG
            path_on = os.path.join(FOLDER_ICONS, f, filename)
            icon_on = self.load_image(path_on)
            
            filename = name + IMAGE_DISABLED_SUFFIX + EXT_PNG
            path_off = os.path.join(FOLDER_ICONS, f, filename)
            icon_off = self.load_image(path_off)
                
            state = State()
            state.name = name
            state.genre = name 
            state.l_genre = self.config[LABELS][name]
            state.l_name = self.config[LABELS][name]
            state.icon_base = icon
            if icon_on:
                state.icon_selected = icon_on
            else:
                state.icon_selected = icon
            if not icon_off:
                state.icon_disabled = icon_on
            state.bgr = self.config[COLORS][COLOR_DARK]
            state.img_x = None
            state.img_y = None
            state.auto_update = True
            state.show_bgr = True
            state.show_img = True
            state.show_label = True
            if comparator == NAME:
                state.comparator_item = state.name
            elif comparator == GENRE:
                state.comparator_item = state.genre
            if disabled_items and name in disabled_items:
                state.enabled = False
            items[state.name] = state            
        return items
        
    def get_screensaver_labels(self):
        """ Return localized screensaver labels 
        
        :return: labels dictionary
        """        
        screensaver_labels = {}
        for name in SCREENSAVER_ITEMS:
            screensaver_labels[name.lower()] = self.config[LABELS][name.lower()]
        return screensaver_labels
        
    def get_screensaver_delays(self):
        """ Get screensaver delay button states
        
        :return: dictionary with button states
        """
        names = [KEY_SCREENSAVER_DELAY_1, KEY_SCREENSAVER_DELAY_3, KEY_SCREENSAVER_DELAY_OFF]
        delays = {}
        for n in names:            
            state = State()
            state.name = n
            state.l_name = self.config[LABELS][n]
            state.comparator_item = n
            state.bgr = self.config[COLORS][COLOR_DARK]
            delays[state.name] = state                
        return delays
        
    def load_screensaver(self, name):
        """ Load screensaver plug-in module and create object
        
        :param name: plug-in name
        
        :return: screensaver object
        """
        p = PACKAGE_SCREENSAVER + ('.' + name.lower())*2
        m = importlib.import_module(p)
        return getattr(m, name.title())(self)
    
