#
#  Logger.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 10/8/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

from Foundation import *
import os.path, datetime
import GenericDataLayer

#try:
#    # Use the KyngChaos sqlite3 if it's available, otherwise use the standard one
#    import pysqlite2 as sqlite
#except ImportError:
#    import sqlite3 as sqlite

import sqlite3 as sqlite


class Logger(NSObject):
    currentTract = objc.ivar()
    currentSegment = objc.ivar()
    enabled = objc.ivar()
    appDelegate = objc.ivar()
    
    layer = objc.ivar()
    layerTrack = objc.ivar()
    
    waypoints = objc.ivar()
    tracks    = objc.ivar()

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
        self.layerTrack = None
        self.enabled = False
        self.sqlCon = sqlite.connect(loggerPath)
        
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
        
        self.waypoints = []
        self.tracks    = []
        
        self.loadWaypoints()
        self.loadTracks()
        
        return self
    
    def loadWaypoints(self):
        waypointsSQL = """select id,latitude,longitude,name.value,desc.value,time.value from waypoints
                          left join waypoint_tags name on (id=name.waypoint_id and name.tag='name')
                          left join waypoint_tags desc on (id=desc.waypoint_id and desc.tag='desc')
                          left join waypoint_tags time on (id=time.waypoint_id and time.tag='time')"""
        
        waypoints = list()
        for row in self.sqlCon.execute(waypointsSQL).fetchall():
            waypoints.append({
                "id":int(row[0]),
                "latitude":float(row[1]),
                "longitude":float(row[2]),
                "name":row[3],
                "description":row[4],
                "time":row[5],
            })
        
        self.willChangeValueForKey_("waypoints")
        self.waypoints = waypoints
        self.didChangeValueForKey_("waypoints")
    
    def loadTracks(self):
        tracksSQL = """select tracks.id,tracks.name,count(distinct(track_segments.id)),count(track_segments.id) from tracks
                   left join track_segments on (tracks.id = track_segments.track_id)
                   left join trackpoints on (track_segments.id = trackpoints.segment_id) group by tracks.id;"""

        tracks = list()
        self.tracksByID = dict()
        for row in self.sqlCon.execute(tracksSQL).fetchall():
            track = {
                "id":int(row[0]),
                "name":row[1],
                "segments":int(row[2]),
                "points":int(row[3]),
            }
            
            tracks.append(track)
            self.tracksByID[track["id"]] = track
        
        self.willChangeValueForKey_("tracks")
        self.tracks = tracks
        self.didChangeValueForKey_("tracks")

    
    def connectToGPS_(self, gps):
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
            self.startTrackWithName_(None)
        
        if not self.currentSegment:
            cur.execute("insert into track_segments (track_id) values (?)", [self.currentTract])
            self.currentSegment = cur.lastrowid
            self.currentSegmentPosition = 0
            
            self.willChangeValueForKey_("tracks")
            self.tracksByID[self.currentTract]["segments"] += 1
            self.didChangeValueForKey_("tracks")
            
        #FIXME: Auto segment every 1000 points or so so that the tracks are easier to deal with?
        
        values = [self.currentSegment, self.currentSegmentPosition, lat, lon, timestamp, hdop, speed]
        cur.execute("insert into trackpoints (segment_id, position, latitude, longitude, timestamp, hdop, speed) values (?,?,?,?,?,?,?)",values)
        self.currentSegmentPosition = self.currentSegmentPosition + 1
        self.sqlCon.commit()
        
        self.willChangeValueForKey_("tracks")
        self.tracksByID[self.currentTract]["points"] += 1
        self.didChangeValueForKey_("tracks")
        
        logLayer = self.getLoggerLayer()
        if self.layerTrack is None:
            self.layerTrack = logLayer.addTrack_WithName_([], None)
        
        logLayer.appendToTrack_PointWithX_Y_(self.layerTrack, lon, lat)
    
    def endSegment(self):
        """Force the next point added to be part of a new segment in the current track"""
        self.currentSegment = None
        self.layerTrack     = None
    
    def startTrackWithName_(self,name):
        if not name:
            name = datetime.datetime.now().strftime("%c")
        
        cur = self.sqlCon.cursor()
        cur.execute("insert into tracks (name) values (?)", [name])
        self.currentTract = cur.lastrowid
        self.currentSegment = None
        self.sqlCon.commit()
        
        track = {
            "id":self.currentTract,
            "name":name,
            "segments":0,
            "points":0,
        }
        
        
        self.willChangeValueForKey_("tracks")
        self.tracks.append(track)
        self.tracksByID[track["id"]] = track
        self.didChangeValueForKey_("tracks")
        
        self.layerTrack = self.getLoggerLayer().addTrack_WithName_([], name)
    
    def endTrack(self):
        """Force the next point added to be part of a new track, if startTrackWithName is not called
        the new track will have a default name."""
        self.currentTract = None
        self.layerTrack   = None
    
    # New waypoint
    def addWaypointAtLon_Lat_(self, lon, lat):
        """Add a waypont at the given lon, lat
        """
        cur = self.sqlCon.cursor()
        cur.execute("insert into waypoints (latitude,longitude) values (?,?)", [lat,lon])
        waypoint = cur.lastrowid
        self.sqlCon.commit()
        
        self.willChangeValueForKey_("waypoints")
        self.waypoints.append({
                "id":int(waypoint),
                "latitude":lat,
                "longitude":lon,
                "name":None,
                "description":None,
                "time":None,
            })
        self.didChangeValueForKey_("waypoints")
        
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
            
        description = None
        if "description" in props:
            description = props["description"]
            
        time = None
        if "time" in props:
            time = props["time"]
        
        self.willChangeValueForKey_("waypoints")
        self.waypoints.append({
                "id":int(waypoint),
                "latitude":lat,
                "longitude":lon,
                "name":name,
                "description":description,
                "time":time,
            })
        self.didChangeValueForKey_("waypoints")
        
        self.getLoggerLayer().addPointWithX_Y_Name_(lon, lat, name)
    
    def getTrackpointsForTrack_(self,id):
        cur = self.sqlCon.cursor()
        track = list()
        for segment_row in cur.execute("select id from track_segments where track_id = ?", [id]).fetchall():
            segment = {
                "position":list(),
                "timestamp":list(),
                "hdop":list(),
                "speed":list(),
            }
            for row in cur.execute("select longitude,latitude,timestamp,hdop,speed from trackpoints where segment_id = ? order by position", [segment_row[0]]).fetchall():
                segment["position"].append([float(row[0]), float(row[1])])
                segment["timestamp"].append(row[2] and float(row[2]))
                segment["hdop"].append(row[3] and float(row[3]))
                segment["speed"].append(row[4] and float(row[4]))
            track.append(segment)
        return track
    
    def deleteWaypoint_(self, id):
        self.willChangeValueForKey_("waypoints")
        for i,waypoint in enumerate(self.waypoints):
            if waypoint["id"] == id:
                del self.waypoints[i]
                break
        self.didChangeValueForKey_("waypoints")
        
        cur = self.sqlCon.cursor()
        cur.execute("delete from waypoints where id = ?", [id])
        cur.execute("delete from waypoint_tags where waypoint_id = ?", [id])
        self.sqlCon.commit()
    
    def deleteTrack_(self, id):
        self.willChangeValueForKey_("tracks")
        for i,track in enumerate(self.tracks):
            if track["id"] == id:
                del self.tracks[i]
                break
        self.didChangeValueForKey_("tracks")
        
        cur = self.sqlCon.cursor()
        for segment_row in cur.execute("select id from track_segments where track_id = ?", [id]).fetchall():
            cur.execute("delete from trackpoints where segment_id = ?", [segment_row[0]]).fetchall()
        cur.execute("delete from track_segments where track_id = ?", [id]).fetchall()
        cur.execute("delete from tracks where id = ?", [id]).fetchall()
        self.sqlCon.commit()        