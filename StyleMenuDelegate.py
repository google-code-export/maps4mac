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
    
    def menuNeedsUpdate_(self, menu):
        if not self.items:
            kLocalDomain = -32765
            kUserDomain = -32763
            kApplicationSupportFolderType = 'asup'
            
            path_prefix = NSBundle.mainBundle().bundlePath() + "/Contents/Resources/styles/"
            #path_prefix = NSBundle.mainBundle().bundlePath() + "/Contents/Resources/"
            
            print "Looking for styles:", path_prefix
            
            files = glob.glob(path_prefix + "*.template")
            
            self.items = list()
            
            for stylefile in files:
                stylename = os.path.basename(stylefile)[:-9]
                #sel = objc.selector(None, selector="styleSelected_", signature="v:@")
                sel = objc.selector(self.styleSelected_, signature="v:@@")

                print sel
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
        print "Selected" + selected
