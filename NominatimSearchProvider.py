#
#  NominatimSearchProvider.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 12/18/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
import urllib

class NominatimSearchProvider(NSObject):
    def init(self):
        self = super(self.NominatimSearchProvider, self).init()
        if self is None:
            return None
        
        return self
    
    def doSearch(self, commands, center, viewBounds = None):
        #url = "http://nominatim.openstreetmap.org/search?format=xml&q=%s" % urllib.quote_plus(commands)
        #xml_result = urllib.urlopen(url)
        # parse here
        return []
