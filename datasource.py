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

import math
import audioop
import time
import statistics

from queue import Queue
from random import uniform
from threading import Thread
from configfileparser import *

SOURCE_CONSTANT = "constant"
SOURCE_NOISE = "noise"
SOURCE_SAW = "saw"
SOURCE_TRIANGLE = "triangle"
SOURCE_SINE = "sine"
SOURCE_PIPE = "pipe"

MONO_ALGORITHM_MAXIMUM = "maximum"
MONO_ALGORITHM_AVERAGE = "average"

STEREO_ALGORITHM_NEW = "new"
STEREO_ALGORITHM_LOGARITHM = "logarithm"
STEREO_ALGORITHM_AVERAGE = "average"

LEFT = (1, 0)
RIGHT = (0, 1)

class DataSource(object):
    """ Provides methods to generate different types of audio signal. """
    
    def __init__(self, c):
        """ Initializer
        
        :param c: configuration dictionary
        """
        config = c[DATA_SOURCE]
        self.left_channel = Queue(maxsize=1)
        self.right_channel = Queue(maxsize=1)
        self.mono_channel = Queue(maxsize=1)
        self.mono_algorithm = config[MONO_ALGORITHM]
        self.stereo_algorithm = config[STEREO_ALGORITHM]
        self.ds_type = config[TYPE]
        self.const = config[VOLUME_CONSTANT]
        self.bits = 16
        self.pipe_name = config[PIPE_NAME]
        self.min = config[VOLUME_MIN]
        self.max = config[VOLUME_MAX]
        self.v = 0
        self.step = config[STEP]
        self.pipe_size = config[PIPE_SIZE]
        self.rng = list(range(int(self.min), int(self.max)))
        self.double_rng = self.rng
        self.double_rng.extend(range(int(self.max) - 1, int(self.min), -1))
        self.pipe = None
        if self.ds_type == SOURCE_PIPE:
            try:
                self.pipe = os.open(self.pipe_name, os.O_RDONLY)
            except:
                print("cannot open pipe")                
        self.k = int(math.pow(2, self.bits)//2 - 1)
        self.previous_left = self.previous_right = self.previous_mono = 0.0
        self.run_flag = True
        self.polling_interval = config[POLLING_INTERVAL]
        self.prev_time = None
    
    def start_data_source(self):
        """ Start data source thread. """        
        self.run_flag = True
        thread = Thread(target=self.get_data)
        thread.start()
        
    def stop_data_source(self):
        """ Stop data source thread. """        
        self.run_flag = False
    
    def get_data(self):
        """ Thread method. Get data and put it into the corresponding queue. """        
        while self.run_flag:
            d = self.get_value()
            
            with self.left_channel.mutex: self.left_channel.queue.clear()
            self.left_channel.put(d[0])
                     
            with self.right_channel.mutex: self.right_channel.queue.clear()
            self.right_channel.put(d[1])
                 
            with self.mono_channel.mutex: self.mono_channel.queue.clear()
            self.mono_channel.put(d[2])
                
            time.sleep(self.polling_interval)
    
    def get_value(self):
        """ Get data depending on the data source type. """        
        d = ()
        if self.ds_type == SOURCE_CONSTANT:
            d = self.get_constant_value()
        elif self.ds_type == SOURCE_NOISE:
            d = self.get_noise_value()
        elif self.ds_type == SOURCE_SAW:
            d = self.get_saw_value()
        elif self.ds_type == SOURCE_TRIANGLE:
            d = self.get_triangle_value()
        elif self.ds_type == SOURCE_SINE:
            d = self.get_sine_value()
        elif self.ds_type == SOURCE_PIPE:
            d = self.get_pipe_value()
        return d
    
    def get_constant_value(self):
        """ Returns constant value for all channels. The value is defined in the configuration file. """        
        return (self.const, self.const, self.const)
    
    def get_noise_value(self):
        """ Generate random value for all channels. """        
        new_left = uniform(self.min, self.max)
        new_right = uniform(self.min, self.max)
        new_mono = self.get_mono(new_left, new_right)
        
        left = self.get_channel(self.previous_left, new_left)
        right = self.get_channel(self.previous_right, new_right)
        mono = self.get_channel(self.previous_mono, new_mono)
        
        self.previous_left = new_left
        self.previous_right = new_right
        self.previous_mono = new_mono
        
        return (left, right, mono)
    
    def get_saw_value(self):
        """ Generate saw shape signal. """        
        s = (self.rng[self.v], self.rng[self.v], self.rng[self.v])
        self.v = (self.v + self.step) % self.max
        return s
    
    def get_triangle_value(self):
        """ Generate triangle shape signal. """        
        t = (self.double_rng[self.v], self.double_rng[self.v], self.double_rng[self.v])
        self.v = (self.v + self.step) % (int(self.max * 2 - 1))
        return t
    
    def get_sine_value(self):
        """ Generate sine shape signal. """        
        a = int(self.max * ((1 + math.sin(math.radians(-90 + self.v)))/2))
        s = (a, a, a)
        self.v = (self.v + self.step * 6) % 360
        return s
    
    def get_pipe_value(self):
        """ Get signal from the named pile. """        
        data = None
        try:
            data = os.read(self.pipe, self.pipe_size)
            new_left = self.get_pipe_channel(data, LEFT)
            new_right = self.get_pipe_channel(data, RIGHT)
            new_mono = self.get_mono(new_left, new_right)
            
            left = self.get_channel(self.previous_left, new_left)
            right = self.get_channel(self.previous_right, new_right)
            mono = self.get_channel(self.previous_mono, new_mono)
            
            self.previous_left = new_left
            self.previous_right = new_right
            self.previous_mono = new_mono
        except:
            pass    
        
        if not data:
            return (2.0, 2.0, 2.0)
        else:
            return (left, right, mono)
    
    def get_pipe_channel(self, data, channel):
        """ Retrieve data for particular channel """        
        ch = audioop.tomono(data, 2, channel[0], channel[1])
        ch_max = audioop.max(ch, 2)
        return int(self.max * (ch_max / self.k))
    
    def get_mono(self, left, right):
        """ Create mono signal from stereo using particular algorithm """               
        if self.mono_algorithm == MONO_ALGORITHM_MAXIMUM:
            mono = max(left, right)
        elif self.mono_algorithm == MONO_ALGORITHM_AVERAGE:
            mono = statistics.mean([left, right])
        return mono
    
    def get_channel(self, previous_value, new_value):
        """ Prepares signal value depending on the previous one and algorithm. """        
        if self.stereo_algorithm == STEREO_ALGORITHM_NEW:
            channel_value = new_value
        elif self.stereo_algorithm == STEREO_ALGORITHM_LOGARITHM:
            if previous_value == 0.0:
                channel_value = 0.0
            else:
                channel_value = 20 * math.log10(new_value/previous_value)
            if channel_value < -20:
                channel_value = -20
            if channel_value > 3:
                channel_value = 3
            channel_value = (channel_value + 20) * (100/23)
        elif self.stereo_algorithm == STEREO_ALGORITHM_AVERAGE:
            channel_value = statistics.mean([previous_value, new_value])    
        return channel_value
        
