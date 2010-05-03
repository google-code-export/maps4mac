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
    buffer = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.map = None
        self.center = [0,0]
        self.zoom   = 100
        self.size   = [1,1]
        
        return self
    
    def setMapXML_(self, xmlPath):
        self.map = mapnik.Map(1,1)
        mapnik.load_map(self.map, str(xmlPath))
        # select ST_XMin(st_estimated_extent),ST_YMin(st_estimated_extent),ST_XMax(st_estimated_extent),ST_YMax(st_estimated_extent) from ST_Estimated_Extent('washington_polygon','way');
    
    def drawRect_(self, rect):
        # We have the center, calculate the projected center, then take the rect as projeciton coordinates
        
        self.map.resize(int(rect.size[0]), int(rect.size[1]))
        print "center",self.center
        print "size",self.size
        print "zoom",self.zoom
        
        #FIXME: Get projection from the layer itself
        prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
        prj_center = prj.forward(mapnik.Coord(self.center[0],self.center[1]))
        print "prj_center",prj_center
        prj_origin = mapnik.Coord(rect.origin[0] - (self.size[0] / 2) * self.zoom, rect.origin[1] - (self.size[1] / 2) * self.zoom)
        prj_size   = mapnik.Coord(rect.size[0], rect.size[1]) * self.zoom
        c0 = prj_center + prj_origin
        c1 = c0 + prj_size
        print "c0",c0,"c1",c1

        bbox = mapnik.Envelope(c0.x,c0.y,c1.x,c1.y)
        print "bbox:", bbox
        
        self.map.zoom_to_box(bbox)
        
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24,int(rect.size.width),int(rect.size.height))
        mapnik.render(self.map, surface)
        print "Rendered"

        newData = array('B')
        
        cairoData = surface.get_data()
        for row in range(0,surface.get_height()):
            for col in range(0,surface.get_width()):
                offset = surface.get_stride() * row + (col * 4)
                pixel = cairoData[offset:offset+4]
                newData.append(ord(pixel[2]))
                newData.append(ord(pixel[1]))
                newData.append(ord(pixel[0]))
        stride = surface.get_width() * 3
        
        rep = NSBitmapImageRep.alloc()
        rep.initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        (newData, None, None, None, None), surface.get_width(), surface.get_height(), 8, 3, False, False, NSDeviceRGBColorSpace, stride, 24)
        
        img = NSImage.alloc().init()
        img.addRepresentation_(rep)
        img.drawAtPoint_fromRect_operation_fraction_(NSPoint(0,0), NSZeroRect, NSCompositeCopy, 1.0)
    
    def setCenter_(self, point):
        self.center = point
    
    def setZoom_(self, zoom):
        self.zoom = int(zoom)
        print self.zoom
    
    def setSize_(self, size):
        self.size = [size.width, size.height]