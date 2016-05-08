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

from configparser import ConfigParser

CURRENT = "current"
METER = "meter"
DATA_SOURCE = "data.source"
TYPE = "type"
POLLING_INTERVAL = "polling.interval"
PIPE_NAME = "pipe.name"
PIPE_SIZE = "pipe.size"
VOLUME_CONSTANT = "volume.constant"
VOLUME_MIN = "volume.min"
VOLUME_MAX = "volume.max"
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

FOLDER_SCREENSAVER = "screensaver"
FOLDER_VUMETER = "vumeter"
FILE_METER_CONFIG = "meters.txt"

TYPE_LINEAR = "linear"
TYPE_CIRCULAR = "circular"

class ConfigFileParser(object):
    """ Configuration file parser """
    
    def __init__(self):
        """ Initializer """        
        self.meter_config = {}
        c = ConfigParser()
        c.read(FILE_METER_CONFIG)
        meter_names = list()
        
        for section in c.sections():
            if section == CURRENT:
                self.meter_config[METER] = c.get(section, METER)
                self.meter_config[RANDOM_METER_INTERVAL] = c.getint(section, RANDOM_METER_INTERVAL)
            elif section == DATA_SOURCE:
                self.meter_config[section] = self.get_data_source_section(c, section)
            else:
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
        d[PIPE_SIZE] = config_file.getint(section, PIPE_SIZE)
        d[VOLUME_CONSTANT] = config_file.getfloat(section, VOLUME_CONSTANT)
        d[VOLUME_MIN] = config_file.getfloat(section, VOLUME_MIN)
        d[VOLUME_MAX] = config_file.getfloat(section, VOLUME_MAX)
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

