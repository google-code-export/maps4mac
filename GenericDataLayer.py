#
#  GenericDataLayer.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 5/10/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

from Foundation import *
from AppKit import *

import mapnik
import Layer

class GenericPoint(NSObject):
    x = objc.ivar()
    y = objc.ivar()
    name = objc.ivar()
    description = objc.ivar()
    icon = objc.ivar()
    font = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.x = 0.0
        self.y = 0.0
        self.name = None
        self.icon = None
        self.font = None
        
        return self
        
    @classmethod
    def GenericPointWithX_Y_(cls, x, y):
        return cls.GenericPointWithX_Y_Name_(x, y, None)
    
    @classmethod
    def GenericPointWithX_Y_Name_(cls, x, y, name):
        p = cls.alloc().init()
        p.x = x
        p.y = y
        p.name = name
        
        return p

class GenericTrack(NSObject):
    points = objc.ivar()
    name = objc.ivar()
    description = objc.ivar()
    color = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.points = list()
        
        return self
    
    @classmethod
    def GenericTrackWithPoints_(cls, points):
        return cls.GenericTrackWithPoints_Name_(cls, points, None)
        
    @classmethod
    def GenericTrackWithPoints_Name_(cls, points, name):
        t = cls.alloc().init()
        t.points = list(points)
        if name is None:
            name = "<Track>"
        t.name = name
        
        return t
    
    def __getitem__(self, index):
        return self.points[index]
    
    def __len__(self):
        return len(self.points)

class GenericPolygon(NSObject):
    name = objc.ivar()
    description = objc.ivar()
    
    rings = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.rings = list()
        
        return self

    @classmethod
    def GenericPolygonWithRings_(cls, rings):
        return cls.GenericPolygonWithRings_Name_(cls, rings, None)
        
    @classmethod
    def GenericPolygonWithRings_Name_(cls, rings, name):
        t = cls.alloc().init()
        t.rings = list(rings)
        if name is None:
            name = "<Polygon>"
        t.name = name
        
        return t
    
    def __getitem__(self, index):
        return self.rings[index]
    
    def __len__(self):
        return len(self.rings)

class GenericDataLayerIcon(NSObject):
    icon = objc.ivar() # NSImage used to represent the point
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

class OutlineEntry(NSObject):
    x = objc.ivar()
    y = objc.ivar()
    name = objc.ivar()
    description = objc.ivar()
    target_object = objc.ivar()
    
    outline = objc.ivar()
    
    def initWithObject_X_Y_Name_(self, target, x, y, name):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.x = x
        self.y = y
        self.target_object = target
        
        if name:
            self.name = name
        else:
            self.name = "<unnamed>"
        
        self.outline = None
        
        return self
    
    def addChild_(self, child):
        if not self.outline:
            self.outline = list()
        
        self.outline.append(child)

