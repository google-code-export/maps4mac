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
import os.path, os

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
    
    downloadWindowDelegate = objc.IBOutlet()
    
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
        
        self.fetchMapnikFiles()
        
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
        if keyPath == "fix":
            fix = object.fix()
            if fix is not None and fix["FixType"] != 0:
                self.mapView.setFixLat_Lon_CenterOnGPS_(fix["Latitude"], fix["Longitude"],self.mapWindowDelegate.useGPS)
            #else:
            #    self.mapView.clearFix()
    
    def buildXML(self, db_prefix, style_filename):
        #path_prefix = NSBundle.mainBundle().bundlePath() + "/Contents/Resources/"
        path_prefix = NSBundle.mainBundle().resourcePath() + "/"
        
        #xml_file = open(path_prefix + "styles/osm_style.xml.template")
        
        with open(style_filename) as style_file:
            xml = style_file.read()
        
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
            #path_prefix = NSBundle.mainBundle().bundlePath() + "/Contents/Resources/"
            path_prefix = NSBundle.mainBundle().resourcePath() + "/"
            
            style_filename = path_prefix + "styles/osm_style.xml.template"
            
            mapName = self.dbList[row]
            
            self.mapWindow.makeKeyAndOrderFront_(self)
            
            #path = "/Users/argon/Prog/Maprender/" + mapName + ".xml"
            
            from TiledMapnikLayer import TiledMapnikLayer
            
            layer = TiledMapnikLayer.alloc().init()
            #layer.setMapXMLFile_(path)
            layer.setMapXML_(self.buildXML(mapName,style_filename))
            layer.setName_("Mapnik: " + mapName)
            
            #FIXME: This should probably be a feature of the layer but I don't want to put DB code in that class if it can be avoided
            center = None
            if self.mapView.center is None:
                con = DBAPI.connect(**self.db_args)
                try:
                    cur = con.cursor()
                    cur.execute("select ST_AsText(ST_centroid(transform(ST_SetSRID(ST_estimated_extent('%s','way'), Find_SRID('public','%s','way')),4326)))" % (mapName + "_point", mapName + "_point"))
                    center = map(float, cur.fetchall()[0][0][6:-1].split())
                finally:
                    con.close()
            
            self.mapView.setMapLayer_(layer)
            if center is not None:
                self.mapView.setCenter_(center)
            
            self.mapName = mapName
            self.searchWindowDelegate.db_args = self.db_args
            self.searchWindowDelegate.mapName = mapName
            self.inspectWindowDelegate.setDBParams(self.db_args)
            self.inspectWindowDelegate.setMapName_(mapName)
            
            self.selectDBWindow.orderOut_(self)
    
    def loadEmptyGlobe(self):
        path_prefix = NSBundle.mainBundle().resourcePath() + "/"
        
        style_filename = path_prefix + "Empty Globe.template"
        with open(style_filename) as style_file:
            xml = style_file.read()
        
        mapName = "Empty Globe"
        
        from TiledMapnikLayer import TiledMapnikLayer
        
        parameters = {
            "symbols":path_prefix + "symbols/",
            "osm2pgsql_projection": "&srs900913;",
            #"osm2pgsql_projection":proj4,
            "world_boundaries":path_prefix + "world_boundaries/",
            #"prefix":db_prefix,
        }
        
        layer = TiledMapnikLayer.alloc().init()
        layer.setMapXML_(str(xml % parameters))
        
        layer.setName_("Mapnik: " + mapName)
        
        self.mapView.setMapLayer_(layer)
        
        self.mapName = mapName
        #self.searchWindowDelegate.db_args = self.db_args
        #self.searchWindowDelegate.mapName = mapName
        #self.inspectWindowDelegate.setDBParams(self.db_args)
        #self.inspectWindowDelegate.setMapName_(mapName)
        
        #self.selectDBWindow.orderOut_(self)
        
        self.mapView.setCenter_([0, 0])
        #self.mapView.setZoom_(50000)
        #self.mapWindow.orderBack_(self)
        self.mapWindow.orderFront_(self)
    
    @objc.IBAction
    def setMapStyle_(self, style_filename):
        from TiledMapnikLayer import TiledMapnikLayer
        
        layer = TiledMapnikLayer.alloc().init()
        #layer.setMapXMLFile_(path)
        layer.setMapXML_(self.buildXML(self.mapName,style_filename))
        self.mapView.setMapLayer_(layer)


    @objc.IBAction
    def clearLayers_(self, sender):
        self.mapView.clearLayers()
        
    def loadFile_(self,path):
        ext = os.path.splitext(path)[1].lower()
        
        if ext == ".gpx" or ext == "":
            from GenericDataLayer import fromGPXFile
            try:
                layer = fromGPXFile(path)
                layer.setName_("GPX: " + os.path.splitext(os.path.basename(path))[0])
                self.mapView.addLayer_(layer)
            except Exception as error:
                print error
        elif ext == ".kml":
            from GenericDataLayer import fromKMLFile
            try:
                layer = fromKMLFile(path)
                layer.setName_("KML: " + os.path.splitext(os.path.basename(path))[0])
                self.mapView.addLayer_(layer)
            except Exception as error:
                print error
    
    def application_openFile_(self, app, filename):
        if self.mapName is None:
            self.loadEmptyGlobe()
        
        self.loadFile_(filename)
    
    @objc.IBAction
    def loadLayerFromFile_(self, sender):
        #FIXME: Disable the menu too
        if (not self.mapView.getLayers()):
            # No map layer, datalayer won't work
            return
        
        panel = NSOpenPanel.alloc().init()
        if NSOKButton == panel.runModalForDirectory_file_types_(NSHomeDirectory(), None, ["gpx", "kml"]):
            self.loadFile_(panel.filename())