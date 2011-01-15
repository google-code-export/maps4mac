#
#  main.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 4/21/10.
#  Copyright __MyCompanyName__ 2010. All rights reserved.
#

#import modules required by application
import objc
import Foundation
import AppKit

from PyObjCTools import AppHelper

# import modules containing classes required to start application and load MainMenu.nib
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

# pass control to AppKit
AppHelper.runEventLoop()
