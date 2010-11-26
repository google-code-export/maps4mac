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
import Layer

class GenericDataPoint(NSObject):
    x = objc.ivar()
    y = objc.ivar()
    name = objc.ivar()
    #FIXME: This doesn't belong on the point
    outline = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        x = 0.0
        y = 0.0
        name = None
        
        return self
    
    @classmethod
    def GenericDataPointWithX_Y_Name_(cls, x, y, name):
        p = cls.alloc().init()
        p.x = x
        p.y = y
        p.name = name
        
        return p
        
    @classmethod
    def GenericDataPointWithX_Y_(cls, x, y):
        p = cls.alloc().init()
        p.x = x
        p.y = y
        p.name = None
        
        return p

class GenericDataset(NSObject):
    icon = objc.ivar() # NSImage used to represent the dataset
    icon_hotspot = objc.ivar() # Where to center the image
    points = objc.ivar()
    tracks = objc.ivar()
    text_format = objc.ivar()
    
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
        
        self.text_format = { 
            NSFontAttributeName : NSFont.fontWithName_size_("Andale Mono", 10.0),
            NSForegroundColorAttributeName : NSColor.colorWithDeviceRed_green_blue_alpha_(1.0, 0.0, 0.0, 1.0),
        }
        
        return self

class GenericDataLayer(Layer.Layer):
    datasets = objc.ivar()
    cache    = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.datasets = list()
        self.name = "Untitled"
        self.cache = None
        self.outline = None
        
        return self
    
    #FIXME: Call this automaticaly
    def updateOutline(self):
        self.outline = list()
        for ds in self.datasets:
            for point in ds.points:
                self.outline.append(point)
    
    def drawRect_WithProjection_Origin_Zoom_(self, rect, proj, origin, zoom):
        """Takes a projection and a rect in that projection, draws the layers contents for the rect with a transparent background"""
        
        # FIXME: Test rect
        
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
            font_height  = ds.text_format[NSFontAttributeName]
            
            for point in ds.points:
                loc = proj.forward(mapnik.Coord(point.x, point.y))
                loc = loc - origin
                loc = loc / zoom
                
                icon.drawAtPoint_fromRect_operation_fraction_(NSPoint(loc.x - icon_hotspot.x,loc.y - icon_hotspot.y), NSZeroRect, NSCompositeSourceOver, 1.0)
                if point.name is not None:
                    name = NSString.stringWithString_(point.name)
                    string_size = name.sizeWithAttributes_(ds.text_format)
                    x_shift = ds.icon.size().width / 2 + 1 # FIXME: If the hotspot isn't centered this will be wrong
                    y_shift = -(string_size.height / 2)
                    NSString.drawAtPoint_withAttributes_(name, NSPoint(loc.x + x_shift, loc.y + y_shift), ds.text_format)
            
            for path in self.cache["tracks"]:
                color = NSColor.colorWithDeviceRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.6)
                color.setStroke()
                path.stroke()
    
    def setName_(self, name):
        self.name = name

def fromGPXFile(filename):
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
            #point = NSPoint(float(wpt.get("lon")), float(wpt.get("lat")))
            point = GenericDataPoint.GenericDataPointWithX_Y_(float(wpt.get("lon")), float(wpt.get("lat")))
            name = wpt.find(prefix + "name")
            cmt  = wpt.find(prefix + "cmt")
            if name is not None:
                point.name = name.text
            elif cmt is not None:
                point.name = cmt.text
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
        
        layer.updateOutline()
        
        return layer
        
    except Exception as e:
        print e
        raise e
        
def fromKMLFile(filename):
    try:
        import xml.etree
        kml_data = xml.etree.ElementTree.parse(filename)
        
        if kml_data.getroot().tag[-3:] != "kml":
            print "KML Load: No root element"
            return None
        
        # Handle etree namespace
        prefix = kml_data.getroot().tag[:-3]
        kml_doc = kml_data.find(prefix + "Document")
        document_name = kml_doc.find(prefix + "name")
        
        ds = GenericDataset.alloc().init()
        # Find all placemarks
        def do_placemarks(node):
            #print kml_doc
            for placemark in node.findall(prefix + "Placemark"):
                #print placemark
                placemark_point = placemark.find(prefix + "Point")
                if placemark_point:
                    cord = placemark_point.find(prefix + "coordinates")
                    #print cord
                    if cord is not None:
                        #print cord.text
                        cord = cord.text.split(",")
                        #print cord
                        point = GenericDataPoint.GenericDataPointWithX_Y_(float(cord[0]), float(cord[1]))
                    
                        name = placemark.find(prefix + "name")
                        if name is not None:
                            point.name = name.text
                
                        ds.points.append(point)
            
            for folder in node.findall(prefix + "Folder"):
                do_placemarks(folder)
        do_placemarks(kml_doc)
        
        layer = GenericDataLayer.alloc().init()
        layer.datasets.append(ds)
        
        layer.updateOutline()
        
        return layer
        
    except Exception as e:
        print e
        raise e