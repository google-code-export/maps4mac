//
//  GPSdConnection.m
//  GPSd Monitor
//
//  Created by Daniel Sabo on 12/14/09.
//  Copyright 2009 __MyCompanyName__. All rights reserved.
//

#import "GPSdConnection.h"
#import "JSON.h"

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>

@implementation GPSdConnection

@synthesize fix, satellites, GPSName, connected;
@synthesize lastUpdate;


enum GPSConnectionStates {
    NoConnection,
    WaitingForVersion,
    StreamRequested,
    StreamRunning
};

enum GPSConnectionTypes {
    Unknown_Connection_Proto,
    JSON_Connection_Proto,
    Old_Connection_Proto
};

void SocketCallback (
                 CFSocketRef s,
                 CFSocketCallBackType callbackType,
                 CFDataRef address,
                 const void *data,
                 void *info
                     ) {
    GPSdConnection *conObj = (GPSdConnection *)info;
    
    if (callbackType == kCFSocketDataCallBack) {
        //NSLog(@"SocketCallback: Read");
        NSData *dataObj = (NSData *)data;
        NSString *dataString = [[NSString alloc] initWithData:dataObj encoding:NSASCIIStringEncoding];
        
        NSArray *messages = [dataString componentsSeparatedByString:@"\r\n"];
    
        NSRange r;
        r.location = 0;
        r.length   = [messages count] - 1;
        for(NSString *messageString in [messages subarrayWithRange:r]) {
            if ([messageString hasPrefix: @"GPSD,"]) {
                for(NSString *message in [[messageString substringFromIndex: 5] componentsSeparatedByString:@","]) {
                    [conObj parseMessage:message];
                }
            }
            else if ([messageString hasPrefix: @"{"]) {
                // New style message
                [conObj parseJSONMessage:messageString];
            }
            else {
                NSLog(@"GPSdConnection: Invalid message");
            }
        }
        
        [dataString release];
        
    }
    else if (callbackType == kCFSocketConnectCallBack) {
        //NSLog(@"SocketCallback: Connect");
    }
    else {
        NSLog(@"SocketCallback: ?");
    }
    
    [conObj setLastUpdate: [NSDate date]];

}


-(GPSdConnection *)init {
    self = [super init];
    if (!self) {
        return self;
    }
    
    sock = NULL;
    lastUpdate = nil;
    idleTimer = nil;
    
    connected = false;
    
    conState = NoConnection;
    
    return self;
}

-(bool)connect {
    return [self connectToHost:[NSHost hostWithAddress:@"127.0.0.1"] port:2947];
}


-(bool) connectToHost: (NSHost*) host port: (int)port {
    [self disconnect];
    
    CFSocketContext context;
    context.version = 0;
    context.info = (void *)self;
    context.retain = NULL;
    context.release = NULL;
    context.copyDescription = NULL;
    
    
    
    //CFSocketRef sock = CFSocketCreate(NULL, PF_INET, SOCK_STREAM, 0, kCFSocketReadCallBack | kCFSocketConnectCallBack, SocketCallback, self);
    sock = CFSocketCreate(NULL, PF_INET, SOCK_STREAM, 0, kCFSocketDataCallBack | kCFSocketConnectCallBack, SocketCallback, &context);
    CFRunLoopSourceRef sockSrc = CFSocketCreateRunLoopSource(NULL, sock, 0);
    CFRunLoopAddSource(CFRunLoopGetCurrent(), sockSrc, kCFRunLoopCommonModes);
    
    struct sockaddr_in theName;
    struct hostent *hp;
    CFDataRef addressData;
    
    theName.sin_port = htons(port);
    theName.sin_family = AF_INET;
    
    hp = gethostbyname( [[host address] UTF8String] );
    if( hp == NULL ) {
        return false;
    }
    
    memcpy( &theName.sin_addr.s_addr, hp->h_addr_list[0], hp->h_length );
    
    addressData = CFDataCreate( NULL, (const UInt8 *)&theName, sizeof( struct sockaddr_in ) );
    
    
    CFSocketConnectToAddress(sock, addressData, -1);
    
    CFRelease(sockSrc);
    CFRelease(addressData);
    
    idleTimer = [NSTimer scheduledTimerWithTimeInterval: 0.5
                                                    target: self
                                                  selector: @selector(idleTimerEvent:)
                                                  userInfo: nil
                                                   repeats: YES];
    [idleTimer retain];
    
    conState = WaitingForVersion;
    conType  = Unknown_Connection_Proto;
    
    return true;
}

