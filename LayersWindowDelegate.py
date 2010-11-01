#
#  LayersWindowDelegate.py
#  Maprender
#
#  Created by Daniel Sabo on 10/31/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *

class LayersWindowDelegate(NSObject):
    outlineView = objc.IBOutlet()
    mapView     = objc.IBOutlet()

    @objc.IBAction
    def deleteSelectedLayers_(self, sender):
        toDelete = list()
        for index in range(0,self.outlineView.numberOfRows()):
            if self.outlineView.isRowSelected_(index):
                toDelete.append(self.outlineView.itemAtRow_(index))
        for layer in toDelete:
            self.mapView.removeLayerByObject_(layer)