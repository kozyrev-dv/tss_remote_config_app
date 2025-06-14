from .connection import Connection
from ..utils import print as print_utils

from typing import Any, Tuple, List
import time as timer
import serial
import io
import os

class Direct_Connect(Connection):
    def __init__(self, root: str, stop_event = None, tty_usb_port: int = 0):
        super().__init__(root, stop_event)
        self.__c = serial.Serial()
        self.__c.port = f"/dev/ttyUSB{tty_usb_port}"
        self.__c.baudrate = 115200
        self.__c.timeout = 0.4
        self.__try_open_serial()

    def setup_connection(self) -> None:
        pass
        # raise NotImplementedError()
    
    def setup_node(self) -> None:
        self.__try_open_serial()
        self.run_node("auxmux 0 0")
        return
    
    def resync_ptp_node(self) -> None:
        if self.check_stop_event("resync_ptp_node"):
            return
        print_utils.print_info("---------- RESTART PTP ----------", 1)
        self.__try_open_serial()
        result = self.run_node("ptp stop 0")
        result = self.run_node("sfp match")
        result = self.run_node("ptp start 0")
        
        self.toggle_stat_on_node()

        timer.sleep(2) # wait for commands to proceed 

        # Cycle file until resynchronized
        print_utils.print_info("---------- START RESYNCHRONOZATION ----------", 1)
        isSync = False
        while(not isSync):
            if self.check_stop_event("resync_ptp_event"):
                self.toggle_stat_off_node()
                return
            timer.sleep(4)
            # check for "TRACK_PHASE" stability
            sync_count = self.__read_node_output().count("TRACK_PHASE")
            print_utils.print_info(f"Sync count (TRACK_PHASE): {sync_count}", 2)
            isSync = (sync_count >= 3)

        self.toggle_stat_off_node()
        print_utils.print_info("---------- END RESYNCHRONOZATION ----------", 1)
        return
    
    def toggle_stat_on_node(self) -> None:
        self.__try_open_serial()
        self.run_node("stat on")
        return
    
    def toggle_stat_off_node(self) -> None:
        self.__try_open_serial()
        self.run_node("stat off")
        return
    
    def run_host(self, op: str, hide: bool = False) -> Any:
        buf = os.popen(op).read()
        if (not hide):
            print_utils.print_untagged(buf, 1)
        return buf
    
    def run_node(self, op: str, hide: bool = False) -> Any:
        self.__c.write(bytes(f"{op} \r", "utf-8"))
        return self.__read_node_output(hide)

    def read_node_log(self, time: int = 60, hide = False) -> List[str]:
        res = []
        self.toggle_stat_on_node()

        if (time > 5):
            for t in print_utils.timer_bar(
                range(time, -1, -1),
                prefix="Logging time:",
                suffix="left",
                length=100):
                if self.check_stop_event("read_node_log"):
                    return []
                timer.sleep(1)
                res.append(self.__read_node_output(hide=hide))
        else:
            for t in range(0, time):
                timer.sleep(1)
                res.append(self.__read_node_output(hide=hide))
        self.toggle_stat_off_node()
        return res

    def __read_node_output(self, hide: bool = False, buf_len: int = 2048) -> str:
        res = []
        buf = str(self.__c.read(buf_len), "utf-8")
        res = "".join(buf)
        if (not hide):
            print_utils.print_untagged(res, 2)
        return res
    
    def apply_calib_offset_node(self, meanOffset: int, node_port: int) -> Tuple[int, int]:
        if self.check_stop_event("apply_calib_offset_node"):
            return
        self.__try_open_serial()
        
        # sfp match
        # Output:
        # Port 0 No SFP.
        # port 1 SFP not matched!
        # SFP1G-SX-85
        # Port 1 Could not match to DB
                
        self.toggle_stat_off_node() # ensure no statuses printed

        result = self.run_node("sfp match", hide=True).upper().split("\n")
        sfpIds = list(filter(lambda line : ("PORT" not in line), result))
        sfpId = sfpIds[1].split()[0] if len(sfpIds) == 4 else sfpIds[node_port + 1].split()[0]

        # sfp show
        # Output:
        # Port 0, SFP 2: PN:SFP1G-SX-85      dTx:   -38753 dRx:    38801 alpha:        0
        # Port 1, SFP 1: PN:SFP1G-LX-31      dTx:        0 dRx:        0 alpha:        0
        result = self.run_node("sfp show", hide=True).split("\n")
        result = [x.upper() for x in list(filter(lambda line : (f"{sfpId}" in line), result))]
        sfpOffsets = list(filter(lambda line : (f"PORT {node_port}" in line), result))
        txOffset, rxOffset = (0, 0)
        if len(sfpOffsets) == 1:
            sfpOffsets = sfpOffsets[0].split(":")
            txOffset = int(''.join(filter(lambda x: (str.isdigit(x) or x=="-"), sfpOffsets[3])))
            rxOffset = int(''.join(filter(lambda x: (str.isdigit(x) or x=="-"), sfpOffsets[4])))

        print_utils.print_info(f"Previous offsets are TX: {txOffset}, RX {rxOffset}", 1)
        # calculate new offsets
        # add new offsets
        # sfp add GE-LC-1310 186840 264568 0 0
        txOffset -= round(meanOffset)
        rxOffset += round(meanOffset)

        if self.check_stop_event("apply_calib_offset_node"):
            return
        result = self.run_node(f"sfp add {sfpId} {txOffset} {rxOffset} 0 {node_port}")
        print_utils.print_info(f"New offsets are TX: {txOffset}, RX {rxOffset}", 1)

        return (txOffset, rxOffset)
    
    def apply_calib_node(self, tx: int, rx: int, node_port: int) -> Tuple[int, int]:
        if self.check_stop_event("apply_calib_node"):
            return
        self.__try_open_serial()
        
        # sfp match
        # Output:
        # Port 0 No SFP.
        # port 1 SFP not matched!
        # SFP1G-SX-85
        # Port 1 Could not match to DB
                
        self.toggle_stat_off_node() # ensure no statuses printed
        
        result = self.run_node("sfp match", hide=True).upper().split("\n")
        sfpIds = list(filter(lambda line : ("PORT" not in line), result))
        sfpId = sfpIds[1].split()[0] if len(sfpIds) == 4 else sfpIds[node_port + 1].split()[0]

        if self.check_stop_event("apply_calib_node"):
            return
        result = self.run_node(f"sfp add {sfpId} {tx} {rx} 0 {node_port}")
        print_utils.print_info(f"New offsets are TX: {tx}, RX {rx}", 1)

        return (tx, rx)

    def close(self) -> int:
        return self.__try_close_serial()
    
    def __try_open_serial(self) -> int:
        if not self.__c.is_open:
            self.__c.open()
            return 1
        return 0
    
    def __try_close_serial(self) -> int:
        if self.__c.is_open:
            self.__c.close()
            return 1
        return 0
