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
        try:
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
            
        except Exception as error:
            print error
            import traceback
            traceback.print_exc()
        
            title = "Couldn't open layer"
            msg = "Maps4Mac couldn't open: \n%s\n\nReason:\n%s" % (url,str(error))
            
            alert = NSAlert.alloc().init()
            alert.setMessageText_(title)
            alert.setInformativeText_(msg) # Use this instead of informativeTextWithFormat to avoid % related errors
            alert.runModal()
        