class GenericDataLayer(Layer.Layer):
    cache    = objc.ivar()
    default_icon = objc.ivar()
    default_text_format = objc.ivar()
    
    points = objc.ivar()
    tracks = objc.ivar()
    polygons = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.name = "Untitled"
        self.cache = None
        self.outline = list()
        
        self.points = list()
        self.tracks = list()
        self.polygons = list()
        
        icon_path = NSBundle.mainBundle().pathForResource_ofType_("target0", "png")
        self.default_icon = GenericDataLayerIcon.initWithFile_(icon_path)
        self.default_text_format = { 
            NSFontAttributeName : NSFont.fontWithName_size_("Andale Mono", 10.0),
            NSForegroundColorAttributeName : NSColor.colorWithDeviceRed_green_blue_alpha_(1.0, 0.0, 0.0, 1.0),
        }
        
        return self
    
    def addPointWithX_Y_Name_(self, x, y, name):
        if name is not None:
            point = GenericPoint.GenericPointWithX_Y_Name_(x,y,name)
        else:
            point = GenericPoint.GenericPointWithX_Y_(x,y)
        self.points.append(point)
        self.outline.append(OutlineEntry.alloc().initWithObject_X_Y_Name_(point, point.x, point.y, point.name))
        
        if self.cache and "proj" in self.cache:
            point = self.cache["proj"].forward(mapnik.Coord(x, y))
            self.cache["points"].append(point)
        
        if self.view:
            self.view.setNeedsDisplay_(True)
        
        return point
    
    def setDescription_ForPoint_(self, description, point):
        entry = None
        for e in self.outline:
            if e.target_object == point:
                entry = e
                break
        
        if entry is None:
            raise IndexError("No such point")
        
        e.description = description
        e.target_object.description = description
    
    
    def setDescription_ForTrack_(self, description, track_id):
        entry = None
        track = self.getTrackByID_(track_id)
        for e in self.outline:
            if e.target_object == track:
                entry = e
                break
        
        if entry is None:
            raise IndexError("No such track")
        
        e.description = description
        e.target_object.description = description
    
    def setDescription_ForPolygon_(self, description, poly_id):
        entry = None
        poly  = self.getPolygonByID_(poly_id)
        for e in self.outline:
            if e.target_object == poly:
                entry = e
                break
        
        if entry is None:
            raise IndexError("No such polygon")
        
        e.description = description
        e.target_object.description = description

    def appendToTrack_PointWithX_Y_(self, t, x, y):
        # If the track was empty before, we need to set it's outline point to it's start
        needsOutline = False
        if not self.tracks[t].points:
            needsOutline = True
        
        self.tracks[t].points.append(mapnik.Coord(x, y))
        
        if needsOutline:
            self.updateOutline()
            #for o in self.outline:
            #    if o.target_object == self.tracks[t]:
            #        print "Found track object"
            #        o.x = x
            #        o.y = y
            #        break;
        
        #FIXME: Should just re-cache the new point insdead of recaluating the track
        if self.cache and self.cache["proj"] and self.cache["zoom"] and id(self.tracks[t]) in self.cache["tracks"]:
            del self.cache["tracks"][id(self.tracks[t])]
            self.cacheTrack_(self.tracks[t])
    
    def addTrack_(self, t):
        return self.addTrack_WithName_(t, "<Track>")
    
    def addTrack_WithName_(self, t, name):
        track = GenericTrack.GenericTrackWithPoints_Name_(t, name)
        self.tracks.append(track)
        result = len(self.tracks) - 1
        
        if not track:
            self.outline.append(OutlineEntry.alloc().initWithObject_X_Y_Name_(track, 0.0, 0.0, track.name))
        else:
            self.outline.append(OutlineEntry.alloc().initWithObject_X_Y_Name_(track, track[0].x, track[0].y, track.name))
        
        if self.cache and self.cache["proj"] and self.cache["zoom"]:
            self.cacheTrack_(track)
        
        if self.view:
            self.view.setNeedsDisplay_(True)
        
        return result
    
    def getTrackByID_(self, t):
        return self.tracks[t]
    
    def getPolygonByID_(self, p):
        return self.polygons[p]
    
    def addPolygon_(self, rings):
        return self.addPolygon_WithName_(self, rings, None)
        
    def addPolygon_WithName_(self, rings, name):
        poly = GenericPolygon.GenericPolygonWithRings_Name_(rings, name)
        self.polygons.append(poly)
        result = len(self.polygons) - 1
        
        if self.cache and self.cache["proj"] and self.cache["zoom"]:
            self.cachePolygon_(poly)
        
        #FIXME: Find center
        if rings and rings[0]:
            self.outline.append(OutlineEntry.alloc().initWithObject_X_Y_Name_(poly, rings[0][0].x, rings[0][0].y, poly.name))
        else:
            self.outline.append(OutlineEntry.alloc().initWithObject_X_Y_Name_(poly, 0.0, 0.0, poly.name))
        
        if self.view:
            self.view.setNeedsDisplay_(True)
        
        return result
    
    def updateOutline(self):
        """Rebuild the outline for this layer"""
        self.outline = list()
        for point in self.points:
            self.outline.append(OutlineEntry.alloc().initWithObject_X_Y_Name_(point, point.x, point.y, point.name))
        for track in self.tracks:
            if len(track) > 0:
                self.outline.append(OutlineEntry.alloc().initWithObject_X_Y_Name_(track, track[0].x, track[0].y, track.name))
            else:
                self.outline.append(OutlineEntry.alloc().initWithObject_X_Y_Name_(track, 0.0, 0., track.name))
    
    def cacheTrack_(self, track):
        proj = self.cache["proj"]
        zoom = self.cache["zoom"]
        
        path = NSBezierPath.alloc().init()
        #path.setLineWidth_(5.0)
        path.setLineCapStyle_(NSRoundLineCapStyle)
        path.setLineJoinStyle_(NSRoundLineJoinStyle)
        path.setFlatness_(1.0)
        
        if track:
            point = track[0]
            loc = proj.forward(mapnik.Coord(point.x, point.y))
            loc = NSPoint(loc.x,loc.y)
            
            path.moveToPoint_(loc)
            path.lineToPoint_(loc)
            lastloc = loc
        
            for point in track[1:]:
                loc = proj.forward(mapnik.Coord(point.x, point.y))
                loc = NSPoint(loc.x,loc.y)
                if abs(loc.x - lastloc.x) > zoom or abs(loc.y - lastloc.y) > zoom:
                    # only include the point if it will move the line at least 1 zoomed pixel
                    path.lineToPoint_(loc)
                    lastloc = loc

        self.cache["tracks"][id(track)] = path
    
    def cachePolygon_(self, polygon):
        proj = self.cache["proj"]
        zoom = self.cache["zoom"]
        
        path = NSBezierPath.alloc().init()
        path.setFlatness_(1.0)
        path.setWindingRule_(NSEvenOddWindingRule)
        
        for ring in polygon.rings:
            point = ring[0]
            loc = proj.forward(mapnik.Coord(point.x, point.y))
            loc = NSPoint(loc.x,loc.y)
            
            path.moveToPoint_(loc)
            path.lineToPoint_(loc)
            lastloc = loc
        
            for point in ring[1:]:
                loc = proj.forward(mapnik.Coord(point.x, point.y))
                loc = NSPoint(loc.x,loc.y)
                if abs(loc.x - lastloc.x) > zoom or abs(loc.y - lastloc.y) > zoom:
                    # only include the point if it will move the line at least 1 zoomed pixel
                    path.lineToPoint_(loc)
                    lastloc = loc
            
            path.closePath()

        self.cache["polygons"][id(polygon)] = path
    
    def drawRect_WithProjection_Origin_Zoom_(self, rect, proj, origin, zoom):
        """Takes a projection and a rect in that projection, draws the layers contents for the rect with a transparent background"""
        
        # FIXME: Test if things are in the rect before drawing them
        
        if not self.cache:
            self.cache = dict()
            self.cache["proj"] = None
            self.cache["zoom"] = None
        
        if self.cache["proj"] != proj or self.cache["zoom"] != zoom:
            self.cache = dict()
            self.cache["proj"] = proj
            self.cache["zoom"] = zoom
            
            self.cache["points"] = []
            for point in self.points:
                point = proj.forward(mapnik.Coord(point.x, point.y))
                self.cache["points"].append(point)
        
            self.cache["tracks"] = dict()
            for track in self.tracks:
                self.cacheTrack_(track)
                
            self.cache["polygons"] = dict()
            for polygon in self.polygons:
                self.cachePolygon_(polygon)
        
        icon = self.default_icon.icon
        icon_hotspot = self.default_icon.icon_hotspot
        
        for point,loc in zip(self.points, self.cache["points"]):
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
        for path in self.cache["tracks"].values():
            color = NSColor.colorWithDeviceRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.6)
            color.setStroke()
            path.setLineWidth_(5.0 * zoom)
            path.stroke()
            
        for path in self.cache["polygons"].values():
            lineColor = NSColor.colorWithDeviceRed_green_blue_alpha_(1.0, 0.0, 0.0, 1.0)
            lineColor.setStroke()
            fillColor = NSColor.colorWithDeviceRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.2)
            fillColor.setFill()
            path.setLineWidth_(1.0 * zoom)
            path.fill()
            path.stroke()
        trans.invert()
        trans.concat()
    
    def setName_(self, name):
        self.name = name
        
    def setDescription_(self, description):
        self.description = description

