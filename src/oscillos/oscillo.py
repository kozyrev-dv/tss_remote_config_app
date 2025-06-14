from ..utils import print as print_utils

class Oscilloscope:
    def __init__(self, root = None, stop_event = None):
        self.__device = None
        self.script = root
        self.stop_event = stop_event
		
    def write(self, op: str):
        raise NotImplementedError()
	
    def write_str(self, op: str):
        raise NotImplementedError()

    def write_str_with_opc(self, op: str, timeout: int = None):
	    raise NotImplementedError()
    
    def write_int(self, op: str, arg: int):
        raise NotImplementedError()

    def write_int_with_opc(self, op: str, arg: int, timeout: int = None):
        raise NotImplementedError()
	
    def write_float(self, op: str, arg: float):
        raise NotImplementedError()
		
    def write_float_with_opc(self, op: str, arg: float, timeout: int = None):
        raise NotImplementedError()
	
    def write_bool(self, op : str, arg: bool):
        raise NotImplementedError()

    def write_bool_with_opc(self, op : str, arg: bool, timeout: int = None):
        raise NotImplementedError()

    def query(self, query: str):
        raise NotImplementedError()
    
    def query_opc(self, timeout: int = 0):
        raise NotImplementedError()
	
    def setup_measurements(self, switch_ch: int, node_ch: int):
        raise NotImplementedError()

    def perform_measurements(self, event_count_to_acquire: int):	
        raise NotImplementedError()

    def reset_measurements(self):
        raise NotImplementedError()
    
    def close_session(self):
        raise NotImplementedError()
    
    def check_stop_event(self, func):
        if self.stop_event.is_set():
            print_utils.print_thread_terminated(self.script, func)
            return True
        return False