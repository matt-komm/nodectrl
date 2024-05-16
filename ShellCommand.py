import subprocess

from typing import Optional

from Command import *

class ShellSpawn(Spawn):
    def __init__(
        self,
        command: 'list[str]',
        config: 'dict[str, Any]' = {},
        argumentList: 'list[str]' =[]
    ):
        self._command = command
        self._config = config
        self._argumentList = argumentList

    def start(self):
        proc = subprocess.Popen(self._command)


class ShellCommand(SpawnCommand):
    def __init__(
            self, 
            name: str,
            command: 'list[str]',
            **kwargs
        ):
        super().__init__(name)
        self._command = command 

    def __call__(self, config: 'dict[str, Any]' = {}, argumentList: 'list[str]' =[]) -> 'tuple[ShellSpawn,dict[str,Any]]':
        return ShellSpawn(self._command, config, argumentList),{}