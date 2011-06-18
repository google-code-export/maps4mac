#
#  SearchWindowDelegate.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 5/7/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

from Foundation import *
from GenericDataLayer import GenericDataLayer

import mapnik

class SearchWindowDelegate(NSObject):
    searchField = objc.IBOutlet()
    resultsView = objc.IBOutlet()
    mapView     = objc.IBOutlet()
    
    results = objc.ivar()
    
    search_providers = objc.ivar()
    searchable = objc.ivar()
        
    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.results = list()
        self.searchable = False
        
        return self
    
    def awakeFromNib(self):
        self.resultsView.setTarget_(self)
        self.resultsView.setDoubleAction_("doubleClicked:")
        self.mapView.addObserver_forKeyPath_options_context_(self, u"layers", 0, None)

        
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if keyPath == "layers":
            self.search_providers = dict()
            for layer in self.mapView.layers:
                provider = layer.getSearchProvider()
                if provider:
                    name = layer.name
                    suffix = 1
                    while name in self.search_providers.keys():
                        name = layer.name + " (%d)" % suffix
                        suffix += 1
                    self.search_providers[name] = provider
            
            #print "Search: Layers did change, %d providers" % len(self.search_providers)
            
            if self.search_providers:
                self.searchable = True
            else:
                self.searchable = False

    @objc.IBAction
    def search_(self, sender):
        if not  self.search_providers:
            return
        commands   = self.searchField.stringValue()
        center     = self.mapView.getWGS84Center()
        viewBounds = self.mapView.getWGS84Envelope()
        
    
        results = None
        self.resultsView.setToolTip_(None)
        #FIXME: For now there's only one possible provider, but there needs to be a list to pick from in the search window
        try:
            results = self.search_providers.values()[0].doSearch(commands,center=center,viewBounds=viewBounds)
        except Exception as error:
            import traceback
            print error
            traceback.print_exc()
            
            self.returnSearch_Error_(commands, str(error))
        else:
            self.returnSearch_Results_(commands, results)
    
    def returnSearch_Results_(self, search_string, results):
        self.willChangeValueForKey_("results")
        self.results = list()
        layer = GenericDataLayer.alloc().init()
        for result in results:
            name = result["name"]
            if name == "":
                name = None
            if "line" in result:
                track = [mapnik.Coord(p[0], p[1]) for p in result["line"]]
                t = layer.addTrack_WithName_(track,name)
                result["loc"] = "%f, %f" % (result["line"][0][1],result["line"][0][0])
                
                if "description" in result:
                    layer.setDescription_ForTrack_(result["description"], t)
                
                del result["line"] #FIXME: Use another object so we don't have to worry about cleanup here
            else:
                p = layer.addPointWithX_Y_Name_(result["loc"][0],result["loc"][1],name)
                result["loc"] = "%f, %f" % (result["loc"][1],result["loc"][0])
                
                if "description" in result:
                    layer.setDescription_ForPoint_(result["description"], p)
            
            self.results.append(result)
        self.didChangeValueForKey_("results")
        
        layer.setName_("Search Results")
        layer.setDescription_(search_string)
        self.mapView.addLayer_(layer)
        
        if self.resultsView is not None:
            self.resultsView.reloadData()
    
    def returnSearch_Error_(self, search_string, error):
        self.resultsView.setToolTip_(str(error))
        self.willChangeValueForKey_("results")
        self.results = [{"type":"DB Error", "name":"DB Error", "loc":"DB Error", "distance":"DB Error"}]
        self.didChangeValueForKey_("results")
        
        title = "Search Error"
        msg =  "Couldn't parse the search:\n" + str(error)
        alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(title, "OK", None, None, msg)
        alert.runModal()
        
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