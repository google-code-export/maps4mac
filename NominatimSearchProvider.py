#
#  NominatimSearchProvider.py
#  Maprender
#
#  Created by Daniel Sabo on 12/18/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
import urllib

class NominatimSearchProvider(NSObject):
    searchRules = objc.ivar()
    
    def init(self):
        self = super(self.NominatimSearchProvider, self).init()
        if self is None:
            return None
        
        self.layer = layer
        self.searchRules = [
            {"displayValue":"Nominatim","type":"label","children":
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
        
        url = "http://nominatim.openstreetmap.org/search?format=xml&q=%s" % urllib.quote_plus(commands)
        #xml_result = urllib.urlopen(url)
        # parse here
        return []
