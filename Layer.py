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
    view     = objc.ivar()
    
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
        self.view = None
        return True
        
    def setView_(self, view):
        """Set the view the layer is displayed in so it can be notified when the layer changes"""
        self.view = view
    
    def getExtent(self):
        """Return the layers extent [right, top, left, bottom]"""
        return None
    
    def getSearchProvider(self):
        """Return a search provider if this layer can be searched, otherwise None"""
        return None
        
    def getStyles(self):
        """Return a list of selectable styles, otherwise None
        A style has the format {"id":id, "name":name}
        """
        return None
    
    def setStyle_(self, styleid):
        pass
