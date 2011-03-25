#
#  osm2pgsql_MapnikLayer_OpenDialogDelegate.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 12/16/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *
import os.path

class osm2pgsql_MapnikLayer_OpenDialogDelegate(NSObject):
    dbAPI = objc.ivar()
    
    host = objc.ivar()
    port = objc.ivar()
    database = objc.ivar()
    user = objc.ivar()
    password = objc.ivar()
    
    dbList    = objc.ivar()
    tableView = objc.IBOutlet()
    window    = objc.IBOutlet()
    
    error = objc.ivar()
    
    appDelegate = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.dbList = list()
        
        defaults = NSUserDefaults.standardUserDefaults()
        self.host = defaults.stringForKey_("db_hostname")
        self.port = defaults.stringForKey_("db_port")
        self.database = defaults.stringForKey_("db_database")
        self.user = defaults.stringForKey_("db_username")
        self.password = defaults.stringForKey_("db_password")
        
        self.refreshList_(self)
        
        return self

    @objc.IBAction
    def refreshList_(self, sender):
        if not self.dbAPI:
            import pgdb
            self.dbAPI = pgdb
        
        extracts = list()
        con = None
        try:
            host = self.host
            if self.port:
                host += ":" + str(self.port)
            con = self.dbAPI.connect(user=self.user,
                                     password=self.password,
                                     host=host,
                                     database=self.database)
            cur = con.cursor()
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            tables = [t[0] for t in cur.fetchall()]
            for table in tables:
                if table.endswith("_point"):
                    extracts.append(table[:-len("_point")])
            self.dbList = extracts
            self.error = ""
        except Exception as error:
            self.error = str(error)
            self.dbList = list()
        finally:
            if con:
                con.close()
        
        if self.tableView is not None:
            self.tableView.reloadData()
    
    def checkFiles(self):
        #FIXME: This path shoud only be calculated in one place
        defaults = NSUserDefaults.standardUserDefaults()
        world_boundaries_path = defaults.stringForKey_("world_boundaries_path")
        if not world_boundaries_path:
            world_boundaries_path = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES)[0] + "/" + NSBundle.mainBundle().infoDictionary()["CFBundleName"]
            world_boundaries_path += "/osm2pgsql_MapnikLayer/world_boundaries/"
        
        archive_files = {
        "world_boundaries-spherical.tgz" : [
            "world_boundaries_m.index",
            "world_bnd_m.shx",
            "builtup_area.shx",
            "world_bnd_m.dbf",
            "builtup_area.prj",
            "places.shp",
            "world_boundaries_m.shx",
            "world_boundaries_m.shp",
            "places.dbf",
            "places.prj",
            "builtup_area.dbf",
            "world_bnd_m.shp",
            "world_bnd_m.prj",
            "world_boundaries_m.dbf",
            "builtup_area.shp",
            "world_boundaries_m.prj",
            "world_bnd_m.index",
            "builtup_area.index",
        ],
        "shoreline_300.tar.bz2" : [
            "shoreline_300.dbf",
            "shoreline_300.index",
            "shoreline_300.shp",
            "shoreline_300.shx",
        ],
        "processed_p.tar.bz2" : [
            "processed_p.dbf",
            "processed_p.index",
            "processed_p.shp",
            "processed_p.shx",
        ],
        }
        
        toDownload = []
        
        for archive,contents in archive_files.items():
            for file in contents:
                if not os.path.exists(os.path.join(world_boundaries_path,file)):
                    toDownload.append(archive)
                    break
                #print file, "OK"
                
        urls = {
        "world_boundaries-spherical.tgz":"http://tile.openstreetmap.org/world_boundaries-spherical.tgz",
        "processed_p.tar.bz2":"http://tile.openstreetmap.org/processed_p.tar.bz2",
        "shoreline_300.tar.bz2":"http://tile.openstreetmap.org/shoreline_300.tar.bz2",
        }
        
        return [urls[x] for x in toDownload]
    
    def downloadDone(self):
        import tarfile, zipfile
        
        defaults = NSUserDefaults.standardUserDefaults()
        world_boundaries_path = defaults.stringForKey_("world_boundaries_path")
        if not world_boundaries_path:
            world_boundaries_path = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES)[0] + "/" + NSBundle.mainBundle().infoDictionary()["CFBundleName"]
            world_boundaries_path += "/osm2pgsql_MapnikLayer/world_boundaries/"
        
        

        if not os.path.exists(world_boundaries_path):
            os.makedirs(world_boundaries_path)

        #for zipname in ["10m-populated-places.zip", "110m-admin-0-boundary-lines.zip"]:
        #    print zipname,"..."
        #    z = zipfile.ZipFile(zipname)
        #    for member in z.infolist():
        #        outpath = os.path.join(world_boundaries_path, os.path.basename(member.filename))
        #        if os.path.exists(outpath):
        #            os.remove(outpath)
        #        z.extract(member, world_boundaries_path)
        #        print " ",outpath
        #    z.close()

        for tarname in ["world_boundaries-spherical.tgz", "shoreline_300.tar.bz2", "processed_p.tar.bz2",]:
            print tarname,"..."
            tar = tarfile.open(tarname)
            for member in tar:
                if member.isfile():
                    outpath = os.path.join(world_boundaries_path, os.path.basename(member.name))
                    if os.path.exists(outpath):
                        os.remove(outpath)
                    tf = tar.extractfile(member)
                    of = open(outpath,"wb")
                    buf = tf.read(256)
                    while buf:
                        of.write(buf)
                        buf = tf.read(256)
                    #of.write(tf.read())
                    of.close()
                    tf.close()
                    print " ",outpath
            tar.close()
    
    @objc.IBAction
    def loadMap_(self, sender):
        row = self.tableView.selectedRow()
        if self.dbList is not None and row != -1:
            mapName = self.dbList[row]
            db_args = {}
            db_args["host"] = str(self.host)
            db_args["port"] = str(self.port)
            if not db_args["port"] or db_args["port"] == "" or db_args["port"] == "None":
                db_args["port"] = 5432
            db_args["database"] = str(self.database)
            db_args["user"] = str(self.user)
            db_args["password"] = str(self.password)
            if not db_args["password"] or db_args["password"] == "None":
                db_args["password"] = ""
            
            toDownload = self.checkFiles()
            
            if toDownload:
                title = "Files needed"
                #msg = "Some files need to be downloaded to display an osm2pgsql layer, click ok to download them."
                msg =  "You need to download the world_boundaries files to render an osm2pgsql layer.\nThe contents of the these files are missing:\n\n"
                msg += "\n".join(toDownload)
                alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(title, "OK", None, None, msg)
                alert.runModal()
                self.window.orderOut_(self)
                return
                #alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(title, "OK", "Cancel", None, msg)
                #result = alert.runModal()
                #if result == 0:
                #    self.window.orderOut_(self)
                #    return
                #else:
                #    print toDownload
            
            self.window.orderOut_(self)
            self.appDelegate.loadosm2pgsqlWithName_dbArgs_(mapName, db_args)

    def numberOfRowsInTableView_(self, tableView):
        return len(self.dbList)
        
    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, row):
        return self.dbList[row]