class FileParseException(Exception):
    pass

def fromGPXFile(filename):
    try:
        import xml.etree
        gpx_data = xml.etree.ElementTree.parse(filename)
        
        if gpx_data.getroot().tag[-3:] != "gpx":
            raise FileParseException("GPX Load: No root element")
        
        # Handle etree namespace
        prefix = gpx_data.getroot().tag[:-3]
        
        layer = GenericDataLayer.alloc().init()
        # Find all waypoints
        for wpt in gpx_data.findall(prefix + "wpt"):
            name = wpt.find(prefix + "name")
            cmt  = wpt.find(prefix + "cmt")
            desc = wpt.find(prefix + "desc")
            
            if name is not None:
                name = name.text
            elif cmt is not None:
                name = cmt.text
            
            description = ""
            for l in [cmt, desc]:
                if l is not None:
                    print l, l.text
                    if description:
                        description += "\n\n"
                    description += l.text
            
            point = layer.addPointWithX_Y_Name_(float(wpt.get("lon")), float(wpt.get("lat")), name)
            
            if description:
                layer.setDescription_ForPoint_(description, point)
            
        for trk in gpx_data.findall(prefix + "trk"):
            for seg in trk.findall(prefix + "trkseg"):
                segment = []
                for trkpt in seg.findall(prefix + "trkpt"):
                    point = NSPoint(float(trkpt.get("lon")), float(trkpt.get("lat")))
                    segment.append(point)
                    
                    # If there's a comment consider it the same as a waypoint
                    #if trkpt.find(prefix + "cmt") is not None:
                    #    layer.points.append(point)
                layer.addTrack_(segment)
        
        return layer
        
    except Exception as e:
        print e
        import traceback
        traceback.print_exc()
        raise
        
