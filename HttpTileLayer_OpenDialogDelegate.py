#
#  HttpTileLayer_OpenDialogDelegate.py
#  Maprender
#
#  Created by Daniel Sabo on 12/18/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *

class HttpTileLayer_OpenDialogDelegate(NSObject):
    urlCombobox = objc.IBOutlet()
    window = objc.IBOutlet()
    appDelegate = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        return self
            
    @objc.IBAction
    def loadMap_(self, sender):
        url = self.urlCombobox.stringValue()
        if not url.startswith("http://"):
            url = "http://" + url
        print url
        # FIXME: Do some real validation
        try:
            print url % {'z':0,'x':0,'y':0}
        except KeyError:
            return
        self.window.performClose_(self)
        
        mapWindow = self.appDelegate.mapWindow
        mapView   = self.appDelegate.mapView
        
        mapWindow.makeKeyAndOrderFront_(self)
        
        #path = "/Users/argon/Prog/Maprender/" + mapName + ".xml"
        from HttpTileLayer import HttpTileLayer
        layer = HttpTileLayer.alloc().init()
        layer.setMapURL_(url)
                    
        if mapView.center is None:
            mapView.setCenter_(layer.getDefaultCenter())
            mapView.setZoom_(layer.getDefaultZoom())
        mapView.setMapLayer_(layer)            
        self.appDelegate.mapName = layer.name
        