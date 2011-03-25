#
#  osm2pgsql_SearchProvider.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 12/17/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *

import pgdb as DBAPI

import SearchParse

def parsedToPGSQL(parsed, center, viewBounds, mapSRID):
    sqlString = ""
    for rule in parsed:
        if type(rule) == list:
            sqlString += "(" + parsedToPGSQL(rule) + ") "
        elif rule[0] == "tagEquals":
            sqlString += "\"%s\" = '%s' " % rule[1]
        elif rule[0] == "tagContains":
            sqlString += "(to_tsvector('simple',\"%s\") @@ to_tsquery('simple','''%s''')) " % rule[1]
        elif rule[0] == "tagNotNull":
            sqlString += "\"%s\" is not null " % rule[1]
        elif rule == "or":
            sqlString += "or "
        elif rule == "and":
            sqlString += "and "
        elif rule[0] == "withinView" and viewBounds:
            sqlString += "way && ST_Transform(ST_SetSRID('BOX3D(%f %f, %f %f)'::box3d, 4326), %d)" % (viewBounds.minx, viewBounds.miny, viewBounds.maxx, viewBounds.maxy, mapSRID)
        elif rule[0] == "sql":
            sqlString += rule[1]
        else:
            raise SearchParse.SearchStringParseException("Rule type not supported by PGSQL", rule)
    
    return sqlString

class osm2pgsql_SearchProvider(NSObject):
    layer = objc.ivar()

    def initWithLayer_(self, layer):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.layer = layer
        
        return self
    
    def doSearch(self, commands, center, viewBounds = None):
        results = None
        
        host = self.layer.db_args["host"]
        if "port" in self.layer.db_args:
            host += ":" + str(self.layer.db_args["port"])
        con = DBAPI.connect(user=self.layer.db_args["user"],
                            password=self.layer.db_args["password"],
                            host=host,
                            database=self.layer.db_args["database"])
        
        try:
            cursor = con.cursor()
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", [str(self.layer.mapName) + "_point"])
            print 
            knownTags = [x[0] for x in cursor.fetchall()]
            del knownTags[knownTags.index("way")]
            
            cursor.execute("select Find_SRID('public', '%s','way')" % (self.layer.mapName + "_point"))
            srid = cursor.fetchone()[0]
            
            print "Search Query:", commands
            
            parser = SearchParse.SearchParser(knownTags)
            tokens = parser.parse(commands)
            
            print "Parsed search:", str(tokens)
            
            query = parsedToPGSQL(tokens, center, viewBounds, srid)
            
            print "SQL:", query
            
            results = list()
            
            sql = \
    """with unsorted_results as (
    (select name, way as point, way, 'point' as type from %(mapName)s_point where %(query)s)
    union
    (select name, ST_StartPoint(way) as point, way, 'line' as type from %(mapName)s_line where %(query)s)
    union
    (select name, ST_Centroid(way) as point, way, 'polygon' as type from %(mapName)s_polygon where %(query)s)
    ), results as (
    select name, point, ST_Distance_Sphere(ST_Transform(way, 4326), ST_GeomFromText('%(center)s', 4326)) as distance, type, way as geom from unsorted_results
    )

    select name, ST_AsText(ST_Transform(point, 4326)), type, distance, ST_AsText(ST_Transform(geom, 4326)) from results order by distance
    """ % {"mapName":self.layer.mapName, "query":query, "center":"POINT(%f %f)" % (center.x, center.y)}
            cursor.execute(sql)
            
            rows = cursor.fetchall()
            
            for row in rows:
                loc = row[1]
                try:
                    loc = loc.split("(")[1].split(")")[0].split(" ")
                except IndexError:
                    print "Bad geometry for \"%s\": %s" % (row[0], loc)
                    break
                loc = map(float, loc)
                
                result = {"type":row[2], "name":row[0], "loc":loc, "distance":row[3]}
                
                if row[2] == "line":
                    try:
                        print row[4]
                        points = row[4].split("(")[1].split(")")[0].split(",")
                        points = [map(float, p.strip().split(" ")) for p in points]
                    except IndexError:
                        print "Bad geometry for \"%s\": %s" % (row[0], loc)
                    except ValueError:
                        print row[4]
                        raise
                    result["line"] = points
                
                results.append(result)
            
            return results
        finally:
            con.close()
