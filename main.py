#
#  main.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 4/21/10.
#  Copyright Daniel Sabo 2010. All rights reserved.
#

#import modules required by application
import objc
import Foundation
import AppKit

from PyObjCTools import AppHelper

def doAbortError(title, msg):
    def showMsg():
        alert = AppKit.NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(msg) # Use this instead of informativeTextWithFormat to avoid % related errors
        alert.setAlertStyle_(AppKit.NSCriticalAlertStyle)
        alert.runModal()
        AppKit.NSApplication.sharedApplication().stop_(None)
    AppHelper.callAfter(showMsg)
    AppKit.NSApplication.sharedApplication()
    AppKit.NSApp.run()

# import modules containing classes required to start application and load MainMenu.nib
try:
    import SourceListDatasource
    import Maps4MacAppDelegate
    import MapWindowDelegate
    import MapView
    import MapnikRenderThread
    import SearchWindowDelegate
    import StyleMenuDelegate
    import LayersOutlineDataSource
    import LayersWindowDelegate
    import DownloadWindowDelegate
    import LoggerDelegate
except ImportError, e:
    import traceback
    traceback.print_exc()
    
    #msg = traceback.format_exc()
    title = "Error Loading Modules"
    doAbortError(title, str(e[0]))
except:
    import traceback
    traceback.print_exc()
    
    msg = traceback.format_exc()
    title = "Initialization Error"
    
    doAbortError(title, msg)
else:
    # pass control to AppKit
    AppHelper.runEventLoop()
