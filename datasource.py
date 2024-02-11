# Copyright 2016-2021 PeppyMeter peppy.player@gmail.com
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
import math
import time
import statistics
import logging

from random import uniform
from threading import Thread, RLock
from configfileparser import *
from collections import deque

SOURCE_CONSTANT = "constant"
SOURCE_NOISE = "noise"
SOURCE_SAW = "saw"
SOURCE_TRIANGLE = "triangle"
SOURCE_SINE = "sine"
SOURCE_PIPE = "pipe"
SOURCE_HTTP = "http"

MONO_ALGORITHM_MAXIMUM = "maximum"
MONO_ALGORITHM_AVERAGE = "average"

STEREO_ALGORITHM_NEW = "new"
STEREO_ALGORITHM_LOGARITHM = "logarithm"
STEREO_ALGORITHM_AVERAGE = "average"

class DataSource(object):
    """ Provides methods to generate different types of audio signal. """
    
    lock = RLock()
    
    def __init__(self, util):
        """ Initializer
        
        :param c: configuration dictionary
        """
        self.volume = 1
        self.config = util[DATA_SOURCE]
        self.mono_algorithm = self.config[MONO_ALGORITHM]
        self.stereo_algorithm = self.config[STEREO_ALGORITHM]
        self.ds_type = self.config[TYPE]
        self.const = self.config[VOLUME_CONSTANT]
        self.pipe_name = self.config[PIPE_NAME]
        self.min = self.config[VOLUME_MIN]
        self.max_in_ui = self.config[VOLUME_MAX]
        self.max_in_pipe = self.config[VOLUME_MAX_IN_PIPE]
        
        self.v = 0
        self.step = self.config[STEP]
        self.pipe_size = 4
        self.PIPE_BUFFER_SIZE = 1048576 # as defined for Raspberry OS in /proc/sys/fs/pipe-max-size
        self.rng = list(range(int(self.min), int(self.max_in_ui)))
        self.double_rng = self.rng
        self.double_rng.extend(range(int(self.max_in_ui) - 1, int(self.min), -1))
        self.pipe = None
        if self.ds_type == SOURCE_PIPE:
            thread = Thread(target=self.open_pipe)
            thread.start()
        self.previous_left = self.previous_right = self.previous_mono = 0.0
        self.run_flag = True
        self.polling_interval = self.config[POLLING_INTERVAL]
        self.pipe_polling_inerval = self.polling_interval / 10
        self.prev_time = None
        self.data = ()
        self.http_data = ()
        self.smooth_buffer_size = self.config[SMOOTH_BUFFER_SIZE]
        self.smooth_buffer = deque(self.smooth_buffer_size*[0], self.smooth_buffer_size)
        for _ in range(self.smooth_buffer_size):
            self.smooth_buffer.append((0,0,0))

        self.SOURCE_FUNCTIONS = {
            SOURCE_CONSTANT: self.get_constant_value,
            SOURCE_NOISE: self.get_noise_value,
            SOURCE_SAW: self.get_saw_value,
            SOURCE_TRIANGLE: self.get_triangle_value,
            SOURCE_SINE: self.get_sine_value,
            SOURCE_PIPE: self.get_pipe_value,
            SOURCE_HTTP: self.get_http_value
        }
    
    def open_pipe(self):
        """ Open named pipe """

        try:            
            logging.debug("opening pipe...")
            self.pipe = os.open(self.pipe_name, os.O_RDONLY | os.O_NONBLOCK)
            logging.debug("pipe opened")
        except:
            logging.debug("Cannot open named pipe: " + self.pipe_name)

    def flush_pipe_buffer(self):
        """ Flush data from the pipe """

        if not self.pipe:
            return

        try:
            os.read(self.pipe, self.PIPE_BUFFER_SIZE)
        except Exception as e:
            logging.debug(e)

        logging.debug("pipe flushed")

    def start_data_source(self):
        """ Start data source thread. """ 

        logging.debug("starting data source...")

        if self.ds_type == SOURCE_PIPE:
            self.flush_pipe_buffer()

        self.run_flag = True
        thread = Thread(target=self.get_data)
        thread.start()

        logging.debug("data source started")
        
    def stop_data_source(self):
        """ Stop data source thread. """ 
               
        self.run_flag = False
    
    def get_current_data(self):
        """ Return current data """
        
        return self.data
        
    def get_current_left_channel_data(self):
        """ Return current left channel value """
        
        if self.data and self.data[0]:
            return self.data[0]
        else:
            return None
    
    def get_current_right_channel_data(self):
        """ Return current right channel value """
        
        if self.data and self.data[1]:
            return self.data[1]
        else:
            return None
        
    def get_current_mono_channel_data(self):
        """ Return current mono value """

        if self.data and self.data[2]:
            return self.data[2]
        else:
            return None
    
    def get_data(self):
        """ Thread method. """ 
               
        while self.run_flag:
            with self.lock:
                self.data = self.get_value()
            time.sleep(self.polling_interval)
    
    def get_value(self):
        """ Get data depending on the data source type. """ 
               
        return self.SOURCE_FUNCTIONS[self.ds_type]()
    
    def get_constant_value(self):
        """ Returns constant value for all channels. The value is defined in the configuration file. """ 
               
        return (self.const, self.const, self.const)
    
    def get_noise_value(self):
        """ Generate random value for all channels. """
        
        new_left = uniform(self.min, self.max_in_ui)
        new_right = uniform(self.min, self.max_in_ui)            
        new_mono = self.get_mono(new_left, new_right)
        
        left = self.get_channel(self.previous_left, new_left)
        right = self.get_channel(self.previous_right, new_right)
        mono = self.get_channel(self.previous_mono, new_mono)

        if self.smooth_buffer_size:
            self.smooth_buffer.append((left, right, mono))
            left = self.get_smooth_value(0)
            right = self.get_smooth_value(1)
            mono = self.get_smooth_value(2)
        
        self.previous_left = new_left
        self.previous_right = new_right
        self.previous_mono = new_mono

        return (left, right, mono)
    
    def get_smooth_value(self, index):
        """ Get smooth value

        :param index: channel index
        :return: smooth value calculated using buffer
        """
        s = 0
        for n in range(self.smooth_buffer_size):
            s += self.smooth_buffer[n][index]
        return s / self.smooth_buffer_size

    def get_saw_value(self):
        """ Generate saw shape signal. """ 
        
        value = self.rng[int(self.v)]      
        s = (value, value, value)
        self.v = (self.v + self.step) % self.max_in_ui
        return s
    
    def get_triangle_value(self):
        """ Generate triangle shape signal. """
        
        value = self.double_rng[self.v]
        t = (value, value, value)
        self.v = (self.v + self.step) % (int(self.max_in_ui * 2 - 1))
        return t
    
    def get_sine_value(self):
        """ Generate sine shape signal. """ 
               
        a = int(self.max_in_ui * ((1 + math.sin(math.radians(-90 + self.v)))/2))
        s = (a, a, a)
        self.v = (self.v + self.step * 6) % 360
        return s

    def get_latest_pipe_data(self):
        """ Read from the named pipe until it's empty """

        latest_data = [0, 0, 0, 0]
        data = None

        while True:
            try:
                data = os.read(self.pipe, self.pipe_size)
                if len(data) != 0:
                    latest_data = [data[0], data[1], data[2], data[3]]
                time.sleep(self.pipe_polling_inerval)
            except:
                break

        return latest_data

    def get_http_value(self):
        """ Fetch HTTP value """

        with self.lock:
            return self.http_data

    def get_pipe_value(self):
        """ Get signal from the named pipe. """

        data = None
        left = right = mono = 0.0
        volume_level = self.volume
        if volume_level == 0:
            volume_level = 1

        if self.pipe == None:
            return (left, right, mono)

        try:
            data = self.get_latest_pipe_data()
            length = len(data) 
            if length == 0:
                return (0, 0, 0)
            
            new_left = int(self.max_in_ui * ((data[length - 4] + (data[length - 3] << 8)) / self.max_in_pipe))
            new_right = int(self.max_in_ui * ((data[length - 2] + (data[length - 1] << 8)) / self.max_in_pipe))
            new_mono = self.get_mono(new_left, new_right)
            
            left = self.get_channel(self.previous_left, new_left)
            right = self.get_channel(self.previous_right, new_right)
            mono = self.get_channel(self.previous_mono, new_mono)

            if self.smooth_buffer_size:
                self.smooth_buffer.append((left, right, mono))
                left = self.get_smooth_value(0)
                right = self.get_smooth_value(1)
                mono = self.get_smooth_value(2)
            
            self.previous_left = left
            self.previous_right = right
            self.previous_mono = mono
        except Exception as e:
            logging.debug(e)
        
        return (self.previous_left, self.previous_right, self.previous_mono)
    
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
