#
#  MapLayer.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 11/16/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
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
    
    def getDefaultCenter(self):
        """Return a default center point as [lat,lon]"""
        return [0.0,0.0]
    
    def getDefaultZoom(self):
        """Return a default zoom (pixels per projected unit)"""
        return 25
        
    def getZoomList(self):
        """Return the default zoom levels for this layer"""
        return [1,5,25,50,125,250,500,1000,2000,4000,7500]