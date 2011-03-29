#
#  NominatimSearchProvider.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 12/18/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

from Foundation import *
import urllib, json

from osm2spatialite_SearchProvider import GeoDistanceSphere
import mapnik

class NominatimSearchProvider(NSObject):
    def init(self):
        self = super(NominatimSearchProvider, self).init()
        if self is None:
            return None
        
        return self
    
    def doSearch(self, commands, center, viewBounds = None):
        url = "http://nominatim.openstreetmap.org/search?format=json&q=%s" % urllib.quote_plus(commands)
        json_result = urllib.urlopen(url)
        json_result = json.load(json_result)
        
        results = []
        
        for row in json_result:
            result_point = mapnik.Coord(float(row["lon"]), float(row["lat"]))
            distance = GeoDistanceSphere(result_point.x, result_point.y, center.x, center.y)
            result = {"type":row["osm_type"], "name":row["display_name"], "loc":[result_point.x,result_point.y], "distance":distance}
            results.append(result)
        return results