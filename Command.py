import subprocess
import time

class Spawn(object):
    #todo: always fork; run /usr/bin/time -vv to montor performance; can attach stuff to python procs for monitoring the status
    def __init__(self):
        pass
        
    def start(self):
        self.startTime = time.time_ns()/1e6
        
    #in ms
    def uptime(self):
        if self.status()=='running':
            return (time.time_ns()/1e6 - self.startTime) 
        else:
            return (self.stopTime-self.startTime)

    def terminate(self):
        pass
        
    def kill(self):
        pass
        
    def status(self):
        pass

class Command(object):
    def __init__(self, name, description, env=None, cwd=None):
        self.interactions = []
        
    def spawn(self, inStream, outStream, argumentList=[]):
        return Spawn()
