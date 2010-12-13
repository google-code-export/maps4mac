#
#  StyleMenuDelegate.py
#  Maprender
#
#  Created by Daniel Sabo on 9/21/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
from AppKit import *

import glob, os.path

class StyleMenuDelegate(NSObject):
    items = objc.ivar()
    appDelegate = objc.IBOutlet()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        items = None
        return self
        
    def menuNeedsUpdate_(self, menu):
        if not self.items:
            kLocalDomain = -32765
            kUserDomain = -32763
            kApplicationSupportFolderType = 'asup'
            
            # NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES)[0]
            
            #path_prefix = NSBundle.mainBundle().bundlePath() + "/Contents/Resources/styles/"
            
            #path_prefix = NSBundle.mainBundle().resourcePath() + "/styles/"
            
            resources_prefix   = NSBundle.mainBundle().resourcePath() + "/styles/"
            app_support_prefix = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES)[0] + "/" + NSBundle.mainBundle().infoDictionary()["CFBundleName"] + "/styles/"
            
            path_prefixs = [resources_prefix, app_support_prefix]
            
            self.items = list()
            
            for path_prefix in path_prefixs:
                print "Looking for styles:", path_prefix
                
                files = glob.glob(path_prefix + "*.template")
                
                for stylefile in files:
                    stylename = os.path.basename(stylefile)[:-9]
                    #sel = objc.selector(None, selector="styleSelected_", signature="v:@")
                    sel = objc.selector(self.styleSelected_, signature="v:@@")

                    menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(stylename, sel, "")
                    menuitem.setTarget_(self)
                    #menuitem.setEnabled_(True)
                    
                    item = [menuitem, stylefile]
                    
                    self.items.append(item)
                
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
            self.appDelegate.setMapStyle_(selected)
