#
#  TiledMapnikLayer.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 4/23/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

from Foundation import *
#from AppKit import NSCalibratedRGBColorSpace, NSDeviceRGBColorSpace, NSAlphaFirstBitmapFormat
from AppKit import NSZeroRect, NSCompositeCopy
from Quartz import *

from MapnikRenderThread import *

#import threading

import mapnik
import MapLayer

# CATiledLayer?

class TiledMapnikLayer(MapLayer.MapLayer):
    zoom = objc.ivar()

    def init(self):
        self = super(TiledMapnikLayer, self).init()
        if self is None:
            return None
        
        self.name = "Mapnik"
        
        self.projectionString = None
        self.projection = None
        self.cache  = dict()
        self.zoom   = 0
        self.render_thread = MapnikRenderThread.alloc().init()
        #thread = threading.Thread(target=self.render_thread.run, name="Render Thread")
        #thread.start()
        self.render_thread.run()
        
        self.view = None
        
        return self
    
    def setMapXML_(self, xml):
        map = mapnik.Map(256,256)
        mapnik.load_map_from_string(map, xml)
        self.projectionString = map.srs
        self.projection = mapnik.Projection(self.projectionString)
        
        self.cache = dict()
        self.render_thread.loadMapString_(xml)
    
    def setMapXMLFile_(self, xmlPath):
        map = mapnik.Map(256,256)
        mapnik.load_map(map, str(xmlPath))
        self.projectionString = map.srs
        self.projection = mapnik.Projection(self.projectionString)
        
        self.cache = dict()
        self.render_thread.loadMapFile_(str(xmlPath))
    
    def drawRect_WithProjection_Origin_Zoom_(self, rect, proj, origin, zoom):
        #FIXME: Handle out of bounds values
        try:
            if int(zoom) != self.zoom:
                self.cache = dict()
                self.zoom  = int(zoom)
                #print "Outer Cancel"
                self.render_thread.cancelTiles()
            
            c0 = origin
            c1 = origin + mapnik.Coord(rect.size[0] * zoom, rect.size[1] * zoom)
            
            tile_size = (256 * zoom)
            
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
                    if img:
                        img.drawAtPoint_fromRect_operation_fraction_(NSPoint(point[0],point[1]), NSZeroRect, NSCompositeCopy, 1.0)
                    else:
                        NSColor.darkGrayColor().setFill()
                        NSRectFill(NSRect(point, [256,256]))
                    point[1] += 256
                    lower_left[1] += tile_size
                point[1] = origin_point[1]
                lower_left[1] = origin_lower_left[1]
                point[0] += 256
                lower_left[0] += tile_size
        except Exception as e:
            print e
            NSColor.redColor().setFill()
            NSRectFill(rect)
        
    def getTileAt_(self, origin):
        if origin[0] in self.cache:
            if origin[1] in self.cache[origin[0]]:
                #print "Cached %d,%d" % (origin[0],origin[1])
                return self.cache[origin[0]][origin[1]]
        else:
            self.cache[origin[0]] = dict()
        
        self.cache[origin[0]][origin[1]] = None
        self.render_thread.renderTileAt_Zoom_Callback_(mapnik.Coord(origin[0], origin[1]), self.zoom, self)
        return None

    
    def finishedTile_(self, tile):
        if self.zoom == tile.zoom:
            self.cache[tile.cord.x][tile.cord.y] = tile.img
        if self.view:
            # Calculate the bounding box to draw
            zoom = self.view.zoom
            size = self.view.bounds().size
            
            prj = self.projection
            prj_center = prj.forward(self.view.center)
            prj_origin = mapnik.Coord(-(size[0] / 2) * zoom, -(size[1] / 2) * zoom)
            target = tile.cord - (prj_center + prj_origin)
            #print int(round(target.x / zoom)), int(round(target.y / zoom))
            
            #self.view.setNeedsDisplay_(True)
            #self.view.setNeedsDisplayInRect_(NSRect((round(target.x / zoom), round(target.y / zoom)),(256,256)))
            self.view.setNeedsDisplayInRect_(NSRect((target.x / zoom, target.y / zoom),(256,256)))
    
    def setName_(self, name):
        self.name = name
        
    def layerDeleted(self):
        self.render_thread.stop()