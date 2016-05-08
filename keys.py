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

import pygame

LABELS = "labels"
CURRENT = "current"
LANGUAGE= "language"
ICON_SIZE_FOLDER = "icon.size.folder"
FONT_KEY = "font.name"
COLORS = "colors"
COLOR_DARK = "color.dark"
KEY_SCREENSAVER = "screensaver"
KEY_SCREENSAVER_DELAY = "screensaver.delay"
KEY_SCREENSAVER_DELAY_1 = "delay.1"
KEY_SCREENSAVER_DELAY_3 = "delay.3"
KEY_SCREENSAVER_DELAY_OFF = "delay.off"
SCREEN_INFO = "screen.info"
PYGAME_SCREEN = "pygame.screen"
WIDTH = "width"
HEIGHT = "height"
DEPTH = "depth"
FRAME_RATE = "frame.rate"
SCREEN_RECT = "screen.rect"
COLOR_WEB_BGR = "color.web.bgr" 
COLOR_MEDIUM = "color.medium"
COLOR_BRIGHT = "color.bright"
COLOR_CONTRAST = "color.contrast"
COLOR_LOGO = "color.logo"
LINUX_PLATFORM = "linux.platform"
H_ALIGN_LEFT = 0
H_ALIGN_CENTER = 1
H_ALIGN_RIGHT = 2
V_ALIGN_TOP = 3
V_ALIGN_CENTER = 4
V_ALIGN_BOTTOM = 5
STATION = "station"
PREVIOUS = "previous"
PLAYLIST = "playlist"
VOLUME = "volume"
ORDER_GENRE_MENU = "order.genre.menu"
ORDER_HOME_MENU = "order.home.menu"
ORDER_LANGUAGE_MENU = "order.language.menu"
ORDER_SCREENSAVER_MENU = "order.screensaver.menu"
ORDER_SCREENSAVER_DELAY_MENU = "order.screensaver.delay.menu"
MODE = "mode"
GENRE = "genre"
NAME= "name"
WEB_SERVER = "web.server"
HTTP_PORT = "http.port"

USER_EVENT_TYPE = pygame.USEREVENT + 1
SUB_TYPE_KEYBOARD = 0
KEY_SUB_TYPE = "sub_type"
KEY_ACTION = "action"
KEY_KEYBOARD_KEY = "keyboard_key"
KEY_LIRC_CODE = "lirc_code"
KEY_VOLUME_UP = "volume-up"
KEY_VOLUME_DOWN = "volume-down"
KEY_MUTE = "mute"
KEY_LEFT = "left"
KEY_RIGHT = "right"
KEY_UP = "up"
KEY_DOWN = "down"
KEY_PAGE_UP = "page-up"
KEY_PAGE_DOWN = "page-down"
KEY_SELECT = "select"
KEY_END = "end"
KEY_HOME = "home"
KEY_PLAY_PAUSE = "play-pause"
KEY_MENU = "menu"
KEY_BACK = "back"

kbd_keys = {KEY_MENU : pygame.K_m,
            KEY_END : pygame.K_END,
            KEY_HOME : pygame.K_HOME,
            KEY_PLAY_PAUSE : pygame.K_SPACE,
            KEY_SELECT : pygame.K_RETURN,
            KEY_LEFT : pygame.K_LEFT,
            KEY_RIGHT : pygame.K_RIGHT,
            KEY_UP : pygame.K_UP,
            KEY_DOWN : pygame.K_DOWN,
            KEY_PAGE_UP : pygame.K_PAGEUP,
            KEY_PAGE_DOWN : pygame.K_PAGEDOWN,
            KEY_VOLUME_UP : pygame.K_KP_PLUS,
            KEY_VOLUME_DOWN : pygame.K_KP_MINUS,
            KEY_MUTE : pygame.K_x,
            KEY_BACK: pygame.K_ESCAPE}
