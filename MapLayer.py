#
#  MapLayer.py
#  Maprender
#
#  Created by Daniel Sabo on 11/16/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
import Layer

class MapLayer(Layer.Layer):
    projectionString = objc.ivar()
    
    def init(self):
        self = super(MapLayer, self).init()
        if self is None:
            return None
        
        self.projectionString = None
        
        return self
