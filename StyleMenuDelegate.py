#
#  StyleMenuDelegate.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 9/21/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

from Foundation import *
from AppKit import *

class StyleMenuDelegate(NSObject):
    items = objc.ivar()
    menu = objc.IBOutlet()
    mapView = objc.IBOutlet()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.items = None
        return self
        
        
    def awakeFromNib(self):
        self.mapView.addObserver_forKeyPath_options_context_(self, u"layers", 0, None)
        
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if keyPath == "layers":
            self.menuNeedsUpdate_(self.menu)
    
    def menuNeedsUpdate_(self, menu):
        self.menu.removeAllItems()
        self.items = []
        
        layers = self.mapView.getLayers()
        if layers:
            styles = layers[0].getStyles()
            sel = objc.selector(self.styleSelected_, signature="v:@@")
            if styles:
                for style in styles:
                    if style:
                        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(style["name"], sel, "")
                        menuitem.setTarget_(self)
                        
                        item = [menuitem, style["id"]]
                    else:
                        menuitem = NSMenuItem.separatorItem()
                        item = [menuitem, None]
                        
                    self.items.append(item)
        
        if not self.items:
            menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("No styles", None, "")
            self.items = [[menuitem, None]]
        
        for i in self.items:
            menu.addItem_(i[0])
    
    def styleSelected_(self, sender):
        selected = None
        for item in self.items:
            if item[0] == sender:
                selected = item[1]
                break
        #print "Selected " + selected
        if selected:
            self.mapView.getLayers()[0].setStyle(selected)
