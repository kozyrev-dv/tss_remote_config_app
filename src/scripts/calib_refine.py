from ..oscillos.rto2000 import RTO2000
from ..oscillos.oscillo import Oscilloscope
from ..connection.ssh_connect import SSH_Connect
from ..connection.direct_connect import Direct_Connect
from ..connection.connection import Connection

from ..utils import print as print_utils
from ..utils import regex as regex_utils
from ..utils import ip as ip_utils

import argparse
import pandas as pd
import numpy as np


calib_refine_stop_event = None
script_name = "calib_refine"

def assign_calib_refine_stop_event(event):
    global calib_refine_stop_event
    calib_refine_stop_event = event
    return

def main(args_list=None):
    parser = argparse.ArgumentParser(
    prog=script_name,
    description='refine calibration data of WR-node via dedicated oscilloscope (RTO 2000 supported only) and direct to WR-Node or SSH access to remote server connected to WR-Node'
    )
    parser.add_argument("instrmodel", choices=['rto2000'], help="oscilloscope model which API to access")
    parser.add_argument('instrip', help="oscilloscope's IP to connect to")
    parser.add_argument('--ttyUSB', help="ttyUSB port number to connect on the linux-running server", default=0, type=int)
    parser.add_argument('--dtcs', help="Data Transfer Chunk Size to use while sending measurements to controlling device", default=100000, type=int)
    parser.add_argument('time', help="time per calibration iteration", type=int)
    parser.add_argument('iter', help="number of iterations for calibration", type=int)
    parser.add_argument('wrndsfp', help="WR-node SFP port number to use for calibration", default=0, type=int)
    parser.add_argument('--crtt', help="crtt calibration time in seconds. Passing -1 disables crtt reset and calibration; 0 resets coefs, but doesn't calibrate crtt. Default: 60 sec", default=60, type=int)

    parser.add_argument('--wfrchsw', help="oscilloscope channel the WR-Switch is connected to", default=1, type=int)
    parser.add_argument('--wfrchnode', help="oscilloscope channel the WR-Node is connected to", default=2, type=int)
    parser.add_argument("-v", "--verbosity", action="count", help="increase output verbosity", default=0)
    
    parser.add_argument("-s", '--ssh', action='store_true', help='Enable SSH connection to PC connected to calibrated WR-Node')
    parser.add_argument('--sshhostname', help="IP address of remote server the WR Node is connected to. (required if --ssh is set)")
    parser.add_argument('--sshpwd', help="password to use for connecting via SSH. (required if --ssh is set)")
    parser.add_argument('--sshhostrootpwd', help="password to use for login as root on host. Default: equals to sshpwd. (required if --ssh is set)")
    
    args = parser.parse_args(args=args_list)
    
    if not ip_utils.is_ip_valid(args.instrip):
        print_utils.print_error(f"Invalid instrument IP: {args.instrip}. Expected format is 2.22.215.05")
        return 1
    
    # Check after parsing if --flag is set, then options must be provided
    if args.ssh:
        missing_options = []
        if args.sshhostname is None:
            missing_options.append('--sshhostname')
        if args.sshpwd is None:
            missing_options.append('--sshpwd')
        if missing_options:
            print_utils.print_error(f"When --ssh is set, the following options are required: {', '.join(missing_options)}")
            return 1
        if not regex_utils.check_ssh_hostname_valid(args.sshhostname):
            print_utils.print_error(f"Invalid ssh host name format: {args.sshhostname}. Expected format is host_name@2.22.215.05")
            return 1

    if args.crtt < -1 or args.crtt is None:
        print_utils.print_error(f"Invalid --crtt value ({args.crtt}). --crtt excepts only non-negative integers or -1")
        return 1

    if args.sshhostrootpwd is None:
        args.sshhostrootpwd = args.sshpwd

    if (is_stop_event_set()):
        print_utils.print_thread_terminated(script_name, "main")
        return

    launch(
        INSTR_MODEL =                args.instrmodel,
        INSTR_IP =                   args.instrip,
        TIC_SWITCH_CHANNEL =         args.wfrchsw,
        TIC_NODE_CHANNEL =           args.wfrchnode,
        TTY_USB_PORT_NUM =           args.ttyUSB,
        WR_NODE_SFP_PORT =           args.wrndsfp,
        DATA_TRANSFER_CHUNK_SIZE =   args.dtcs,
        CRTT_TIME =                  args.crtt,
        EVENT_COUNT_TO_ACQUIRE =     args.time,
        ITERATIONS_PER_CALIBRATION = args.iter,
        IS_SSH_MODE =                args.ssh,
        SSH_HOST_NAME =              args.sshhostname,
        SSH_CONNECT_PWD =            args.sshpwd,
        SSH_HOST_ROOT_PWD =          args.sshhostrootpwd,
		VERBOSITY_LEVEL =            args.verbosity
    )
    return 0

