# Copyright 2021 PeppyMeter peppy.player@gmail.com
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

import time
import requests

from threading import Thread
from configfileparser import HTTP_INTERFACE, TARGET_URL, UPDATE_PERIOD

class HTTPInterface(object):
    """ HTTP interface class. Send VU Meter data to the provided URL using PUT.
    The JSON payload:
    {
        left: 12,
        right: 14,
        mono: 13
    }
    The values change in range 0-100
    """

    def __init__(self, config, data_source):
        """ Initializer """

        self.data_source = data_source
        self.url = config[HTTP_INTERFACE][TARGET_URL]
        self.update_period = config[HTTP_INTERFACE][UPDATE_PERIOD]

    def start_writing(self):
        """ Start writing thread """

        self.running = True
        thread = Thread(target = self.write_data)
        thread.start()

    def write_data(self):
        """ Method of the writing thread """

        while self.running:
            v = self.data_source.get_current_data()
            if v:
                d = {"left": v[0], "right": v[1], "mono": v[2]}
                try:
                    requests.put(self.url, json=d)
                except:
                    pass
            time.sleep(self.update_period)

    def stop_writing(self):
        """ Stop writing thread """

        self.running = False
        time.sleep(self.update_period)
