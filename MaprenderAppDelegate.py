#
#  MaprenderAppDelegate.py
#  Maprender
#
#  Created by Daniel Sabo on 4/21/10.
#  Copyright __MyCompanyName__ 2010. All rights reserved.
#

from Foundation import *
from AppKit import *

import loaddb
from TiledMapnikLayer import TiledMapnikLayer

class MaprenderAppDelegate(NSObject):
    dbListSource = objc.IBOutlet()
    dbTableView  = objc.IBOutlet()
    mapView   = objc.IBOutlet()
    mapWindow = objc.IBOutlet()
    mapWindowDelegate = objc.IBOutlet()
    
    searchWindow = objc.IBOutlet()
    searchWindowDelegate = objc.IBOutlet()
    loggingWindow = objc.IBOutlet()
    
    mapName = objc.ivar()
    
    gpsdConnection = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        return self
    
    def awakeFromNib(self):
        self.dbList = None

    def applicationDidFinishLaunching_(self, sender):
        NSLog("Application did finish launching.")
        #self.mapWindow.makeFirstResponder_(self.mapView)
        self.mapWindow.setAcceptsMouseMovedEvents_(True)
        
        db_args = {'host':'localhost', 'user':'postgres', 'database':'osm_test'}
        newList = loaddb.get_current_names(**db_args)
        self.dbList = newList
        self.dbListSource.setList_(newList)
        
        self.gpsdConnection = GPSdConnection.alloc().init()
        self.gpsdConnection.connect()
        self.gpsdConnection.addObserver_forKeyPath_options_context_(self, u"fix", 0, None)
        
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if keyPath == "fix":
            fix = object.fix()
            if fix["FixType"]:
                self.mapView.setFixLat_Lon_(fix["Latitude"], fix["Longitude"])
                if self.mapWindowDelegate.useGPS:
                    self.mapView.setCenter_((fix["Longitude"], fix["Latitude"]))
    
    @objc.IBAction
    def loadMap_(self, sender):
        row = self.dbTableView.selectedRow()
        if self.dbList is not None and row != -1:
            mapName = self.dbList[row]
            
            self.mapWindowDelegate.setDBParams({'host':'localhost', 'user':'postgres', 'database':'osm_test'})
            self.mapWindowDelegate.loadMap_(mapName)
            
            path = "/Users/argon/Prog/Maprender/" + mapName + ".xml"
            
            layer = TiledMapnikLayer.alloc().init()
            layer.setMapXML_(path)
            self.mapView.setLayer_(layer)
            
            self.mapName = mapName
            self.searchWindowDelegate.db_args = {'host':'localhost', 'user':'postgres', 'database':'osm_test'}
            self.searchWindowDelegate.mapName = mapName
        
    @objc.IBAction
    def showSearchWindow_(self, sender):
        if self.searchWindow:
            self.searchWindow.makeKeyAndOrderFront_(self)
    
    @objc.IBAction
    def showLoggingWindow_(self, sender):
        if self.loggingWindow:
            self.loggingWindow.makeKeyAndOrderFront_(self)
    
            