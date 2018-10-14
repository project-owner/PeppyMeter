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

import os
import logging

from configparser import ConfigParser

CURRENT = "current"
SCREEN_INFO = "screen.info"
PYGAME_SCREEN = "pygame.screen"
WIDTH = "width"
HEIGHT = "height"
DEPTH = "depth"
FRAME_RATE = "frame.rate"
SCREEN_SIZE = "screen.size"
SCREEN_RECT = "screen.rect"
OUTPUT_DISPLAY = "output.display"
OUTPUT_SERIAL = "output.serial"
OUTPUT_I2C = "output.i2c"
SERIAL_INTERFACE = "serial.interface"
DEVICE_NAME = "device.name"
BAUD_RATE = "baud.rate"
INCLUDE_TIME = "include.time"
UPDATE_PERIOD = "update.period"
I2C_INTERFACE = "i2c.interface"
PORT = "port"
LEFT_CHANNEL_ADDRESS = "left.channel.address"
RIGHT_CHANNEL_ADDRESS = "right.channel.address"
OUTPUT_SIZE = "output.size"
USE_LOGGING = "use.logging"
USE_VU_METER = "use.vu.meter"
METER = "meter"
DATA_SOURCE = "data.source"
TYPE = "type"
POLLING_INTERVAL = "polling.interval"
PIPE_NAME = "pipe.name"
VOLUME_CONSTANT = "volume.constant"
VOLUME_MIN = "volume.min"
VOLUME_MAX = "volume.max"
VOLUME_MAX_IN_PIPE = "volume.max.in.pipe"
STEP = "step"
MONO_ALGORITHM = "mono.algorithm"
STEREO_ALGORITHM = "stereo.algorithm"
METER_TYPE = "meter.type"
CHANNELS = "channels"
UI_REFRESH_PERIOD = "ui.refresh.period"
BGR_FILENAME = "bgr.filename"
FGR_FILENAME = "fgr.filename"
INDICATOR_FILENAME = "indicator.filename"
LEFT_X = "left.x"
LEFT_Y = "left.y"
RIGHT_X = "right.x"
RIGHT_Y = "right.y"
MONO_X = "mono.x"
MONO_Y = "mono.y"       
POSITION_REGULAR = "position.regular"
POSITION_OVERLOAD = "position.overload"
STEP_WIDTH_REGULAR = "step.width.regular"
STEP_WIDTH_OVERLOAD = "step.width.overload"  
STEPS_PER_DEGREE = "steps.per.degree"
START_ANGLE = "start.angle"
STOP_ANGLE = "stop.angle"
DISTANCE = "distance"
MONO_ORIGIN_X = "mono.origin.x"
MONO_ORIGIN_Y = "mono.origin.y"
LEFT_CENTER_X = "left.center.x"
LEFT_CENTER_Y = "left.center.y"
LEFT_ORIGIN_X = "left.origin.x"
LEFT_ORIGIN_Y = "left.origin.y"
RIGHT_CENTER_X = "right.center.x"
RIGHT_CENTER_Y = "right.center.y"
RIGHT_ORIGIN_X = "right.origin.x"
RIGHT_ORIGIN_Y = "right.origin.y"
METER_NAMES = "meter.names"
RANDOM_METER_INTERVAL = "random.meter.interval"
BASE_PATH = "base.path"

FILE_CONFIG = "config.txt"
FILE_METER_CONFIG = "meters.txt"

SMALL = "small"
MEDIUM = "medium"
MEDIUM_WIDTH = 480
MEDIUM_HEIGHT = 320
SMALL_WIDTH = 320
SMALL_HEIGHT = 240
DEFAULT_DEPTH = 32
DEFAULT_FRAME_RATE = 30

TYPE_LINEAR = "linear"
TYPE_CIRCULAR = "circular"

