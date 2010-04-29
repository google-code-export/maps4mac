#
#  MapView.py
#  Maprender
#
#  Created by Daniel Sabo on 4/23/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from objc import YES, NO, IBAction, IBOutlet
from Foundation import *
from AppKit import *

class MapView(NSView):
    layers = objc.ivar()

    def initWithFrame_(self, frame):
        self = super(MapView, self).initWithFrame_(frame)
        if self is None:
            return self
        
        self.layers = []
        
        return self

    def drawRect_(self, rect):
        NSColor.darkGrayColor().setFill()
        NSRectFill(rect)
        
        for layer in self.layers:
            layer.drawRect_(rect)
        
    def setLayer_(self, layer):
        layer.setSize_(self.bounds().size)
        self.layers = [layer]
        
        self.setNeedsDisplay_(True)
    
    def setCenter_(self, point):
        for layer in self.layers:
            layer.setCenter_(point)
    
    def setZoom_(self, zoom):
        for layer in self.layers:
            pass
            #layer.setZoom_(point)
    