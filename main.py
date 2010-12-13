#
#  main.py
#  Maprender
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
import MaprenderAppDelegate
import MapWindowDelegate
import MapView
import MapnikRenderThread
import SearchWindowDelegate
import InspectWindowDelegate
import StyleMenuDelegate
import LayersOutlineDataSource
import LayersWindowDelegate
import DownloadWindowDelegate

# pass control to AppKit
AppHelper.runEventLoop()
