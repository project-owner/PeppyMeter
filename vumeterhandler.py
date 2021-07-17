# Copyright 2021 Peppy Player peppy.player@gmail.com
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

import json
import logging

from tornado.web import RequestHandler

class VuMeterHandler(RequestHandler):
    def initialize(self, peppy_meter):
        self.data_source = peppy_meter.data_source

    def put(self):
        if not self.request.body:
            return

        try:
            b = self.request.body.decode("utf-8")
            d = json.loads(b)
            self.data_source.http_data = (d["left"], d["right"], d["mono"])
        except Exception as e:
            logging.debug(e)
