#
#  HttpTileLayer_OpenDialogDelegate.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 12/18/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
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
        self.window.performClose_(self)
        
        mapWindow = self.appDelegate.mapWindow
        mapView   = self.appDelegate.mapView
        
        mapWindow.makeKeyAndOrderFront_(self)
        
        from HttpTileLayer import HttpTileLayer
        layer = HttpTileLayer.alloc().init()
        layer.setMapURL_(url)
                    
        if mapView.center is None:
            mapView.setCenter_(layer.getDefaultCenter())
            mapView.setZoom_(layer.getDefaultZoom())
        mapView.setMapLayer_(layer)            
        self.appDelegate.mapName = layer.name
        