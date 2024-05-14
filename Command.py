import subprocess
import time

from collections.abc import Callable


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

    

class SpawnCommand(object):
    def __init__(
        self, 
        name: str, 
        description: str
    ):
        self.name = name
        self.description = description
        
    def spawn(self, cfg: 'dict[str, str]' = {}, argumentList: 'list[str]' =[]) -> Spawn:
        raise NotImplementedError()

class CallCommand(object):
    def __init__(
        self, 
        name: str, 
        description: str,
        function: 'Callable[...,dict[str, Any]]'
    ):
        self.name = name
        self.description = description
        self.function = function
        
    def __call__(self, cfg: 'dict[str, str]' = {}, argumentList: 'list[str]' =[]) -> 'dict[str, Any]':
        return self.function(cfg,argumentList)