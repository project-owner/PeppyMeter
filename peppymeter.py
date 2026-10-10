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

"""启动 PeppyMeter，并按运行平台连接图形界面与音频数据源。"""

import pygame
import os
import sys
import logging

from meterutil import MeterUtil
from pygame.time import Clock
from vumeter import Vumeter
from datasource import (
    DataSource,
    SOURCE_PIPE,
    SOURCE_HTTP,
    SOURCE_LOOPBACK,
    get_platform_data_source_type,
)
from serialinterface import SerialInterface
from i2cinterface import I2CInterface
from pwminterface import PWMInterface
from httpinterface import HTTPInterface
from screensavermeter import ScreensaverMeter
from configfileparser import *
from contextmenu import MeterContextMenu

# 右键菜单允许切换到仓库中提供的四组皮肤资源。
METER_RESOLUTION_FOLDERS = ("320x240", "480x320", "800x480", "1280x400")

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
        
        # Windows 将旧 FIFO 配置连接到默认播放设备的系统回环采集。
        configured_source = self.util.meter_config[DATA_SOURCE][TYPE]
        active_source = get_platform_data_source_type(configured_source)
        if active_source != configured_source:
            logging.info("Windows 音频数据源切换为系统回环采集")
            self.util.meter_config[DATA_SOURCE][TYPE] = active_source

        self.context_menu = MeterContextMenu(
            [(folder.replace("x", " × "), folder) for folder in METER_RESOLUTION_FOLDERS],
            self.util.meter_config[RANDOM_METER_INTERVAL],
        )
        
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
        self.set_display_mode()

    def set_display_mode(self):
        """按当前皮肤分辨率和 SDL 选项设置 Pygame 窗口。"""
        info = self.util.meter_config[SCREEN_INFO]
        width = info[WIDTH]
        height = info[HEIGHT]
        depth = info[DEPTH]
        env = self.util.meter_config[SDL_ENV]

        if env[DOUBLE_BUFFER]:
            flags = pygame.DOUBLEBUF
            if env[NO_FRAME]:
                flags |= pygame.NOFRAME
            self.util.PYGAME_SCREEN = pygame.display.set_mode((width, height), flags, depth)
        elif env[NO_FRAME]:
            self.util.PYGAME_SCREEN = pygame.display.set_mode((width, height), pygame.NOFRAME)
        else:
            self.util.PYGAME_SCREEN = pygame.display.set_mode((width, height))
        self.util.meter_config[SCREEN_RECT] = pygame.Rect(0, 0, width, height)
    
    def start_interface_outputs(self):
        """ Starts writing to interfaces """

        for v in self.outputs.values():
            v.start_writing()
    
    def start(self):
        """ Start VU meter. This method called by Peppy Meter to start meter """

        pygame.event.clear()
        if self.util.meter_config[DATA_SOURCE][TYPE] in (SOURCE_PIPE, SOURCE_LOOPBACK) or self.use_vu_meter == True:
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
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                    if self.context_menu.is_open:
                        self.redraw_current_meter()
                    screen = pygame.display.get_surface()
                    self.context_menu.open_at(event.pos, screen.get_size())
                    continue
                elif self.context_menu.is_open and event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
                    was_open = self.context_menu.is_open
                    action = self.context_menu.handle_event(event)
                    if action is not None:
                        self.handle_context_menu_action(action)
                    elif was_open and not self.context_menu.is_open:
                        self.redraw_current_meter()
                    continue
                elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                    keys = pygame.key.get_pressed() 
                    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and event.key == pygame.K_c:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        self.handle_shortcut_key(event.key)
                elif event.type in exit_events and (self.util.meter_config[EXIT_ON_TOUCH] or self.util.meter_config[STOP_DISPLAY_ON_TOUCH]):
                    running = False

            areas = self.meter.run()
            if self.context_menu.is_open:
                screen = pygame.display.get_surface()
                self.context_menu.draw(
                    screen,
                    self.meter.timed_random_enabled,
                    self.util.meter_config[SCREEN_INFO][METER_FOLDER].replace("x", " × "),
                )
                pygame.display.update()
            else:
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

    def handle_context_menu_action(self, action):
        """执行右键菜单返回的动作。"""
        if isinstance(action, tuple) and action[0] == "resolution":
            self.change_resolution(action[1])
        elif action == "random_now":
            self.meter.switch_to_random_meter()
        elif action == "toggle_timed":
            self.meter.set_timed_random_enabled(not self.meter.timed_random_enabled)
            self.redraw_current_meter()
        elif action == "previous":
            self.meter.previous_manual_meter()
        elif action == "next":
            self.meter.next_manual_meter()

    def handle_shortcut_key(self, key):
        """处理方向键：上下切分辨率，左右切当前分辨率的皮肤。"""
        if key in (pygame.K_UP, pygame.K_DOWN):
            current_folder = self.util.meter_config[SCREEN_INFO][METER_FOLDER]
            try:
                current_index = METER_RESOLUTION_FOLDERS.index(current_folder)
            except ValueError:
                logging.error("Unsupported current meter resolution: %s", current_folder)
                return False
            step = 1 if key == pygame.K_UP else -1
            next_index = (current_index + step) % len(METER_RESOLUTION_FOLDERS)
            next_folder = METER_RESOLUTION_FOLDERS[next_index]
            if self.context_menu.is_open:
                self.context_menu.close()
            return self.change_resolution(next_folder)

        if key == pygame.K_LEFT:
            action = self.meter.previous_manual_meter
        elif key == pygame.K_RIGHT:
            action = self.meter.next_manual_meter
        else:
            return False

        if self.context_menu.is_open:
            self.context_menu.close()
        action()
        return True

    def redraw_current_meter(self):
        """重绘当前皮肤，清除已经关闭的菜单图层。"""
        current_meter = getattr(self.meter, "meter", None)
        if current_meter is not None:
            current_meter.start()
        pygame.display.update()

    def change_resolution(self, meter_folder):
        """重新加载分辨率对应的皮肤配置并调整窗口。"""
        if meter_folder not in METER_RESOLUTION_FOLDERS:
            logging.error("Unsupported meter resolution: %s", meter_folder)
            return False

        old_config = self.util.meter_config
        old_meter = self.meter
        old_current_image = self.current_image
        old_update_period = self.update_period
        old_folder = old_config[SCREEN_INFO][METER_FOLDER]
        if meter_folder == old_folder:
            return True

        current_meter_name = old_meter.current_meter_name
        timed_random_enabled = old_meter.timed_random_enabled

        try:
            new_config = ConfigFileParser(meter_folder=meter_folder).meter_config
            meter_names = new_config[METER_NAMES]
            if not meter_names:
                raise ValueError("No meter skins are configured for " + meter_folder)

            if timed_random_enabled:
                new_config[METER] = "random"
            elif current_meter_name in meter_names:
                new_config[METER] = current_meter_name
            else:
                new_config[METER] = meter_names[0]
            new_config[DATA_SOURCE][TYPE] = get_platform_data_source_type(
                new_config[DATA_SOURCE][TYPE]
            )
            width = new_config[SCREEN_INFO][WIDTH]
            height = new_config[SCREEN_INFO][HEIGHT]
            new_config[SCREEN_RECT] = pygame.Rect(0, 0, width, height)

            self.util.meter_config = new_config
            self.set_display_mode()
            new_meter = self.output_display(self.data_source)
            new_meter.set_timed_random_enabled(timed_random_enabled)
            old_meter.stop()
            self.meter = new_meter
            self.meter.start()
            pygame.display.update()
            return True
        except Exception as error:
            logging.exception("Cannot switch meter resolution to %s: %s", meter_folder, error)
            self.util.meter_config = old_config
            self.meter = old_meter
            self.current_image = old_current_image
            self.update_period = old_update_period
            try:
                self.set_display_mode()
                if old_meter is not None:
                    old_meter.start()
                pygame.display.update()
            except Exception:
                logging.exception("Cannot restore meter after failed resolution change")
            return False

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

    if source not in (SOURCE_PIPE, SOURCE_LOOPBACK):
        pm.data_source.start_data_source()
        
    pm.init_display()
        
    if pm.util.meter_config[OUTPUT_DISPLAY]:
        pm.start_display_output()    
