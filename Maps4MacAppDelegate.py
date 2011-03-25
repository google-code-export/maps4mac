#
#  Maps4MacAppDelegate.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 4/21/10.
#  Copyright __MyCompanyName__ 2010. All rights reserved.
#

from Foundation import *
from AppKit import *

import os.path, os
import Logger

class Maps4MacAppDelegate(NSObject):
    mapView   = objc.IBOutlet()
    mapWindow = objc.IBOutlet()
    mapWindowDelegate = objc.IBOutlet()
    
    openOSM2PGSQLDelegate = objc.ivar()
    httpTileOpenDelegate = objc.ivar()
    
    searchWindow = objc.IBOutlet()
    searchWindowDelegate = objc.IBOutlet()
    loggingWindow = objc.IBOutlet()
    preferencesWindow = objc.IBOutlet()
    
    mapName = objc.ivar()
    
    gpsdConnection = objc.ivar()
    logger = objc.ivar()
    
    downloadWindowDelegate = objc.IBOutlet()
    
    openOSM2PGSQLMenuItem = objc.IBOutlet()
    openOSM2SpatialLiteMenuItem = objc.IBOutlet()
    openMapnikXMLMenuItem = objc.IBOutlet()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        return self
    
    def awakeFromNib(self):
        self.dbList = None
        
    def applicationWillFinishLaunching_(self, sender):
        #self.mapWindow.makeFirstResponder_(self.mapView)
        self.mapWindow.setAcceptsMouseMovedEvents_(True)

    def applicationDidFinishLaunching_(self, sender):
        defaults = NSUserDefaults.standardUserDefaults()
            
        self.gpsdConnection = GPSdConnection.alloc().init()
        self.gpsdConnection.connect()
        
        self.logger = Logger.Logger.alloc().init()
        self.logger.connectToGPS_(self.gpsdConnection)
        self.mapWindowDelegate.connectToGPS_(self.gpsdConnection)
        
        self.logger.appDelegate = self
        
        if self.mapName is None:
            # There may already be a map loaded if we were asked to launch a file
            defaultWindow = defaults.integerForKey_("defaultWindow")
            #print defaultWindow
            if not defaultWindow or defaultWindow == 0:
                self.loadEmptyGlobe_(self)
            elif defaultWindow == 1:
                self.openSpatiaLite_(self)
            elif defaultWindow == 2:
                self.openosm2pgsql_(self)
            elif defaultWindow == 3:
                self.openMapnikXML_(self)
            else:
                print "Warning: Unknown default window:", defaultWindow
        
        
        if not defaults.integerForKey_("defaultOpenCommand"):
            defaults.setInteger_forKey_(0, "defaultOpenCommand")
        #defaults.addObserver_forKeyPath_options_context_(self, u"defaultOpenCommand", 0, None)
        NSUserDefaultsController.sharedUserDefaultsController().addObserver_forKeyPath_options_context_(self, u"values.defaultOpenCommand", 0, None)
        self.setCommandOAction_(defaults.integerForKey_("defaultOpenCommand"))
    
    def setCommandOAction_(self, menuTag):
        if not menuTag or menuTag == 1:
            self.openOSM2SpatialLiteMenuItem.setKeyEquivalent_("o")
            self.openOSM2SpatialLiteMenuItem.setKeyEquivalentModifierMask_(NSCommandKeyMask)
            
            self.openOSM2PGSQLMenuItem.setKeyEquivalent_("")
            self.openMapnikXMLMenuItem.setKeyEquivalent_("")
        elif menuTag == 2:
            self.openOSM2PGSQLMenuItem.setKeyEquivalent_("o")
            self.openOSM2PGSQLMenuItem.setKeyEquivalentModifierMask_(NSCommandKeyMask)
            
            self.openOSM2SpatialLiteMenuItem.setKeyEquivalent_("")
            self.openMapnikXMLMenuItem.setKeyEquivalent_("")
        elif menuTag == 3:
            self.openMapnikXMLMenuItem.setKeyEquivalent_("o")
            self.openMapnikXMLMenuItem.setKeyEquivalentModifierMask_(NSCommandKeyMask)
            
            self.openOSM2SpatialLiteMenuItem.setKeyEquivalent_("")
            self.openOSM2PGSQLMenuItem.setKeyEquivalent_("")
        
    def fetchMapnikFiles(self):
        urls = [
        ("http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/10m-populated-places.zip",
            "10m-populated-places.zip"),
        ("http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/110m-admin-0-boundary-lines.zip",
            "110m-admin-0-boundary-lines.zip"),
        ("http://tile.openstreetmap.org/world_boundaries-spherical.tgz",
            "world_boundaries-spherical.tgz"),
        ("http://tile.openstreetmap.org/processed_p.tar.bz2",
            "processed_p.tar.bz2"),
        ("http://tile.openstreetmap.org/shoreline_300.tar.bz2",
            "shoreline_300.tar.bz2"),
        ]

        save_path = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES)[0] + "/" + NSBundle.mainBundle().infoDictionary()["CFBundleName"] + "/mapnik_osm/"        
        
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        for url,file in urls:
            path = save_path + file
            if not os.path.exists(path):
                self.downloadWindowDelegate.queueURL_toPath_(url, path)
        
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if keyPath == "values.defaultOpenCommand":
            newKey = NSUserDefaults.standardUserDefaults().integerForKey_("defaultOpenCommand")
            print newKey
            self.setCommandOAction_(newKey)
    
    @objc.IBAction
    def openosm2pgsql_(self, sender):
        
        #self.fetchMapnikFiles()
    
        try:
            import osm2pgsql_MapnikLayer_OpenDialogDelegate
            if not self.openOSM2PGSQLDelegate:
                self.openOSM2PGSQLDelegate = osm2pgsql_MapnikLayer_OpenDialogDelegate.osm2pgsql_MapnikLayer_OpenDialogDelegate.alloc().init()
                self.openOSM2PGSQLDelegate.appDelegate = self
                
                NSBundle.loadNibNamed_owner_("osm2pgsql_MapnikLayer", self.openOSM2PGSQLDelegate)
            self.openOSM2PGSQLDelegate.window.makeKeyAndOrderFront_(self)
        except ImportError as error:
            self.openOSM2PGSQLDelegate.window.orderOut_(self)
            title = "Import failed"
            msg = "Couldn't find the modules needed for the osm2pgsql layer.\nYou probably need to install PyGreSQL.\n\n%s" % str(error)
            alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(title, None, None, None, msg)
            alert.runModal()
    
    def loadosm2pgsqlWithName_dbArgs_(self, mapName, db_args):
        path_prefix = NSBundle.mainBundle().resourcePath() + "/"
        
        style_filename = path_prefix + "styles/osm2pgsql/Maps4Mac Default.template"
        
        self.mapWindow.makeKeyAndOrderFront_(self)
        
        from osm2pgsql_MapnikLayer import osm2pgsql_MapnikLayer
        layer = osm2pgsql_MapnikLayer.alloc().init()
        layer.loadMap(db_args, mapName, style_filename)
                    
        if self.mapView.center is None:
            self.mapView.setCenter_(layer.getDefaultCenter())
            self.mapView.setZoom_(layer.getDefaultZoom())
        self.mapView.setMapLayer_(layer)            
        self.mapName = mapName
        
    @objc.IBAction
    def openSpatiaLite_(self, sender):
        path_prefix = NSBundle.mainBundle().resourcePath() + "/"
        style_filename = path_prefix + "styles/osm2spatialite/Maps4Mac Default.template"
        
        panel = NSOpenPanel.alloc().init()
        panel.setTitle_("Open osm2spatialite Database")
        if NSOKButton == panel.runModalForDirectory_file_types_(NSHomeDirectory(), None, None):
            filename = panel.filename()
            
            try:
                from osm2spatialite_MapnikLayer import osm2spatialite_MapnikLayer
                layer = osm2spatialite_MapnikLayer.alloc().init()
                layer.loadMap(filename, style_filename)
                
                if self.mapView.center is None:
                    self.mapView.setCenter_(layer.getDefaultCenter())
                    self.mapView.setZoom_(layer.getDefaultZoom())
                    
                self.mapView.setMapLayer_(layer)
                self.mapName = "SpatiaLite"
                
                self.mapWindow.makeKeyAndOrderFront_(self)
            except Exception as error:
                print error
                import traceback
                traceback.print_exc()
            
                title = "Couldn't open file"
                msg = "Maps4Mac couldn't open: \n%s\n\nReason:\n%s" % (filename,str(error))
                alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(title, None, None, None, msg)
                alert.runModal()

    @objc.IBAction
    def openMapnikXML_(self, sender):
        panel = NSOpenPanel.alloc().init()
        panel.setTitle_("Open Mapnik XML")
        if NSOKButton == panel.runModalForDirectory_file_types_(NSHomeDirectory(), None, ["xml"]):
            filename = panel.filename()
            
            from TiledMapnikLayer import TiledMapnikLayer
            layer = TiledMapnikLayer.alloc().init()
            layer.setMapXMLFile_(filename)
            layer.setName_("Mapnik: " + os.path.splitext(os.path.basename(filename))[0])
            
            
            if self.mapView.center is None:
                self.mapView.setCenter_(layer.getDefaultCenter())
                self.mapView.setZoom_(layer.getDefaultZoom())
                
            self.mapView.setMapLayer_(layer)
            self.mapName = "Mapnik"
            
            self.mapWindow.makeKeyAndOrderFront_(self)
            
    @objc.IBAction
    def openHTTPTiles_(self, sender):
        if not self.httpTileOpenDelegate:
            import HttpTileLayer_OpenDialogDelegate
            self.httpTileOpenDelegate = HttpTileLayer_OpenDialogDelegate.HttpTileLayer_OpenDialogDelegate.alloc().init()
            self.httpTileOpenDelegate.appDelegate = self
            
            NSBundle.loadNibNamed_owner_("HttpTileLayer", self.httpTileOpenDelegate)
        self.httpTileOpenDelegate.window.makeKeyAndOrderFront_(self)
    
    @objc.IBAction
    def loadEmptyGlobe_(self, sender):
        path_prefix = NSBundle.mainBundle().resourcePath() + "/"
        
        mapName = "Empty Globe"
        
        from TiledMapnikLayer import TiledMapnikLayer
        layer = TiledMapnikLayer.alloc().init()

        layer.setMapXMLFile_(path_prefix + "EmptyGlobeSQLite.xml")
        layer.setName_(mapName)
        
        if self.mapView.center is None:
            self.mapView.setCenter_([0, 0])
            self.mapView.setZoom_(50000)
        self.mapWindow.makeKeyAndOrderFront_(self)
        
        self.mapView.setMapLayer_(layer)
        self.mapName = mapName

    @objc.IBAction
    def clearLayers_(self, sender):
        self.mapView.clearLayers()
        
    def loadFile_(self,path):
        ext = os.path.splitext(path)[1].lower()
        
        try:
            if ext == ".gpx" or ext == "":
                from GenericDataLayer import fromGPXFile
                layer = fromGPXFile(path)
                layer.setName_("GPX: " + os.path.splitext(os.path.basename(path))[0])
                self.mapView.addLayer_(layer)
            elif ext == ".kml" or ext == ".kmz":
                from GenericDataLayer import fromKMLFile
                layer = fromKMLFile(path)
                layer.setName_("KML: " + os.path.splitext(os.path.basename(path))[0])
                self.mapView.addLayer_(layer)
            else:
                raise ValueError("Unknown file type: " + ext)
        except Exception as error:
            print error
            import traceback
            traceback.print_exc()
        
            title = "Couldn't open file"
            msg = "Maps4Mac couldn't open: \n%s\n\nReason:\n%s" % (path,str(error))
            alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(title, None, None, None, msg)
            alert.runModal()
    
    def application_openFile_(self, app, filename):
        if self.mapName is None:
            self.loadEmptyGlobe_(self)
        
        self.loadFile_(filename)
    
    @objc.IBAction
    def loadLayerFromFile_(self, sender):
        if (not self.mapView.getLayers()):
            # No map layer, datalayer won't work
            return
        
        panel = NSOpenPanel.alloc().init()
        panel.setTitle_("Open File Layer")
        if NSOKButton == panel.runModalForDirectory_file_types_(NSHomeDirectory(), None, ["gpx", "kml", "kmz"]):
            self.loadFile_(panel.filename())