-(void) disconnect {
    [self setConnected:false];
    
    [idleTimer invalidate];
    [idleTimer release];
    
    if (NULL != sock) {
        CFRelease(sock);
        sock = NULL;
    }
}

#if 0
- (void)stream:(NSStream *)aStream handleEvent:(NSStreamEvent)eventCode {
    if (NSStreamEventErrorOccurred == eventCode) {
        /*
        if (aStream == iStream) {
            NSLog(@"Input Stream Error, Disconnecting");
        }
        else if (aStream == oStream) {
            NSLog(@"Output Stream Error, Disconnecting");
        }
         */
        [self disconnect];
        [self connect];
    }
    /*
    else if (NSStreamEventOpenCompleted == eventCode) {
        NSLog(@"%@ Stream Open", streamName);
    }
     */
    
    else if (NSStreamEventHasSpaceAvailable == eventCode) {
        if (aStream == oStream) {
            if ([pendingCommands count] > 0) {
                NSMutableString *command = [NSMutableString stringWithString: [pendingCommands objectAtIndex:0]];
                [command appendString: @"\n"];
                const char *str = [command UTF8String];
                NSUInteger len = strlen(str);
                NSInteger result = [oStream write:(const uint8_t *)str maxLength:len];
                
                [pendingCommands removeObjectAtIndex:0];
                
                if (-1 == result) {
                    NSLog(@"Network write error");
                }
            }
        }
    }
    else if (NSStreamEventHasBytesAvailable == eventCode) {
        NSInteger       bytesRead;
        uint8_t         buffer[1024];
        
        bytesRead = [iStream read:buffer maxLength:sizeof(buffer)];
        if (bytesRead == -1) {
            NSLog(@"Network read error");
            [self disconnect];
        }
        else {
            if (!connected) {
                [self setConnected:true];
            }
            NSString *newData = [[NSString alloc] initWithBytesNoCopy:buffer length:bytesRead encoding:NSASCIIStringEncoding freeWhenDone:false];
            [inputBuffer appendString:newData];
            [newData release];
        }
        
        NSArray *messages = [inputBuffer componentsSeparatedByString:@"\r\n"];
        
        if ([messages count] > 1) {
            [inputBuffer setString:[messages lastObject]];
            
            NSRange r;
            r.location = 0;
            r.length   = [messages count] - 1;
            for(NSString *messageString in [messages subarrayWithRange:r]) {
                if ([messageString hasPrefix: @"GPSD,"]) {
                    for(NSString *message in [[messageString substringFromIndex: 5] componentsSeparatedByString:@","]) {
                        [self parseMessage:message];
                    }
                }
                else if ([messageString hasPrefix: @"{"]) {
                    // New style message
                    [self parseJSONMessage:messageString];
                }
                else {
                    NSLog(@"GPSdConnection: Invalid message");
                }
            }
        }
    }
}
#endif

