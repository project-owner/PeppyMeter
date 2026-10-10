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

"""提供 PeppyMeter 的模拟、FIFO、HTTP 和 Windows 系统音频数据源。"""

import os
import math
import time
import statistics
import logging
import sys

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
SOURCE_LOOPBACK = "loopback"


def get_platform_data_source_type(source_type, platform_name=None):
    """返回当前平台应使用的数据源类型。"""
    platform_name = platform_name or sys.platform
    if platform_name.startswith("win") and source_type == SOURCE_PIPE:
        return SOURCE_LOOPBACK
    return source_type

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
        try:
            self.gain_db = float(self.config.get(VOLUME_GAIN_DB, 0.0))
        except Exception:
            self.gain_db = 0.0
        self.gain_mult = 10.0 ** (self.gain_db / 20.0)
        self.gain_source = self.config.get(VOLUME_GAIN_DB_SOURCE, "")
        
        self.v = 0
        self.step = self.config[STEP]
        self.pipe_size = 4
        self.PIPE_BUFFER_SIZE = 1048576 # as defined for Raspberry OS in /proc/sys/fs/pipe-max-size
        self.rng = list(range(int(self.min), int(self.max_in_ui)))
        self.double_rng = self.rng
        self.double_rng.extend(range(int(self.max_in_ui) - 1, int(self.min), -1))
        self.pipe = None
        self.loopback_sample_rate = 48000
        if self.ds_type == SOURCE_PIPE:
            thread = Thread(target=self.open_pipe, daemon=True)
            thread.start()
        self.previous_left = self.previous_right = self.previous_mono = 0.0
        self.run_flag = True
        self.data_thread = None
        self.polling_interval = self.config[POLLING_INTERVAL]
        self.loopback_frame_count = max(1, int(self.loopback_sample_rate * self.polling_interval))
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
            SOURCE_HTTP: self.get_http_value,
            SOURCE_LOOPBACK: self.get_loopback_value
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

        # 回环设备只能由一个录音线程持有，避免重复启动争用 WASAPI。
        if self.ds_type == SOURCE_LOOPBACK and self.data_thread is not None:
            if self.data_thread.is_alive():
                if self.run_flag:
                    return
                self.data_thread.join(timeout=max(self.polling_interval * 2, 0.1))
                if self.data_thread.is_alive():
                    self.run_flag = True
                    return

        if self.ds_type == SOURCE_PIPE:
            self.flush_pipe_buffer()

        self.run_flag = True
        self.data_thread = Thread(target=self.get_data, daemon=True)
        self.data_thread.start()

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
        if self.ds_type == SOURCE_LOOPBACK:
            self.get_loopback_data()
            return

        while self.run_flag:
            with self.lock:
                self.data = self.get_value()
            time.sleep(self.polling_interval)

    def create_loopback_recorder(self):
        """创建连接到 Windows 默认播放设备的双声道回环录音器。"""
        try:
            import soundcard
        except ImportError as error:
            raise RuntimeError(
                "缺少 soundcard 依赖，请运行 python -m pip install soundcard"
            ) from error

        speaker = soundcard.default_speaker()
        microphone = soundcard.get_microphone(
            id=str(speaker.name), include_loopback=True
        )
        return microphone.recorder(
            samplerate=self.loopback_sample_rate,
            channels=2,
            blocksize=max(256, self.loopback_frame_count),
        )

    def get_loopback_data(self):
        """持续采集系统播放音频；后端不可用时保留静音并记录原因。"""
        try:
            recorder = self.create_loopback_recorder()
            with recorder as active_recorder:
                while self.run_flag:
                    samples = active_recorder.record(numframes=self.loopback_frame_count)
                    with self.lock:
                        self.data = self.get_loopback_value(samples)
        except ImportError as error:
            self.data = (0, 0, 0)
            self.run_flag = False
            logging.error("Windows 系统音频采集依赖不可用：%s", error)
        except Exception as error:
            self.data = (0, 0, 0)
            self.run_flag = False
            logging.error("Windows WASAPI 回环采集失败，请检查默认播放设备：%s", error)

    def get_loopback_value(self, samples=None):
        """将双声道浮点采样的 RMS 电平转换为现有 VU 表量程。"""
        left_rms = self.get_loopback_channel_rms(samples, 0)
        right_rms = self.get_loopback_channel_rms(samples, 1)
        gain = self.gain_mult * self.get_gain_source_mult()
        new_left = self.get_loopback_level(left_rms * gain)
        new_right = self.get_loopback_level(right_rms * gain)
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
        return (left, right, mono)

    def get_loopback_channel_rms(self, samples, channel):
        """计算一个声道的 RMS；兼容单声道及空采样块。"""
        if samples is None:
            return 0.0
        try:
            if len(samples) == 0:
                return 0.0
            first_frame = samples[0]
            if hasattr(first_frame, "__len__"):
                channel_count = len(first_frame)
                if channel_count == 0:
                    return 0.0
                values = [float(frame[min(channel, channel_count - 1)]) for frame in samples]
            else:
                values = [float(value) for value in samples]
            mean_square = sum(value * value for value in values) / len(values)
            return math.sqrt(mean_square)
        except (TypeError, ValueError, ZeroDivisionError, IndexError):
            return 0.0

    def get_loopback_level(self, rms):
        """将 -60 至 0 dBFS 映射到配置中的 VU 表数值区间。"""
        if not math.isfinite(rms) or rms <= 0:
            return self.min
        dbfs = 20.0 * math.log10(rms)
        fraction = max(0.0, min(1.0, (dbfs + 60.0) / 60.0))
        return self.min + fraction * (self.max_in_ui - self.min)
    
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
                if len(data) == 0:
                    # End of file: no process holds the pipe open for writing.
                    # Return what was read so far instead of looping until
                    # a writer appears.
                    break
                latest_data = [data[0], data[1], data[2], data[3]]
                time.sleep(self.pipe_polling_inerval)
            except:
                break

        return latest_data

    def get_http_value(self):
        """ Fetch HTTP value """

        with self.lock:
            return self.http_data

    def get_gain_source_mult(self):
        """ Read a live gain value in dB from the configured source file.

        Returns a linear multiplier (10**(dB/20)), or 1.0 (unity) when no
        source is configured or the file is missing/empty/unreadable.
        """
        if not self.gain_source:
            return 1.0
        try:
            with open(self.gain_source) as f:
                return 10.0 ** (float(f.read().strip()) / 20.0)
        except Exception:
            return 1.0

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
            
            gain = self.gain_mult * self.get_gain_source_mult()
            new_left = int(self.max_in_ui * ((data[length - 4] + (data[length - 3] << 8)) / self.max_in_pipe) * gain)
            new_right = int(self.max_in_ui * ((data[length - 2] + (data[length - 1] << 8)) / self.max_in_pipe) * gain)
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
