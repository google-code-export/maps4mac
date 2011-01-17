#
#  Logger.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 10/8/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
import os.path, datetime
import GenericDataLayer

#try:
#    # Use the KyngChaos sqlite3 if it's available, otherwise use the standard one
#    import pysqlite2 as sqlite3
#except ImportError:
#    import sqlite3

import sqlite3


class Logger(NSObject):
    currentTract = objc.ivar()
    currentSegment = objc.ivar()
    enabled = objc.ivar()
    appDelegate = objc.ivar()
    layer = objc.ivar()

    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        # Find or create logging directory in application support
        
        loggerPath = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES)[0]
        loggerPath += "/" + NSBundle.mainBundle().infoDictionary()['CFBundleName']
        if not os.path.exists(loggerPath):
            os.makedirs(loggerPath)
        loggerPath += "/logger.sqlite"
        
        self.currentTract = None
        self.currentSegment = None
        self.layer = None
        self.enabled = False
        self.sqlCon = sqlite3.connect(loggerPath)
        
        schema = """
        create table tracks (id integer primary key autoincrement, name text);
        create table track_segments (id integer primary key autoincrement, track_id integer not null);
        create table trackpoints (segment_id integer, position integer, latitude real not null, longitude real not null, timestamp real, hdop real, speed real);
        create table waypoints (id integer primary key autoincrement, latitude real not null, longitude real not null);
        create table waypoint_tags (waypoint_id integer, tag text, value text);
        """
        
        # Check if there's anything in the DB or initialize it
        cur = self.sqlCon.cursor()
        if not 5 == cur.execute("select count(name) from sqlite_master where name in ('tracks', 'track_segments','trackpoints','waypoints','waypoint_tags')").fetchall()[0][0]:
            cur.executescript(schema)
        
        cur.execute("PRAGMA journal_mode=truncate") # To reduce the amount of disk fiddling when recording tracks
        
        return self
    
    def connect_(self, gps):
        gps.addObserver_forKeyPath_options_context_(self, u"fix", 0, None)
        
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if keyPath == "fix" and self.enabled:
            fix = object.fix()
            if fix is not None and fix["FixType"] != 0:
                self.addTrackpointWithValues_(fix)
                
        # FIXME: Check how long it's been since the last GPS data to see if we should split the tract
    
    def getLoggerLayer(self):
        if not self.layer:
            self.layer = GenericDataLayer.GenericDataLayer.alloc().init()
            self.layer.setName_("Logger")
            
        if not self.layer.view and self.appDelegate.mapView:
            self.appDelegate.mapView.addLayer_(self.layer)
        
        return self.layer
    
    def addTrackpointWithValues_(self, fix):
        def orNone(k, d):
            if k in d:
                return d[k]
            else:
                return None
        
        lat = fix["Latitude"]
        lon = fix["Longitude"]
        timestamp = orNone("Timestamp", fix)
        hdop = orNone("HDOP", fix)
        speed = orNone("Speed", fix)
        
        cur = self.sqlCon.cursor()
        
        if not self.currentTract:
            cur.execute("insert into tracks (name) values (?)", [datetime.datetime.now().strftime("%c")])
            self.currentTract = cur.lastrowid
        
        if not self.currentSegment:
            cur.execute("insert into track_segments (track_id) values (?)", [self.currentTract])
            self.currentSegment = cur.lastrowid
            self.currentSegmentPosition = 0
            
        #FIXME: Auto segment every 1000 points or so so that the tracks are easier to deal with?
        
        values = [self.currentSegment, self.currentSegmentPosition, lat, lon, timestamp, hdop, speed]
        cur.execute("insert into trackpoints (segment_id, position, latitude, longitude, timestamp, hdop, speed) values (?,?,?,?,?,?,?)",values)
        self.currentSegmentPosition = self.currentSegmentPosition + 1
        self.sqlCon.commit()
    
    def endSegment(self):
        """Force the next point added to be part of a new segment in the current track"""
        self.currentSegment = None
    
    def startTrackWithName_(self,name):
        if not name:
            name = datetime.datetime.now().strftime("%c")
        
        cur = self.sqlCon.cursor()
        cur.execute("insert into tracks (name) values (?)", [name])
        self.currentTract = cur.lastrowid
        self.currentSegment = None
        self.sqlCon.commit()
    
    def endTrack(self):
        """Force the next point added to be part of a new track, if startTrackWithName is not called
        the new track will have a default name."""
        self.currentTract = None
    
    # New waypoint
    def addWaypointAtLon_Lat_(self, lon, lat):
        """Add a waypont at the given lon, lat
        """
        cur = self.sqlCon.cursor()
        cur.execute("insert into waypoints (latitude,longitude) values (?,?)", [lat,lon])
        self.sqlCon.commit()
        
        self.getLoggerLayer().addPointWithX_Y_Name_(lon, lat, None)
    
    def addWaypointAtLon_Lat_Properties_(self, lon, lat, props):
        """Add a waypont at the given lon, lat with additional properties
        provided in a dictionary.
        """
        cur = self.sqlCon.cursor()
        cur.execute("insert into waypoints (latitude,longitude) values (?,?)", [lat,lon])
        waypoint = cur.lastrowid
        for key,value in props.items():
            cur.execute("insert into waypoint_tags (waypoint_id,tag,value) values (?,?,?)", [waypoint,key,value])
        self.sqlCon.commit()
        
        name = None
        if "name" in props:
            name = props["name"]
        
        self.getLoggerLayer().addPointWithX_Y_Name_(lon, lat, name)
    
    def getWaypoints(self):
        cur = self.sqlCon.cursor()
        points = cur.execute("select id,latitude,longitude,name.value,time.value from waypoints left join waypoint_tags name on (id=name.waypoint_id and name.tag='name') left join waypoint_tags time on (id=time.waypoint_id and time.tag='time')").fetchall()
        #for point in points:
        #    pos = [point[1],point[0]]
        #    name = point[2]
        #    time = point[3]
        return points
    
    def getWaypointsLen(self):
        cur = self.sqlCon.cursor()
        return cur.execute("select count(*) from waypoints").fetchall()[0][0]
    
    def getWaypoint_(self,num):
        cur = self.sqlCon.cursor()
        wpt = cur.execute("select id,latitude,longitude,name.value,time.value from waypoints left join waypoint_tags name on (id=name.waypoint_id and name.tag='name') left join waypoint_tags time on (id=time.waypoint_id and time.tag='time') limit 1 offset (?);", [num]).fetchall()[0]
        if not wpt:
            return None
        return wpt
    
    def getTracksLen(self):
        cur = self.sqlCon.cursor()
        return cur.execute("select count(*) from tracks").fetchall()[0][0]
    
    def getTrack_(self,num):
        cur = self.sqlCon.cursor()
        track = cur.execute("select * from tracks limit 1 offset (?);", [num]).fetchall()[0]
        if not track:
            return None
        return track
    
    def getTracks(self):
        cur = self.sqlCon.cursor()
        tracks = cur.execute("select id,name from tracks").fetchall()
        return tracks
    
    def getTrackpointsForTrack_(self,id):
        cur = self.sqlCon.cursor()
        points = cur.execute("select latitude,longitude,timestamp from track_segments,trackpoints where ?=track_segments.track_id and track_segments.id=trackpoints.segment_id group by tracks.id", int(id)).fetchall()
        return points
        