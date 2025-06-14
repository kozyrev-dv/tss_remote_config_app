from .connection import Connection as Con
from ..utils import print as print_utils

from typing import Tuple, Any, List
from fabric import Connection, Config
import time as timer

class SSH_Connect(Con):

    def __init__(self, host_name: str, connect_pwd: str, host_root_pwd: str, root: str, stop_event = None, tty_usb_port: int = 0):
        super().__init__(root, stop_event)
        self.__c = None
        self.__HOST_NAME = host_name
        self.__CONNECT_PWD = connect_pwd
        self.__HOST_ROOT_PWD = host_root_pwd
        self.__TTY_USB__ = f"/dev/ttyUSB{tty_usb_port}"
        self.__tryNewSSHConnection()

    def setup_connection(self) -> None:
        if super().check_stop_event("setup_connection"):
            return
        self.__tryNewSSHConnection()

        result = self.run_host(f"stat {self.__TTY_USB__}")
        result = str(result)
        result = result.split("Gid")[1].split("/")[1].split(")")[0]
        result = " ".join(result.split())

        self.__c.sudo(f"usermod -a -G {result} $USER")
        print_utils.print_info(f"---------- ACCESS TO {self.__TTY_USB__} GRANTED ----------", 1)

        return

    def setup_node(self) -> None:
        if self.check_stop_event("setup_node"):
            return
        self.__tryNewSSHConnection()
        self.run_node(f"auxmux 0 0")
        return

    def resync_ptp_node(self) -> None:
        if self.check_stop_event("resync_ptp_node"):
            return
        self.__tryNewSSHConnection()
        result = self.run_host(f"stty -F {self.__TTY_USB__} 115200 raw -echo -echoe -echok -echoctl -echoke", hide=True)

        print_utils.print_info("---------- RESTART PTP ----------", 1)
        result = self.run_node("ptp stop 0")
        result = self.run_node("sfp match")
        result = self.run_node("ptp start 0")
        
        self.toggle_stat_on_node()

        timer.sleep(2) # wait for commands to proceed 

        # Cycle file until resynchronized
        print_utils.print_info("---------- START RESYNCHRONIZATION ----------", 1)
        isSync = False
        while(not isSync):
            if self.check_stop_event("resync_ptp_node"):
                self.toggle_stat_off_node()
                return
            output_file = "output.txt"
            self.__run_node_to_file(None, 4, file=output_file)
            # check for "TRACK_PHASE" stability
            sync_count = self.run_host(f"cat {output_file}").stdout.count("TRACK_PHASE")
            print_utils.print_info(f"Sync count (TRACK_PHASE): {sync_count}", 2)
            isSync = (sync_count >= 3)

        self.toggle_stat_off_node()
        print_utils.print_info("---------- END RESYNCHRONOZATION ----------", 1)
        return

    def toggle_stat_on_node(self) -> None:
        self.__tryNewSSHConnection()
        self.run_node(f"stat on")
        return

    def toggle_stat_off_node(self) -> None:
        self.__tryNewSSHConnection()
        self.run_node(f"stat off")
        return

    def run_host(self, op: str, hide: bool = False) -> Any:
        return self.__c.run(f"{op}",
            hide=(hide and print_utils.is_verbosity_printable(1)))
    
    def run_node(self, op: str, hide: bool = False) -> Any:
        return self.__c.run(f"echo -e -n '{op}\r' > {self.__TTY_USB__}",
            hide=(hide and print_utils.is_verbosity_printable(2)))

    def read_node_log(self, time: int = 60, hide = True) -> List[str]:
        output_file = "stat.log"
        self.toggle_stat_on_node()
        self.__run_node_to_file(None, time, output_file, hide=hide)
        self.toggle_stat_off_node()
        return self.run_host(f"cat {output_file}").stdout.split("\n")

    def __run_node_to_file(self, op: str | None, sleep: int, file: str = "output.txt", hide:bool = True):
        if self.check_stop_event("__run_node_to_file"):
            return
        result = self.__c.run(f"cat -v < {self.__TTY_USB__} > {file}&", asynchronous=True,
            hide=(hide and print_utils.is_verbosity_printable(2)))
        ps_id = str(self.run_host("ps | grep -w 'cat'").stdout).split()[0]
        print_utils.print_info(ps_id, 2)
        
        if op is not None:
            result = self.run_node(op)

        if (sleep > 5):
            for t in print_utils.timer_bar(
                range(sleep, -1, -1),
                prefix="Logging time:",
                suffix="left",
                length=100):
                if self.check_stop_event("__run_node_to_file"):
                    result = self.run_host(f"kill -9 {ps_id}", hide=hide)
                    return
                timer.sleep(1)
        else:
            timer.sleep(sleep)

        result = self.run_host(f"kill -9 {ps_id}", hide=hide)
        # print(result.stdout)
        return

    def apply_calib_offset_node(self, meanOffset: int, node_port: int) -> Tuple[int, int]:
        if self.check_stop_event("apply_calib_offset_node"):
            return
        self.__tryNewSSHConnection()
        
        # sfp match
        # Output:
        # Port 0 No SFP.
        # port 1 SFP not matched!
        # SFP1G-SX-85
        # Port 1 Could not match to DB

                
        self.toggle_stat_off_node() # ensure no statuses printed

        output_file = "output.txt"
        self.__run_node_to_file("sfp match", 1, file=output_file)
        result = self.run_host(f"cat {output_file}", hide=True).stdout.upper().split("\n")
        sfpIds = list(filter(lambda line : ("PORT" not in line), result))
        sfpId = sfpIds[1].split()[0] if len(sfpIds) == 4 else sfpIds[node_port + 1].split()[0]

        # sfp show
        # Output:
        # Port 0, SFP 2: PN:SFP1G-SX-85      dTx:   -38753 dRx:    38801 alpha:        0
        # Port 1, SFP 1: PN:SFP1G-LX-31      dTx:        0 dRx:        0 alpha:        0
        output_file = "output.txt"
        self.__run_node_to_file("sfp show", 1, file=output_file)
        result = self.run_host(f"cat {output_file} | grep {sfpId}", hide=True).stdout.upper().split("\n")
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
        self.__tryNewSSHConnection()

        # sfp match
        # Output:
        # Port 0 No SFP.
        # port 1 SFP not matched!
        # SFP1G-SX-85
        # Port 1 Could not match to DB

        self.toggle_stat_off_node() # ensure no statuses printed

        output_file = "output.txt"
        self.__run_node_to_file("sfp match", 1, file=output_file)
        result = self.run_host(f"cat {output_file}", hide=True).stdout.upper().split("\n")
        sfpIds = list(filter(lambda line : ("PORT" not in line), result))
        # print(result)
        # print(sfpIds)
        sfpId = sfpIds[1].split()[0] if len(sfpIds) == 4 else sfpIds[node_port + 1].split()[0]
        
        if self.check_stop_event("apply_calib_node"):
            return
        result = self.run_node(f"sfp add {sfpId} {tx} {rx} 0 {node_port}")
        print_utils.print_info(f"New offsets are TX: {tx}, RX {rx}", 1)

        return (tx, rx)

    def __tryNewSSHConnection(self) -> int:
        if type(self.__c) is not Connection:
            config = Config(overrides={'sudo': {'password': self.__HOST_ROOT_PWD}})
            print_utils.print_info("---------- CONNECT SSH ----------", 1)
            self.__c = Connection(self.__HOST_NAME, port=22, connect_kwargs={"password": self.__CONNECT_PWD}, config=config)
            return 1
        return 0

    def __tryCloseSSHConnection(self) -> int:
        if type(self.__c) is Connection:
            self.__c.close()
            self.__c = None
            print_utils.print_info("---------- SSH SESSION CLOSED ----------", 1)
            return 1
        return 0

    def close(self) -> int:
        return self.__tryCloseSSHConnection()