-(void) parseJSONMessage: (NSString *)message {
    NSError *err = nil;
    SBJSON *parser = [[SBJSON alloc] init];
    id obj = [parser objectWithString:message error:&err];
    //NSLog(@"JSON: %@", message);
    //NSLog(@"JSON: err: %@", [err localizedDescription]);
    //NSLog(@"JSON: class: %@", [obj objectForKey:@"class"]);
    
    NSString *messageType = [obj objectForKey:@"class"];
    
    if ([messageType isEqualToString:@"VERSION"]) {
        conType = JSON_Connection_Proto;
        NSData *data = [@"?WATCH={\"enable\":true,\"json\":true};" dataUsingEncoding:NSASCIIStringEncoding];
        
        CFSocketError err = CFSocketSendData(sock, NULL, (CFDataRef)data, 0);
        if (kCFSocketSuccess != err) {
            NSLog(@"SocketCallback: Error sending data");
        }
    }
    else if ([messageType isEqualToString:@"TPV"]) {
        [self->pendingFix release];
        self->pendingFix = [[NSMutableDictionary alloc] initWithCapacity:14];
        
        NSString *value = nil;
        
        NSString *device = [obj objectForKey:@"device"];
        if ((device != nil)  && !([device isEqualToString:GPSName])) {
            [self setGPSName:device];
        }
        
        NSDictionary * fixMap = [NSDictionary dictionaryWithObjectsAndKeys:
                                 @"Latitude", @"lat",
                                 @"Longitude", @"lon",
                                 @"Altitude", @"alt",
                                 @"Timestamp",@"time",
                                 @"Heading",@"track",
                                 @"Speed",@"speed",
                                 @"Climb",@"climb",
                                 @"TimeError",@"ept",
                                 @"HorizontalError",@"epx", //FIXME: x and y how have different errors
                                 @"VerticalError",@"epv",
                                 @"HeadingError",@"epd",
                                 @"SpeedError",@"eps",
                                 @"ClimbError",@"epc",
                                 nil];
        
        for(NSString *key in fixMap) {
            NSString *value = [obj objectForKey:key];
            if (nil != value) {
                [pendingFix setObject:[NSNumber numberWithDouble:[value doubleValue]] forKey:[fixMap objectForKey:key]];
            }
        }
        
        value = [obj objectForKey:@"tag"];
        if (nil != value) {
            [pendingFix setObject:value forKey:@"Tag"];
        }
        
        value = [obj objectForKey:@"mode"];
        if (nil != value) {
            int fixType = [value intValue];
            switch (fixType) {
                case 3:
                    [pendingFix setObject:[NSNumber numberWithInt:GPSFixType_3D] forKey:@"FixType"];
                    break;
                case 2:
                    [pendingFix setObject:[NSNumber numberWithInt:GPSFixType_2D] forKey:@"FixType"];
                    break;
                case 1:
                case 0:
                default:
                    [pendingFix setObject:[NSNumber numberWithInt:GPSFixType_None] forKey:@"FixType"];
                    break;
            }
        }
        
        NSArray *cachedKeys = [NSArray arrayWithObjects: @"HDOP", @"PDOP", @"VDOP", @"SatelliteCount", nil];
        for(NSString *key in cachedKeys) {
            NSString *value = [cachedValues objectForKey:key];
            if (nil != value) {
                [pendingFix setObject:value forKey:key];
            }
        }
        
        
        
        
        [self setFix:pendingFix];
    }
    else if ([messageType isEqualToString:@"SKY"]) {
        [self->cachedValues release];
        self->cachedValues = [[NSMutableDictionary alloc] initWithCapacity:4];
        
        NSArray *satList = [obj objectForKey:@"satellites"];
        
        NSMutableArray *satArray = [NSMutableArray arrayWithCapacity:[satList count]];
        
        int satCount = 0;
        
        for(NSDictionary *sat in satList) {
            if ([[sat objectForKey:@"used"] boolValue])
                satCount++;
            
            NSDictionary *satDict = [NSDictionary dictionaryWithObjectsAndKeys:
                                     [sat objectForKey:@"PRN"],@"PRN",
                                     [sat objectForKey:@"el"],@"Elevation",
                                     [sat objectForKey:@"az"],@"Azimuth",
                                     [sat objectForKey:@"ss"],@"Signal",
                                     [sat objectForKey:@"used"],@"Used",
                                     nil];
            [satArray addObject:satDict];
        }
        
        [self setSatellites:satArray];
        
        [cachedValues setObject:[NSNumber numberWithInt:satCount] forKey:@"SatelliteCount"];
        
        NSDictionary *skyMap = [NSDictionary dictionaryWithObjectsAndKeys:
                                @"HDOP", @"hdop",
                                @"VDOP", @"vdop",
                                @"PDOP", @"pdop",
                                nil];
        
        for(NSString *key in skyMap) {
            NSString *value = [obj objectForKey:key];
            if (nil != value) {
                [cachedValues setObject:[NSNumber numberWithDouble:[value doubleValue]] forKey:[skyMap objectForKey:key]];
            }
        }
    }
    else if ([messageType isEqualToString:@"DEVICES"]) {
    }
    else if ([messageType isEqualToString:@"WATCH"]) {
    }
    else if ([messageType isEqualToString:@"DEVICE"]) {
    }
    else if ([messageType isEqualToString:@"ERROR"]) {
    }
    else {
        NSLog(@"Unknown message class: '%@'", messageType);
    }

}

