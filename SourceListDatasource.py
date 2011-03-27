#
#  SourceListDatasource.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 4/21/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

from Foundation import *

class SourceListDatasource(NSObject):
    dbList    = objc.ivar()
    tableView = objc.IBOutlet()

    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.dbList = []
        self.tableView = None
        
        return self

    def numberOfRowsInTableView_(self, tableView):
        return len(self.dbList)
        
    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, row):
        return self.dbList[row]
    
    def setList_(self, l):
        self.dbList = l
        if self.tableView is not None:
            self.tableView.reloadData()
        