class ConfigFileParser(object):
    """ Configuration file parser """
    
    def __init__(self, base_path):
        """ Initializer """  
              
        self.meter_config = {}
        c = ConfigParser()
        
        self.meter_config[BASE_PATH] = base_path 
        peppy_meter_path = os.path.join(base_path, FILE_CONFIG)
        c.read(peppy_meter_path)
        meter_names = list()
        
        self.meter_config[METER] = c.get(CURRENT, METER)
        self.meter_config[RANDOM_METER_INTERVAL] = c.getint(CURRENT, RANDOM_METER_INTERVAL)
        self.meter_config[OUTPUT_DISPLAY] = c.getboolean(CURRENT, OUTPUT_DISPLAY)
        self.meter_config[OUTPUT_SERIAL] = c.getboolean(CURRENT, OUTPUT_SERIAL)
        self.meter_config[OUTPUT_I2C] = c.getboolean(CURRENT, OUTPUT_I2C)
        self.meter_config[USE_LOGGING] = c.getboolean(CURRENT, USE_LOGGING)
        
        self.meter_config[SERIAL_INTERFACE] = {}
        self.meter_config[SERIAL_INTERFACE][DEVICE_NAME] = c.get(SERIAL_INTERFACE, DEVICE_NAME)
        self.meter_config[SERIAL_INTERFACE][BAUD_RATE] = c.getint(SERIAL_INTERFACE, BAUD_RATE)
        self.meter_config[SERIAL_INTERFACE][INCLUDE_TIME] = c.getboolean(SERIAL_INTERFACE, INCLUDE_TIME)
        self.meter_config[SERIAL_INTERFACE][UPDATE_PERIOD] = c.getfloat(SERIAL_INTERFACE, UPDATE_PERIOD)
        
        self.meter_config[I2C_INTERFACE] = {}
        self.meter_config[I2C_INTERFACE][PORT] = c.getint(I2C_INTERFACE, PORT)
        self.meter_config[I2C_INTERFACE][LEFT_CHANNEL_ADDRESS] = int(c.get(I2C_INTERFACE, LEFT_CHANNEL_ADDRESS), 0)
        self.meter_config[I2C_INTERFACE][RIGHT_CHANNEL_ADDRESS] = int(c.get(I2C_INTERFACE, RIGHT_CHANNEL_ADDRESS), 0)
        self.meter_config[I2C_INTERFACE][OUTPUT_SIZE] = c.getint(I2C_INTERFACE, OUTPUT_SIZE)
        self.meter_config[I2C_INTERFACE][UPDATE_PERIOD] = c.getfloat(I2C_INTERFACE, UPDATE_PERIOD)

        screen_size = c.get(CURRENT, SCREEN_SIZE)
        self.meter_config[SCREEN_INFO] = {}
        self.meter_config[SCREEN_INFO][SCREEN_SIZE] = screen_size
        self.meter_config[SCREEN_INFO][DEPTH] = DEFAULT_DEPTH
        self.meter_config[SCREEN_INFO][FRAME_RATE] = DEFAULT_FRAME_RATE        
        
        if screen_size == MEDIUM:
            self.meter_config[SCREEN_INFO][WIDTH] = MEDIUM_WIDTH
            self.meter_config[SCREEN_INFO][HEIGHT] = MEDIUM_HEIGHT
        elif screen_size == SMALL:
            self.meter_config[SCREEN_INFO][WIDTH] = SMALL_WIDTH
            self.meter_config[SCREEN_INFO][HEIGHT] = SMALL_HEIGHT
        else:
            logging.debug("Not supported screen size")
            os._exit(0)

        self.meter_config[DATA_SOURCE] = self.get_data_source_section(c, DATA_SOURCE)
        
        meter_config_path = os.path.join(base_path, screen_size, FILE_METER_CONFIG)
        c = ConfigParser()
        c.read(meter_config_path)
        
        for section in c.sections():
            meter_names.append(section)
            meter_type = c.get(section, METER_TYPE)
            if meter_type == TYPE_LINEAR:
                self.meter_config[section] = self.get_linear_section(c, section, meter_type)
            elif meter_type == TYPE_CIRCULAR:
                self.meter_config[section] = self.get_circular_section(c, section, meter_type)
        self.meter_config[METER_NAMES] = meter_names
    
    def get_data_source_section(self, config_file, section):
        """ Parser for data source section
        
        :param config_file: configuration file
        :param section: section name
        """
        d = {}
        d[TYPE] = config_file.get(section, TYPE)
        d[POLLING_INTERVAL] = config_file.getfloat(section, POLLING_INTERVAL)
        d[PIPE_NAME] = config_file.get(section, PIPE_NAME)
        d[VOLUME_CONSTANT] = config_file.getfloat(section, VOLUME_CONSTANT)
        d[VOLUME_MIN] = config_file.getfloat(section, VOLUME_MIN)
        d[VOLUME_MAX] = config_file.getfloat(section, VOLUME_MAX)
        d[VOLUME_MAX_IN_PIPE] = config_file.getfloat(section, VOLUME_MAX_IN_PIPE)
        d[MONO_ALGORITHM] = config_file.get(section, MONO_ALGORITHM)
        d[STEREO_ALGORITHM] = config_file.get(section, STEREO_ALGORITHM)
        d[STEP] = config_file.getint(section, STEP)        
        return d
    
    def get_linear_section(self, config_file, section, meter_type):
        """ Parser for linear meter
        
        :param config_file: configuration file
        :param section: section name
        :param meter_type: type of the meter
        """
        d = {}
        self.get_common_options(d, config_file, section, meter_type)
        d[LEFT_X] = config_file.getint(section, LEFT_X)
        d[LEFT_Y] = config_file.getint(section, LEFT_Y)
        d[RIGHT_X] = config_file.getint(section, RIGHT_X)
        d[RIGHT_Y] = config_file.getint(section, RIGHT_Y)
        d[POSITION_REGULAR] = config_file.getint(section, POSITION_REGULAR)
        d[STEP_WIDTH_REGULAR] = config_file.getint(section, STEP_WIDTH_REGULAR)
        try:
            d[POSITION_OVERLOAD] = config_file.getint(section, POSITION_OVERLOAD)
            d[STEP_WIDTH_OVERLOAD] = config_file.getint(section, STEP_WIDTH_OVERLOAD)
        except:
            pass
        return d

    def get_circular_section(self, config_file, section, meter_type):
        """ Parser for circular meter
        
        :param config_file: configuration file
        :param section: section name
        :param meter_type: type of the meter
        """
        d = {}
        self.get_common_options(d, config_file, section, meter_type)
        d[STEPS_PER_DEGREE] = config_file.getint(section, STEPS_PER_DEGREE)
        d[START_ANGLE] = config_file.getint(section, START_ANGLE)
        d[STOP_ANGLE] = config_file.getint(section, STOP_ANGLE)
        d[DISTANCE] = config_file.getint(section, DISTANCE)        
        if d[CHANNELS] == 1:                  
            d[MONO_ORIGIN_X] = config_file.getint(section, MONO_ORIGIN_X)
            d[MONO_ORIGIN_Y] = config_file.getint(section, MONO_ORIGIN_Y)            
        else:            
            d[LEFT_ORIGIN_X] = config_file.getint(section, LEFT_ORIGIN_X)
            d[LEFT_ORIGIN_Y] = config_file.getint(section, LEFT_ORIGIN_Y)            
            d[RIGHT_ORIGIN_X] = config_file.getint(section, RIGHT_ORIGIN_X)
            d[RIGHT_ORIGIN_Y] = config_file.getint(section, RIGHT_ORIGIN_Y)
        return d
        
    def get_common_options(self, d, config_file, section, meter_type):
        """ Parser for the common section of the configuration file
        
        :param d: common section dictionary
        :param config_file: configuration file
        :param section: section name
        :param meter_type: type of the meter
        """
        d[METER_TYPE] = meter_type
        d[CHANNELS] = config_file.getint(section, CHANNELS)
        d[UI_REFRESH_PERIOD] = config_file.getfloat(section, UI_REFRESH_PERIOD)                
        d[BGR_FILENAME] = config_file.get(section, BGR_FILENAME)
        try:
            d[FGR_FILENAME] = config_file.get(section, FGR_FILENAME)
        except:
            d[FGR_FILENAME] = None
        d[INDICATOR_FILENAME] = config_file.get(section, INDICATOR_FILENAME)

