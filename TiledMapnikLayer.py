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
        
        return self
    
    def setMapXML_(self, xmlPath):
        self.map = mapnik.Map(1,1)
        mapnik.load_map(self.map, str(xmlPath))
        # select ST_XMin(st_estimated_extent),ST_YMin(st_estimated_extent),ST_XMax(st_estimated_extent),ST_YMax(st_estimated_extent) from ST_Estimated_Extent('washington_polygon','way');
    
    def drawRect_(self, rect):
        #print rect
        # Fudge:
        ll = (-124.1084, 40.8961, -124.0452, 40.8577)
        
        prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
        c0 = prj.forward(mapnik.Coord(ll[0],ll[1]))
        c1 = prj.forward(mapnik.Coord(ll[2],ll[3]))

        bbox = mapnik.Envelope(c0.x,c0.y,c1.x,c1.y)
        
        self.map.zoom_to_box(bbox)
        
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24,int(rect.size.width),int(rect.size.height))
        mapnik.render(self.map, surface)
        print "Rendered"
        #surface.write_to_png("dump_tmp_file.png")
        
        
        #dataProvider = CGDataProviderCreateWithData(None,surface.get_data(),len(surface.get_data()),None)

        #bitmapInfo = kCGImageAlphaNoneSkipFirst | kCGBitmapByteOrder32Little
        
        #ref = CGImageCreate(surface.get_width(), surface.get_height(), 8, 32, surface.get_stride(),
        #                   CGColorSpaceCreateWithName(kCGColorSpaceGenericRGB), bitmapInfo,
        #                   dataProvider, None, False, kCGRenderingIntentDefault)
        
        #rep = NSBitmapImageRep.alloc()
        #rep.initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        #(surface.get_data(), None, None, None, None), surface.get_width(), surface.get_height(), 8, 3, False, False, NSDeviceRGBColorSpace, surface.get_stride(), 32)

        newData = array('B')
        #step = 0
        #for b in surface.get_data():
        #    newData.append(ord(b))
        #    step = step + 1
        
        cairoData = surface.get_data()
        for row in range(0,surface.get_height()):
            for col in range(0,surface.get_width()):
                offset = surface.get_stride() * row + (col * 4)
                pixel = cairoData[offset:offset+4]
                #newData.append(ord(pixel[0]))
                #print pixel
                newData.append(ord(pixel[2]))
                newData.append(ord(pixel[1]))
                newData.append(ord(pixel[0]))
        stride = surface.get_width() * 3
        
        rep = NSBitmapImageRep.alloc()
        rep.initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        (newData, None, None, None, None), surface.get_width(), surface.get_height(), 8, 3, False, False, NSDeviceRGBColorSpace, stride, 24)
        #(newData, None, None, None, None), surface.get_width(), surface.get_height(), 8, 1, False, False, NSCalibratedWhiteColorSpace, stride, 0)
        
        #img = NSImage.alloc().initByReferencingFile_("dump_tmp_file.png")
        #img = NSImage.alloc().initWithCGImage_size_(ref, NSZeroSize)
        img = NSImage.alloc().init()
        img.addRepresentation_(rep)
        img.drawAtPoint_fromRect_operation_fraction_(NSPoint(0,0), NSZeroRect, NSCompositeCopy, 1.0)
    
    def setCenter_(self, point):
        pass
    
    # Does this mean anything or should we just wait for the rect?
    def setSize_(self, size):
        self.map.resize(int(size.width), int(size.height))