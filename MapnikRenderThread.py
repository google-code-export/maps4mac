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

import mapnik
import cairo
import time

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
    
    work_condition_lock = objc.ivar()
    map_lock = objc.ivar()
    
    map = objc.ivar()
    prj = objc.ivar()

    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
            
        self.queue = list()
        self.map = None
        self.prj = None
        self.stop_flag = False
        
        
        self.work_condition_lock = NSCondition.alloc().init()
        self.work_condition_lock.setName_("MapnikRenderThread: WorkLock")
        self.map_lock = NSLock.alloc().init()
        self.map_lock.setName_("MapnikRenderThread: MapLock")
        
        return self
    
    def run(self):
        NSThread.detachNewThreadSelector_toTarget_withObject_(self.runThread_,self,None)
    
    def runThread_(self, arg):
        pool = NSAutoreleasePool.alloc().init()
        willStop = False
        
        while not willStop:
            self.work_condition_lock.lock()
            if not self.queue:
                self.work_condition_lock.wait()
            
            if self.queue:
                tile = self.queue.pop(0)
            else:
                tile = None
                
            willStop = self.stop_flag
            self.work_condition_lock.unlock()
            
            if tile:
                #FIXME: It's possible to get here after loadMap has been called, but
                #       a spurious render request should be harmless
                self.map_lock.lock()
                try:
                    self._renderTile(tile)
                except Exception as ex:
                    print "Excpetion rendering tile:", ex
                    import traceback
                    traceback.print_exc()
                self.map_lock.unlock()
        
        pool.release()
    
    def _renderTile(self, tile):    
        origin = tile[0]
        zoom   = tile[1]
        callback = tile[2]
        c0 = origin
        c1 = c0 + mapnik.Coord(256 * zoom, 256 * zoom)
        bbox = mapnik.Envelope(c0.x,c0.y,c1.x,c1.y)
        self.map.zoom_to_box(bbox)
        
        
        rep = NSBitmapImageRep.alloc()
        # Cairo Render, doing the byte swap makes this one a LOT slower
        if False:
            surface = cairo.ImageSurface(cairo.FORMAT_RGB24,256,256)
            mapnik.render(self.map, surface)
        
            data = surface.get_data()
            stride = surface.get_width() * 3
            
            rep.initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            None, surface.get_width(), surface.get_height(), 8, 3, False, False, NSDeviceRGBColorSpace, stride, 24)
            
            newDataIndex = 0
            newData = rep.bitmapData()
            for row in range(0,surface.get_height()):
                for col in range(0,surface.get_width()):
                    offset = surface.get_stride() * row + (col * 4)
                    pixel = data[offset:offset+4]
                    newData[newDataIndex] = pixel[2]
                    newDataIndex += 1
                    newData[newDataIndex] = pixel[1]
                    newDataIndex += 1
                    newData[newDataIndex] = pixel[0]
                    newDataIndex += 1
        
        # AGG Render
        if True:
            surface = mapnik.Image(256,256)
            mapnik.render(self.map, surface)
            
            data = surface.tostring()
            #stride = 256 * 3
            stride = 256 * 4
            
            rep.initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            #None, 256, 256, 8, 3, False, False, NSDeviceRGBColorSpace, stride, 24)
            None, 256, 256, 8, 4, True, False, NSDeviceRGBColorSpace, stride, 32)
            
            #newDataIndex = 0
            newData = rep.bitmapData()
            newData[:] = data
        
        
        img = NSImage.alloc().init()
        img.addRepresentation_(rep)
        
        result = RenderThreadTileResult.alloc().init()
        result.cord = origin
        result.zoom = zoom
        result.img  = img
        
        callback.performSelectorOnMainThread_withObject_waitUntilDone_("finishedTile:", result, False)

    def loadMapFile_(self, xmlPath):
        self.cancelTiles()
        
        self.map_lock.lock()
        self.map = mapnik.Map(256,256)
        self.map.buffer_size = 128
        mapnik.load_map(self.map, xmlPath)
        self.prj = mapnik.Projection(self.map.srs)
        self.map_lock.unlock()
    
    def loadMapString_(self, xml):
        self.cancelTiles()
        
        self.map_lock.lock()
        self.map = mapnik.Map(256,256)
        self.map.buffer_size = 128
        mapnik.load_map_from_string(self.map, xml)
        self.prj = mapnik.Projection(self.map.srs)
        self.map_lock.unlock()
    
    def renderTileAt_Zoom_Callback_(self, cord, zoom, callback):
        tile = [cord,zoom,callback]
        
        self.work_condition_lock.lock()
        self.queue.append(tile)
        self.work_condition_lock.signal()
        self.work_condition_lock.unlock()
    
    def cancelTiles(self):
        self.work_condition_lock.lock()
        self.queue = list()
        # No need to signal, if nothing is rendering then nothing is rendering
        #self.work_condition_lock.signal()
        self.work_condition_lock.unlock()
    
    def stop(self):
        self.work_condition_lock.lock()
        self.queue = list()
        self.stop_flag = True
        self.work_condition_lock.signal()
        self.work_condition_lock.unlock()
    