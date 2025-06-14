from typing import Tuple, Any, List

from ..utils import print as print_utils

class Connection:
    def __init__(self, root = None, stop_event = None):
        self.__c = None
        self.stop_event = stop_event
        self.script = root

    def setup_connection(self) -> None:
        raise NotImplementedError()
    
    def setup_node(self) -> None:
        raise NotImplementedError()
    
    def resync_ptp_node(self) -> None:
        raise NotImplementedError()
    
    def toggle_stat_on_node(self) -> None:
        raise NotImplementedError()

    def toggle_stat_off_node(self) -> None:
        raise NotImplementedError()
    
    def run_host(self, op: str, hide: bool = False) -> Any:
        raise NotImplementedError()
    
    def run_node(self, op: str, hide: bool = False) -> Any:
        raise NotImplementedError()
    
    def read_node_log(self, time: int = 60, hide: bool = False) -> List[str]:
        raise NotImplementedError()

    def apply_calib_offset_node(self, meanOffset: int, node_port: int) -> Tuple[int, int]:
        raise NotImplementedError()
    
    def apply_calib_node(self, tx: int, rx: int, node_port: int) -> Tuple[int, int]:
        raise NotImplementedError()

    def close(self) -> int:
        raise NotImplementedError
    
    def check_stop_event(self, func):
        if self.stop_event.is_set():
            print_utils.print_thread_terminated(self.script, func)
            self.close()
            return True
        return False