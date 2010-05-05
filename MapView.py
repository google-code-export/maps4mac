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

import mapnik

class MapView(NSView):
    layers = objc.ivar()
    center = objc.ivar()
    centerLatLon = objc.ivar()
    zoom = objc.ivar()

    def initWithFrame_(self, frame):
        self = super(MapView, self).initWithFrame_(frame)
        if self is None:
            return self
        
        self.layers = []
        self.zoom = 1
        
        return self
    
    def awakeFromNib(self):
        self.scrolling = False
        self.projection = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
        
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, objc.selector(None, selector="frameChanged", signature="v:"), NSViewFrameDidChangeNotification, self)
    
    def acceptsFirstResponder(self):
        return True
        
    def frameChanged(self):
        size = self.bounds().size
        for layer in self.layers:
            layer.setSize_(size)
    
    def scrollWheel_(self, event):
        shift = mapnik.Coord(-1 * self.zoom * event.deviceDeltaX(), self.zoom * event.deviceDeltaY())
        shift = self.projection.inverse(shift)
        
        self.center = self.center + shift
        self.centerLatLon = self.projection.forward(self.center)
        
        for layer in self.layers:
            layer.setCenter_([self.center.x,self.center.y])
        
        self.setNeedsDisplay_(True)
                    
    def swipeWithEvent_(self, event):
        shift = mapnik.Coord((-100 * self.zoom) * event.deltaX(), (100 * self.zoom) * event.deltaY())
        shift = self.projection.inverse(shift)
        
        self.center = self.center + shift
        self.centerLatLon = self.projection.forward(self.center)
        
        for layer in self.layers:
            layer.setCenter_([self.center.x,self.center.y])
        
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        NSColor.darkGrayColor().setFill()
        NSRectFill(rect)
        
        for layer in self.layers:
            layer.drawRect_(rect)
        
    def setLayer_(self, layer):
        layer.setSize_(self.bounds().size)
        
        layer.setCenter_([self.center.x,self.center.y])
        layer.setZoom_(self.zoom)
        layer.setView_(self)
        self.layers = [layer]
        
        self.setNeedsDisplay_(True)
    
    def setCenter_(self, point):
        self.center = mapnik.Coord(point[0],point[1])
        self.centerLatLon = self.projection.forward(self.center)
        for layer in self.layers:
            layer.setCenter_([self.center.x,self.center.y])
    
    def setZoom_(self, zoom):
        self.zoom = int(zoom)
        for layer in self.layers:
            layer.setZoom_(zoom)
        