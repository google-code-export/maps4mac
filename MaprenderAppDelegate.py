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
from GenericDataLayer import GenericDataLayer, GenericDataset
import csv

class MaprenderAppDelegate(NSObject):
    dbListSource = objc.IBOutlet()
    dbTableView  = objc.IBOutlet()
    mapView   = objc.IBOutlet()
    mapWindow = objc.IBOutlet()
    mapWindowDelegate = objc.IBOutlet()
    
    selectDBWindow = objc.IBOutlet()
    
    searchWindow = objc.IBOutlet()
    searchWindowDelegate = objc.IBOutlet()
    loggingWindow = objc.IBOutlet()
    preferencesWindow = objc.IBOutlet()
    
    inspectWindow = objc.IBOutlet()
    inspectWindowDelegate = objc.IBOutlet()
    
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
        
        defaults = NSUserDefaults.standardUserDefaults()
        
        self.db_args = {
            "host":defaults.stringForKey_("db_hostname"),
            "user":defaults.stringForKey_("db_username"),
            "database":defaults.stringForKey_("db_database"),
            "password":defaults.stringForKey_("db_password")
        }
        
        #self.db_args = {'host':'localhost', 'user':'postgres', 'database':'osm_test'}
        newList = loaddb.get_current_names(**self.db_args)
        self.dbList = newList
        self.dbListSource.setList_(newList)
        
        self.gpsdConnection = GPSdConnection.alloc().init()
        self.gpsdConnection.connect()
        self.gpsdConnection.addObserver_forKeyPath_options_context_(self, u"fix", 0, None)
        
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if keyPath == "fix":
            fix = object.fix()
            if fix is not None and fix["FixType"]:
                self.mapView.setFixLat_Lon_(fix["Latitude"], fix["Longitude"])
                if self.mapWindowDelegate.useGPS:
                    self.mapView.setCenter_((fix["Longitude"], fix["Latitude"]))
    
    @objc.IBAction
    def loadMap_(self, sender):
        row = self.dbTableView.selectedRow()
        if self.dbList is not None and row != -1:
            mapName = self.dbList[row]
            
            self.mapWindowDelegate.setDBParams(self.db_args)
            self.mapWindowDelegate.loadMap_(mapName)
            
            path = "/Users/argon/Prog/Maprender/" + mapName + ".xml"
            
            layer = TiledMapnikLayer.alloc().init()
            layer.setMapXML_(path)
            self.mapView.setMapLayer_(layer)
            
            self.mapName = mapName
            self.searchWindowDelegate.db_args = self.db_args
            self.searchWindowDelegate.mapName = mapName
            self.inspectWindowDelegate.setDBParams(self.db_args)
            self.inspectWindowDelegate.setMapName_(mapName)
            
            # Experimental hackery
            #reader = csv.reader(open("/Users/argon/Downloads/Campground Info/NORTHWEST.csv"))
            #ds = GenericDataset.alloc().init()
            #for line in reader:
            #    point = NSPoint(float(line[0]), float(line[1]))
            #    ds.points.append(point)
            #layer = GenericDataLayer.alloc().init()
            #layer.datasets.append(ds)
            
            #self.mapView.addLayer_(layer)
            
            self.selectDBWindow.orderOut_(self)
            