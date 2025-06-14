from RsInstrument import *  # The RsInstrument package is hosted on pypi.org, see Readme.txt for more details
from ..oscillos.oscillo import Oscilloscope
from ..utils import print as print_utils

import time as timer
import pathlib

class RTO2000(Oscilloscope):
	def __init__(self, ip_address, data_transfer_chunk_size, root: str, stop_event = None):
		super().__init__(root, stop_event)
		# Make sure you have the last version of the RsInstrument
	
		RsInstrument.assert_minimum_version('1.53.0')
		try:
			self.__device = RsInstrument(f'TCPIP::{ip_address}', True, True)
			self.__device.visa_timeout = 3000  # Timeout for VISA Read Operations
			self.__device.opc_timeout = 15000  # Timeout for opc-synchronised operations
			self.__device.instrument_status_checking = True  # Error check after each command
			self.__device.events.on_read_handler = None
			self.__device.events.io_events_include_data = False
			self.__device.data_chunk_size = data_transfer_chunk_size # !! // 8
		except Exception as ex:
			raise ValueError('Error initializing the instrument session:\n' + ex.args[0])

	def write(self, op: str):
		self.__device.write(op)
		return
	
	def write_str(self, op: str):
		self.__device.write_str(op)
		return

	def write_str_with_opc(self, op: str, timeout: int = None):
		self.__device.write_str_with_opc(op, timeout)
		return

	def write_int(self, op: str, arg: int):
		self.__device.write_int(op, arg)
		return

	def write_int_with_opc(self, op: str, arg: int, timeout: int = None):
		self.__device.write_int_with_opc(op, arg, timeout)
		return

	def write_float(self, op: str, arg: float):
		self.__device.write_float(op, arg)
		return

	def write_float_with_opc(self, op: str, arg: float, timeout: int = None):
		self.__device.write_float_with_opc(op, arg, timeout)
		return

	def write_bool(self, op : str, arg: bool):
		self.__device.write_bool(op, arg)
		return

	def write_bool_with_opc(self, op : str, arg: bool, timeout: int = None):
		self.__device.write_bool_with_opc(op, arg, timeout)
		return

	def query(self, query: str):
		self.__device.query(query)
		return

	def query_opc(self, timeout: int = 0):
		self.__device.query_opc(timeout)
		return	
	
	def setup_measurements(self, switch_ch: int, node_ch: int):
		if self.check_stop_event("setup_measurements"):
			self.close_session()
			return

		def setup_channel(num):
			self.write_int(f"channel{num}:state", 1)
			self.write_str(f"channel{num}:coupling dc")
			self.write_float(f"channel{num}:position", -1.06)
			self.write_float(f"channel{num}:scale", 0.5)

		self.write_bool("system:display:update", True)

		self.write_float("timebase:scale", 10e-9)
		for channel in [switch_ch, node_ch]:
			setup_channel(channel)
		self.query_opc()

		self.write_str(f"trigger1:source channel{switch_ch}")
		self.write_str("trigger1:type edge")
		self.write_str("trigger1:edge:slope pos")
		self.write_float("trigger1:level1:value", 1.0)
		self.write_str("trigger1:mode normal")
		self.query_opc()

		self.write_str("measurement1:main delay")
		self.write_str(f"measurement1:source c{switch_ch}w1, c{node_ch}w1")
		self.query_opc()
		self.write_str("measurement1:amptime:delay1:lselect middle")
		self.write_str("measurement1:amptime:delay2:lselect middle")
		self.query_opc()
		self.write_int("measurement1:detthreshold", 5)
		self.write_str("measurement1:amptime:delay1:slope positive")
		self.write_str("measurement1:amptime:delay2:slope positive")
		self.write_str("measurement1:amptime:delay1:direction FRFI")
		self.write_str("measurement1:amptime:delay2:direction FRFI")
		self.write_int("measurement1:amptime:delay1:ecount", 1)
		self.write_int("measurement1:amptime:delay1:ecount", 1)
		self.query_opc()

		self.write_str("measurement1:ltmeas:state ON")
		self.write_str("measurement1:statistics:enable ON")
		self.write_str("measurement1:statistics:mode meas")
		self.write_int("measurement1:statistics:rmeascount", 1)
		self.write_str("measurement1:ltmeas:count MIN")
		self.write_str("measurement1:vertical:cont ON")
		self.query_opc()
		return
	
	def perform_measurements(self, event_count_to_acquire: int):	
		if self.check_stop_event("perform_measurements"):
			self.close_session()
			return
		print_utils.print_loop("---------- START ACQUISITION----------", 1)
		# sleeptime = max(EVENT_COUNT_TO_ACQUIRE * 0.9, EVENT_COUNT_TO_ACQUIRE - 30)
		self.write_str("measurement1:enable ON")
		self.write_str("run")
		self.query_opc()

		# ----------- accessing measurement results ----------- 
		print_utils.print_loop("---------- WAITING FOR ACQUISITION TO BE DONE----------", 1)
		for i in range(event_count_to_acquire):
			if self.check_stop_event("perform_measurements"):
				self.write_str("stop")
				self.close_session()
				return None
			timer.sleep(1)
		
		self.write_str("stop")
		self.write_str("export:measurement:select MEAS1")
		self.write_str("export:measurement:type LONGTERM")
		temp_file_path = "C:\\temp\\temp"
		self.write_str(f"export:measurement:name '{temp_file_path}.csv'")
		self.write_str_with_opc("export:measurement:save")

		self.__device.events.on_read_handler = transfer_handler
		file_path_to_results = f"{pathlib.Path().resolve()}\\meas1.csv"
		if self.check_stop_event("perform_measurements"):
			self.close_session()
			return None
		self.__device.read_file_from_instrument_to_pc(
			f"{temp_file_path}.Wfm.csv",
			file_path_to_results
		)
		self.__device.events.on_read_handler = None
		return file_path_to_results
	
	def reset_measurements(self):
		self.write_str_with_opc("measurement1:statistics:reset")
		return

	def close_session(self):
		if (self.__device.is_connection_active):
			self.__device.events.on_read_handler = None
			self.__device.clear_status()
			self.__device.go_to_local()
			self.__device.close()

def transfer_handler(args):
	total_size = args.total_size if args.total_size is not None else "unknown"
	percent = f"{(100 * args.transferred_size / args.total_size):.2f}" if args.total_size != "unknown" else "unknown"
	print_utils.print_info(f"Context: '{args.context}{'with opc' if args.opc_sync else ''}',\n"
            f"chunk {args.chunk_ix},\n"
            f"transferred {args.transferred_size} bytes // {percent},\n"
            f"total size {total_size}, \n"
            f"direction {'reading' if args.reading else 'writing'}", 2)
	if args.end_of_transfer:
		print_utils.print_info('--- transferring finished ---', 2)
		return
	timer.sleep(1)
