# Copyright 2021 PeppyMeter peppy.player@gmail.com
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

import logging
import tornado.httpserver
import tornado.ioloop
import tornado.web
import asyncio

from threading import Thread, RLock
from configfileparser import HTTP_PORT
from tornado.web import Application
from tornado.httpserver import HTTPServer
from vumeterhandler import VuMeterHandler

class WebServer(object):
    """ Starts Tornado web server in a separate thread """
    
    def __init__(self, peppy_meter):
        """ Initializer. Start web server in separate thread
        
        :param peppy_meter: the reference to the root object
        """
        self.lock = RLock()
        self.peppy_meter = peppy_meter
        self.web_clients = []
        self.instance = None
        thread = Thread(target=self.start_web_server)
        thread.daemon = True        
        thread.start()
     
    def start_web_server(self):
        """ Prepare request handlers and start server """
        
        app = Application([(r"/vumeter", VuMeterHandler, {"peppy_meter": self.peppy_meter})])
        http_server = HTTPServer(app)
        port = self.peppy_meter.util.meter_config[HTTP_PORT]
        asyncio.set_event_loop(asyncio.new_event_loop())
        http_server.listen(port)
        self.instance = tornado.ioloop.IOLoop.instance()
        logging.debug("Web Server Started")
        self.instance.start()
        
    def shutdown(self):
        """ Shutdown Web Server """
        
        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.add_callback(ioloop.stop)
