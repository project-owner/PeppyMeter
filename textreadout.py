# Copyright 2016-2022 PeppyMeter peppy.player@gmail.com
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
import pygame

from configfileparser import *

class TextReadout(object):
    """ Text readout (volume.text or text): the value read from its source file, drawn over the meter background,
    one line per newline in the value """

    def __init__(self, meter, data_source, readout):
        """ Initializer

        :param meter: meter owning the background/foreground and the screen
        :param data_source: data source providing get_text_value()
        :param readout: key prefix, volume.text or text
        """
        self.meter = meter
        self.data_source = data_source
        self.readout = readout
        self.screen = meter.util.PYGAME_SCREEN
        options = meter.meter_parameters[readout]
        self.center = (options[TEXT_CENTER_X] + meter.meter_x, options[TEXT_CENTER_Y] + meter.meter_y)
        self.color = options[TEXT_COLOR]
        self.max_width = options[TEXT_MAX_WIDTH]
        self.format = options[TEXT_FORMAT]
        self.format_text = options[TEXT_FORMAT_TEXT]
        font = options[TEXT_FONT]
        if font and not os.path.isabs(font):
            font = os.path.join(meter.meter_config[BASE_PATH], meter.meter_config[SCREEN_INFO][METER_FOLDER], font)
        try:
            self.font = pygame.font.Font(font or None, options[TEXT_FONT_SIZE])
        except Exception:
            self.font = pygame.font.Font(None, options[TEXT_FONT_SIZE])
        self.value = None
        self.rect = None

    def get_text(self, value):
        """ Format the source value: numbers with format when it is set, anything else with format.text """

        if value is None:
            return ""
        if self.format:
            try:
                return self.format.format(float(value))
            except Exception:
                pass
        try:
            return self.format_text.format(value)
        except Exception:
            return value

    def fit(self, text):
        """ Cut the text with an ellipsis when it is wider than max.width """

        if not self.max_width or self.font.size(text)[0] <= self.max_width:
            return text
        while text and self.font.size(text + "\u2026")[0] > self.max_width:
            text = text[:-1]
        return text.rstrip() + "\u2026"

    def run(self, areas, force=False):
        """ Redraw the readout when its value changed or an update overwrote it

        :param areas: rectangles updated during this frame
        :param force: redraw unconditionally
        :return: rectangle to update, or None
        """
        value = self.data_source.get_text_value(self.readout)
        overwritten = self.rect and any(r and self.rect.colliderect(r) for r in areas)
        if not force and value == self.value and not overwritten:
            return None
        self.value = value

        # One line per newline in the value, stacked and centered as a block
        lines = [self.font.render(self.fit(line), True, self.color) for line in self.get_text(value).split("\n")]
        line_size = self.font.get_linesize()
        width = max(line.get_width() for line in lines)
        height = line_size * (len(lines) - 1) + lines[-1].get_height()
        rect = pygame.Rect(0, 0, width, height)
        rect.center = self.center
        area = rect.union(self.rect) if self.rect else rect.copy()
        self.meter.draw_bgr_fgr(area, self.meter.bgr)
        for i, line in enumerate(lines):
            self.screen.blit(line, line.get_rect(centerx=rect.centerx, top=rect.top + i * line_size))
        if self.meter.fgr:
            self.meter.draw_bgr_fgr(area, self.meter.fgr)
        self.rect = rect
        return area
