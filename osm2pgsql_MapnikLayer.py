#
#  osm2pgsql_MapnikLayer.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 12/14/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *

import TiledMapnikLayer
import osm2pgsql_SearchProvider

import pgdb as DBAPI

import glob, os.path

class osm2pgsql_MapnikLayer(TiledMapnikLayer.TiledMapnikLayer):
    mapName = objc.ivar()
    mapExtent = objc.ivar()
    db_args = objc.ivar()

    def init(self):
        self = super(osm2pgsql_MapnikLayer, self).init()
        if self is None:
            return None
        
        db_args = None
        
        return self
    
    def loadMap(self, db_args, mapName, style_filename):
        self.db_args = db_args
        self.mapName = mapName
        
        self.setMapXML_(self.buildXML(mapName,style_filename))
        self.setName_("Mapnik: " + mapName)
    
    def setStyle(self, style_filename):
        self.setMapXML_(self.buildXML(self.mapName,style_filename))
        
        self.view.redrawMap()
    
    def buildXML(self, db_prefix, style_filename):
        symbols_path = NSBundle.mainBundle().resourcePath() + "/symbols/"

        defaults = NSUserDefaults.standardUserDefaults()
        world_boundaries_path = defaults.stringForKey_("world_boundaries_path")
        if not world_boundaries_path:
            world_boundaries_path = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES)[0] + "/" + NSBundle.mainBundle().infoDictionary()["CFBundleName"]
            world_boundaries_path += "/osm2pgsql_MapnikLayer/world_boundaries/"
        
        with open(style_filename) as style_file:
            xml = style_file.read()
        
        host = self.db_args["host"]
        if "port" in self.db_args:
            host += ":" + str(self.db_args["port"])
        con = DBAPI.connect(user=self.db_args["user"],
                            password=self.db_args["password"],
                            host=host,
                            database=self.db_args["database"])
        try:
            cur = con.cursor()
            cur.execute("select proj4text from spatial_ref_sys where srid=Find_SRID('public', '%s','way')" % (db_prefix + "_point"))
            proj4 = cur.fetchall()[0][0]
        finally:
            con.close()
        
        parameters = {
        "symbols":symbols_path,
        "osm2pgsql_projection":proj4,
        "world_boundaries":world_boundaries_path,
        "prefix":db_prefix,
        }
        
        import mapnik
        epsg900913 = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +units=m +k=1.0 +nadgrids=@null +no_defs"
        projection = mapnik.Projection(epsg900913)
        # Not quite but close to the whole world
        extent = [projection.forward(mapnik.Coord(180.0,89.0)),projection.forward(mapnik.Coord(-180.0,-89.0))]
        
        self.mapExtent = (extent[0].x,extent[0].y,extent[1].x,extent[1].y)
        
        datasource_parameters = {
        "password":self.db_args["password"],
        "host":self.db_args["host"],
        "port":self.db_args["port"],
        "user":self.db_args["user"],
        "dbname":self.db_args["database"],
        "estimate_extent":"false",
        #"extent":"19926188.852,30240971.9584,-19926188.852,-30240971.9584",
        "extent":"%f,%f,%f,%f" % self.mapExtent,
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
    
    def getExtent(self):
        if not self.mapExtent:
            return super(osm2pgsql_MapnikLayer, self).getExtent()
        return self.mapExtent
    
    def getDefaultCenter(self):
        """Return a default center point as [lat,lon]"""
        center = None
        
        if not self.db_args:
            return super(osm2pgsql_MapnikLayer, self).getDefaultCenter()
        else:
            host = self.db_args["host"]
            if "port" in self.db_args:
                host += ":" + str(self.db_args["port"])
            con = DBAPI.connect(user=self.db_args["user"],
                                password=self.db_args["password"],
                                host=host,
                                database=self.db_args["database"])
            
            for suffix in ["_point", "_line", "_polygon"]:
                try:
                    cur = con.cursor()
                    cur.execute("select ST_AsText(ST_centroid(transform(ST_SetSRID(ST_estimated_extent('%s','way'), Find_SRID('public','%s','way')),4326)))" % (self.mapName + suffix, self.mapName + suffix))
                    center = map(float, cur.fetchall()[0][0][6:-1].split())
                    break
                except Exception as error:
                    print error
                    con.rollback()
            if not center:
                center = [0.0, 0.0]
            con.close()
        
        return center
    
    def getDefaultZoom(self):
        """Return a default zoom (pixels per projected unit)"""
        zoom = None
        
        if not self.db_args:
            return super(osm2pgsql_MapnikLayer, self).getDefaultZoom()
        else:
            host = self.db_args["host"]
            if "port" in self.db_args:
                host += ":" + str(self.db_args["port"])
            con = DBAPI.connect(user=self.db_args["user"],
                                password=self.db_args["password"],
                                host=host,
                                database=self.db_args["database"])
            
            for suffix in ["_point", "_line", "_polygon"]:
                try:
                    cur = con.cursor()
                    #cur.execute("select ST_AsText(ST_centroid(transform(ST_SetSRID(ST_estimated_extent('%s','way'), Find_SRID('public','%s','way')),4326)))" % (self.mapName + suffix, self.mapName + suffix))
                    cur.execute("select abs(ST_XMax(extent) - ST_XMin(extent)) as x, abs(ST_YMax(extent) - ST_YMin(extent)) as y from ST_estimated_extent('%s','way') as extent" % (self.mapName + suffix))
                    size = map(float, cur.fetchall()[0])
                    zoom = int(max(size[0] / 1024, size[1] / 768))
                    break
                except Exception as error:
                    print error
                    con.rollback()
            if not zoom:
                zoom = 25
            con.close()
        return zoom
    
    def getSearchProvider(self):
        return osm2pgsql_SearchProvider.osm2pgsql_SearchProvider.alloc().initWithLayer_(self)
        
    def getStyles(self):
        resources_prefix   = NSBundle.mainBundle().resourcePath() + "/styles/"
        app_support_prefix = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES)[0] + "/" + NSBundle.mainBundle().infoDictionary()["CFBundleName"] + "/styles/"
        
        path_prefixs = [resources_prefix, app_support_prefix]
        
        styles = list()
        
        for path_prefix in path_prefixs:
            #print "Looking for styles:", path_prefix
            
            files = glob.glob(path_prefix + "*.template")
            
            for file in files:
                styles.append({"id":file, "name":os.path.basename(file)[:-9]})
            
            styles.append(None)
        if styles:
            del styles[-1] # Remove trailing separator None
        
        return styles