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
    oulineViewMenu = objc.IBOutlet()
    
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
    
    @objc.IBAction
    def infoForSelectedLayers_(self, sender):
        selectedRows = list()
        for index in range(0,self.outlineView.numberOfRows()):
            if self.outlineView.isRowSelected_(index):
                selectedRows.append(self.outlineView.itemAtRow_(index))
        
        if selectedRows:
            item = selectedRows[0]
            description = None
            name = None
            x, y = None, None
            try:
                description = item.description
                name = item.name
            except AttributeError:
                print "Outline item has no name or description"
                return
                
            try:
                x, y = item.x, item.y
            except AttributeError:
                pass
            
            title = "Info for " + name
            if not description:
                description = "<no description>"
            if x is not None and y is not None:
                description = "Location: %.4f, %.4f\n\n" % (y, x) + description
            
            #FIXME: We could use a nicer menu than an alert dialog
            msg = str(description)
            alert = NSAlert.alloc().init()
            alert.setMessageText_(title)
            alert.setInformativeText_(msg) # Use this instead of informativeTextWithFormat to avoid % related errors
            alert.runModal()
    
    def doubleClicked(self):
        row = self.outlineView.clickedRow()
        if row != -1:
            item = self.outlineView.itemAtRow_(row)
            try:
                self.mapView.setCenter_([item.x,item.y])
            except AttributeError:
                pass
    
    # Right Click Menu Delegate Functions
    def menuNeedsUpdate_(self, menu):
        if menu == self.oulineViewMenu:
            row = self.outlineView.clickedRow()
            if row != -1:
                item = self.outlineView.itemAtRow_(row)
        return