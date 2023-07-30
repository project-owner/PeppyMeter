# Copyright 2016-2023 PeppyMeter peppy.player@gmail.com
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

class MaskFactory(object):
    """ Factory to prepare masks for linear animator """
    
    def __init__(self):
        """ Initializer """ 
               
        pass
    
    def create_masks(self, positions_regular, positions_overload, step_width_regular, step_width_overload):
        """ Create linear animator masks
        
        :param positions_regular: number of regular steps
        :param positions_overload: number of overload steps
        :param step_width_regular: the width in pixels of the regular step
        :param step_width_overload: the width in pixels of the overload step
        """
        masks = [0]
             
        for n in range(1, positions_regular + 1):
            masks.append(n * step_width_regular)
        for n in range(1, positions_overload + 1):
            masks.append(positions_regular * step_width_regular + n * step_width_overload)
        
        return masks
