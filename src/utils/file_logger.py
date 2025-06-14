from ..connection.exceptions.execution_statuses import ScriptRunStatusesEnum
from . import print as print_utils

class FileLogger():
    def __init__(self):
        self.__is_logging_on__ = False
        self.__log_file__ = None
        self.__log_file_path__ = "run.log"
        self.__log_file_mode__ = "w"
    
    def is_logging_on(self):
        return self.__is_logging_on__

    def open(self, path: str = None, mode: str = None):
        if path is not None:
            self.__log_file_path__ = path
        if mode is not None:
            self.__log_file_mode__ = mode
        self.__log_file__ = open(self.__log_file_path__, self.__log_file_mode__)
        self.__is_logging_on__ = True
        return

    def log(self, ip: str, status: ScriptRunStatusesEnum):
        if self.__log_file__ is None or self.__log_file__.closed:
            self.__log_file__ = open(self.__log_file_path__, self.__log_file_mode__)
        
        msg = f"{ip}:\t {ScriptRunStatusesEnum(status).name}(0x{status:X})\n"
        self.__log_file__.write(msg)
        return

    def  close_log(self):
        if self.__log_file__ is None:
            print_utils.print_info("Trying to close log file, while none was used", 2)
        elif not self.__log_file__.closed:
            self.__log_file__.close()
            self.__log_file__ = None
        self.__is_logging_on__ = False
        return