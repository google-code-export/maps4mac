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

defaultZooms = [1,5,25,50,125,250,500,1000,2000,4000,7500]

class MapView(NSView):
    layers = objc.ivar()
    center = objc.ivar()
    centerLonLat = objc.ivar()
    zoom = objc.ivar()
    projection = objc.ivar()
    
    centerDot = objc.ivar()
    gpsFix = objc.ivar()

    def initWithFrame_(self, frame):
        self = super(MapView, self).initWithFrame_(frame)
        if self is None:
            return self
        
        self.layers = []
        self.zoom = 25
        
        self.centerDot = False
        self.gpsFix = None
        self.projection = None
        
        return self
    
    def awakeFromNib(self):
        self.scrolling = False
        self.projection = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
        
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, objc.selector(None, selector="frameChanged", signature="v:"), NSViewFrameDidChangeNotification, self)
    
    def isOpaque(self):
        return True
    
#    def acceptsFirstResponder(self):
#        return True
        
    def frameChanged(self):
        size = self.bounds().size
        for layer in self.layers:
            layer.setSize_(size)
    
    def scrollWheel_(self, event):
        shift = mapnik.Coord(-1 * self.zoom * event.deviceDeltaX(), self.zoom * event.deviceDeltaY())
        shift = self.projection.inverse(shift)
        
        self.center = self.center + shift
        self.centerLonLat = self.projection.forward(self.center)
        
        #for layer in self.layers:
        #    layer.setCenter_([self.center.x,self.center.y])
        
        self.setNeedsDisplay_(True)
                    
    def swipeWithEvent_(self, event):
        #shift = mapnik.Coord((-100 * self.zoom) * event.deltaX(), (100 * self.zoom) * event.deltaY())
        #shift = self.projection.inverse(shift)
        
        #self.center = self.center + shift
        #self.centerLonLat = self.projection.forward(self.center)
        
        #for layer in self.layers:
        #    layer.setCenter_([self.center.x,self.center.y])
        
        if event.deltaY() > 0:
            if self.zoom >= defaultZooms[-1]:
                self.zoom = int(self.zoom * 2)
            else:
                zoomIndex = 0
                while defaultZooms[zoomIndex] <= self.zoom:
                    zoomIndex += 1
                self.zoom = defaultZooms[zoomIndex]
                
        elif event.deltaY() < 0:
            if int(self.zoom / 2) >= defaultZooms[-1]:
                self.zoom = int(self.zoom / 2)
            else:
                zoomIndex = len(defaultZooms) - 1
                while defaultZooms[zoomIndex] >= self.zoom and zoomIndex > 0:
                    zoomIndex -= 1
                self.zoom = defaultZooms[zoomIndex]
        
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        size = self.bounds().size
        
        prj_center = self.projection.forward(self.center)
        prj_shift  = mapnik.Coord(rect.origin[0] - (size[0] / 2) * self.zoom, rect.origin[1] - (size[1] / 2) * self.zoom)
        prj_origin = prj_center + prj_shift
    
        NSColor.darkGrayColor().setFill()
        NSRectFill(rect)
        
        for layer in self.layers:
            layer.drawRect_WithProjection_Origin_Zoom_(rect, self.projection, prj_origin, self.zoom)
            
        if self.centerDot:
            center = [0,0]
            center[0] = self.bounds().origin.x + (self.bounds().size.width / 2)
            center[1] = self.bounds().origin.y + (self.bounds().size.height / 2)
            
            color = NSColor.colorWithDeviceRed_green_blue_alpha_(0.0, 0.0, 0.5, 0.8)
            color.setFill()
            rect = NSRect((0,0), (10,10))
            path = NSBezierPath.bezierPathWithOvalInRect_(rect)
            
            xform = NSAffineTransform.transform()
            xform.translateXBy_yBy_(center[0] - rect.size[0] / 2.0, center[1] - rect.size[1] / 2.0)
            xform.concat()
            path.fill()
            xform.invert()
            xform.concat()
        
        if self.gpsFix is not None:
            prj_gps = self.projection.forward(self.gpsFix)
            rect = self.bounds()
            prj_center = self.projection.forward(self.center)
            shift = (prj_gps - prj_center) / self.zoom

            center = [0,0]
            center[0] = self.bounds().origin.x + (self.bounds().size.width / 2)
            center[1] = self.bounds().origin.y + (self.bounds().size.height / 2)
            
            center[0] += shift.x
            center[1] += shift.y
            
            color = NSColor.colorWithDeviceRed_green_blue_alpha_(0.5, 0.0, 0.0, 0.8)
            color.setFill()
            rect = NSRect((0,0), (10,10))
            path = NSBezierPath.bezierPathWithOvalInRect_(rect)
            
            xform = NSAffineTransform.transform()
            xform.translateXBy_yBy_(center[0] - rect.size[0] / 2.0, center[1] - rect.size[1] / 2.0)
            xform.concat()
            path.fill()
            xform.invert()
            xform.concat()
    
    def setMapLayer_(self, layer):
        """Set the base map layer for this view, which will define the projection"""
        #layer.setSize_(self.bounds().size)
        
        #layer.setCenter_([self.center.x,self.center.y])
        #layer.setZoom_(self.zoom)
        layer.setView_(self)
        
        self.willChangeValueForKey_("layers")
        if self.layers and hasattr(self.layers[0], "layerDeleted"):
            self.layers[0].layerDeleted()
            self.layers[0] = layer
        else:
            self.layers = [layer]
        
        self.didChangeValueForKey_("layers")
        self.setNeedsDisplay_(True)
    
    def addLayer_(self, layer):
        """Add a layer to the top of the layer stack"""
        
        self.willChangeValueForKey_("layers")
        self.layers.append(layer)
        self.didChangeValueForKey_("layers")
        self.setNeedsDisplay_(True)
    
    def removeLayerAtIndex_(self, layerIndex):
        """Remove a layer"""
        if layerIndex >= 0 and layerIndex < len(self.layers):
            self.willChangeValueForKey_("layers")
            if hasattr(self.layers[layerIndex], "layerDeleted"):
                self.layers[layerIndex].layerDeleted()
            del self.layers[layerIndex]
            self.didChangeValueForKey_("layers")
            self.setNeedsDisplay_(True)
    
    def removeLayerByObject_(self, layer):
        """Remove a layer"""
        try:
            index = self.layers.index(layer)
            self.removeLayerAtIndex_(index)
        except ValueError:
            # No such object
            print "Object: %s is not a layer", str(layer)
            
    
    def clearLayers(self):
        """Remove all layers except the base"""
        self.willChangeValueForKey_("layers")
        while len(self.layers) > 1:
            if hasattr(self.layers[-1], "layerDeleted"):
                self.layers[-1].layerDeleted()
            del self.layers[-1]
            
        self.didChangeValueForKey_("layers")
        self.setNeedsDisplay_(True)
    
    def getLayers(self):
        """Return a list of layers being rendered, including the map layer"""
        return self.layers
    
    def setCenter_(self, point):
        changed = (self.center != mapnik.Coord(point[0],point[1]))
    
        self.center = mapnik.Coord(point[0],point[1])
        self.centerLonLat = self.projection.forward(self.center)
        
        
        #for layer in self.layers:
        #    layer.setCenter_([self.center.x,self.center.y])
        
        if changed:
            self.setNeedsDisplay_(True)
    
    def setZoom_(self, zoom):
        self.zoom = int(zoom)
        #for layer in self.layers:
        #    layer.setZoom_(zoom)
    
    def setFixLat_Lon_CenterOnGPS_(self, lat, lon, center_map_on_gps):
        self.gpsFix = mapnik.Coord(lon, lat)
        
        if center_map_on_gps:
            self.setCenter_((lon, lat))
        else:
            #FIXME: We only need to redisplay the GPS dot
            self.setNeedsDisplay_(True)
    
    def clearFix(self):
        self.gpsFix = None
        self.setNeedsDisplay_(True)
    
    