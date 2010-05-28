#
#  InspectWindowDelegate.py
#  Maprender
#
#  Created by Daniel Sabo on 5/18/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
import mapnik

import pgdb as DBAPI
import pg

class InspectWindowDelegate(NSObject):
    inspectWindow = objc.IBOutlet()
    mapView       = objc.IBOutlet()
    inspectString = objc.ivar()
    
    db_args = objc.ivar()
    mapName = objc.ivar()
    
    
    def awakeFromNib(self):
        self.db_args = None
        self.db_con  = None
        #self.mapView.addObserver_forKeyPath_options_context_(self, u"centerLonLat", 0, None)
        self.mapView.addObserver_forKeyPath_options_context_(self, u"centerLonLat", 0, None)
        
    def setDBParams(self,dbParams):
        #FIXME: This should be replaced by preferences
        self.db_args = dbParams
        self.db_con  = DBAPI.connect(**self.db_args)
    
    def setMapName_(self, value):
        self.mapName = value
        cur = self.db_con.cursor()
        table = self.mapName + "_polygon"
        sql = "select srid,proj4text from spatial_ref_sys where srid=Find_SRID('public', '%s', 'way')" % table
        cur.execute(sql)
        result = cur.fetchall()
        
        srid = result[0][0]
        srs  = result[0][1]
        
        self.srid = srid
        self.projection = mapnik.Projection(srs)
            
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        return
    
        #if keyPath == "centerLonLat" and self.inspectWindow.isVisible():
        if keyPath == "centerLonLat":
            prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
            #print 1
            #FIXME: For some reason I can't get the mapview's projection
            #print 2
            center = prj.forward(object.center)
            wktPoint = "POINT(%f %f)" % (center.x, center.y)
            
            

            #"select name from british_columbia_polygon where boundary is not NULL and ST_Contains(way, ST_GeomFromText('POINT(49.6499 -115.6514)')) order by admin_level"
            inspectString = ""
            #print 3
            try:
                con = DBAPI.connect(**self.db_args)
                table = self.mapName + "_polygon"
                #print 3.1
                cur = con.cursor()
                #print 3.2
                #FIXME: Second argument of ST_GeomFromText is SRID, this needs to be found dynamicaly
                #sql = "select name from %s where boundary is not NULL and ST_Contains(way, ST_GeomFromText('%s', 900913)) order by admin_level" % (table, wktPoint)
                #sql = "select name from %s where ST_Within(ST_Transform('SRID=4326;POINT(-116.028896107598 46.2271089325307)'::geometry, %d), way)" % (table, self.srid)
                sql = "select name from %s where name IS NOT Null and ST_Within('SRID=%d;%s'::geometry, way)" % (table, self.srid, wktPoint)
                #print sql
                #print 3.3
                cur.execute(sql)
                #print 3.4
                rows = cur.fetchall()
                #print 3.5
                
                inspectString += "Area:\n"
                for row in rows:
                    #print row
                    inspectString += inspectString + row[0] + "\n"
                #print 3.6
                
                range = self.mapView.zoom * 10
                
                table = self.mapName + "_point"
                sql = "select name from %s where name IS NOT Null and ST_DWithin('SRID=%d;%s'::geometry, way, %d)" % (table, self.srid, wktPoint, range)
                
                cur.execute(sql)
                rows = cur.fetchall()
                
                
                inspectString += "Nodes:\n"
                for row in rows:
                    inspectString += inspectString + row[0] + "\n"
                    
                #table = self.mapName + "_line"
                #sql = "select name from %s where name IS NOT Null and ST_DWithin('SRID=%d;%s'::geometry, way, %d)" % (table, self.srid, wktPoint, range)
                
                #cur.execute(sql)
                #rows = cur.fetchall()
                
                
                #inspectString += "Lines:\n"
                #for row in rows:
                #    inspectString += inspectString + row[0] + "\n"

            except pg.DatabaseError:
                inspectString = "DB Error"
            except Exception as e:
                print e
            finally:
                con.close()
            #print 4
            
            self.setInspectString_(inspectString)
            
            #self.inspectString = inspectString
        
        
    