import subprocess
import time

from collections.abc import Callable
from typing import Any

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
    def __init__(self, name: str):
        self._name = name

    def name(self) -> str:
        return self._name
    

class SpawnCommand(Command):
    def __init__(
        self, 
        name: str
    ):
        super().__init__(name)
        
    def __call__(self, cfg: 'dict[str, str]' = {}, argumentList: 'list[str]' =[]) -> 'tuple[Spawn, dict[str, Any]]':
        raise NotImplementedError()

class CallCommand(Command):
    def __init__(
        self, 
        name,
        function: 'Callable[...,dict[str, Any]]'
    ):
        super().__init__(name)
        self.function = function
        
    def __call__(self, cfg: 'dict[str, str]' = {}, argumentList: 'list[str]' =[]) -> 'dict[str, Any]':
        return self.function(cfg,argumentList)