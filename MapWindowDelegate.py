#
#  MapWindowDelegate.py
#  Maprender
#
#  Created by Daniel Sabo on 4/24/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
from AppKit import NSStringPboardType
import pgdb as DBAPI
import mapnik

class MapWindowDelegate(NSObject):
    mapView   = objc.IBOutlet()
    mapWindow = objc.IBOutlet()
    
    mapCenterLat = objc.ivar()
    mapCenterLon = objc.ivar()
    mapZoom      = objc.ivar()
    
    latField = objc.IBOutlet()
    lonField = objc.IBOutlet()
    zoomField = objc.IBOutlet()
    
    useGPS = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.mapCenterLat = 0.0
        self.mapCenterLon = 0.0
        self.mapZoom = 100
        
        self.useGPS = False
        
        return self
    
    def awakeFromNib(self):
        self.db_args = None
        #self.mapView.setCenter_([self.mapCenterLat, self.mapCenterLon])
        #self.mapView.setZoom_(self.mapZoom)
        self.mapView.addObserver_forKeyPath_options_context_(self, u"centerLonLat", 0, None)
        self.mapView.addObserver_forKeyPath_options_context_(self, u"zoom", 0, None)
    
    def setDBParams(self,dbParams):
        #FIXME: This should be replaced by preferences
        self.db_args = dbParams
    
    def loadMap_(self, mapName):
        con = DBAPI.connect(**self.db_args)
        try:
            table = mapName + "_polygon"
            cur = con.cursor()
            cur.execute("select proj4text from spatial_ref_sys where srid=Find_SRID('public', '%s','way')" % table)
            proj4 = cur.fetchall()[0][0]
            #FIXME: This needs to use the mapnik projection not the DB one...
            prj = mapnik.Projection(str(proj4))
            cur.execute("select ST_XMin(st_estimated_extent),ST_YMin(st_estimated_extent),ST_XMax(st_estimated_extent),ST_YMax(st_estimated_extent) from ST_Estimated_Extent('%s','way');" % table)
            bounds = cur.fetchall()[0]
            size = [bounds[2] - bounds[0], bounds[3] - bounds[1]]
            center = [size[0] + bounds[0], size[1] + bounds[1]]
            center_ll = prj.inverse(mapnik.Coord(center[0], center[1]))
            self.mapCenterLat = center_ll.x
            self.mapCenterLon = center_ll.y
            self.mapView.setCenter_([self.mapCenterLat, self.mapCenterLon])
        finally:
            con.close()
        
        #FIXME: Calculate Zoom
        self.mapZoom = self.mapView.zoom
            
        self.mapWindow.makeKeyAndOrderFront_(self)
        
        
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if keyPath == "centerLonLat":
            self.mapCenterLat = object.center.y
            self.mapCenterLon = object.center.x
        elif keyPath == "zoom":
            self.mapZoom = object.zoom
    
    @objc.IBAction
    def updateMap_(self, sender):
        self.mapCenterLat = float(self.latField.stringValue())
        self.mapCenterLon = float(self.lonField.stringValue())
        self.mapZoom = int(self.zoomField.stringValue())
        
        self.mapView.setCenter_([float(self.mapCenterLon), float(self.mapCenterLat)])
        self.mapView.setZoom_(self.mapZoom)
        self.mapView.setNeedsDisplay_(True)
        
    @objc.IBAction
    def copyPosition_(self, sender):
        posString = "%f %f" % (self.mapCenterLat, self.mapCenterLon)
    
        pasteBoard = NSPasteboard.generalPasteboard()
        pasteBoard.declareTypes_owner_(NSArray.arrayWithObjects_(NSStringPboardType), None)
        pasteBoard.setString_forType_(posString, NSStringPboardType)
    
    @objc.IBAction
    def copyViewBounds_(self, sender):
        size = self.mapView.bounds().size
        zoom = self.mapView.zoom
        prj  = self.mapView.projection
        prj_center = prj.forward(self.mapView.center)
        prj_origin = mapnik.Coord(-(size[0] / 2) * zoom, -(size[1] / 2) * zoom)
        prj_size   = mapnik.Coord(size[0], size[1]) * zoom
        c0 = prj_center + prj_origin
        c1 = c0 + prj_size
        c0 = prj.inverse(c0)
        c1 = prj.inverse(c1)
        bbString = "%f, %f; %f, %f" % (c1.x, c1.y, c0.x, c0.y)
        
        pasteBoard = NSPasteboard.generalPasteboard()
        pasteBoard.declareTypes_owner_(NSArray.arrayWithObjects_(NSStringPboardType), None)
        pasteBoard.setString_forType_(bbString, NSStringPboardType)
