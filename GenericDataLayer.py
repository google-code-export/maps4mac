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
    icon = objc.ivar()
    font = objc.ivar()
    #FIXME: This doesn't belong on the point
    outline = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        x = 0.0
        y = 0.0
        name = None
        icon = None
        font = None
        
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

class GenericDataLayerIcon(NSObject):
    icon = objc.ivar() # NSImage used to represent the dataset
    icon_hotspot = objc.ivar() # Where to center the image
    
    @classmethod
    def initWithFile_(cls, path):
        self = cls.alloc().init()
        self.icon = NSImage.alloc().initByReferencingFile_(path)
        size = self.icon.size()
        self.icon_hotspot = NSPoint(size.width / 2, size.height / 2)
        
        return self
    
    @classmethod
    def initWithFile_Hotspot_(cls, path, hotspot):
        self = cls.alloc().init()
        self.icon = NSImage.alloc().initByReferencingFile_(path)
        self.icon_hotspot = hotspot
        
        return self

class GenericDataset(NSObject):
    points = objc.ivar()
    tracks = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.points = list()
        self.tracks = list()
        
        return self

class GenericDataLayer(Layer.Layer):
    cache    = objc.ivar()
    datasets = objc.ivar()
    default_icon = objc.ivar()
    default_text_format = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.datasets = [GenericDataset.alloc().init()]
        self.name = "Untitled"
        self.cache = None
        self.outline = None
        
        icon_path = NSBundle.mainBundle().pathForResource_ofType_("target0", "png")
        if not icon_path:
            icon_path = "/Users/argon/Prog/Maprender/target0.png"
        self.default_icon = GenericDataLayerIcon.initWithFile_(icon_path)
        self.default_text_format = { 
            NSFontAttributeName : NSFont.fontWithName_size_("Andale Mono", 10.0),
            NSForegroundColorAttributeName : NSColor.colorWithDeviceRed_green_blue_alpha_(1.0, 0.0, 0.0, 1.0),
        }
        
        return self
    
    def addPoint_(self, p):
        self.datasets[0].points.append(p)
        
        if self.cache and "proj" in self.cache:
            point = self.cache["proj"].forward(mapnik.Coord(p.x, p.y))
            self.cache["points"].append(point)
        
        if self.view:
            self.view.setNeedsDisplay_(True)
    
    def addPointWithX_Y_Name_(self, x, y, name):
        if name is not None:
            point = GenericDataPoint.GenericDataPointWithX_Y_Name_(x,y,name)
        else:
            point = GenericDataPoint.GenericDataPointWithX_Y_(x,y)
        self.datasets[0].points.append(point)
        if not self.outline:
            self.outline = list()
        self.outline.append(point)
        
        
        if self.cache and "proj" in self.cache:
            point = self.cache["proj"].forward(mapnik.Coord(x, y))
            self.cache["points"].append(point)
        
        if self.view:
            self.view.setNeedsDisplay_(True)
    
    def appendToTrack_PointWithX_Y_(self, t, x, y):
        pass
    
    def addTrack_(self, t):
        self.datasets[0].tracks.append(t)
        self.outline.append(GenericDataPoint.GenericDataPointWithX_Y_Name_(t[0].x,t[0].y,"<Track>"))
        
        if self.view:
            self.cache = dict()
            self.cache["proj"] = None
            self.cache["zoom"] = None

            self.view.setNeedsDisplay_(True)
    
    #FIXME: Call this automaticaly
    def updateOutline(self):
        self.outline = list()
        for ds in self.datasets:
            for point in ds.points:
                self.outline.append(point)
            for track in ds.tracks:
                self.outline.append(GenericDataPoint.GenericDataPointWithX_Y_Name_(track[0].x,track[0].y,"<Track>"))
    
    def drawRect_WithProjection_Origin_Zoom_(self, rect, proj, origin, zoom):
        """Takes a projection and a rect in that projection, draws the layers contents for the rect with a transparent background"""
        
        # FIXME: Test rect
        
        # FIXME: Need to monitor changes 
        
        if not self.cache:
            self.cache = dict()
            self.cache["proj"] = None
            self.cache["zoom"] = None
        
        if self.cache["proj"] != proj or self.cache["zoom"] != zoom:
            self.cache = dict()
            self.cache["proj"] = proj
            self.cache["zoom"] = zoom
            
            
            for ds in self.datasets:
                self.cache["points"] = []
                for point in ds.points:
                    point = proj.forward(mapnik.Coord(point.x, point.y))
                    self.cache["points"].append(point)
            
                self.cache["tracks"] = []
                for track in ds.tracks:
                    path = NSBezierPath.alloc().init()
                    #path.setLineWidth_(5.0)
                    path.setLineCapStyle_(NSRoundLineCapStyle)
                    path.setLineJoinStyle_(NSRoundLineJoinStyle)
                    
                    lastloc = None
                    if track:
                        point = track[0]
                        loc = proj.forward(mapnik.Coord(point.x, point.y))
                        loc = NSPoint(loc.x,loc.y)
                        
                        path.moveToPoint_(loc)
                        path.lineToPoint_(loc)
                        lastloc = loc
                
                    total = 0
                    for point in track[1:]:
                        loc = proj.forward(mapnik.Coord(point.x, point.y))
                        loc = NSPoint(loc.x,loc.y)
                        if abs(loc.x - lastloc.x) > zoom or abs(loc.y - lastloc.y) > zoom:
                            # only include the point if it will move the line at least 1 zoomed pixel
                            path.lineToPoint_(loc)
                            lastloc = loc
            
                    self.cache["tracks"].append(path)
        
        for ds in self.datasets:
            icon = self.default_icon.icon
            icon_hotspot = self.default_icon.icon_hotspot
            font_height  = self.default_text_format[NSFontAttributeName]
            
            for point,loc in zip(ds.points, self.cache["points"]):
                #loc = proj.forward(mapnik.Coord(point.x, point.y))
                # The cache only contains the location
                loc = loc - origin
                loc = loc / zoom
                
                icon.drawAtPoint_fromRect_operation_fraction_(NSPoint(loc.x - icon_hotspot.x,loc.y - icon_hotspot.y), NSZeroRect, NSCompositeSourceOver, 1.0)
                if point.name is not None:
                    name = NSString.stringWithString_(point.name)
                    string_size = name.sizeWithAttributes_(self.default_text_format)
                    x_shift = icon.size().width / 2 + 1 # FIXME: If the hotspot isn't centered this will be wrong
                    y_shift = -(string_size.height / 2)
                    NSString.drawAtPoint_withAttributes_(name, NSPoint(loc.x + x_shift, loc.y + y_shift), self.default_text_format)
            
            # Translate the origin for cached paths
            trans = NSAffineTransform.alloc().init()
            trans.scaleBy_(1.0 / zoom)
            trans.translateXBy_yBy_(-origin.x, -origin.y)
            trans.concat()
            for path in self.cache["tracks"]:
                color = NSColor.colorWithDeviceRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.6)
                color.setStroke()
                path.setLineWidth_(5.0 * zoom)
                path.stroke()
            trans.invert()
            trans.concat()
    
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