-(void) parseMessage: (NSString *)message {
    char messageType = [message characterAtIndex:0];
    char firstChar   = [message characterAtIndex:2];
    
    if ('?' == firstChar) {
        // No data for the message
        switch (messageType) {
            case 'X':
            case 'I':
                [self setFix:[NSDictionary dictionaryWithObject:[NSNumber numberWithInt:GPSFixType_None] forKey:@"FixType"]];
                [self setGPSName:nil];
            default:
                break;
        }
        return;
    }
    
    // Handle the message if there's data
    
    if ('X' == messageType) {
        /*
        double time;
        time = ScanGPSDouble(scanner);
        
        if ((0 == time) || (NAN == time)) {
            [self updateGPSName: @"No GPS connected"];
        }
         */
    }
    else if ('I' == messageType) {
        [self setGPSName: [message substringFromIndex:2]];
    }
    else if ('O' == messageType) {
        NSArray *messageArray = [message componentsSeparatedByString:@" "];
        
        if ([messageArray count] < 15) {
            NSLog(@"O message too short: %d parts", [messageArray count]);
        }
        
        [self->pendingFix release];
        self->pendingFix = [[NSMutableDictionary alloc] initWithCapacity:14];
        
        [pendingFix setObject:[[[messageArray objectAtIndex:0] componentsSeparatedByString:@"="] objectAtIndex:1] forKey:@"Tag"];
        if (![@"?" isEqual:[messageArray objectAtIndex:1]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:1] doubleValue]] forKey:@"Timestamp"];
        if (![@"?" isEqual:[messageArray objectAtIndex:2]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:2] doubleValue]] forKey:@"TimeError"];
        if (![@"?" isEqual:[messageArray objectAtIndex:3]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:3] doubleValue]] forKey:@"Latitude"];
        if (![@"?" isEqual:[messageArray objectAtIndex:4]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:4] doubleValue]] forKey:@"Longitude"];
        if (![@"?" isEqual:[messageArray objectAtIndex:5]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:5] doubleValue]] forKey:@"Altitude"];
        if (![@"?" isEqual:[messageArray objectAtIndex:6]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:6] doubleValue]] forKey:@"HorizontalError"];
        if (![@"?" isEqual:[messageArray objectAtIndex:7]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:7] doubleValue]] forKey:@"VerticalError"];
        
        if (![@"?" isEqual:[messageArray objectAtIndex:8]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:8] doubleValue]] forKey:@"Heading"];
        if (![@"?" isEqual:[messageArray objectAtIndex:9]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:9] doubleValue]] forKey:@"Speed"];
        if (![@"?" isEqual:[messageArray objectAtIndex:10]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:10] doubleValue]] forKey:@"Climb"];
        
        if (![@"?" isEqual:[messageArray objectAtIndex:11]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:11] doubleValue]] forKey:@"HeadingError"];
        if (![@"?" isEqual:[messageArray objectAtIndex:12]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:12] doubleValue]] forKey:@"SpeedError"];
        if (![@"?" isEqual:[messageArray objectAtIndex:13]])
            [pendingFix setObject:[NSNumber numberWithDouble:[[messageArray objectAtIndex:13] doubleValue]] forKey:@"ClimbError"];
        
        char fixType = [[messageArray objectAtIndex:14] characterAtIndex:0];
        
        switch (fixType) {
            case '3':
                [pendingFix setObject:[NSNumber numberWithInt:GPSFixType_3D] forKey:@"FixType"];
                break;
            case '2':
                [pendingFix setObject:[NSNumber numberWithInt:GPSFixType_2D] forKey:@"FixType"];
                break;
            case '1':
            case '?':
            default:
                [pendingFix setObject:[NSNumber numberWithInt:GPSFixType_None] forKey:@"FixType"];
                break;
        }
        
        NSData *outData = [@"qs\n" dataUsingEncoding:NSASCIIStringEncoding];
        
        CFSocketError err = CFSocketSendData(sock, NULL, (CFDataRef)outData, 0);
        if (kCFSocketSuccess != err) {
            NSLog(@"SocketCallback: Error sending data");
        }        
        
        //[oStream write:(const uint8_t *)"qs\n" maxLength:2];
        
        //[self->pendingCommands addObject:@"q"];
    }
    else if ('Q' == messageType) {
        NSArray *messageArray = [message componentsSeparatedByString:@" "];
        NSString *strValue = nil;
        
        strValue = [[[messageArray objectAtIndex:0] componentsSeparatedByString:@"="] objectAtIndex:1];
        if (![strValue isEqual:@"?"]) {
            int value = [strValue intValue];
            if (value != 0.0) {
                [pendingFix setObject:[NSNumber numberWithInt:value] forKey:@"SatelliteCount"];
            }
        }        
        
        strValue = [messageArray objectAtIndex:1];
        if (![strValue isEqual:@"?"]) {
            double value = [strValue doubleValue];
            if (value != 0.0) {
                [pendingFix setObject:[NSNumber numberWithDouble:value] forKey:@"DOP"];
            }
        }
        
        strValue = [messageArray objectAtIndex:2];
        if (![strValue isEqual:@"?"]) {
            double value = [strValue doubleValue];
            if (value != 0.0) {
                [pendingFix setObject:[NSNumber numberWithDouble:value] forKey:@"HDOP"];
            }
        }
        
        strValue = [messageArray objectAtIndex:3];
        if (![strValue isEqual:@"?"]) {
            double value = [strValue doubleValue];
            if (value != 0.0) {
                [pendingFix setObject:[NSNumber numberWithDouble:value] forKey:@"VDOP"];
            }
        }
    }
    else if ('S' == messageType) {
        if (2 == [[message substringFromIndex:2] intValue]) {
            [pendingFix setObject:[NSNumber numberWithInt:1] forKey:@"DGPS"];
        }
        else {
            [pendingFix setObject:[NSNumber numberWithInt:0] forKey:@"DGPS"];
        }

        
        [self setFix:pendingFix];
    }
    else if ('Y' == messageType) {
        /* Satellites message */
        NSArray *messageArray = [message componentsSeparatedByString:@":"];
        // We just ignore the header, we'll get the number of satellites based on the split
        if ([messageArray count] > 2) {
            NSMutableArray *satArray = [NSMutableArray arrayWithCapacity:[messageArray count] - 2];
            NSArray *keys = [NSArray arrayWithObjects:@"PRN", @"Elevation", @"Azimuth", @"Signal", @"Used", nil];
            
            for(int i = 1; i < [messageArray count] - 1; ++i) {
                NSArray *sat = [[messageArray objectAtIndex:i] componentsSeparatedByString:@" "];
                NSMutableDictionary *satDict = [NSMutableDictionary dictionary];
                
                for(int j = 0; j < [keys count]; ++j) {
                    [satDict setObject:[NSNumber numberWithInt:[[sat objectAtIndex:j] integerValue]] forKey:[keys objectAtIndex:j]];
                }
                [satArray addObject:satDict];
            }
            [self setSatellites:satArray];
        }
        else {
            [self setSatellites:[NSArray array]];
        }

                                        
    }
    else if ('W' == messageType) {
        /* Response to our W request */
    }
    else {
        NSLog(@"Unknown message type %c", messageType);
    }
}
                                      
