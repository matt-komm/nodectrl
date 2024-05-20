import subprocess
import time

from DataMessage import *

from collections.abc import Callable
from typing import Any

class Spawn(object):
    #todo: always fork; run /usr/bin/time -vv to montor performance; can attach stuff to python procs for monitoring the status
    def __init__(self):
        pass
        
    def start(self):
        raise NotImplementedError()
        
    #in ms
    def uptime(self):
        raise NotImplementedError()

    def terminate(self):
        raise NotImplementedError()
        
    def kill(self):
        raise NotImplementedError()
        
    def status(self):
        raise NotImplementedError()

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
        
    def __call__(
            self, 
            inputAddress: str, 
            outputAddress: str,
            channel: str, 
            config: 'dict[str, str]' = {}, 
            argumentList: 'list[str]' =[]
        ) -> 'tuple[Spawn, dict[str, Any]]':
        raise NotImplementedError()

class CallCommand(Command):
    def __init__(
        self, 
        name,
        function: 'Callable[[str,str,str,dict[str, Any],list[str]],dict[str, Any]]'
    ):
        super().__init__(name)
        self.function = function
        
    def __call__(
            self, 
            inputAddress: str, 
            outputAddress: str,
            channel: str, 
            config: 'dict[str, str]' = {}, 
            argumentList: 'list[str]' =[]
        ) -> 'tuple[Spawn, dict[str, Any]]':
        return self.function(inputAddress,outputAddress,channel,config,argumentList)