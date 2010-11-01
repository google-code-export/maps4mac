#
#  MapnikRenderThread.py
#  Maprender
#
#  Created by Daniel Sabo on 5/4/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
from AppKit import NSCalibratedRGBColorSpace, NSDeviceRGBColorSpace, NSZeroRect, NSCompositeCopy, NSAlphaFirstBitmapFormat
from Quartz import *

import threading
import mapnik
import cairo

class RenderThreadTileRequest(NSObject):
    cord = objc.ivar()
    zoom = objc.ivar()
    callback = objc.ivar()

class RenderThreadTileResult(NSObject):
    cord = objc.ivar()
    zoom = objc.ivar()
    img  = objc.ivar()

class MapnikRenderThread(NSObject):
    queue = objc.ivar()
    stop_flag  = objc.ivar()
    work_sem   = objc.ivar()
    queue_lock = objc.ivar()
    
    map = objc.ivar()
    prj = objc.ivar()

    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
            
        self.queue = list()
        self.work_sem = threading.Semaphore(0)
        self.queue_lock = threading.Lock()
        self.map = mapnik.Map(256,256)
        self.prj = None
        self.stop_flag = False
        
        self.map.buffer_size = 128
        
        return self
    
    def run(self):
        pool = NSAutoreleasePool.alloc().init()
        
        while not self.stop_flag:
            self.work_sem.acquire(True)
            self.queue_lock.acquire(True)
            if self.queue:
                tile = self.queue.pop(0)
            else:
                tile = None
            self.queue_lock.release()
            if tile:
                self._renderTile(tile)
        
        #pool.release()
    
    def _renderTile(self, tile):
        origin = tile[0]
        zoom   = tile[1]
        callback = tile[2]
        c0 = origin
        c1 = c0 + mapnik.Coord(256 * zoom, 256 * zoom)
        bbox = mapnik.Envelope(c0.x,c0.y,c1.x,c1.y)
        self.map.zoom_to_box(bbox)

        surface = cairo.ImageSurface(cairo.FORMAT_RGB24,256,256)
        mapnik.render(self.map, surface)
        
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
        
        result = RenderThreadTileResult.alloc().init()
        result.cord = origin
        result.zoom = zoom
        result.img  = img
        
        callback.performSelectorOnMainThread_withObject_waitUntilDone_("finishedTile:", result, False)

    def loadMapFile_(self, xmlPath):
        self.cancelTiles()
        mapnik.load_map(self.map, xmlPath)
        self.prj = mapnik.Projection(self.map.srs)
    
    def loadMapString_(self, xml):
        self.cancelTiles()
        mapnik.load_map_from_string(self.map, xml)
        self.prj = mapnik.Projection(self.map.srs)
    
    def renderTileAt_Zoom_Callback_(self, cord, zoom, callback):
        tile = [cord,zoom,callback]
        self.queue_lock.acquire(True)
        self.queue.append(tile)
        self.queue_lock.release()
        self.work_sem.release()
    
    def cancelTiles(self):
        self.queue_lock.acquire(True)
        self.queue = list()
        self.queue_lock.release()
    
    def stop(self):
        self.queue_lock.acquire(True)
        self.queue = list()
        self.stop_flag = True
        self.queue_lock.release()
        self.work_sem.release()
    