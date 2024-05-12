import threading
import time
import logging

from collections.abc import Callable

class HeartbeatChecker(object):
    MIN_DELAY = 10 #in ms

    def __init__(
        self, 
        intervalInMS: int,
        callbackOnSuccess: Callable[[],[]],
        callbackOnFailure: Callable[[],[]]
    ):
        if intervalInMS<HeartbeatChecker.MIN_DELAY:
           logging.critical(f"heartbeat interval too low ({intervalInMS}<{HeartbeatChecker.MIN_DELAY})")
           sys.exit(1)
           
        self.intervalInMS = intervalInMS
        self.callbackOnFailure = callbackOnFailure
        
        self._heartbeatTimestamp = 0
        self._heartbeatTimestampLock = threading.Lock()
        self.resetHeartbeatTimestamp()
        
        self.heartbeatThread = threading.Thread(target=self._heartbeatLoop, daemon=True)
        self.heartbeatThread.start()
        
    def currentTimestamp():
        return time.time_ns() // 1000000
        
    def resetHeartbeatTimestamp(self):
        with self._heartbeatTimestampLock:
            self._heartbeatTimestamp = HeartbeatGenerator.currentTimestamp()
            
    def emitHeartbeat(self):
        self.callbackFunction()
        self.resetHeartbeatTimestamp()
        
    def _heartbeatLoop(self):
        while True:
            #since read-only no lock needed here
            elapsedTime = HeartbeatGenerator.currentTimestamp() - self._heartbeatTimestamp
            timeLeft = self.intervalInMS - elapsedTime
            if (timeLeft<=0):
                self.emitHeartbeat()
            else:
                time.sleep(0.001*(timeLeft*0.33 + HeartbeatGenerator.MIN_DELAY))
    
