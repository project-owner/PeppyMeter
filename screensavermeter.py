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

class ScreensaverMeter():
    """ Parent class for all screensaver plug-ins """
    
    def __init__(self):
        """ Initializer. Sets the default update period - 1 second """ 
                           
        self.update_period = 1
        
    def get_update_period(self):
        """ Return screensaver update period """
                      
        return self.update_period
    
    def set_image(self, image):
        """ Set station image. The method can be used by plug-ins which use station logo images 
        
        :param image: station logo image
        """
        pass
    
    def set_image_folder(self, state):
        """ Set image folder. 
        
        :param: state object defining image folder
        """
        pass
    
    def set_volume(self, volume):
        """ Set volume level. The method can be used by plug-ins which use volume level 
        
        :param volume: new volume level
        """
        pass
    
    def refresh(self):
        """ Refresh the screensaver. Used for animation """
        
        pass
    
    def start(self):
        """ Start screensaver """
        
        pass
    
    def stop(self):
        """ Stop screensaver """
        
        pass