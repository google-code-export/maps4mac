#
#  SearchWindowDelegate.py
#  Maprender
#
#  Created by Daniel Sabo on 5/7/10.
#  Copyright (c) 2010 __MyCompanyName__. All rights reserved.
#
import pgdb as DBAPI
import pg

from Foundation import *

class SearchWindowDelegate(NSObject):
    searchField = objc.IBOutlet()
    resultsView = objc.IBOutlet()
    mapView     = objc.IBOutlet()
    
    db_args = objc.ivar()
    mapName = objc.ivar()
    results = objc.ivar()
    
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.results = list()
        
        return self
    
    def awakeFromNib(self):
        self.resultsView.setTarget_(self)
        self.resultsView.setDoubleAction_("doubleClicked:")

    @objc.IBAction
    def search_(self, sender):
        if self.mapName is None:
            return
        
        commands = self.searchField.stringValue()
        con = DBAPI.connect(**self.db_args)
        
        self.results = list()
        
        transform = \
        {"point":"way",
         "line" :"ST_StartPoint(way)",
         "polygon":"ST_Centroid(way)"}
        
        try:
            tables = ["point", "line", "polygon"]
            for tableSuffix in tables:
                table = self.mapName + "_" + tableSuffix
                cur = con.cursor()
                # Keep lines instead of centroid
                sql = "select name, ST_AsText(ST_Transform(%s, 4269)) from %s where %s" % (transform[tableSuffix], table, commands)
                cur.execute(sql)
            
                rows = cur.fetchall()
                
                for row in rows:
                    loc = row[1]
                    loc = loc.split("(")[1].split(")")[0].split(" ")
                    loc = map(float, loc)
                    loc = "%.4f,%.4f" % (loc[1],loc[0])
                    self.results.append({"type":tableSuffix, "name":row[0], "loc":loc})
        except pg.DatabaseError:
            self.results = [{"type":"DB Error", "name":"DB Error", "loc":"DB Error"}]
        finally:
            con.close()
        
        if self.resultsView is not None:
            self.resultsView.reloadData()

    def numberOfRowsInTableView_(self, tableView):
        if self.results:
            return len(self.results)
        else:
            return 0

    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, row):        
        columnId = tableColumn.identifier()
        if columnId in self.results[row]:
            return self.results[row][columnId]
    
    def doubleClicked_(self,sender):
        row = sender.clickedRow()
        
        if row != -1:
            loc = self.results[row]['loc'].split(',')
            loc = map(float, loc)
            if self.mapView:
                self.mapView.setCenter_([loc[1],loc[0]])