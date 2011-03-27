#
#  LayersWindowDelegate.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 10/31/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

from Foundation import *

class LayersWindowDelegate(NSObject):
    outlineView = objc.IBOutlet()
    mapView     = objc.IBOutlet()
    
    def awakeFromNib(self):
        self.outlineView.setTarget_(self)
        self.outlineView.setDoubleAction_(self.doubleClicked)

    @objc.IBAction
    def deleteSelectedLayers_(self, sender):
        toDelete = list()
        for index in range(0,self.outlineView.numberOfRows()):
            if self.outlineView.isRowSelected_(index):
                toDelete.append(self.outlineView.itemAtRow_(index))
        for layer in toDelete:
            self.mapView.removeLayerByObject_(layer)
    
    def doubleClicked(self):
        row = self.outlineView.clickedRow()
        if row != -1:
            item = self.outlineView.itemAtRow_(row)
            try:
                self.mapView.setCenter_([item.x,item.y])
            except AttributeError:
                pass