#
#  TiledMapnikLayer.py
#  Maprender
#
#  Created by Daniel Sabo on 4/23/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
from AppKit import NSCalibratedRGBColorSpace, NSDeviceRGBColorSpace, NSZeroRect, NSCompositeCopy, NSAlphaFirstBitmapFormat
from Quartz import *

import mapnik
import cairo
from array import array
from StringIO import StringIO

# CATiledLayer?

class TiledMapnikLayer(NSObject):
    map = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.map = None
        self.center = [0,0]
        self.zoom   = 100
        self.size   = [1,1]
        self.cache  = dict()
        
        return self
    
    def setMapXML_(self, xmlPath):
        self.map = mapnik.Map(256,256)
        mapnik.load_map(self.map, str(xmlPath))
        # select ST_XMin(st_estimated_extent),ST_YMin(st_estimated_extent),ST_XMax(st_estimated_extent),ST_YMax(st_estimated_extent) from ST_Estimated_Extent('washington_polygon','way');
    
    def drawRect_(self, rect):
        #FIXME: Get projection from the layer itself
        prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
        prj_center = prj.forward(mapnik.Coord(self.center[0],self.center[1]))
        prj_origin = mapnik.Coord(rect.origin[0] - (self.size[0] / 2) * self.zoom, rect.origin[1] - (self.size[1] / 2) * self.zoom)
        prj_size   = mapnik.Coord(rect.size[0], rect.size[1]) * self.zoom
        c0 = prj_center + prj_origin
        c1 = c0 + prj_size
        
        tile_size = (256 * self.zoom)
        
        # Build the tile list, tiles are identified by their lower left corner
        origin_lower_left = [int(c0.x) - int(c0.x) % tile_size, int(c0.y) - int(c0.y) % tile_size]
        lower_left = origin_lower_left[:]
        
        # Offset for the lower corner will be (origin_lower_left - c0) / zoom
        point = [(origin_lower_left[0] - c0.x) / self.zoom, (origin_lower_left[1] - c0.y) / self.zoom]
        point = [int(i) for i in point]
        origin_point = point[:]
        
        while lower_left[0] < c1.x:
            while lower_left[1] < c1.y:
                img = self.getTileAt_(lower_left)
                img.drawAtPoint_fromRect_operation_fraction_(NSPoint(point[0],point[1]), NSZeroRect, NSCompositeCopy, 1.0)
                point[1] += 256
                lower_left[1] += tile_size
            point[1] = origin_point[1]
            lower_left[1] = origin_lower_left[1]
            point[0] += 256
            lower_left[0] += tile_size
        
    def getTileAt_(self, origin):
        if origin[0] in self.cache:
            if origin[1] in self.cache[origin[0]]:
                #print "Cached %d,%d" % (origin[0],origin[1])
                return self.cache[origin[0]][origin[1]]
        else:
            self.cache[origin[0]] = dict()
        
        c0 = mapnik.Coord(origin[0], origin[1])
        c1 = c0 + mapnik.Coord(256 * self.zoom, 256 * self.zoom)
        bbox = mapnik.Envelope(c0.x,c0.y,c1.x,c1.y)
        self.map.zoom_to_box(bbox)
        
        prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
        
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24,256,256)
        mapnik.render(self.map, surface)
        
        #print "Rendered %d,%d" % (origin[0],origin[1])

        cairoData = surface.get_data()
        stride = surface.get_width() * 3
        
        rep = NSBitmapImageRep.alloc()
        rep.initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, surface.get_width(), surface.get_height(), 8, 3, False, False, NSDeviceRGBColorSpace, stride, 24)
        
        newDataIndex = 0
        newData = rep.bitmapData()
        for row in range(0,surface.get_height()):
            for col in range(0,surface.get_width()):
                offset = surface.get_stride() * row + (col * 4)
                pixel = cairoData[offset:offset+4]
                newData[newDataIndex] = pixel[2]
                newDataIndex += 1
                newData[newDataIndex] = pixel[1]
                newDataIndex += 1
                newData[newDataIndex] = pixel[0]
                newDataIndex += 1
        
        img = NSImage.alloc().init()
        img.addRepresentation_(rep)
        
        self.cache[origin[0]][origin[1]] = img
        return img
        
    def setCenter_(self, point):
        self.center = point
    
    def setZoom_(self, zoom):
        # Empty the cache on zoom change
        if int(zoom) != self.zoom:
            self.cache = dict()
        
        self.zoom = int(zoom)
    
    def setSize_(self, size):
        self.size = [size.width, size.height]