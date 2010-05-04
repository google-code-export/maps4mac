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
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        return self
    
    def awakeFromNib(self):
        self.dbList = None

    def applicationDidFinishLaunching_(self, sender):
        NSLog("Application did finish launching.")
        self.mapWindow.makeFirstResponder_(self.mapView)
        self.mapWindow.setAcceptsMouseMovedEvents_(True)
        
        db_args = {'host':'localhost', 'user':'postgres', 'database':'osm_test'}
        newList = loaddb.get_current_names(**db_args)
        self.dbList = newList
        self.dbListSource.setList_(newList)
    
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
            