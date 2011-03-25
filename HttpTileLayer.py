#
#  HttpTileLayer.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 11/25/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
#from AppKit import NSCalibratedRGBColorSpace, NSDeviceRGBColorSpace, NSZeroRect, NSCompositeCopy, NSAlphaFirstBitmapFormat
from Quartz import *

import MapLayer
import math
import mapnik

class HttpTileLayer(MapLayer.MapLayer):
    zoom = objc.ivar()
    url  = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.name = "HTTP Tiles"
        
        # AFAIK All "tile" style maps are in the google projection?
        self.projectionString = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over"
        self.cache  = dict()
        self.zoom   = 0
        self.view = None
        
        return self
    
    def setMapURL_(self, url):
        self.url = url
        if url.startswith("http://"):
            self.name = url[7:].split('/')[0]
        else:
            self.name = url.split('/')[0]
        
    def drawRect_WithProjection_Origin_Zoom_(self, rect, proj, origin, zoom):
        NSColor.grayColor().setFill()
        NSRectFill(rect)
        
        # map zoom to tile zoom
        #FIXME: It's very likely these aren't the real values, they
        z = 18
        zoomIn  = [1, 25, 50,125,250,500,1000,2000,4000,7500,15000,30000,65000,125000,250000,500000,1000000,2000000,2000000]
        zoomOut = [18,17, 16, 15, 14, 13,  12,  11,  10,   9,    8,    7,    6,     5,     4,     3,      2,      1,      0]
        index = 0
        while index < len(zoomIn) and zoomIn[index] < zoom:
            index += 1
            z = zoomOut[index]
        
        topRight  = proj.inverse(origin + mapnik.Coord(rect.size[0] * zoom, rect.size[1] * zoom))
        lowerLeft = proj.inverse(origin)
        
        def calcTileURL(lat_deg, lon_deg):
            lat_rad = math.radians(lat_deg)
            #n = 2.0 ** zoom
            n = 2.0 ** z
            x = int((lon_deg + 180.0) / 360.0 * n)
            y = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
            return self.url % {'z':z,'x':x,'y':y}
        
        # Calculate tile URLs
        try:
            print calcTileURL(lowerLeft.y,lowerLeft.x)
            print calcTileURL(topRight.y,topRight.x)
        except ValueError:
            print "Bad lat,lon:",lowerLeft.y,lowerLeft.x
        
    def drawTile(self):
        proj = mapnik.Projection(self.projectionString)
        xtile, ytile, zoom = 0,0,0
        def num2deg(xtile, ytile, zoom):
           n = 2.0 ** zoom
           lon_deg = xtile / n * 360.0 - 180.0
           lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
           lat_deg = math.degrees(lat_rad)
           #return(lat_deg, lon_deg)
           return mapnik.Coord(lon_deg,lat_deg)
        
        # Get the projection coordinates for the tile's corners
        proj.forward(num2deg(xtile, ytile, zoom))
        proj.forward(num2deg(xtile+1, ytile+1, zoom))
        