//
//  SatelliteTableController.h
//  GPSd Monitor
//
//  Created by Daniel Sabo on 11/18/09.
//  Copyright 2009 __MyCompanyName__. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import "GPSdConnection.h"

@interface SatelliteTableController : NSObject {
    IBOutlet NSTableView *tableViewOutlet;
    
    @private
    NSMutableArray *tableData;
    NSSortDescriptor *sortDesc;

}

@property (readwrite, retain) NSMutableArray *tableData;

- (int)numberOfRowsInTableView:(NSTableView *)tableView;
- (id)tableView:(NSTableView *)tableView objectValueForTableColumn:(NSTableColumn *)tableColumn row:(int)row;

- (void)observeGPSdConnection:(GPSdConnection *)connection;
- (void)observeValueForKeyPath:(NSString *)keyPath ofObject:(id)object change:(NSDictionary *)change context:(void *)context;

@end
