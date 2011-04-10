#
#  MapView.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 4/23/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

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
    hdop  = objc.ivar()

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
        pass
        #size = self.bounds().size
        
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
        
        prj_shift  = mapnik.Coord((rect.origin[0] - (size[0] / 2)) * self.zoom, (rect.origin[1] - (size[1] / 2)) * self.zoom)
        #prj_shift  = mapnik.Coord(0 - (size[0] / 2) * self.zoom, 0 - (size[1] / 2) * self.zoom)
        prj_origin = self.projectedCenter + prj_shift
        
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
            
            gps_dot_width = 0
            center_dot_width = 10
            
            if self.hdop:
                # Degree offset for HDOP = (360 * HDOP * UERE) / (earth circumference in meters)
                # UERE Values:
                # Non-DGPS: 8m @ 66% confidence, 15m @ 95% confidence
                # DGPS: 2m @ 66% confidence, 4m @ 95% confidence
                hdop_deg = 360 * (self.hdop * 15) / (2 * 6370986 *  math.pi)
                
                hdop_bound = mapnik.Coord(self.center.x + hdop_deg, self.center.y)
                if hdop_bound.x > 180:
                    hdop_bound = mapnik.Coord(self.center.x - hdop_deg, self.center.y)
                    
                prj_hdop = self.projection.forward(hdop_bound)
                gps_dot_width = abs(self.projectedCenter.x - prj_hdop.x) * 2
                
                gps_dot_width = gps_dot_width / self.zoom
            
            # Give extra preference to the HDOP circle when it's big enough to replace the default dot
            if gps_dot_width > 10:
                center_dot_width = 5
            
            shift = (prj_gps - self.projectedCenter) / self.zoom

            center = [0,0]
            center[0] = self.bounds().origin.x + (self.bounds().size.width / 2)
            center[1] = self.bounds().origin.y + (self.bounds().size.height / 2)
            
            center[0] += shift.x
            center[1] += shift.y
            
            
            # If the HDOP circle would be smaller than our center dot, don't bother drawing it
            if self.hdop and center_dot_width < gps_dot_width:
                
                strokeColor = NSColor.colorWithDeviceRed_green_blue_alpha_(0.5, 0.0, 0.0, 0.8)
                strokeColor.setStroke()
                fillColor = NSColor.colorWithDeviceRed_green_blue_alpha_(0.5, 0.0, 0.0, 0.3)
                fillColor.setFill()
                
                rect = NSRect((0,0), (gps_dot_width, gps_dot_width))
                
                xform = NSAffineTransform.transform()
                xform.translateXBy_yBy_(center[0] - rect.size[0] / 2.0, center[1] - rect.size[1] / 2.0)
                xform.concat()
                
                path = NSBezierPath.bezierPathWithOvalInRect_(rect)
                path.setLineWidth_(2.0)
                path.fill()
                path.stroke()
                
                xform.invert()
                xform.concat()
            
            color = NSColor.colorWithDeviceRed_green_blue_alpha_(0.5, 0.0, 0.0, 0.8)
            color.setFill()
            
            rect = NSRect((0,0), (center_dot_width, center_dot_width))
            
            xform = NSAffineTransform.transform()
            xform.translateXBy_yBy_(center[0] - rect.size[0] / 2.0, center[1] - rect.size[1] / 2.0)
            xform.concat()
                
            path = NSBezierPath.bezierPathWithOvalInRect_(rect)
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
    
    def setFix_CenterOnGPS_(self, fix, center_map_on_gps):
        lon, lat = fix["Longitude"], fix["Latitude"]
        if "HDOP" in fix:
            self.hdop = fix["HDOP"]
        else:
            self.hdop = None
        
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
    