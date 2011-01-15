#
#  MapWindowDelegate.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 4/24/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
from AppKit import NSStringPboardType
import mapnik

class MapWindowDelegate(NSObject):
    mapView   = objc.IBOutlet()
    mapWindow = objc.IBOutlet()
    
    centerField = objc.IBOutlet()
    zoomField = objc.IBOutlet()
    
    useGPS = objc.ivar()
    
    mapViewEnabled = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.useGPS = False
        
        return self
    
    def awakeFromNib(self):
        self.mapView.addObserver_forKeyPath_options_context_(self, u"centerLonLat", 0, None)
        self.mapView.addObserver_forKeyPath_options_context_(self, u"zoom", 0, None)
        self.mapView.addObserver_forKeyPath_options_context_(self, u"layers", 0, None)
        self.mapWindow.makeFirstResponder_(self.mapView)
        
        mapViewEnabled = False
        
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if keyPath == "centerLonLat":
            self.centerField.setStringValue_("%f, %f" % (object.center.y, object.center.x))
        elif keyPath == "zoom":
            self.zoomField.setIntValue_(object.zoom)
        elif keyPath == "layers":
            self.mapViewEnabled = bool(object.layers)
    
    @objc.IBAction
    def updateMap_(self, sender):
        try:
            # FIXME: Handle D M"S'
            lat,lon = map(float, self.centerField.stringValue().split(","))
            mapZoom = int(self.zoomField.stringValue())
        except ValueError:
            # Couldn't parse something, do nothing
            #FIXME: Mark what is wrong
            return
        
        self.mapView.setCenter_([lon,lat])
        self.mapView.setZoom_(mapZoom)
        
    @objc.IBAction
    def copyPosition_(self, sender):
        centerCoord = self.mapView.center
        posString = "%f, %f" % (centerCoord.y, centerCoord.x)
    
        pasteBoard = NSPasteboard.generalPasteboard()
        pasteBoard.declareTypes_owner_(NSArray.arrayWithObjects_(NSStringPboardType), None)
        pasteBoard.setString_forType_(posString, NSStringPboardType)
    
    @objc.IBAction
    def copyViewBounds_(self, sender):
        #FIXME: This should be a call to the map view
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
