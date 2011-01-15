#
#  osm2spatialite_MapnikLayer.py
#  Maprender
#
#  Created by Daniel Sabo on 1/14/11.
#  Copyright (c) 2011 Daniel Sabo. All rights reserved.
#

from Foundation import *

from pysqlite2 import dbapi2 as sqlite

class osm2spatialite_MapnikLayer(NSObject):
    dbapi = objc.ivar()
    filename = objc.ivar()
    

    def loadMap_(self, filename):
        from pysqlite2 import dbapi2
        self.dbapi = dbapi2
        self.filename = filename