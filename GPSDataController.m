//
//  GPSDataController.m
//  GPSd Monitor
//
//  Created by Daniel Sabo on 12/19/09.
//  Copyright 2009 __MyCompanyName__. All rights reserved.
//

#import "GPSDataController.h"


@implementation GPSDataController

- (void)observeGPSdConnection:(GPSdConnection *)connection {
    [connection addObserver:self forKeyPath:@"fix"        options:0 context:nil];
    [connection addObserver:self forKeyPath:@"GPSName"    options:0 context:nil];
    
    outputFormatDoubles = [[NSArray alloc] initWithObjects:
                           [NSArray arrayWithObjects:@"Latitude",  @"%.6f°", latitudeOutlet, nil],
                           [NSArray arrayWithObjects:@"Longitude", @"%.6f°", longitudeOutlet, nil],
                           [NSArray arrayWithObjects:@"HorizontalError",@"±%.4fm", horizontalErrorOutlet, nil],
                           [NSArray arrayWithObjects:@"Altitude",  @"%.4fm", altitudeOutlet, nil],
                           [NSArray arrayWithObjects:@"VerticalError", @"±%.4fm", altitudeErrorOutlet, nil],
                           [NSArray arrayWithObjects:@"Heading",   @"%.4f°", headingOutlet, nil],
                           [NSArray arrayWithObjects:@"HeadingError",@"±%.4f°", headingErrorOutlet, nil],
                           [NSArray arrayWithObjects:@"Speed",     @"%.4fm/s", speedOutlet, nil],
                           [NSArray arrayWithObjects:@"SpeedError",@"±%.4fm/s", speedErrorOutlet, nil],                           
                           [NSArray arrayWithObjects:@"Climb",     @"%.4fm/s", climbOutlet, nil],
                           [NSArray arrayWithObjects:@"ClimbError",@"±%.4fm/s", climbErrorOutlet, nil],
                           [NSArray arrayWithObjects:@"DOP",       @"%.4f", DOPOutlet, nil],
                           [NSArray arrayWithObjects:@"VDOP",      @"%.4f", VDOPOutlet, nil],
                           [NSArray arrayWithObjects:@"HDOP",      @"%.4f", HDOPOutlet, nil],
                           nil];
                           
                    
}

- (void)observeValueForKeyPath:(NSString *)keyPath ofObject:(id)object change:(NSDictionary *)change context:(void *)context {
    if ([keyPath isEqual:@"fix"]) {
        NSDictionary *fixDict = [object valueForKey:keyPath];
        
        for(NSArray *format in outputFormatDoubles) {
            if (3 == [format count]) { // If the outlet was nil the array will be short
                NSNumber *value = [fixDict valueForKey:[format objectAtIndex:0]];
                if (nil != value) {
                    NSString *formattedVal = [NSString stringWithFormat:[format objectAtIndex:1], [value doubleValue]];
                    [[format objectAtIndex:2] setStringValue:formattedVal];
                }
                else {
                    [[format objectAtIndex:2] setStringValue:@""];
                }
            }
        }
        
        NSNumber *gpsTime = [fixDict valueForKey:@"Timestamp"];
        if (nil != gpsTime) {
            [timeOutlet setStringValue:[[NSDate dateWithTimeIntervalSince1970:[gpsTime doubleValue]] description]];
        }
        
        NSString *tag = [fixDict valueForKey:@"Tag"];
        if (nil != tag) {
            [tagOutlet setStringValue:tag];
        }
        
        NSNumber *value = [fixDict valueForKey:@"FixType"];
        if((nil == value) || (GPSFixType_None == [value intValue])) {
            [fixTypeOutput setStringValue:@"No Fix"];
        }
        else if (GPSFixType_2D == [value intValue]) {
            if ([[fixDict valueForKey:@"DGPS"] intValue]) {
                [fixTypeOutput setStringValue:@"2D DGPS Fix"];
            }
            else {
                [fixTypeOutput setStringValue:@"2D Fix"];
            }
        }
        else if (GPSFixType_3D == [value intValue]) {
            if ([[fixDict valueForKey:@"DGPS"] intValue]) {
                [fixTypeOutput setStringValue:@"3D DGPS Fix"];
            }
            else {
                [fixTypeOutput setStringValue:@"3D Fix"];
            }
            
        }
    }
    else if ([keyPath isEqual:@"GPSName"]) {
        NSString *value = [object valueForKey:@"GPSName"];
        if (nil == value) {
            [gpsNameOutput setStringValue:@"No GPS Connected"];
        }
        else {
            [gpsNameOutput setStringValue:[object valueForKey:@"GPSName"]];
        }
    }
}

@end
