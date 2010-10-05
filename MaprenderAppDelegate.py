#
#  MaprenderAppDelegate.py
#  Maprender
#
#  Created by Daniel Sabo on 4/21/10.
#  Copyright __MyCompanyName__ 2010. All rights reserved.
#

from Foundation import *
from AppKit import *

import pgdb as DBAPI
import loaddb

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
        #self.mapWindow.makeFirstResponder_(self.mapView)
        self.mapWindow.setAcceptsMouseMovedEvents_(True)
        
        defaults = NSUserDefaults.standardUserDefaults()
        
        port = defaults.stringForKey_("db_portnumber")
        host = defaults.stringForKey_("db_hostname")
        if port:
            host = host + ":" + port
        
        self.db_args = {
            "host":defaults.stringForKey_("db_hostname"),
            "user":defaults.stringForKey_("db_username"),
            "database":defaults.stringForKey_("db_database"),
            "password":defaults.stringForKey_("db_password")
        }
        
        newList = loaddb.get_current_names(**self.db_args)
        newList.sort()
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
    
    def buildXML(self, db_prefix):
        path_prefix = NSBundle.mainBundle().bundlePath() + "/Contents/Resources/"
        
        xml_file = open(path_prefix + "styles/osm_style.xml.template")
        xml = xml_file.read()
        xml_file.close()
        
        con = DBAPI.connect(**self.db_args)
        try:
            cur = con.cursor()
            cur.execute("select proj4text from spatial_ref_sys where srid=Find_SRID('public', '%s','way')" % (db_prefix + "_point"))
            proj4 = cur.fetchall()[0][0]
        finally:
            con.close()
        
        parameters = {
        "symbols":path_prefix + "symbols/",
        #"osm2pgsql_projection": "&srs900913;", #FIXME: Get from DB
        "osm2pgsql_projection":proj4,
        "world_boundaries":path_prefix + "world_boundaries/",
        "prefix":db_prefix,
        #"datasource_settings":,
        }
        
        defaults = NSUserDefaults.standardUserDefaults()
        
        host = defaults.stringForKey_("db_hostname")
        port = defaults.stringForKey_("db_portnumber")
        if not port:
            port = 5432 #FIXME: Get rid of the magic number
        user = defaults.stringForKey_("db_username")
        database = defaults.stringForKey_("db_database")
        password = defaults.stringForKey_("db_password")
        
        
        import mapnik
        #projection = mapnik.Projection(proj4)
        epsg900913 = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +units=m +k=1.0 +nadgrids=@null +no_defs"
        projection = mapnik.Projection(epsg900913)
        # Not quite but close to the whole world
        extent = [projection.forward(mapnik.Coord(180.0,89.0)),projection.forward(mapnik.Coord(-180.0,-89.0))]
        
        datasource_parameters = {
        "password":password,
        "host":host,
        "port":port,
        "user":user,
        "dbname":self.db_args["database"],
        "estimate_extent":"false",
        #"extent":"19926188.852,30240971.9584,-19926188.852,-30240971.9584",
        "extent":"%f,%f,%f,%f" % (extent[0].x,extent[0].y,extent[1].x,extent[1].y),
        }

        parameters["datasource_settings"] = \
        """
        <Parameter name="type">postgis</Parameter>
        <Parameter name="password">%(password)s</Parameter>
        <Parameter name="host">%(host)s</Parameter>
        <Parameter name="port">%(port)s</Parameter>
        <Parameter name="user">%(user)s</Parameter>
        <Parameter name="dbname">%(dbname)s</Parameter>
        <!-- this should be 'false' if you are manually providing the 'extent' -->
        <Parameter name="estimate_extent">%(estimate_extent)s</Parameter>
        <!-- manually provided extent in epsg 900913 for whole globe -->
        <!-- providing this speeds up Mapnik database queries -->
        <Parameter name="extent">%(extent)s</Parameter>
        """ % datasource_parameters
        
        xml = xml % parameters
        
        return str(xml)
    
    @objc.IBAction
    def loadMap_(self, sender):
        row = self.dbTableView.selectedRow()
        if self.dbList is not None and row != -1:
            mapName = self.dbList[row]
            
            self.mapWindowDelegate.setDBParams(self.db_args)
            self.mapWindowDelegate.loadMap_(mapName)
            
            #path = "/Users/argon/Prog/Maprender/" + mapName + ".xml"
            
            from TiledMapnikLayer import TiledMapnikLayer
            
            layer = TiledMapnikLayer.alloc().init()
            #layer.setMapXMLFile_(path)
            layer.setMapXML_(self.buildXML(mapName))
            self.mapView.setMapLayer_(layer)
            
            self.mapName = mapName
            self.searchWindowDelegate.db_args = self.db_args
            self.searchWindowDelegate.mapName = mapName
            self.inspectWindowDelegate.setDBParams(self.db_args)
            self.inspectWindowDelegate.setMapName_(mapName)
            
            self.selectDBWindow.orderOut_(self)

    @objc.IBAction
    def clearLayers_(self, sender):
        self.mapView.clearLayers()
    
    @objc.IBAction
    def loadGPXFile_(self, sender):
        #FIXME: Disable the menu too
        if (not self.mapView.getLayers()):
            # No map layer, datalayer won't work
            return
        
        panel = NSOpenPanel.alloc().init()
        if NSOKButton == panel.runModalForDirectory_file_types_(NSHomeDirectory(), None, ["gpx"]):
            path = panel.filename()
            
            from GenericDataLayer import fromGPXFile
            layer = fromGPXFile(path)
            
            self.mapView.addLayer_(layer)