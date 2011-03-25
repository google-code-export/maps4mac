#
#  MapWindowDelegate.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 4/24/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
from AppKit import NSStringPboardType

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
        self.mapViewEnabled = False
        
        return self
    
    def awakeFromNib(self):
        self.mapView.addObserver_forKeyPath_options_context_(self, u"center", 0, None)
        self.mapView.addObserver_forKeyPath_options_context_(self, u"zoom", 0, None)
        self.mapView.addObserver_forKeyPath_options_context_(self, u"layers", 0, None)
        self.mapWindow.makeFirstResponder_(self.mapView)
    
    def connectToGPS_(self, gps):
        gps.addObserver_forKeyPath_options_context_(self, u"fix", 0, None)
        
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if keyPath == "center":
            self.centerField.setStringValue_("%f, %f" % (object.center.y, object.center.x))
        elif keyPath == "zoom":
            self.zoomField.setIntValue_(object.zoom)
        elif keyPath == "layers":
            self.mapViewEnabled = bool(object.layers)
        elif keyPath == "fix":
            fix = object.fix()
            if fix is not None and fix["FixType"] != 0:
                self.mapView.setFix_CenterOnGPS_(fix, self.useGPS)
    
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
        env = self.mapView.getWGS84Envelope()
        bbString = "%f, %f; %f, %f" % (env.minx, env.miny, env.maxx, env.maxy)
        
        pasteBoard = NSPasteboard.generalPasteboard()
        pasteBoard.declareTypes_owner_(NSArray.arrayWithObjects_(NSStringPboardType), None)
        pasteBoard.setString_forType_(bbString, NSStringPboardType)
