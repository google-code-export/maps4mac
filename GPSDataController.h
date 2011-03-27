//
//  GPSDataController.h
//  GPSd Monitor
//
//  Created by Daniel Sabo on 12/19/09.
//  Copyright 2009 __MyCompanyName__. All rights reserved.
//

#import <Cocoa/Cocoa.h>

#import "GPSdConnection.h"


@interface GPSDataController : NSObject {
    IBOutlet id latitudeOutlet;
    IBOutlet id longitudeOutlet;
    IBOutlet id altitudeOutlet;
    IBOutlet id horizontalErrorOutlet;
    IBOutlet id altitudeErrorOutlet;
    
    IBOutlet id headingOutlet;
    IBOutlet id cardinalHeadingOutlet;
    IBOutlet id headingErrorOutlet;
    
    IBOutlet id climbOutlet;
    IBOutlet id climbErrorOutlet;
    
    IBOutlet id speedOutlet;
    IBOutlet id speedErrorOutlet;
    
    IBOutlet id DOPOutlet;
    IBOutlet id HDOPOutlet;
    IBOutlet id VDOPOutlet;
    
    IBOutlet id timeOutlet;
    
    IBOutlet id gpsNameOutput;
    IBOutlet id fixTypeOutput;
    
    IBOutlet id tagOutlet;
    
    NSArray *outputFormatDoubles;
}

- (void)observeGPSdConnection:(GPSdConnection *)connection;

- (void)observeValueForKeyPath:(NSString *)keyPath ofObject:(id)object change:(NSDictionary *)change context:(void *)context;

@end
