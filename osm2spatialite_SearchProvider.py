#
#  osm2spatialite_SearchProvider.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 1/17/11.
#  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
#

from Foundation import *

from pysqlite2 import dbapi2 as sqlite

class osm2spatialite_SearchProvider(NSObject):
    layer = objc.ivar()

    def initWithLayer_(self, layer):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.layer = layer
        
        return self
    
    def getRules(self):
        return None

    def doSearch(self, rules):
        commands = rules[1]
        center   = rules[2]
        
        results = None
        
        con = sqlite.connect(self.layer.filename)
        
        def doQuery(commands):
            results = list()
            
            cur = con.cursor()
            #TODO: Keep lines instead of centroid
            #FIXME: Distance unitless, so we need to sort the results ourselves
            sql = \
"""select name, ST_AsText(Transform(point, 4326)), type from (
select name, point, Distance(Transform(way, 4326), ST_GeomFromText('%(center)s', 4326)) as distance, type from (
select name, way as point, way, 'point' as type from %(mapName)s_point where %(query)s
union
select name, ST_StartPoint(way) as point, way, 'line' as type from %(mapName)s_line where %(query)s
union
select name, ST_Centroid(way) as point, way, 'polygon' as type from %(mapName)s_polygon where %(query)s
)
) order by distance
""" % {"mapName":"world", "query":commands, "center":"POINT(%f %f)" % (center.x, center.y)}
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
        except Exception as error: #FIXME: Wrong exception type
            try:
                con.rollback()
                results = doQuery("name like '%%%s%%'" % commands)
            except Exception as error:
                print error
                raise error
        finally:
            con.close()
        
        return results