import subprocess
import os
import logging
import shutil
import threading

import zmq

from typing import Optional

from Command import *
from DataMessage import *

class ShellSpawn(Spawn):
    TIMEOUT = 1000

    def __init__(
        self,
        inputAddress: str,
        outputAddress: str,
        channel: str,
        command: str,
        shell: bool = False,
        cwd: Optional[str] = None,
        env: Optional[str] = None,
        config: 'dict[str, Any]' = {},
        argumentList: 'list[str]' =[],
    ):


        self._inputAddress = inputAddress
        self._outputAddress = outputAddress
        self._channel = channel
        self._command = command
        self._shell = shell
        self._cwd = cwd
        self._env = env
        self._config = config
        self._argumentList = argumentList

        self._commandThread = threading.Thread(
            target=ShellSpawn._start,
            args=(
                self._inputAddress,
                self._outputAddress,
                self._channel,
                self._command,
                self._shell,
                self._cwd,
                self._env,
                self._config,
                self._argumentList
            ),
            daemon=True
        )
        self._commandThread.start()

    def _start(
        inputAddress, 
        outputAddress,
        channel,
        command,
        shell,
        cwd,
        env,
        config,
        argumentList
    ):
        context = zmq.Context()
        dataSocket = context.socket(zmq.PUB)
        dataSocket.connect(outputAddress)

        heartbeatSocket = context.socket(zmq.SUB)
        heartbeatSocket.connect(outputAddress)
        heartbeatSocket.setsockopt(zmq.SUBSCRIBE,DataMessage.encodedChannel('heartbeat'))
        if heartbeatSocket.poll(ShellSpawn.TIMEOUT, zmq.POLLIN):
            heartbeatSocket.recv()
        #can just send output regardless of heartbeat will only loose messages to client but not kill process

        proc = subprocess.Popen(
            command+argumentList,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
            cwd=cwd,
            env=env,
            universal_newlines=True
        )
        os.set_blocking(proc.stdout.fileno(), False)
        os.set_blocking(proc.stderr.fileno(), False)
        
        while proc.poll() is None:
            line = proc.stdout.readline().strip()
            while len(line)>0:
                logging.debug(f"'{channel}' stdout >>> {line}")
                dataSocket.send(DataMessage(channel,{'stdout':line}).encode())
                line = proc.stdout.readline().strip()
                
            line = proc.stderr.readline().strip()
            while len(line)>0:
                logging.debug(f"'{channel}' stderr >>> {line}")
                dataSocket.send(DataMessage(channel,{'stderr':line}).encode())
                line = proc.stderr.readline().strip()
        
        logging.debug(f"{channel} command terminated with '{proc.returncode}'")
        
        line = proc.stdout.readline().strip()
        while len(line)>0:
            logging.debug(f"'{channel}' stdout >>> {line}")
            dataSocket.send(DataMessage(channel,{'stdout':line}).encode())
            line = proc.stdout.readline().strip()
            
        line = proc.stderr.readline().strip()
        while len(line)>0:
            logging.debug(f"'{channel}' stderr >>> {line}")
            dataSocket.send(DataMessage(channel,{'stderr':line}).encode())
            line = proc.stderr.readline().strip()
        dataSocket.send(DataMessage(channel,{'terminated':proc.returncode}).encode())
        
    def onInputEvent(self, message: DataMessage):
        logging.debug(f"'{message.channel()}' received input: '{message}'")
        return True
    


class ShellCommand(SpawnCommand):
    def __init__(
        self, 
        name: str,
        command: 'list[str]',
        shell: bool = False,
        cwd: Optional[str] = None,
        env: Optional[str] = None
    ):
        super().__init__(name)

        if len(command)==0 or len(command[0])==0:
            raise RuntimeError("Command empty")
        if shutil.which(command[0]) is None:
            raise RuntimeError("Command '{command}' not found")

        self._command = command 
        self._shell = shell
        self._cwd = cwd
        self._env = env

    def __call__(
        self, 
        inputAddress: str, 
        outputAddress: str,
        channel: str, 
        config: 'dict[str, Any]' = {}, 
        argumentList: 'list[str]' =[]
    ) -> 'tuple[ShellSpawn,dict[str,Any]]':
        return ShellSpawn(
            inputAddress, 
            outputAddress, 
            channel,
            self._command,
            self._shell,
            self._cwd,
            self._env,
            config, 
            argumentList,
        ),{}