-(void) idleTimerEvent: (NSTimer*)theTimer {
    // Check if we've gotten data, otherwise try to restart the connection
    
    if ([lastUpdate timeIntervalSinceNow] < -5.0) {
        if (JSON_Connection_Proto == conType) {
            //NSLog(@"idleTimerEvent: Timeout on GPSd, pinging...");
            NSData *data = [@"?WATCH={\"enable\":true,\"json\":true};\r\n" dataUsingEncoding:NSASCIIStringEncoding];
            
            CFSocketError err = CFSocketSendData(sock, NULL, (CFDataRef)data, 0);
            if (kCFSocketSuccess != err) {
                //NSLog(@"idleTimerEvent: No connection");
            }
        }
        else {
            //NSLog(@"idleTimerEvent: Timeout on GPSd (oldstyle), pinging...");
            NSData *data = [@"w+\r\n" dataUsingEncoding:NSASCIIStringEncoding];
            
            CFSocketError err = CFSocketSendData(sock, NULL, (CFDataRef)data, 0);
            if (kCFSocketSuccess != err) {
                //NSLog(@"idleTimerEvent: No connection");
            }
        }

    }
    
    if (Unknown_Connection_Proto == conType) {
        NSData *data = [@"w+\r\n" dataUsingEncoding:NSASCIIStringEncoding];
        
        CFSocketError err = CFSocketSendData(sock, NULL, (CFDataRef)data, 0);
        if (kCFSocketSuccess != err) {
            //NSLog(@"idleTimerEvent: Error sending data");
        }
        
        conType = Old_Connection_Proto;
    }
}

@end
