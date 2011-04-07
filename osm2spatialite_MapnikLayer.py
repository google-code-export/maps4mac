#
#  osm2spatialite_MapnikLayer.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 1/14/11.
#  Copyright (c) 2011 Daniel Sabo. All rights reserved.
#

from Foundation import *

import TiledMapnikLayer

import os.path

from pysqlite2 import dbapi2 as sqlite
import osm2spatialite_SearchProvider

class osm2spatialite_MapnikLayer(TiledMapnikLayer.TiledMapnikLayer):
    filename = objc.ivar()
    internal_projection = objc.ivar()

    def loadMap(self, map_filename, style_filename):
        try:
            self.filename = map_filename
            self.stylefile = style_filename
            
            self.setMapXML_(self.buildXML(map_filename,style_filename))
            self.setName_("Mapnik: " + os.path.basename(map_filename))
        except Exception as ex:
            import traceback
            print ex
            traceback.print_exc()
            raise
        
        self.description  = "SQlite File:\n" + map_filename 
        self.description += "\n\n"
        self.description += "Style File:\n" + style_filename
        self.description += "\n\n"
        self.description += "Internal Projection:\n" + self.internal_projection
        self.description += "\n\n"
        self.description += "Rendered Projection:\n" + self.projectionString
        
    def buildXML(self, map_filename, style_filename):
        db_prefix = "world"
        symbols_path = NSBundle.mainBundle().resourcePath() + "/symbols/"

        defaults = NSUserDefaults.standardUserDefaults()
        world_boundaries_path = defaults.stringForKey_("world_boundaries_path")
        if not world_boundaries_path:
            world_boundaries_path = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES)[0] + "/" + NSBundle.mainBundle().infoDictionary()["CFBundleName"]
            world_boundaries_path += "/osm2pgsql_MapnikLayer/world_boundaries/"
        
        with open(style_filename) as style_file:
            xml = style_file.read()
        
        con = sqlite.connect(map_filename)
        
        try:
            cur = con.cursor()            
            cur.execute("select proj4text from geometry_columns,spatial_ref_sys where f_table_name = ? and geometry_columns.srid = spatial_ref_sys.srid", [db_prefix + "_point"])
            proj4 = cur.fetchone()[0]
        finally:
            con.close()
        
        self.internal_projection = proj4
        
        parameters = {
        "symbols":symbols_path,
        "osm2pgsql_projection":proj4,
        "world_boundaries":world_boundaries_path,
        "prefix":db_prefix,
        }
        
        #import mapnik
        #epsg900913 = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +units=m +k=1.0 +nadgrids=@null +no_defs"
        #projection = mapnik.Projection(epsg900913)
        # Not quite but close to the whole world
        #extent = [projection.forward(mapnik.Coord(180.0,89.0)),projection.forward(mapnik.Coord(-180.0,-89.0))]
        
        #self.mapExtent = (extent[0].x,extent[0].y,extent[1].x,extent[1].y)
        
        datasource_parameters = {
        "filename":map_filename,
        "estimate_extent":"false",
        "extent":"%f,%f,%f,%f" % (180.0,89.0,-180.0,-89.0),
        #"extent":"19926188.852,30240971.9584,-19926188.852,-30240971.9584",
        #"extent":"%f,%f,%f,%f" % self.mapExtent,
        }

        parameters["datasource_settings"] = \
        """
        <Parameter name="type">sqlite</Parameter>
        <Parameter name="file">%(filename)s</Parameter>
        <Parameter name="key_field">rowid</Parameter>
        <Parameter name="geometry_field">way</Parameter>
        <Parameter name="wkb_format">spatialite</Parameter>
        <Parameter name="estimate_extent">%(estimate_extent)s</Parameter>
        <Parameter name="extent">%(extent)s</Parameter>
        <Parameter name="use_spatial_index">true</Parameter>
        """ % datasource_parameters
                
        xml = xml % parameters
        
        return str(xml)
    
    def getSearchProvider(self):
        return osm2spatialite_SearchProvider.osm2spatialite_SearchProvider.alloc().initWithLayer_(self)
    
    def getDefaultCenter(self):
        """Return a default center point as [lat,lon]"""
        center = None
        db_prefix = "world"
        
        if not self.filename:
            return super(osm2pgsql_MapnikLayer, self).getDefaultCenter()
        else:
            con = sqlite.connect(self.filename)
            for suffix in ["_point", "_line", "_polygon"]:
                try:
                    cur = con.cursor()
                    cur.execute("select Min(MbrMinX(way)),Min(MbrMinY(way)),Max(MbrMaxX(way)),Max(MbrMaxY(way)) from %s" % db_prefix + suffix)
                    extent = map(float, cur.fetchone())
                    center = [(extent[0] + extent[2]) / 2, (extent[1] + extent[3]) / 2]
                    #cur.execute("select ST_AsText(ST_centroid(transform(ST_SetSRID(ST_estimated_extent('%s','way'), Find_SRID('public','%s','way')),4326)))" % (self.mapName + suffix, self.mapName + suffix))
                    #center = map(float, cur.fetchall()[0][0][6:-1].split())
                    break
                except Exception as error:
                    print error
                    con.rollback()
            if not center:
                center = [0.0, 0.0]
            con.close()
        
        return center