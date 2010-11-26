#
#  Layer.py
#  Maprender
#
#  Created by Daniel Sabo on 11/16/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *

class Layer(NSObject):
    outline  = objc.ivar()
    name     = objc.ivar()
    description = objc.ivar()
    
    def init(self):
        self = super(Layer, self).init()
        if self is None:
            return None
        
        outline  = None
        name     = None
        description = None
        
        return self
        
    def drawRect_WithProjection_Origin_Zoom_(self, rect, proj, origin, zoom):
        pass
    
    def willDelete(self):
        """Check if the layer wants to prevent it's deletion"""
        return True
        
    def layerDeleted(self):
        """They layer has been deleted and should clean up"""
        return True
