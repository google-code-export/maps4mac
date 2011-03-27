#
#  DownloadWindowDelegate.py
#  Maps4Mac
#
#  Created by Daniel Sabo on 11/26/10.
#  Copyright (c) 2010 Daniel Sabo. All rights reserved.
#

from Foundation import *
import os.path

class DownloadWindowDelegate(NSObject):
    pendingURLs = objc.ivar()
    download = objc.ivar()
    targetPath = objc.ivar()
    statusStr = objc.ivar()
    window = objc.IBOutlet()
    progress = objc.ivar()
    bytesDownloaded = objc.ivar()
    contentLenghtOfdownload = objc.ivar()
    cancelButtonString = objc.ivar()

    def init(self):
        self = super(self.__class__, self).init()
        if self is None:
            return None
        
        self.pendingURLs = []
        self.download = None
        self.statusStr = ""
        self.cancelButtonString = "Close"
        
        self.bytesDownloaded = 0
        self.contentLenghtOfdownload = 1
                
        return self
    
    def queueURL_toPath_(self, url, path):
        self.pendingURLs.append((url, path))
        self.doDownload()
    
    def doDownload(self):
        if self.pendingURLs:
            url,self.targetPath = self.pendingURLs.pop()
            request = NSURLRequest.requestWithURL_(NSURL.URLWithString_(url))
            self.download = NSURLDownload.alloc().initWithRequest_delegate_(request, self)
            self.download.setDestination_allowOverwrite_(self.targetPath, False)
            self.statusStr = "(1 of %d) Starting: %s" % (len(self.pendingURLs) + 1, os.path.basename(self.targetPath))
            if not self.window.isVisible():
                self.window.makeKeyAndOrderFront_(self)
            self.cancelButtonString = "Cancel"
        else:
            self.cancelButtonString = "Close"
    
    # Download delegate methods
    def download_didReceiveDataOfLength_(self, download, length):
        self.bytesDownloaded += length
        self.statusStr = "(1 of %d) %s" % (len(self.pendingURLs) + 1, os.path.basename(self.targetPath))
        self.progress = (float(self.bytesDownloaded) / float(self.contentLenghtOfdownload)) * 100.0
    
    def download_didReceiveResponse_(self, download, response):
        self.contentLenghtOfdownload = response.expectedContentLength()
    
    def download_didFailWithError_(self, download, error):
        print error
        self.statusStr = ""
    
    def downloadDidBegin_(self, download):
        self.statusStr = download.request().URL()
    
    def downloadDidFinish_(self, download):
        self.statusStr = "Finished: %s" % (len(self.pendingURLs) + 1, os.path.basename(self.targetPath))
        self.contentLenghtOfdownload = 1
        self.progress = 0.0
        
        self.doDownload()
    
    def download_willSendRequest_redirectResponse_(self, download, request, redirectResponse):
        return request
    
    def download_shouldDecodeSourceDataOfMIMEType_(self, download, encodingType):
        return False
    
    @objc.IBAction
    def doCancel_(self,sender):
        self.download.cancel()
        self.pendingURLs = []
        self.window.orderOut_(self)
        self.cancelButtonString = "Close"
