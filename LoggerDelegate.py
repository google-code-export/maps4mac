#
#  LoggerDelegate.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 12/22/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

from Foundation import *
from AppKit import *

import GenericDataLayer

import mapnik
import datetime

class LoggerDelegate(NSController):
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
    
    trackList = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.trackMenuTitles = {False:"Start Track...", True:"End Track"}
        
        defaults = NSUserDefaults.standardUserDefaults()
        self.alwaysLog = bool(defaults.boolForKey_("always_log"))
        self.tracking  = False
        
        self.trackMenuTitle = self.trackMenuTitles[self.tracking]
        
        self.waypointLocationCache = dict()
        
        return self
    
    def awakeFromNib(self):
        self.appDelegate.addObserver_forKeyPath_options_context_(self, u"logger", 0, None)
    
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if keyPath == "logger":
            self.logger = self.appDelegate.logger
            self.logger.addObserver_forKeyPath_options_context_(self, u"waypoints", 0, None)
            self.logger.addObserver_forKeyPath_options_context_(self, u"tracks", 0, None)
        elif object == self.logger:
            if keyPath == "waypoints":
                self.waypointsTableView.reloadData()
            if keyPath == "tracks":
                self.tracksTableView.reloadData()
    
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
        self.commitEditing()
        
        props = {
        "name":str(self.addWaypointName),
        "desc":str(self.addWaypointDesc)
        }
        try:
            lat, lon = map(float,self.addWaypointPoint.split(","))
        except:
            return
        
        
        
        self.logger.addWaypointAtLon_Lat_Properties_(lon, lat, props)
        self.addWaypointWindow.orderOut_(self)
    
    @objc.IBAction
    def showAddTrackWindow_(self, sender):
        if not self.tracking:
            self.addTrackWindow.makeKeyAndOrderFront_(self)
        else:
            self.logger.endTrack()
            self.tracking = False
            
            self.logger.enabled = self.tracking
            self.trackMenuTitle = self.trackMenuTitles[self.tracking]
    
    @objc.IBAction
    def doAddTrack_(self, sender):
        self.commitEditing()
        
        self.logger.startTrackWithName_(str(self.addTrackName))
        self.addTrackWindow.orderOut_(self)
        
        self.tracking = True
        self.logger.enabled = self.tracking
        self.trackMenuTitle = self.trackMenuTitles[self.tracking]
    
    @objc.IBAction
    def addSelectionToLoggingLayer_(self, sender):
        layer = GenericDataLayer.GenericDataLayer.alloc().init()
        layer.setName_("Saved Data")
        print "Waypoints:"
        for row,waypoint in enumerate(self.logger.waypoints):
            if self.waypointsTableView.isRowSelected_(row):
                print "\t",waypoint["latitude"],waypoint["longitude"],waypoint["name"]
                layer.addPointWithX_Y_Name_(waypoint["longitude"],waypoint["latitude"],waypoint["name"])
        print "Tracks:"
        for row,track in enumerate(self.logger.tracks):
            if self.tracksTableView.isRowSelected_(row):
                print "\t",track["name"]
                for segment in self.logger.getTrackpointsForTrack_(track["id"]):
                    layer.addTrack_WithName_([mapnik.Coord(p[0], p[1]) for p in segment["position"]], track["name"])
                    
        if self.appDelegate.mapView:
            self.appDelegate.mapView.addLayer_(layer)
    
    @objc.IBAction
    def saveSelectionAsGPX_(self, sender):
        panel = NSSavePanel.alloc().init()
        panel.setTitle_("Save Data to GPX")
        panel.setAllowsOtherFileTypes_(True)
        panel.setCanSelectHiddenExtension_(True)
        if NSOKButton == panel.runModalForDirectory_file_types_(NSHomeDirectory(), None, ["gpx"]):
            filename = panel.filename()
            gpx = """<?xml version="1.0" encoding="UTF-8" ?><gpx>\n"""
            for row,waypoint in enumerate(self.logger.waypoints):
                if self.waypointsTableView.isRowSelected_(row):
                    wpt = """<wpt lat="%f" lon="%f"><name>%s</name></wpt>\n"""
                    gpx += wpt % (waypoint["latitude"],waypoint["longitude"],waypoint["name"])
                    
            for row,track in enumerate(self.logger.tracks):
                if self.tracksTableView.isRowSelected_(row):
                    gpx += "<trk>\n"
                    for segment in self.logger.getTrackpointsForTrack_(track["id"]):
                        gpx += "<trkseg>\n"
                        for i in range(len(segment["position"])):
                            gpx += """<trkpt lat="%f" lon="%f">\n""" % (segment["position"][i][1], segment["position"][i][0])
                            for tag in ["hdop","speed"]:
                                if segment[tag][i]:
                                    gpx += "<%s>%s</%s>\n" % (tag,str(segment[tag][i]),tag)
                            if segment["timestamp"][i]:
                                gpx += "<time>%s</time>\n" % (datetime.datetime.fromtimestamp(float(segment["timestamp"][i])).isoformat() + 'Z')
                            gpx += "</trkpt>\n"
                        gpx += "</trkseg>\n"
                    gpx += "</trk>\n"
            gpx += "</gpx>"
            f = open(filename,"w")
            f.write(gpx)
            f.close()
    
    @objc.IBAction
    def deleteSelection_(self,sender):
        #FIXME: Only delete from the table that had focus
        
        waypointsToDelete = list()
        tracksToDelete = list()
        for row,waypoint in enumerate(self.logger.waypoints):
            if self.waypointsTableView.isRowSelected_(row):
                waypointsToDelete.append(waypoint["id"])
                    
        for row,track in enumerate(self.logger.tracks):
            if self.tracksTableView.isRowSelected_(row):
                tracksToDelete.append(track["id"])
        
        if waypointsToDelete and tracksToDelete:
            msg = "Permanently delete the selected %d waypoints and %d tracks from the log?" % (len(waypointsToDelete), len(tracksToDelete))
        elif waypointsToDelete:
            msg = "Permanently delete the selected %d waypoints from the log?" % (len(waypointsToDelete))
        elif tracksToDelete:
            msg = "Permanently delete the selected %d tracks from the log?" % (len(tracksToDelete))
        else:
            return
        
        title = "Confirm Delete"
        alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(title, "Delete", "Cancel", None, msg)
        result = alert.runModal()
        
        if result == NSAlertAlternateReturn:
            return
        else:
            for id in waypointsToDelete:
                self.logger.deleteWaypoint_(id)
            for id in tracksToDelete:
                self.logger.deleteTrack_(id)
        
        self.waypointsTableView.deselectAll_(self)
        self.tracksTableView.deselectAll_(self)
    
    def numberOfRowsInTableView_(self, tableView):
        if tableView == self.tracksTableView:
            return len(self.logger.tracks)
        elif tableView == self.waypointsTableView:
            return len(self.logger.waypoints)
        return 0
        
    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, row):
        if tableView == self.tracksTableView:
            track = self.logger.tracks[row]
            if "Name" == tableColumn.identifier():
                return track["name"]
            if "Segments" == tableColumn.identifier():
                return track["segments"]
            if "Points" == tableColumn.identifier():
                return track["points"]
            else:
                print self.__class__,"Unknown table view identifier:",tableColumn.identifier()
                return None
        elif tableView == self.waypointsTableView:
            waypoint = self.logger.waypoints[row]
            if "Name" == tableColumn.identifier():
                return waypoint["name"]
            elif "Location" == tableColumn.identifier():
                self.waypointLocationCache[row] = "%f, %f" % (waypoint["latitude"],waypoint["longitude"])
                return self.waypointLocationCache[row]
            elif "Time" == tableColumn.identifier():
                return waypoint["time"]
            else:
                print self.__class__,"Unknown table view identifier:",tableColumn.identifier()
                return None
        else:
            return None