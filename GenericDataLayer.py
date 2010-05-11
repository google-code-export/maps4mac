#
#  GenericDataLayer.py
#  Maprender
#
#  Created by Daniel Sabo on 5/10/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *

import mapnik

class GenericDataset(NSObject):
    icon = objc.ivar() # NSImage used to represent the dataset
    points = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.points = list()
        
        return self
    
    

class GenericDataLayer(NSObject):
    datasets = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.datasets = list()
        
        return self
    
    def drawRect_WithProjection_(self, rect, proj):
        """Takes a projection and a rect in that projection, draws the layers contents for the rect with a transparent background"""
        
        for ds in self.datasets:
            icon = ds.icon
            
            for point in ds.points
                loc = proj.forward(mapnik.Coord(point.lon, point.lat))
                
                icon.drawAtPoint_(NSPoint(loc.y,loc.x))
