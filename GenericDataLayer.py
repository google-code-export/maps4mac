#
#  GenericDataLayer.py
#  Maprender
#
#  Created by Daniel Sabo on 5/10/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
from AppKit import *

import mapnik

class GenericDataset(NSObject):
    icon = objc.ivar() # NSImage used to represent the dataset
    icon_hotspot = objc.ivar() # Where to center the image
    points = objc.ivar()
    tracks = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.points = list()
        self.tracks = list()
        path = NSBundle.mainBundle().pathForResource_ofType_("target0", "png")
        self.icon = NSImage.alloc().initByReferencingFile_(path)
        size = self.icon.size()
        self.icon_hotspot = NSPoint(size.width / 2, size.height / 2)
        
        return self
    
    

class GenericDataLayer(NSObject):
    datasets = objc.ivar()
    cache    = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.datasets = list()
        self.name = "Untitled"
        self.cache = None
        
        return self
    
    def drawRect_WithProjection_Origin_Zoom_(self, rect, proj, origin, zoom):
        """Takes a projection and a rect in that projection, draws the layers contents for the rect with a transparent background"""
        
        # FIXME: Cache projections
        if not self.cache:
            self.cache = dict()
            self.cache["proj"] = None
            self.cache["zoom"] = None
        
        if self.cache["proj"] != proj or self.cache["zoom"] != zoom:
            self.cache = dict()
            self.cache["proj"] = None
            self.cache["zoom"] = None
            
            
            for ds in self.datasets:
                #FIXME: points...
            
                self.cache["tracks"] = []
                for track in ds.tracks:
                    path = NSBezierPath.alloc().init()
                    path.setLineWidth_(5.0)
                    path.setLineCapStyle_(NSRoundLineCapStyle)
                    path.setLineJoinStyle_(NSRoundLineJoinStyle)
                    
                    if track:
                        point = track[0]
                        loc = proj.forward(mapnik.Coord(point.x, point.y))
                        loc = loc - origin
                        loc = loc / zoom
                        loc = NSPoint(loc.x,loc.y)
                        
                        path.moveToPoint_(loc)
                
                    for point in track:
                        loc = proj.forward(mapnik.Coord(point.x, point.y))
                        loc = loc - origin
                        loc = loc / zoom
                        path.lineToPoint_(NSPoint(loc.x,loc.y))
            
                    self.cache["tracks"].append(path)
        
        for ds in self.datasets:
            icon = ds.icon
            icon_hotspot = ds.icon_hotspot
            
            for point in ds.points:
                loc = proj.forward(mapnik.Coord(point.x, point.y))
                loc = loc - origin
                loc = loc / zoom
                
                icon.drawAtPoint_fromRect_operation_fraction_(NSPoint(loc.x - icon_hotspot.x,loc.y - icon_hotspot.y), NSZeroRect, NSCompositeSourceOver, 1.0)
            
            for path in self.cache["tracks"]:
                color = NSColor.colorWithDeviceRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.6)
                color.setStroke()
                path.stroke()
    
    def setName_(self, name):
        self.name = name
    
    def setSize_(self, size):
        self.size = [size.width, size.height]

def fromGPXFile(filename):
    file = open(filename)
    try:
        import xml.etree
        gpx_data = xml.etree.ElementTree.parse(filename)
        
        if gpx_data.getroot().tag[-3:] != "gpx":
            print "GPX Load: No root element"
            return None
        
        # Handle etree namespace
        prefix = gpx_data.getroot().tag[:-3]
        
        ds = GenericDataset.alloc().init()
        # Find all waypoints
        for wpt in gpx_data.findall(prefix + "wpt"):
            point = NSPoint(float(wpt.get("lon")), float(wpt.get("lat")))
            ds.points.append(point)
            
        for trk in gpx_data.findall(prefix + "trk"):
            for seg in trk.findall(prefix + "trkseg"):
                segment = []
                for trkpt in seg.findall(prefix + "trkpt"):
                    point = NSPoint(float(trkpt.get("lon")), float(trkpt.get("lat")))
                    segment.append(point)
                    
                    # If there's a comment consider it the same as a waypoint
                    #if trkpt.find(prefix + "cmt") is not None:
                    #    ds.points.append(point)
                ds.tracks.append(segment)
        
        layer = GenericDataLayer.alloc().init()
        layer.datasets.append(ds)
        return layer
        
    except Exception as e:
        print e
        raise e
    finally:
        file.close()