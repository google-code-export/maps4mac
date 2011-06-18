#
#  HttpTileLayer.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 11/25/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

from Foundation import *
#from AppKit import NSCalibratedRGBColorSpace, NSDeviceRGBColorSpace, NSZeroRect, NSCompositeCopy, NSAlphaFirstBitmapFormat
from Quartz import *

import MapLayer
import math
import mapnik
import time

import NominatimSearchProvider

#TODO: http://developer.mapquest.com/web/products/open/map
        
def calcTileXY(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x = int((lon_deg + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return NSPoint(x, y)


def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return mapnik.Coord(lon_deg,lat_deg)

class HttpTileLayer(MapLayer.MapLayer):
    zoom = objc.ivar()
    url  = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.name = "HTTP Tiles"
        
        # AFAIK All "tile" style maps are in the google projection
        self.projectionString = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over"
        self.cache  = dict()
        self.zoom   = 0
        self.tileZoom = 18
        self.view = None
        
        self.maxConnections = 4
        self.connections = dict()
        self.requestQueue = list()
        
        return self
    
    def setMapURL_(self, url):
        if url.startswith("http://"):
            self.name = url[7:].split('/')[0]
        else:
            self.name = url.split('/')[0]
        
        # Expand our simple vars into real python substitutions
        self.url = url.replace("%z", "%(z)d").replace("%x", "%(x)d").replace("%y", "%(y)d")
        print "HTTP Tile Layer URL:", self.url
        
        self.description = "HTTP Tiles from:\n" + self.url
        
        if "openstreetmap.org" in url:
            self.maxConnections = 2 # Obey OSMs max tile query limits
        else:
            self.maxConnections = 4
    
    def getSearchProvider(self):
        return NominatimSearchProvider.NominatimSearchProvider.alloc().init()
    
    def getDefaultZoom(self):
        return 78271 # z1
    
    def drawRect_WithProjection_Origin_Zoom_(self, rect, proj, origin, zoom):
        try:
            # map zoom to tile zoom
            #FIXME: The google zooms don't appear to be whole numbers (in terms of pixels/projection), either we need to support
            #       fractional zooms for this type of layer or we need to pick the closes tile size and just stretch it.
            
            zoomMap = {
                        0: 156543.033928,
                        1: 78271.516964,
                        2: 39135.758482,
                        3: 19567.879241,
                        4: 9783.9396205,
                        5: 4891.96981025,
                        6: 2445.98490513,
                        7: 1222.99245256,
                        8: 611.496226281,
                        9: 305.748113141,
                        10: 152.87405657,
                        11: 76.4370282852,
                        12: 38.2185141426,
                        13: 19.1092570713,
                        14: 9.55462853565,
                        15: 4.77731426782,
                        16: 2.38865713391,
                        17: 1.19432856695,
                        18: 0.597164283477,
                        19: 0.30 # From Bing zoom list: http://msdn.microsoft.com/en-us/library/cc161076.aspx
                      }
            
            z = 19
            while z > 0 and zoomMap[z] < zoom * .8:
                z -= 1
            #print "zoom",zoom,"true zoom",zoomMap[z],"z-level",z
            
            if self.tileZoom != z:
                self.cancelPending()
                self.cache = dict()
            self.tileZoom = z
            
            topRight  = proj.inverse(origin + mapnik.Coord(rect.size[0] * zoom, rect.size[1] * zoom))
            lowerLeft = proj.inverse(origin)
            
            ll = calcTileXY(lowerLeft.y,lowerLeft.x, z)
            tr = calcTileXY(topRight.y,topRight.x, z)
            
            #print "LL:", ll
            #print "TR:", tr
            
            for x in range(min(ll.x, tr.x) - 1, max(ll.x, tr.x) + 1):
                for y in range(min(ll.y, tr.y) - 1, max(ll.y, tr.y) + 1):
                    if x in self.cache and y in self.cache[x]:
                        tile = self.cache[x][y]
                        #tileOrigin = num2deg(x, y, z)
                        tileOrigin = num2deg(x, y + 1, z)
                        tileOrigin = proj.forward(tileOrigin)
                        tileOrigin -= origin
                        tileOrigin /= zoom
                        #tileOrigin = NSPoint(int(tileOrigin.x), int(tileOrigin.y))
                        tileTop = num2deg(x + 1, y, z)
                        tileTop = proj.forward(tileTop)
                        tileTop -= origin
                        tileTop /= zoom
                        tileSize = tileTop - tileOrigin
                        #FIXME: It would look nicer to force these to integers so we didn't end up with lines between tiles, but
                        #       simple rounding isn't enough.
                        targetRect = NSRect([tileOrigin.x, tileOrigin.y], [tileSize.x, tileSize.y])
                        #print "Tile is z:", tileSize.x / 256, tileSize.y / 256
                        if tile:
                            if tile["img"]:
                                #tile["img"].drawAtPoint_fromRect_operation_fraction_(tileOrigin, NSZeroRect, NSCompositeCopy, 1.0)
                                tile["img"].drawInRect_fromRect_operation_fraction_(targetRect, NSZeroRect, NSCompositeCopy, 1.0)
                            else:
                                NSColor.redColor().setFill()
                                NSRectFill(NSRect([int(tileOrigin.x), int(tileOrigin.y)], [256,256]))
                        else:
                            # Null == pending tile
                            NSColor.darkGrayColor().setFill()
                            NSRectFill(NSRect([int(tileOrigin.x), int(tileOrigin.y)], [256,256]))
                    else:
                        self.requestTileAtX_Y_Zoom_(x, y, z)
        except Exception as e:
            print e
            import traceback
            traceback.print_exc()
            
            NSColor.redColor().setFill()
            NSRectFill(rect)
    
    def requestTileAtX_Y_Zoom_(self, x, y, zoom):
        if not x in self.cache:
            self.cache[x] = dict()
        self.cache[x][y] = None

        self.requestQueue.append([x, y, zoom])
        print "Requesting:", [x, y, zoom], "Active:", len(self.connections), "Pending:", len(self.requestQueue)
        self.fetchQueue()
    
    def cancelPending(self):
        self.requestQueue = list()
        for connection in self.connections.keys():
            connection.cancel()
            self.connections[connection] = None
            del self.connections[connection]
    
    def fetchQueue(self):
        while len(self.connections) < self.maxConnections and self.requestQueue:
            x, y, zoom = self.requestQueue.pop()
            url = self.url % {'x':x, 'y':y, 'z':zoom}
            request = NSURLRequest.requestWithURL_(NSURL.URLWithString_(url))
            conn = NSURLConnection.connectionWithRequest_delegate_(request, self)
            self.connections[conn] = {"data":NSMutableData.dataWithLength_(0),
                                      "url":url,
                                      "tileX":x,
                                      "tileY":y,
                                      "tileZoom":zoom,
                                     }
            print "Connecting:", url, "Active:", len(self.connections), "Pending:", len(self.requestQueue)
    
    # Connection delegate methods:
    def connection_didReceiveResponse_(self, connection, response):
        #FIXME: Take care of 404 here? response.statusCode()
        self.connections[connection]["data"].setLength_(0)
    
    def connection_didReceiveData_(self, connection, data):
        self.connections[connection]["data"].appendData_(data)
    
    def connection_didFailWithError_(self, connection, error):
        print "HTTP tile fetch failed:", error
        self.connections[connection] = None
        del self.connections[connection]
        
        self.fetchQueue()
    
    def connectionDidFinishLoading_(self, connection):
        # If the request was for an old zoom just ignore it
        request = self.connections[connection]
        if self.tileZoom == request["tileZoom"]:
            img = NSImage.alloc().initWithData_(request["data"])
            if img:
                url = request["url"]
                self.cache[request["tileX"]][request["tileY"]] = {"url":url, "img":img, "fetched":time.time()}
            
            if self.view:
                self.view.setNeedsDisplay_(True)
        
        self.connections[connection] = None
        del self.connections[connection]
        
        self.fetchQueue()