def fromKMLFile(filename):
    try:
        import xml.etree
        
        if filename.endswith(".kmz"):
            import zipfile
            z = zipfile.ZipFile(filename)
            if "doc.kml" in z.namelist():
                datafile = "doc.kml"
            else:
                datafile = None
                for fn in z.namelist():
                    if fn.endswith(".kml"):
                        datafile = fn
                        break
            if not datafile:
                raise FileParseException("Couldn't find a kml file in the kmz archive")
            
            data = z.open(datafile)
            kml_data = xml.etree.ElementTree.parse(data)
            data.close()
            z.close()
        else:
            kml_data = xml.etree.ElementTree.parse(filename)
        
        if kml_data.getroot().tag[-3:] != "kml":
            raise FileParseException("KML Load: No root element")
        
        # Handle etree namespace
        prefix = kml_data.getroot().tag[:-3]
        kml_doc = kml_data.find(prefix + "Document")
        if not kml_doc:
            #FIXME: This is probably a valid KML document
            raise FileParseException("No Document node")
        
        #document_name = kml_doc.find(prefix + "name")
        
        layer = GenericDataLayer.alloc().init()
        
        def do_placemarks(node):
            for placemark in node.findall(prefix + "Placemark"):
                name = placemark.find(prefix + "name")
                if name is not None:
                    name = name.text
                description = placemark.find(prefix + "description")
                if description is not None:
                    description = description.text
                
                
                geom_parent = placemark.find(prefix + "GeometryCollection") #FIXME: This isn't quite right, a collection couuld contain multis
                
                if not geom_parent:
                    geom_parent = placemark.find(prefix + "MultiGeometry")
                    
                    if not geom_parent:
                        geom_parent = placemark
                    
                for point in geom_parent.findall(prefix + "Point"):
                    cord = point.find(prefix + "coordinates")
                    if cord is not None:
                        cord = cord.text.split(",")
                        p = layer.addPointWithX_Y_Name_(float(cord[0]), float(cord[1]), name)
                        if description:
                            layer.setDescription_ForPoint_(description, p)
                        
                    
                for ls in geom_parent.findall(prefix + "LineString"):
                    coords = ls.find(prefix + "coordinates")
                    if coords is not None:
                        # [:2] is to strip off altitude
                        coords = [map(float, c.split(",")[:2]) for c in coords.text.strip().split()]
                        coords = [mapnik.Coord(c[0],c[1]) for c in coords]
                    t = layer.addTrack_WithName_(coords, name)
                    if description:
                        layer.setDescription_ForTrack_(description, t)
                    
                for poly in geom_parent.findall(prefix + "Polygon"):
                    def find_rings(node):
                        result = list()
                        for ring in node.findall(prefix + "LinearRing"):
                            coords = ring.find(prefix + "coordinates")
                            if coords is not None:
                                # [:2] is to strip off altitude
                                coords = [map(float, c.split(",")[:2]) for c in coords.text.strip().split()]
                                coords = [mapnik.Coord(c[0],c[1]) for c in coords]
                                result.append(coords)
                        return result
                    
                    rings = list()
                    
                    for outer in poly.findall(prefix + "outerBoundaryIs"):
                        outer_rings = find_rings(outer)
                        if outer_rings:
                            rings.extend(outer_rings)
                    
                    for inner in poly.findall(prefix + "innerBoundaryIs"):
                        inner_rings = find_rings(inner)
                        if inner_rings:
                            rings.extend(inner_rings)
                    
                    p = layer.addPolygon_WithName_(rings, name)
                    if description:
                        layer.setDescription_ForPolygon_(description, p)
                    
            
            for folder in node.findall(prefix + "Folder"):
                do_placemarks(folder)
        
        do_placemarks(kml_doc)
        
        return layer
        
    except Exception as e:
        print e
        import traceback
        traceback.print_exc()
        raise