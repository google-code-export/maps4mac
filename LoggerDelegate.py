#
#  LoggerDelegate.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 12/22/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
from AppKit import *

class LoggerDelegate(NSObject):
    addWaypointWindow = objc.IBOutlet()
    addTrackWindow = objc.IBOutlet()
    appDelegate = objc.IBOutlet()
    
    tracksTableView = objc.IBOutlet()
    trackpointsTableView = objc.IBOutlet()
    waypointsTableView = objc.IBOutlet()
    
    addWaypointPoint = objc.ivar()
    addWaypointName  = objc.ivar()
    addWaypointDesc  = objc.ivar()
    
    addTrackName  = objc.ivar()
    addTrackDesc  = objc.ivar()
    
    trackMenuTitles = objc.ivar()
    trackMenuTitle = objc.ivar()
    
    tracking = objc.ivar()
    alwaysLog = objc.ivar()
    
    waypointsList = objc.ivar()
    trackList = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.trackMenuTitles = {False:"Start Track...", True:"End Track"}
        
        defaults = NSUserDefaults.standardUserDefaults()
        self.alwaysLog = bool(defaults.boolForKey_("always_log"))
        self.tracking  = False
        #self.appDelegate.logger.enabled = self.tracking
        
        self.trackMenuTitle = self.trackMenuTitles[self.tracking]
        
        return self
    
    @objc.IBAction
    def showAddWaypointWindow_(self, sender):
        mapView = self.appDelegate.mapView
        centerCoord = mapView.center
        posString = "%f, %f" % (centerCoord.y, centerCoord.x)
        
        self.willChangeValueForKey_("addWaypointPoint")
        self.addWaypointPoint = posString
        self.didChangeValueForKey_("addWaypointPoint")
        
        self.addWaypointWindow.makeKeyAndOrderFront_(self)
    
    @objc.IBAction
    def doAddWaypoint_(self, sender):
        props = {
        "name":str(self.addWaypointName), "desc":str(self.addWaypointDesc)}
        try:
            lat, lon = map(float,self.addWaypointPoint.split(","))
        except:
            return
        
        self.appDelegate.logger.addWaypointAtLon_Lat_Properties_(lon, lat, props)
        self.addWaypointWindow.orderOut_(self)
    
    @objc.IBAction
    def showAddTrackWindow_(self, sender):
        if not self.tracking:
            self.addTrackWindow.makeKeyAndOrderFront_(self)
        else:
            self.appDelegate.logger.endTrack()
            self.tracking = False
            
            self.appDelegate.logger.enabled = self.tracking
            self.trackMenuTitle = self.trackMenuTitles[self.tracking]
    
    @objc.IBAction
    def doAddTrack_(self, sender):
        self.appDelegate.logger.startTrackWithName_(str(self.addTrackName))
        self.addTrackWindow.orderOut_(self)
        
        self.tracking = True
        self.appDelegate.logger.enabled = self.tracking
        self.trackMenuTitle = self.trackMenuTitles[self.tracking]
    
    @objc.IBAction
    def addSelectionToLoggingLayer_(self, sender):
        #FIXME: Enable this
        print "Waypoints:"
        for row,waypoint in enumerate(self.waypointsList):
            if self.waypointsTableView.isRowSelected_(row):
                print "\t",waypoint[0],waypoint[3]
        print "Tracks:"
        for row,track in enumerate(self.trackList):
            if self.tracksTableView.isRowSelected_(row):
                print "\t",track[0],track[1]
    
    @objc.IBAction
    def saveSelectionAsGPX_(self, sender):
        panel = NSSavePanel.alloc().init()
        panel.setTitle_("Save Data to GPX")
        if NSOKButton == panel.runModalForDirectory_file_types_(NSHomeDirectory(), None, ["gpx"]):
            filename = panel.filename()
            gpx = """<?xml version="1.0" encoding="UTF-8" ?><gpx>\n"""
            for row,waypoint in enumerate(self.waypointsList):
                if self.waypointsTableView.isRowSelected_(row):
                    wpt = """<wpt lat="%f" lon="%f"><name>%s</name></wpt>\n"""
                    gpx += wpt % (waypoint[1],waypoint[2],waypoint[3])
            gpx += "</gpx>"
            f = open(filename,"w")
            f.write(gpx)
            f.close()
    
    @objc.IBAction
    def deleteSelection_(self,sender):
        pass
    
    def numberOfRowsInTableView_(self, tableView):
        if tableView == self.tracksTableView:
            #return self.appDelegate.logger.getTracksLen()
            if not self.trackList:
                self.trackList = self.appDelegate.logger.getTracks()
            return len(self.trackList)
        if tableView == self.trackpointsTableView:
            return 0
        elif tableView == self.waypointsTableView:
            #return self.appDelegate.logger.getWaypointsLen()
            if not self.waypointsList:
                self.waypointsList = []
                for waypoint in self.appDelegate.logger.getWaypoints():
                    loc = None
                    try:
                        loc = "%.4f, %.4f" % (waypoint[2],waypoint[1])
                    except:
                        pass
                    self.waypointsList.append([waypoint[0],waypoint[1],waypoint[2],waypoint[3],waypoint[4],loc])
                #self.waypointsList = self.appDelegate.logger.getWaypoints()
            return len(self.waypointsList)
        return 0
        
    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, row):
        if tableView == self.tracksTableView:
            track = self.trackList[row]
            #track = self.appDelegate.logger.getTrack_(row)
            if not track:
                return None
            if "Name" == tableColumn.identifier():
                return track[1]
            else:
                print self.__class__,"Unknown table view identifier:",tableColumn.identifier()
                return None
        elif tableView == self.waypointsTableView:
            waypoint = self.waypointsList[row]
            #waypoint = self.appDelegate.logger.getWaypoint_(row)
            # Stuff the location somewhere so it doesn't get garbage collected
            #self.waypointCache[row] = [waypoint[3],waypoint[4],None]
            if not waypoint:
                return None
            if "Name" == tableColumn.identifier():
                return waypoint[3]
            elif "Location" == tableColumn.identifier():
                return waypoint[5]
                #try:
                #    loc = "%.4f, %.4f" % (waypoint[2],waypoint[1])
                #    self.waypointCache[row][5] = loc
                #except:
                #    return None
                #return loc
            elif "Time" == tableColumn.identifier():
                return waypoint[4]
            else:
                print self.__class__,"Unknown table view identifier:",tableColumn.identifier()
                return None
        else:
            return None