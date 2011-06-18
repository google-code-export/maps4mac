#
#  osm2pgsql_SearchProvider.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 12/17/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
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
            # osm2pgsql doesn't have a uniform tag list between tables, for now only allow searching on the common tags
            cursor = con.cursor()
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", [str(self.layer.mapName) + "_point"])
            knownTags = [x[0] for x in cursor.fetchall()]
            del knownTags[knownTags.index("way")]
            del knownTags[knownTags.index("z_order")]
            knownTags = set(knownTags)
            print knownTags
            
            cursor = con.cursor()
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", [str(self.layer.mapName) + "_line"])
            knownTags = knownTags.intersection([x[0] for x in cursor.fetchall()])
            
            cursor = con.cursor()
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", [str(self.layer.mapName) + "_polygon"])
            knownTags = knownTags.intersection([x[0] for x in cursor.fetchall()])
            
            cursor.execute("select Find_SRID('public', '%s','way')" % (self.layer.mapName + "_point"))
            srid = cursor.fetchone()[0]
            
            print "Search Query:", commands
            
            parser = SearchParse.SearchParser(knownTags)
            tokens = parser.parse(commands)
            
            print "Parsed search:", str(tokens)
            
            query = parsedToPGSQL(tokens, center, viewBounds, srid)
            
            print "SQL:", query
            
            results = list()
            
            query_params_list = [
                {"table":"point",   "center_func":"way"},
                {"table":"line",    "center_func":"ST_StartPoint(way)"},
                {"table":"polygon", "center_func":"ST_Centroid(way)"},
            ]
            
            sql_tags = ", ".join(['"%s"' % tag for tag in knownTags])
            
            for query_params in query_params_list:
                query_params.update({"mapName":self.layer.mapName, "query":query, "tags":sql_tags, "center":"POINT(%f %f)" % (center.x, center.y)})
                
                sql = """SELECT
                         ST_AsText(ST_Transform(%(center_func)s, 4326)) as point,
                         ST_AsText(ST_Transform(way, 4326)) as geom,
                         ST_Distance_Sphere(ST_Transform(way, 4326), ST_GeomFromText('%(center)s', 4326)),
                         '%(table)s' as type,
                         %(tags)s
                         FROM %(mapName)s_%(table)s WHERE %(query)s""" % query_params
                print sql
                cursor.execute(sql)
                rows = cursor.fetchall()
                for row in rows:
                    loc, geom, distance, type = row[:4]
                    
                    tags = dict(zip(knownTags, row[4:]))
                    
                    description = "\n".join(["%s: %s" % t for t in tags.items() if t[1]])
                    name = tags["name"]
                    
                    try:
                        loc = loc.split("(")[1].split(")")[0].split(" ")
                    except IndexError:
                        print "Bad geometry for \"%s\": %s" % (name, loc)
                        break
                    loc = map(float, loc)
                    
                    result = {"type":type, "name":name, "loc":loc, "distance":distance, "description": description}
                    
                    if type == "line":
                        try:
                            print geom
                            points = geom.split("(")[1].split(")")[0].split(",")
                            points = [map(float, p.strip().split(" ")) for p in points]
                        except IndexError:
                            print "Bad geometry for \"%s\": %s" % (name, loc)
                        except ValueError:
                            print geom
                            raise
                        result["line"] = points
                    
                    results.append(result)
            
            return results
        finally:
            con.close()
