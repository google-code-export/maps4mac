//
//  SatelliteTableController.m
//  GPSd Monitor
//
//  Created by Daniel Sabo on 11/18/09.
//  Copyright 2009 Daniel Sabo. All rights reserved.
//

#import "SatelliteTableController.h"


@implementation SatelliteTableController

@synthesize tableData;

- (SatelliteTableController *)init {
    self = [super init];
    
    if (nil == self) {
        return self;
    }
    
    tableData = [[NSArray alloc] initWithObjects:nil];
    sortDesc  = [[NSSortDescriptor alloc] initWithKey:@"PRN" ascending:true];
    
    return self;
}


- (void)observeGPSdConnection:(GPSdConnection *)connection {
    [connection addObserver:self forKeyPath:@"satellites" options:0 context:nil];
}

- (void)tableView:(NSTableView *)tableView didClickTableColumn:(NSTableColumn *)tableColumn
{
    NSSortDescriptor *newSort;
    NSString *columnId = [tableColumn identifier];
    if (NSOrderedSame == [[sortDesc key] compare:columnId]) {
        newSort = [sortDesc reversedSortDescriptor];
        [newSort retain];
    }
    else {
        newSort = [[NSSortDescriptor alloc] initWithKey:columnId ascending:true];
    }
    
    [sortDesc release];
    sortDesc = newSort;
    
    [tableData sortUsingDescriptors: [NSArray arrayWithObject: sortDesc]];
    
    [(NSTableView *)tableViewOutlet reloadData];
}

- (int)numberOfRowsInTableView:(NSTableView *)tableView {
    return [tableData count];
}

- (id)tableView:(NSTableView *)tableView objectValueForTableColumn:(NSTableColumn *)tableColumn row:(int)row {
    NSString *columnId = [tableColumn identifier];
    NSNumber * val = [[tableData objectAtIndex:row] objectForKey:columnId];

    if (NSOrderedSame == [columnId compare:@"Used"]) {
        if ([val intValue] == 1) {
            return @"Yes";
        }
        else {
            return @"No";
        }

    }
    return [val stringValue];
}

- (void)observeValueForKeyPath:(NSString *)keyPath ofObject:(id)object change:(NSDictionary *)change context:(void *)context {
    [self setTableData:[object valueForKey:keyPath]];
    
    [tableViewOutlet reloadData];
}

- (void)dealloc {
    [super dealloc];
    
    [tableData release];
    [sortDesc  release];
}

@end
