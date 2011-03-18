#
#  MapView.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 4/23/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from objc import YES, NO, IBAction, IBOutlet
from Foundation import *
from AppKit import *

import mapnik
import math

defaultZooms = [1,5,25,50,125,250,500,1000,2000,4000,7500]

class MapView(NSView):
    layers = objc.ivar()
    center = objc.ivar()
    projectedCenter = objc.ivar()
    zoom = objc.ivar()
    projection = objc.ivar()
    
    centerDot = objc.ivar()
    gpsFix = objc.ivar()

    def initWithFrame_(self, frame):
        self = super(MapView, self).initWithFrame_(frame)
        if self is None:
            return self
        
        self.layers = []
        self.zoom = None
        self.center = None
        
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
    
    def acceptsFirstResponder(self):
        return True
        
    def frameChanged(self):
        size = self.bounds().size
        
    #def mouseMoved_(self, event):
    #    print "Moved",event
    
    def scrollByX_Y_(self, x, y):
        if self.layers:
            # Don't try to scroll if there's nothing there
            shift = mapnik.Coord(-1 * self.zoom * x, self.zoom * y)
            #shift = self.projection.inverse(shift)
            
            newCenter = self.projectedCenter + shift
            newCenter = self.projection.inverse(newCenter)
            
            newCenter.x = max(newCenter.x, -179.999)
            newCenter.x = min(newCenter.x, 179.999)
            newCenter.y = max(newCenter.y, -89.999)
            newCenter.y = min(newCenter.y, 89.999)
            
            self.center = newCenter
            self.projectedCenter = self.projection.forward(self.center)
        
        self.setNeedsDisplay_(True)
    
    def mouseDragged_(self, event):
        self.scrollByX_Y_(event.deltaX(), event.deltaY())
    
    def scrollWheel_(self, event):
        self.scrollByX_Y_(event.deviceDeltaX(), event.deviceDeltaY())
                    
    def swipeWithEvent_(self, event):
        if self.layers:
            # Don't try to zoom if there's nothing there
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
        
        NSColor.darkGrayColor().setFill()
        NSRectFill(rect)
        
        if not self.projection or not self.center:
            return
        
        prj_center = self.projection.forward(self.center)
        prj_shift  = mapnik.Coord((rect.origin[0] - (size[0] / 2)) * self.zoom, (rect.origin[1] - (size[1] / 2)) * self.zoom)
        #prj_shift  = mapnik.Coord(0 - (size[0] / 2) * self.zoom, 0 - (size[1] / 2) * self.zoom)
        prj_origin = prj_center + prj_shift
        
        for layer in self.layers:
            #FIXME: Don't ask layers to draw things outside of the world
            extent = layer.getExtent()
            clamped_origin = mapnik.Coord(prj_origin.x,prj_origin.y)
            xform = NSAffineTransform.transform()
            if extent:
                if extent and prj_origin.x < extent[2]:
                    clamped_origin.x = extent[2]
                if extent and prj_origin.y < extent[3]:
                    clamped_origin.y = extent[3]
                offset = prj_origin - clamped_origin
                offset = offset / self.zoom
                rect.size[0] -= int(offset.x)
                rect.size[1] -= int(offset.y)
                
                xform.translateXBy_yBy_(int(-offset.x), int(-offset.y))
            #FIXME: This translate makes the passed origin line up with the passed origin
            xform.translateXBy_yBy_(rect.origin[0],rect.origin[1]) ###
            rr = NSRect((0,0),rect.size) ###
            xform.concat()
            
            #layer.drawRect_WithProjection_Origin_Zoom_(rect, self.projection, clamped_origin, self.zoom)
            layer.drawRect_WithProjection_Origin_Zoom_(rr, self.projection, clamped_origin, self.zoom)
            
            xform.invert()
            xform.concat()
            
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
        
        #layer.setCenter_([self.center.x,self.center.y])
        #layer.setZoom_(self.zoom)
        layer.setView_(self)
        
        # Get a default center if we have none, otherwise stay where the last map was centered
        #FIXME: Get the center from the map layer
        if self.center is None:
            self.setCenter_([0,0])
        if self.zoom is None:
            self.zoom = 25
        
        self.willChangeValueForKey_("layers")
        if self.layers:
            self.layers[0].layerDeleted()
            self.layers[0] = layer
        else:
            self.layers = [layer]
        self.didChangeValueForKey_("layers")
        
        self.setNeedsDisplay_(True)
    
    def addLayer_(self, layer):
        """Add a layer to the top of the layer stack"""
        
        self.willChangeValueForKey_("layers")
        layer.setView_(self)
        self.layers.append(layer)
        self.didChangeValueForKey_("layers")
        self.setNeedsDisplay_(True)
    
    def removeLayerAtIndex_(self, layerIndex):
        """Remove a layer"""
        if layerIndex >= 0 and layerIndex < len(self.layers):
            self.willChangeValueForKey_("layers")
            
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
            self.layers[-1].layerDeleted()
            del self.layers[-1]
            
        self.didChangeValueForKey_("layers")
        self.setNeedsDisplay_(True)
    
    def getLayers(self):
        """Return a list of layers being rendered, including the map layer"""
        return self.layers
    
    def setCenter_(self, point):
        point = [point[0], point[1]]
        point[0] = max(point[0], -179.999)
        point[0] = min(point[0], 179.999)
        point[1] = max(point[1], -89.999)
        point[1] = min(point[1], 89.999)
        changed = (self.center != mapnik.Coord(point[0],point[1]))
    
        self.center = mapnik.Coord(point[0],point[1])
        self.projectedCenter = self.projection.forward(self.center)
        
        
        #for layer in self.layers:
        #    layer.setCenter_([self.center.x,self.center.y])
        
        if changed:
            self.setNeedsDisplay_(True)
    
    def getProjectedEnvelope(self):
        size = self.bounds().size
        zoom = self.zoom
        prj  = self.projection
        prj_origin = mapnik.Coord(-(size[0] / 2) * zoom, -(size[1] / 2) * zoom)
        prj_size   = mapnik.Coord(size[0], size[1]) * zoom
        c0 = self.projectedCenter + prj_origin
        c1 = c0 + prj_size
        
        return mapnik.Envelope(c0.x,c0.y,c1.x,c1.y)
    
    def getWGS84Envelope(self):
        env = self.getProjectedEnvelope()
        prj = self.projection
    
        c0 = mapnik.Coord(env.minx, env.miny)
        c1 = mapnik.Coord(env.maxx, env.maxy)
        c0 = prj.inverse(c0)
        c1 = prj.inverse(c1)

        return mapnik.Envelope(c0.x,c0.y,c1.x,c1.y)
    
    def getWGS84Center(self):
        return self.center
    
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
    
    def redrawMap(self):
        self.setNeedsDisplay_(True)
    