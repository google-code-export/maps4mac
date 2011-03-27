//
//  GPSdConnection.h
//  GPSd Monitor
//
//  Created by Daniel Sabo on 12/14/09.
//  Copyright 2009 Daniel Sabo. All rights reserved.
//

#import <Cocoa/Cocoa.h>

/* Keys you might find in a fix:
 * FixType: 0 = No Fix
 *          1 = 2D Fix
 *          2 = 3D Fix
 *
 * Talker:    The talker name GPSd gave us for this fix
 * Timestamp: Seconds since Unix epoc GMT
 * Latitude:  Latitude (degrees)
 * Longitude: Longitude (degrees)
 * Altitude:  Altitude (meters)
 * Heading:   Heading (degrees)
 * Speed:     Speed (meters/second)
 * Climb:     Vertical Speed (meters/second)
 *
 * TimeError:
 * HorizontalError: Calculated horizontal error (meters)
 * VerticalError:   Calculated horizontal error (meters)
 * HeadingError:    Heading (degrees)
 * SpeedError:      Speed (meters/second)
 * ClimbError:      Vertical Speed (meters/second)
 *
 * SatelliteCount:
 * 
 * HDOP
 * VDOP
 * PDOP
 * DGPS: 0 = No DPGS
 *       1 = DPGS Fix
 */

enum GPSFixType {
    GPSFixType_None = 0,
    GPSFixType_2D   = 1,
    GPSFixType_3D   = 2
};

@interface GPSdConnection : NSObject <NSStreamDelegate> {
    NSTimer *idleTimer;
    CFSocketRef sock;
    NSDate *lastUpdate;
    
    // Current fix
    NSString     *GPSName;
    NSDictionary *fix;
    NSMutableDictionary *pendingFix;
    NSMutableDictionary *cachedValues;
    NSArray      *satellites;
    
    bool connected;
    
    int conState;
    int conType;
}

/* Properties */
@property (readwrite, retain) NSDate *lastUpdate;
@property (readwrite, retain) NSDictionary *fix;
@property (readwrite, retain) NSArray      *satellites;
@property (readwrite, retain) NSString     *GPSName;
@property (readwrite) bool connected;

/* Control */
-(bool) connect;
-(bool) connectToHost: (NSHost*) host port: (int)port;
-(void) disconnect;
//TODO: List GPSs, Set GPS, filter updates

-(void) parseMessage: (NSString *)message;
-(void) parseJSONMessage: (NSString *)message;

-(void) idleTimerEvent: (NSTimer*)theTimer;

@end
