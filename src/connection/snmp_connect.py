from ..utils import print as print_utils
from .exceptions.node_errors import *

# import os
import subprocess
import time as timer
from typing import List, Any


class SNMP_Connect:
    def __init__(self, mibs: str, libs: List[str], ip: str, root_script: str, stop_event = None):
        self.__mibs = mibs
        self.__libs = ":".join(libs)
        self.__ip = ip
        self.__retries = 1
        self.__timeout = 1
        self.__was_connected = False
        self.root_script = root_script
        self.stop_event = stop_event

    def set_retries(self, count: int):
        self.__retries = count

    def set_timeout(self, timeout: int):
        self.__timeout = timeout

    def snmpget(self, obj: str, hide: bool = False) -> str:
        cmd = [
            "snmpget",
            "-c", "public",
            "-v2c",
            "-m", self.__mibs,
            "-M", f"+/var/lib/mibs/ietf:{self.__libs}",
            "-r", f"{self.__retries}",
            "-t", f"{self.__timeout}",
            "-O", "vq",
            self.__ip,
            f"{obj}"
        ]
        print_utils.print_executable(" ".join(cmd), 2)
        buf = SNMP_Connect.__run_cmd(cmd).strip("\n ")
        
        self.__check_for_error(SnmpCommandCode.GET, obj, buf)
        self.__was_connected = True
        if(not hide):
            print_utils.print_info(f"{obj} = {buf}", 2)
        return buf
    
    def snmpwalk(self, obj: str, val_only: bool = False, hide: bool = False) -> str:
        if self.check_stop_event("snmpwalk"):
            return
        cmd = [
            "snmpwalk",
            "-c", "public",
            "-v2c",
            "-m", self.__mibs,
            "-M", f"+/var/lib/mibs/ietf:{self.__libs}",
            "-r", f"{self.__retries}",
            "-t", f"{self.__timeout}"
        ]
        if (val_only):
            cmd.extend(["-O", "vq"])
        cmd.extend([self.__ip, f"{obj}"])

        print_utils.print_executable(" ".join(cmd), 2)
        buf = SNMP_Connect.__run_cmd(cmd).strip("\n ")
        
        self.__check_for_error(SnmpCommandCode.WALK, obj, buf)
        self.__was_connected = True
        if(not hide):
            print_utils.print_info(buf, 2)
        return buf
    
    def snmpset(self, obj: str, value: Any, val_only: bool = False, hide: bool = False) -> str:
        cmd = [
            "snmpset",
            "-c", "public",
            "-v2c",
            "-m", self.__mibs,
            "-M", f"+/var/lib/mibs/ietf:{self.__libs}",
            "-r", f"{self.__retries}",
            "-t", f"{self.__timeout}",
        ]
        if (val_only):
            cmd.extend(["-O", "vq"])
        cmd.extend([self.__ip, f"{obj}", "i", f"{value}"])
        
        print_utils.print_executable(" ".join(cmd), 2)
        buf = SNMP_Connect.__run_cmd(cmd).strip("\n ")
        
        self.__check_for_error(SnmpCommandCode.SET, obj, buf)
        self.__was_connected = True
        if(not hide):
            print_utils.print_info(buf, 2)
        return buf

    def ptp_resync(self, timeout: int = 60) -> bool:
        if self.check_stop_event("ptp_resync"):
            return
        self.snmpset("wrpcPtpConfigRestart.0", "restartPtp")
        if timeout == 0:
            return True
        res = []
        timer_secs = range(timeout-1, -1, -1)
        for sec in print_utils.timer_bar(
                timer_secs,
                prefix="Timeout:",
                suffix="left",
                length=100):
            if self.check_stop_event("ptp_resync"):
                return False
            res.append(self.snmpget("wrpcPtpServoStateN.0", hide=True))
            if sec % 4 == 0:
                print_utils.print_info(res, 2)
                if (len(list(filter(lambda x: ("trackPhase" in x), res))) >= 3):
                    return True
                res = []
            timer.sleep(1)

        raise NodeSyncTimeoutError(f"Synchronisation timeout ({timeout} sec) reached. Script discontinued")

    def __check_for_error(self, stage: SnmpCommandCode, obj: str, *buf: str):
        # print_utils.print_info(obj, 1)
        # print_utils.print_info(buf, 1)
        if ("Timeout" in "".join(buf)): # Could not connect
            if self.__was_connected:
                raise NodeConnectError(stage, ScriptRunStatusesEnum.CONNECTION_LOSS, buf)
            else:
                raise NodeConnectError(stage, ScriptRunStatusesEnum.DESTINATION_UNREACHABLE, buf)
        if ("Unknown Object Identifier" in "".join(buf)): #  Unknown Object Identifier (Sub-id not found: (top) -> wrpcSfpTy)
            raise NodeValueError(stage, ScriptRunStatusesEnum.UNKNOWN_MIB_OBJECT, obj, buf)
        if ("Error" in "".join(buf)): # I don't remember :(
            raise NodeValueError(stage, ScriptRunStatusesEnum.UNKNOWN_ERROR, obj, buf)
        return False

    def __run_cmd(cmd: List[str]) -> str:
        p = subprocess.Popen(cmd, text = True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        return p.communicate()[0]
    
    def close(self):
        pass

    def check_stop_event(self, func):
        if self.stop_event.is_set():
            print_utils.print_thread_terminated(self.script, func)
            self.close()
            return True
        return False