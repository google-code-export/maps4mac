#
#  LayerOutlineDataSource.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 10/31/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *

class LayersOutlineDataSource(NSObject):
    outlineView = objc.IBOutlet()
    outlineDelegate = objc.IBOutlet()
    
    mapView = objc.IBOutlet()

    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        return self
    
    def awakeFromNib(self):
        self.mapView.addObserver_forKeyPath_options_context_(self, u"layers", 0, None)
    
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if object == self.mapView and keyPath == "layers":
            #print str(self), "Reload Layers"
            self.outlineView.reloadData()

    def outlineView_child_ofItem_(self, outlineView, index, item):
        if item is None:
            return self.mapView.getLayers()[index]
        else:
            return item.outline[index]
        
    def outlineView_isItemExpandable_(self, outlineView, item):
        if item.outline is not None:
            return True
        return False
    
    def outlineView_numberOfChildrenOfItem_(self, outlineView, item):
        if item is None:
            return len(self.mapView.getLayers())
        if item.outline is not None:
            return len(item.outline)
        return 0
    
    def outlineView_objectValueForTableColumn_byItem_(self, outlineView, tableColumn, item):
        #if item is None:
        #    item = self.root
        
        #if tableColumn.identifier() == "Title" and "Title" in item:
        #    return item["Title"]
        #elif tableColumn.identifier() == "Description":
        #    if "A" in item:
        #        actionObj = self.pdf.resolvePath(item, "A")
        #        return "A: " + str(actionObj["S"])
        #    elif "Dest" in item:
        #        return str(item["Dest"])
        
        #return ""
        
        if item.name is not None:
            return str(item.name)
        return str(item)
    
#    def outlineView_setObjectValue_forTableColumn_byItem_(self, outlineView, object, tableColumn, item):
#        if item is None:
#            return
#            
#        if tableColumn.identifier() == "Title":
#            item["Title"] = str(object)
#        return
