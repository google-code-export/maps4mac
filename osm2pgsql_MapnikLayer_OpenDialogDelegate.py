#
#  osm2pgsql_MapnikLayer_OpenDialogDelegate.py
#  Maprender
#
#  Created by Daniel Sabo on 12/16/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#

from Foundation import *

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
        
        return self
    
    def setDBParams_(self, db_args):
        def orNone(d, k):
            if not k in d:
                return None
            return d[k]
        self.host = orNone(db_args,"host")
        self.port = orNone(db_args,"port")
        self.database = orNone(db_args,"database")
        self.user = orNone(db_args,"user")
        self.password = orNone(db_args,"password")
        
        self.refreshList_(self)

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
            
    @objc.IBAction
    def loadMap_(self, sender):
        row = self.tableView.selectedRow()
        if self.dbList is not None and row != -1:
            mapName = self.dbList[row]
            self.window.orderOut_(self)
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
            
            self.appDelegate.loadosm2pgsqlWithName_dbArgs_(mapName, db_args)

    def numberOfRowsInTableView_(self, tableView):
        return len(self.dbList)
        
    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, row):
        return self.dbList[row]
