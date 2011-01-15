#
#  osm2pgsql_SearchProvider.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 12/17/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *

import pgdb as DBAPI
import pg

class osm2pgsql_SearchProvider(NSObject):
    searchRules = objc.ivar()
    layer = objc.ivar()

    def initWithLayer_(self, layer):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.layer = layer
        self.searchRules = [
            {"displayValue":"Name","type":"label","children":
                [
                    {"displayValue":"","type":"text"}
                ]
            },
            {"displayValue":"SQL","type":"label","children":
                [
                    {"displayValue":"","type":"text"}
                ]
            },
        ]
        
        return self
    
    def getRules(self):
        return self.searchRules
    
    def doSearch(self, rules):
        commands = rules[1]
        center   = rules[2]
        
        results = None
        
        
        host = self.layer.db_args["host"]
        if "port" in self.layer.db_args:
            host += ":" + str(self.layer.db_args["port"])
        con = DBAPI.connect(user=self.layer.db_args["user"],
                            password=self.layer.db_args["password"],
                            host=host,
                            database=self.layer.db_args["database"])
    
        def doQuery(commands):
            results = list()
            
            cur = con.cursor()
            #TODO: Keep lines instead of centroid
            #sql = "select name, ST_AsText(ST_Transform(%s, 4269)) from %s where %s" % (transform[tableSuffix], table, commands)
            sql = \
"""with unsorted_results as (
(select name, way as point, way, 'point' as type from %(mapName)s_point where %(query)s)
union
(select name, ST_StartPoint(way) as point, way, 'line' as type from %(mapName)s_line where %(query)s)
union
(select name, ST_Centroid(way) as point, way, 'polygon' as type from %(mapName)s_polygon where %(query)s)
), results as (
select name, point, ST_Distance_Sphere(ST_Transform(way, 4269), ST_GeomFromText('%(center)s', 4269)) as distance, type from unsorted_results
)

select name, ST_AsText(ST_Transform(point, 4269)), type from results order by distance
""" % {"mapName":self.layer.mapName, "query":commands, "center":"POINT(%f %f)" % (center.x, center.y)}
            cur.execute(sql)
            #print sql
        
            rows = cur.fetchall()
            
            for row in rows:
                loc = row[1]
                try:
                    loc = loc.split("(")[1].split(")")[0].split(" ")
                except IndexError as e:
                    print "Bad geometry for \"%s\": %s" % (row[0], loc)
                    break
                loc = map(float, loc)
                results.append({"type":row[2], "name":row[0], "loc":loc})
            return results
        
        try:
            results = doQuery(commands)
        except pg.DatabaseError:
            try:
                con.rollback()
                # This version takes advantage of vector indexes if available
                results = doQuery("to_tsvector('simple',name) @@ to_tsquery('simple','''%s''')" % commands.replace("'","\\'"))
            except pg.DatabaseError as error:
                print error
                raise error
                #self.results = [{"type":"DB Error", "name":"DB Error", "loc":(0,0)}]
        finally:
            con.close()
        
        return results

