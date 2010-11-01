#
#  Logger.py
#  Maprender
#
#  Created by Daniel Sabo on 10/8/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *

class Logger(NSObject):
    currentTract = objc.IBOutlet()

    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        # Find or create logging directory in application support
        
        loggerPath = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES)[0]
        loggerPath += "/" + NSBundle.mainBundle().infoDictionary()['CFBundleName'] + "/Logger/"
        
        # 
        currentTract = None
        
        return self
    
    # New fix
    def setGPSFix_(self, fixDict):
        pass
        
        # Check how long it's been since the last GPS data to see if we should split the tract
    
    # New waypoint
    def addWaypointAtLon_Lat_(self, lon, lat):
        """Add a waypont at the given lon, lat
        """
        pass
    
    def addWaypointAtLon_Lat_Properties(self, lon, lat):
        """Add a waypont at the given lon, lat with additional properties
        provided in a dictionary. Supported properties are:
        Name
        Elevation
        Description
        """
        pass