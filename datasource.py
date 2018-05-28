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
import audioop
import time
import statistics
import logging

from queue import Queue
from random import uniform
from threading import Thread, RLock
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

PLAYER_MPD = "mpd"
PLAYER_VLC = "vlc"
PLAYER_MPLAYER = "mplayer"

LEFT = (1, 0)
RIGHT = (0, 1)

class DataSource(object):
    """ Provides methods to generate different types of audio signal. """
    
    lock = RLock()
    
    def __init__(self, c):
        """ Initializer
        
        :param c: configuration dictionary
        """
        self.config = c[DATA_SOURCE]
        self.audio_channel = Queue(maxsize=1)
        self.mono_algorithm = self.config[MONO_ALGORITHM]
        self.stereo_algorithm = self.config[STEREO_ALGORITHM]
        self.ds_type = self.config[TYPE]
        self.const = self.config[VOLUME_CONSTANT]
        self.pipe_name = self.config[PIPE_NAME]
        self.min = self.config[VOLUME_MIN]
        self.max = self.config[VOLUME_MAX]
        
        self.player = c[PLAYER]
        self.v = 0
        self.step = self.config[STEP]
        self.pipe_size = self.config[PIPE_SIZE]
        self.rng = list(range(int(self.min), int(self.max)))
        self.double_rng = self.rng
        self.double_rng.extend(range(int(self.max) - 1, int(self.min), -1))
        self.pipe = None
        if self.ds_type == SOURCE_PIPE:
            thread = Thread(target=self.open_pipe)
            thread.start()
        self.k = 32767 # for 16 bits
        self.previous_left = self.previous_right = self.previous_mono = 0.0
        self.run_flag = True
        self.polling_interval = self.config[POLLING_INTERVAL]
        self.prev_time = None
        self.data = ()        
    
    def open_pipe(self):
        try:            
            logging.debug("opening pipe...")
            self.pipe = os.open(self.pipe_name, os.O_RDONLY)
            logging.debug("pipe opened")
        except:
            logging.debug("Cannot open named pipe: " + self.pipe_name)
            os._exit(0)
    
    def start_data_source(self):
        """ Start data source thread. """ 
               
        self.run_flag = True
        thread = Thread(target=self.get_data)
        thread.start()
        
    def stop_data_source(self):
        """ Stop data source thread. """ 
               
        self.run_flag = False
    
    def get_current_data(self):
        """ Return current data """
        
        with self.lock:
            return self.data
        
    def get_current_left_channel_data(self):
        """ Return current left channel value """
        
        with self.lock:
            if self.data and self.data[0]:
                return self.data[0]
    
    def get_current_right_channel_data(self):
        """ Return current right channel value """
        
        with self.lock:
            if self.data and self.data[1]:
                return self.data[1]
        
    def get_current_mono_channel_data(self):
        """ Return current mono value """
        
        with self.lock:
            if self.data and self.data[2]:
                return self.data[2]
    
    def get_data(self):
        """ Thread method. """ 
               
        while self.run_flag:
            self.data = self.get_value()
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
        
        value = self.rng[int(self.v)]      
        s = (value, value, value)
        self.v = (self.v + self.step) % self.max
        return s
    
    def get_triangle_value(self):
        """ Generate triangle shape signal. """
        
        value = self.double_rng[self.v]       
        t = (value, value, value)
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
        left = right = mono = 1.0
        
        if self.pipe == None:
            return (left, right, mono)
        
        try:
            data = os.read(self.pipe, self.pipe_size)
            
            if self.player == PLAYER_VLC:
                new_left = new_right = self.get_pipe_channel(data, RIGHT)
            else:
                new_left = self.get_pipe_channel(data, LEFT)
                new_right = self.get_pipe_channel(data, RIGHT)
            
            new_mono = self.get_mono(new_left, new_right)
            
            left = self.get_channel(self.previous_left, new_left)
            right = self.get_channel(self.previous_right, new_right)
            mono = self.get_channel(self.previous_mono, new_mono)
            
            self.previous_left = new_left
            self.previous_right = new_right
            self.previous_mono = 0
            self.previous_mono = new_mono
        except:
            pass
        
        return (left, right, mono)
    
    def get_pipe_channel(self, data, channel):
        """ Retrieve data for particular channel """
        
        if self.player == PLAYER_MPD:
            n = self.config[ADJUSTMENT_MPD]
        elif self.player == PLAYER_VLC:
            n = self.config[ADJUSTMENT_VLC]
        elif self.player == PLAYER_MPLAYER:
            n = self.config[ADJUSTMENT_MPLAYER]
        else:
            n = 1.0
        
        ch = audioop.tomono(data, 2, channel[0], channel[1])
        mul = audioop.mul(ch, 2, n)
        ch_signal = audioop.rms(mul, 2)       
        v = int(self.max * (ch_signal / self.k))
        
        return v
    
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
        
