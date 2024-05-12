import daqnodectrl as dctrl

def loadFirmware(self,status,*args,**kwargs):
    status.update("Begin")
    status.update("done")
    
    #note starting DAQServer wont quit here; how to indicate success cmd exec?
    return status.ok() # status.error() #status.retry()
    

class TesterCtrl(object):
    def __init__(self):
        self.commandExecutor = dctrl.CommandExecutor()
        self.commandExecutor.registerCommand("load_fw",loadFirmware)
        
        
