from .execution_statuses import ScriptRunStatusesEnum, SnmpCommandCode

class NodeConnectError(TimeoutError):
    def __init__(self, cmd: SnmpCommandCode, err_code: ScriptRunStatusesEnum, *args):
        super().__init__(*args)
        self.cmd= cmd
        self.err_code = err_code

class NodeValueError(ValueError):
    def __init__(self, cmd: SnmpCommandCode, err_code: ScriptRunStatusesEnum, obj: str, *args):
        super().__init__(*args)
        self.cmd = cmd
        self.obj = obj
        self.err_code = err_code

class NodeSyncTimeoutError(TimeoutError):
    def __init__(self, *args):
        super().__init__(*args)