if __name__ == script_name:
    main()

def __measure_skew_mean(con: Connection, tic: Oscilloscope, event_count_to_acquire: int):
    global calib_refine_stop_event
    
    con.resync_ptp_node()
    con.close()
    
    if is_stop_event_set():
        print_utils.print_thread_terminated(script_name, "__measure_skew_mean")
        con.close()
        tic.close_session()
        return
    
    file_path_to_write_data = tic.perform_measurements(event_count_to_acquire)
    if file_path_to_write_data is None:
        return []
    delays = pd.read_csv(file_path_to_write_data, names=["a", "b", "c", "d", "e", "f", "g"])["a"] * 10 ** 12
    return delays


def launch(
        INSTR_MODEL: str,
        INSTR_IP: str,
        TIC_SWITCH_CHANNEL: int,
        TIC_NODE_CHANNEL: int,      
		TTY_USB_PORT_NUM: int,
		WR_NODE_SFP_PORT: int,
		DATA_TRANSFER_CHUNK_SIZE: int,
        CRTT_TIME: int,
		EVENT_COUNT_TO_ACQUIRE: int,
		ITERATIONS_PER_CALIBRATION: int,
        IS_SSH_MODE: bool,
        SSH_HOST_NAME: str,
		SSH_CONNECT_PWD: str,
		SSH_HOST_ROOT_PWD: str,
		VERBOSITY_LEVEL: int
):
    global calib_refine_stop_event

    print_utils.set_print_verbosity_lvl(VERBOSITY_LEVEL)
    
    con = Connection()
    if(IS_SSH_MODE):
        con = SSH_Connect(host_name=SSH_HOST_NAME,
                          connect_pwd=SSH_CONNECT_PWD,
                          host_root_pwd=SSH_HOST_ROOT_PWD,
                          tty_usb_port=TTY_USB_PORT_NUM,
                          root=script_name,
                          stop_event=calib_refine_stop_event)
    else:
        con = Direct_Connect(tty_usb_port=TTY_USB_PORT_NUM,
                            root=script_name,
                            stop_event=calib_refine_stop_event)	

    if is_stop_event_set():
        con.close()
        print_utils.print_thread_terminated(script_name, "launch")
        return
    
    con.setup_connection()
    con.setup_node()
    if (CRTT_TIME != -1):
        if is_stop_event_set():
            con.close()
            print_utils.print_thread_terminated(script_name, "launch")
            return
        print_utils.print_info("---------- RESETTING COEFS ----------", 1)
        
        con.apply_calib_node(0, 0, WR_NODE_SFP_PORT)
        
        if is_stop_event_set():
            con.close()
            print_utils.print_thread_terminated(script_name, "launch")
            return
        
        con.resync_ptp_node()
        
        if is_stop_event_set():
            con.close()
            print_utils.print_thread_terminated(script_name, "launch")
            return
        
        print_utils.print_info("---------- MEASURING CRTT ----------", 1)
        crtt_mean = __calc_crtt_mean(con.read_node_log(time = CRTT_TIME))
        
        if is_stop_event_set():
            con.close()
            print_utils.print_thread_terminated(script_name, "launch")
            return
        
        con.apply_calib_node(crtt_mean // 2, crtt_mean // 2, WR_NODE_SFP_PORT)
    # con.resync_ptp_node() # - needed ONLY when supoport of dynamic horizontal axis scaling will be on

	# ----------- start instrument ----------- 
    if is_stop_event_set():
            con.close()
            print_utils.print_thread_terminated(script_name, "launch")
            return
    print_utils.print_info("---------- START OSCILLOSCOPE SESSION ----------", 1)

    tic = Oscilloscope()
    if (INSTR_MODEL == "rto2000"):
        tic = RTO2000(ip_address=INSTR_IP,
                      data_transfer_chunk_size=DATA_TRANSFER_CHUNK_SIZE,
                      root=script_name,
                      stop_event=calib_refine_stop_event)
    else:
        pass

	# ----------- setup measurements ----------- 
    print_utils.print_info("---------- SETUP ACQUISITION ----------", 1)
    tic.setup_measurements(TIC_SWITCH_CHANNEL, TIC_NODE_CHANNEL)
    
    if is_stop_event_set():
        print_utils.print_thread_terminated(script_name, "launch")
        con.close()
        tic.close_session()
        return
    
    # Main Measurements Loop
    sampled_delays = []
    for i in range(ITERATIONS_PER_CALIBRATION):
        print_utils.inc_loop_num()
        print_utils.print_loop("Loop started", 1)
        
        if is_stop_event_set():
            print_utils.print_thread_terminated(script_name, "launch")
            con.close()
            tic.close_session()
            return
        
        delays = __measure_skew_mean(con, tic, EVENT_COUNT_TO_ACQUIRE)
        if is_stop_event_set():
            print_utils.print_thread_terminated(script_name, "launch")
            con.close()
            tic.close_session()
            return
        sampled_delays.extend(delays.to_list())
        print_utils.print_loop(f"Measurement no. {i + 1}, loaded to delays. {len(delays)} samples added.", 2)
        print_utils.print_loop(f"Measurements' mean: {np.mean(delays):.3f} ps", 1)

        if is_stop_event_set():
            print_utils.print_thread_terminated(script_name, "launch")
            con.close()
            tic.close_session()
            return
        tic.reset_measurements()

    print_utils.print_info("Measurements are done", 1)
    meanOffset = np.mean(sampled_delays)
    print_utils.print_info(f"Measurements' total mean: {meanOffset:.3f} ps", 1)
    
    if is_stop_event_set():
        print_utils.print_thread_terminated(script_name, "launch")
        con.close()
        tic.close_session()
        return
    
    con.apply_calib_offset_node(meanOffset, WR_NODE_SFP_PORT)
    
    if is_stop_event_set():
        print_utils.print_thread_terminated(script_name, "launch")
        con.close()
        tic.close_session()
        return
    
    delays = __measure_skew_mean(con, tic, EVENT_COUNT_TO_ACQUIRE)
    
    if is_stop_event_set():
        print_utils.print_thread_terminated(script_name, "launch")
        con.close()
        tic.close_session()
        return
    
    print_utils.print_info("Calibration performed.", 1)
    print_utils.print_info(f"Old mean was: {meanOffset:.3f}ps . New mean is: {np.mean(delays):.3f}ps", 1)

    tic.close_session()

def __calc_crtt_mean(lines) -> int:
    crtt = 0
    buf = list(filter(lambda x: "TRACK_PHASE" in x, lines))
    for line in buf:
        crtt += int(line.split("crtt:")[1].split(" ")[0])
    return crtt // len(buf)

def is_stop_event_set():
    return calib_refine_stop_event is not None and calib_refine_stop_event.is_set()