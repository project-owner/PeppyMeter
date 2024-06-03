# Copyright 2016-2024 PeppyMeter peppy.player@gmail.com
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

import pygame
import os
import sys
import logging

from meterutil import MeterUtil
from pygame.time import Clock
from vumeter import Vumeter
from datasource import DataSource, SOURCE_NOISE, SOURCE_PIPE, SOURCE_HTTP
from serialinterface import SerialInterface
from i2cinterface import I2CInterface
from pwminterface import PWMInterface
from httpinterface import HTTPInterface
from screensavermeter import ScreensaverMeter
from configfileparser import *

class Peppymeter(ScreensaverMeter):
    """ Peppy Meter class """
    
    def __init__(self, util=None, standalone=False, timer_controlled_random_meter=True, quit_pygame_on_stop=True):
        """ Initializer
        
        :param util: utility object
        :param standalone: True - standalone version, False - part of Peppy player
        """
        ScreensaverMeter.__init__(self)
        if util:
            self.util = util
        else:
            self.util = MeterUtil()
            
        self.use_vu_meter = getattr(self.util, USE_VU_METER, None)
        
        self.name = "peppymeter"
        self.quit_pygame_on_stop = quit_pygame_on_stop

        parser = ConfigFileParser()
        self.util.meter_config = parser.meter_config
        self.util.exit_function = self.exit
        self.outputs = {}
        self.timer_controlled_random_meter = timer_controlled_random_meter
        self.dependent = None
        
        if standalone:
            if self.util.meter_config[USE_LOGGING]:
                log_handlers = []
                try:
                    log_handlers.append(logging.StreamHandler(sys.stdout))
                    log_handlers.append(logging.FileHandler(filename="peppymeter.log", mode='w'))
                    logging.basicConfig(
                        level=logging.NOTSET,
                        format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                        handlers=log_handlers
                    )
                except:
                    pass
            else:
                logging.disable(logging.CRITICAL)
        
        # no VU Meter support for Windows
        if "win" in sys.platform and self.util.meter_config[DATA_SOURCE][TYPE] == SOURCE_PIPE:
            self.util.meter_config[DATA_SOURCE][TYPE] = SOURCE_NOISE
        
        self.data_source = DataSource(self.util.meter_config)
        if self.util.meter_config[DATA_SOURCE][TYPE] or self.use_vu_meter == True:
            self.data_source.start_data_source()
        
        if self.util.meter_config[OUTPUT_DISPLAY]:
            self.meter = self.output_display(self.data_source)
            
        if self.util.meter_config[OUTPUT_SERIAL]:
            self.outputs[OUTPUT_SERIAL] = SerialInterface(self.util.meter_config, self.data_source)
            
        if self.util.meter_config[OUTPUT_I2C]:
            self.outputs[OUTPUT_I2C] = I2CInterface(self.util.meter_config, self.data_source)
            
        if self.util.meter_config[OUTPUT_PWM]:
            self.outputs[OUTPUT_PWM] = PWMInterface(self.util.meter_config, self.data_source)

        if self.util.meter_config[OUTPUT_HTTP]:
            self.outputs[OUTPUT_HTTP] = HTTPInterface(self.util.meter_config, self.data_source)

        self.start_interface_outputs()
        logging.debug("PeppyMeter initialized")
    
    def output_display(self, data_source):
        """ Initialize display
        
        :data_source: data source
        :return: graphical VU Meter
        """
        meter = Vumeter(self.util, data_source, self.timer_controlled_random_meter)
        self.current_image = None
        self.update_period = meter.get_update_period()
        
        return meter
    
    def init_display(self):
        """ Initialize Pygame display """

        screen_w = self.util.meter_config[SCREEN_INFO][WIDTH]
        screen_h = self.util.meter_config[SCREEN_INFO][HEIGHT]
        depth = self.util.meter_config[SCREEN_INFO][DEPTH]
        
        os.environ["SDL_FBDEV"] = self.util.meter_config[SDL_ENV][FRAMEBUFFER_DEVICE]

        if self.util.meter_config[SDL_ENV][MOUSE_ENABLED]:
            os.environ["SDL_MOUSEDEV"] = self.util.meter_config[SDL_ENV][MOUSE_DEVICE]
            os.environ["SDL_MOUSEDRV"] = self.util.meter_config[SDL_ENV][MOUSE_DRIVER]
        else:
            os.environ["SDL_NOMOUSE"] = "1"
        
        if not self.util.meter_config[OUTPUT_DISPLAY]:
            os.environ["SDL_VIDEODRIVER"] = self.util.meter_config[SDL_ENV][VIDEO_DRIVER]
            os.environ["DISPLAY"] = self.util.meter_config[SDL_ENV][VIDEO_DISPLAY]
            pygame.display.init()
            pygame.font.init()
            if self.util.meter_config[SDL_ENV][DOUBLE_BUFFER]:
                self.util.PYGAME_SCREEN = pygame.display.set_mode((1,1), pygame.DOUBLEBUF, depth)
            else:
                self.util.PYGAME_SCREEN = pygame.display.set_mode((1,1))
            return
        
        if "win" not in sys.platform:
            if not self.util.meter_config[SDL_ENV][VIDEO_DRIVER] == "dummy":
                os.environ["SDL_VIDEODRIVER"] = self.util.meter_config[SDL_ENV][VIDEO_DRIVER]
                os.environ["DISPLAY"] = self.util.meter_config[SDL_ENV][VIDEO_DISPLAY]
            pygame.display.init()
            pygame.mouse.set_visible(False)
        else:            
            pygame.init()
            pygame.display.set_caption("Peppy Meter")

        pygame.font.init()

        if self.util.meter_config[SDL_ENV][DOUBLE_BUFFER]:
            if self.util.meter_config[SDL_ENV][NO_FRAME]:
                self.util.PYGAME_SCREEN = pygame.display.set_mode((screen_w, screen_h), pygame.DOUBLEBUF | pygame.NOFRAME, depth)
            else:
                self.util.PYGAME_SCREEN = pygame.display.set_mode((screen_w, screen_h), pygame.DOUBLEBUF, depth)
        else:
            if self.util.meter_config[SDL_ENV][NO_FRAME]:
                self.util.PYGAME_SCREEN = pygame.display.set_mode((screen_w, screen_h), pygame.NOFRAME)
            else:
                self.util.PYGAME_SCREEN = pygame.display.set_mode((screen_w, screen_h))

        self.util.meter_config[SCREEN_RECT] = pygame.Rect(0, 0, screen_w, screen_h)
    
    def start_interface_outputs(self):
        """ Starts writing to interfaces """

        for v in self.outputs.values():
            v.start_writing()
    
    def start(self):
        """ Start VU meter. This method called by Peppy Meter to start meter """

        pygame.event.clear()
        if self.util.meter_config[DATA_SOURCE][TYPE] == SOURCE_PIPE or self.use_vu_meter == True:
            self.data_source.start_data_source()
        self.meter.start()
        pygame.display.update(self.util.meter_config[SCREEN_RECT])

        for v in self.outputs.values():
            v.start_writing()

    def start_display_output(self):
        """ Start thread for graphical VU meter """
        
        pygame.event.clear()
        clock = Clock()
        self.meter.start()
        pygame.display.update(self.util.meter_config[SCREEN_RECT])
        running = True
        exit_events = [pygame.MOUSEBUTTONUP]

        if pygame.version.ver.startswith("2"):
            exit_events.append(pygame.FINGERUP)

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                    keys = pygame.key.get_pressed() 
                    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and event.key == pygame.K_c:
                        running = False
                elif event.type in exit_events and (self.util.meter_config[EXIT_ON_TOUCH] or self.util.meter_config[STOP_DISPLAY_ON_TOUCH]):
                    running = False

            areas = self.meter.run()
            pygame.display.update(areas)
            self.refresh()

            if self.dependent:
                self.dependent()

            clock.tick(self.util.meter_config[FRAME_RATE])

        if self.util.meter_config[STOP_DISPLAY_ON_TOUCH]:
            self.meter.stop()
            if self.quit_pygame_on_stop:
                pygame.quit()
        else:
            self.exit()

    def stop(self):
        """ Stop meter animation. """

        if not self.use_vu_meter:
            for v in self.outputs.values():
                v.stop_writing()

            self.data_source.stop_data_source()

        self.meter.stop()
    
    def restart(self):
        """ Restart random meter """

        self.meter.restart()

    def refresh(self):
        """ Refresh meter. Used to switch from one random meter to another. """
        
        self.meter.refresh()

    def set_volume(self, volume):
        """ Set volume level.

        :param volume: new volume level
        """
        self.data_source.volume = volume
    
    def exit(self):
        """ Exit program """
        
        for v in self.outputs.values():
            v.stop_writing()
        pygame.quit()

        if hasattr(self, "malloc_trim"):
            self.malloc_trim()

        os._exit(0)

    def set_visible(self, flag):
        """ Set visible/invisible flag.

        :param flag: True - visible, False - invisible
        """
        pass
       
if __name__ == "__main__":
    """ This is called by stand-alone PeppyMeter """

    pm = Peppymeter(standalone=True)
    source = pm.util.meter_config[DATA_SOURCE][TYPE]

    if source == SOURCE_HTTP:
        try:
            f = open(os.devnull, 'w')
            sys.stdout = sys.stderr = f
            from webserver import WebServer
            web_server = WebServer(pm)
        except Exception as e:
            logging.debug(e)

    if source != SOURCE_PIPE:
        pm.data_source.start_data_source()
        
    pm.init_display()
        
    if pm.util.meter_config[OUTPUT_DISPLAY]:
        pm.start_display_output()    
