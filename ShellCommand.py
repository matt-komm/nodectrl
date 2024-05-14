import subprocess

from typing import Optional

from Command import *

class ShellCommandSpawn(Spawn):
    def __init__(
        self
    ):
        pass

    def start(self):
        pass


class ShellCommand(SpawnCommand):
    def __init__(
            self, 
            name: str,
            description: str,
            command: 'list[str]',
            **kwargs
        ):
        super().__init__(self,name,description)


    def spawn(self, inStream, outStream, **kwargs) -> ShellCommandSpawn:
        return ShellCommandSpawn()