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
    
    def awakeFromNib(self):
        self.center = [0,0]
        self.zoom = 1

    def drawRect_(self, rect):
        NSColor.darkGrayColor().setFill()
        NSRectFill(rect)
        
        for layer in self.layers:
            layer.drawRect_(rect)
        
    def setLayer_(self, layer):
        layer.setSize_(self.bounds().size)
        
        layer.setCenter_(self.center)
        layer.setZoom_(self.zoom)
        self.layers = [layer]
        
        self.setNeedsDisplay_(True)
    
    def setCenter_(self, point):
        self.center = point
        for layer in self.layers:
            layer.setCenter_(point)
    
    def setZoom_(self, zoom):
        self.zoom = zoom
        for layer in self.layers:
            layer.setZoom_(zoom)
    