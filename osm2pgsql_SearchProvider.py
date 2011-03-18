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

import SearchParse

def parsedToPGSQL(parsed, center = None, viewBounds = None):
    sqlString = ""
    for rule in parsed:
        if type(rule) == list:
            sqlString += "(" + parsedToPGSQL(rule) + ") "
        elif rule[0] == "tagEquals":
            sqlString += "\"%s\" = '%s' " % rule[1]
        elif rule[0] == "tagContains":
            sqlString += "(to_tsvector('simple',\"%s\") @@ to_tsquery('simple','%s')) " % rule[1]
        elif rule[0] == "tagNotNull":
            sqlString += "\"%s\" is not null " % rule[1]
        elif rule == "or":
            sqlString += "or "
        elif rule == "and":
            sqlString += "and "
        else:
            raise SearchParse.SearchStringParseException("Rule type not supported by PGSQL", rule)
    
    return sqlString

class osm2pgsql_SearchProvider(NSObject):
    searchRules = objc.ivar()
    layer = objc.ivar()

    def initWithLayer_(self, layer):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.layer = layer
        
        return self
    
    def getRules(self):
        return None
    
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
            
            print "Search Query:", commands
            
            parser = SearchParse.SearchParser(knownTags)
            tokens = parser.parse(commands)
            
            print "Parsed search:", str(tokens)
            
            query = parsedToPGSQL(tokens, center, viewBounds)
            
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
    select name, point, ST_Distance_Sphere(ST_Transform(way, 4326), ST_GeomFromText('%(center)s', 4326)) as distance, type from unsorted_results
    )

    select name, ST_AsText(ST_Transform(point, 4326)), type from results order by distance
    """ % {"mapName":self.layer.mapName, "query":query, "center":"POINT(%f %f)" % (center.x, center.y)}
            cursor.execute(sql)
            
            for row in cursor.fetchall():
                loc = row[1]
                try:
                    loc = loc.split("(")[1].split(")")[0].split(" ")
                except IndexError as e:
                    print "Bad geometry for \"%s\": %s" % (row[0], loc)
                    break
                loc = map(float, loc)
                results.append({"type":row[2], "name":row[0], "loc":loc})
            
            return results
        finally:
            con.close()
