from ..connection.exceptions.node_errors import *
from ..connection.snmp_connect import SNMP_Connect

from ..utils import print as print_utils
from ..utils import ip as ip_utils
from ..utils import math  as math_utils 

from ..connection.exceptions.execution_statuses import ScriptRunStatusesEnum

import argparse

__NODE_MODEL__ = None

remote_config_stop_event = None
script_name = "remote_config"

def assign_remote_config_stop_event(event):
    global remote_config_stop_event
    remote_config_stop_event = event
    return

def main(args_list=None) -> int:
    global __NODE_MODEL__
    global remote_config_stop_event

    parser = argparse.ArgumentParser(
    prog=script_name,
    description='Remote configuration of calibration coefficients of the WR-Node in network via SNMP'
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("-ip", help="target IP-address to config", type=str)
    source_group.add_argument("-f", "--file", help="file of IP-addresses to config", type=str)
    parser.add_argument("tx",       help="tx delay coefficient", type=int)
    parser.add_argument("rx",       help="rx delay coefficient", type=int)
    parser.add_argument("alpha",    help="fiber assymetry coefficient", type=int)
    parser.add_argument("--sfp",    help="SFP PN to set the coefficients to. If none supplied, coefficients are applied to the current inserted", type=str)
    parser.add_argument("-v", "--verbosity",help="increase output verbosity", action="count", default=0)
    parser.add_argument("-l", "--log",      help="path to output file for logging the application results to. If left empty: log to 'run.log'", type=str)
    parser.add_argument("-rs", "--resync",  help="restart PTP with applied coefficients", action="store_true", default=False)
    parser.add_argument("--wait",           help="wait time in secods for resynchronization after PTP restart. Default: 0 sec - wait is turned off", type=int, default=0)
    parser.add_argument("-nm", "--nodemodel", help="specify node model for platform specific coefficient calculations", type=str)
    args = parser.parse_args(args=args_list)

    if (args.log is not None):
        print_utils.logger.open(args.log, "a")

    print_utils.set_print_verbosity_lvl(args.verbosity)
    __NODE_MODEL__ = args.nodemodel.upper() if args.nodemodel is not None else None

    if (not args.resync):
        if (args.wait):
            print_utils.print_error("--wait flag is required only if --resync flag is on")
            return 1

    if (args.wait < 0):
        print_utils.print_error("--wait flag accepts non-negative integers only")
        return 1
    if __is_stop_event_set():
            print_utils.print_thread_terminated(script_name, "main")
            return
    if args.ip is not None:
        
        __x_launch(
            IP_ADDRESS=args.ip,
            TX_DELAY=args.tx,
            RX_DELAY=args.rx,
            ALPHA_COEF=args.alpha,
            SFP_PN=args.sfp,
            RESYNC=args.resync,
            RESYNC_TIMEOUT=args.wait
        )
    elif args.file is not None: # if exception - break interation but not the whole cycle
            with open(args.file, "r") as addresses:
                ip = ""
                try:
                    for line in addresses:
                        print_utils.print_untagged("------------------------", 0)
                        ip = line.strip()
                        __x_launch(
                            IP_ADDRESS=ip,
                            TX_DELAY=args.tx,
                            RX_DELAY=args.rx,
                            ALPHA_COEF=args.alpha,
                            SFP_PN=args.sfp,
                            RESYNC=args.resync,
                            RESYNC_TIMEOUT=args.wait
                        )
                except Exception as ex:
                    __print_error(ip, ScriptRunStatusesEnum.UNKNOWN_ERROR, str(ex))
                    remote_config_stop_event.set()
                finally:
                    if print_utils.logger.is_logging_on():
                        print_utils.logger.close_log()
                    if __is_stop_event_set():
                        print_utils.print_thread_terminated(script_name, "main")
                        return
    else:
        print_utils.print_error("No -ip/-f is given. One of the options is required to be set")
        return 1
    return 0

def launch(
        IP_ADDRESS: str,
        TX_DELAY: int,
        RX_DELAY: int,
        ALPHA_COEF: int,
        SFP_PN: str,
        RESYNC: bool,
        RESYNC_TIMEOUT: int
) -> int:
    global remote_config_stop_event
    __MIBS_FOLDER__ = ["src/mibs"]
    
    if __is_stop_event_set():
        print_utils.print_thread_terminated(script_name, "launch")
        return
    
    node_con = SNMP_Connect(
        mibs="WR-WRPC-MIB",
        libs=__MIBS_FOLDER__,
        ip=IP_ADDRESS,
        root_script=script_name,
        stop_event=remote_config_stop_event
    )
    node_con.set_retries(2)

    set_error_flag = False
    tx_get = None
    rx_get = None
    alpha_get = None
    for i in range(2):
        if __is_stop_event_set():
            node_con.close()
            print_utils.print_thread_terminated(script_name, "launch")
            return
        
        set_error_flag = False   
        set_tx = __prepare_coef(TX_DELAY)
        set_rx = __prepare_coef(RX_DELAY)
        set_alpha = __prepare_coef(ALPHA_COEF)
        print_utils.print_info(f"Trying to load coefficients: {TX_DELAY}({set_tx}), {RX_DELAY}({set_rx}), {ALPHA_COEF}({set_alpha})", 0)
        node_con.snmpset("wrpcPtpConfigDeltaTx.0",  set_tx)
        node_con.snmpset("wrpcPtpConfigDeltaRx.0",  set_rx)
        node_con.snmpset("wrpcPtpConfigAlpha.0",    set_alpha)
        if (SFP_PN is None):
            node_con.snmpset("wrpcPtpConfigApply.0", "writeToFlashCurrentSfp")
        else:
            node_con.snmpset("wrpcPtpConfigSfpPn.0", SFP_PN)
            node_con.snmpset("wrpcPtpConfigApply.0", "writeToFlashGivenSfp")
        
        print_utils.print_info(f"SNMP sets to {IP_ADDRESS} performed.", 1)

        if __is_stop_event_set():
            node_con.close()
            print_utils.print_thread_terminated(script_name, "launch")
            return
        
        print_utils.print_info(f"Validating correct assignments...", 2)
        
        # config check
        # check via wrpcSfpTable
        buf = node_con.snmpwalk("wrpcSfpTable", hide=True).split("\n")
        
        matched_sfp = node_con.snmpget("wrpcPortSfpPn.0").strip("\" \n")
        print_utils.print_info(f"Matched SFP: {matched_sfp}", 2)
        table_index = next(x for x in buf if matched_sfp in x).split(".")[1].split("=")[0].strip()
        print_utils.print_info(f"Table index: {table_index}", 2)

        buf = list(filter(lambda x: (f"wrpcSfpDeltaTx.{table_index}" in x or f"wrpcSfpDeltaRx.{table_index}" in x or f"wrpcSfpAlpha.{table_index}" in x), buf))
        tx_get = int("".join(filter(lambda x: (str.isdigit(x) or x=="-"), buf[0].split("=")[1])))
        rx_get = int("".join(filter(lambda x: (str.isdigit(x) or x=="-"), buf[1].split("=")[1])))
        alpha_get = int("".join(filter(lambda x: (str.isdigit(x) or x=="-"), buf[2].split("=")[1])))

        print_utils.print_untagged("", 2)
        print_utils.print_info(f"The set TX delay: {tx_get}. The set RX delay: {rx_get}. The set alpha: {alpha_get}", 2)
        print_utils.print_info(f"Expected TX delay: {set_tx}. Expected RX delay: {set_rx}. Expected alpha: {set_alpha}", 2)
        print_utils.print_untagged("", 2)
        set_error_flag = (tx_get != set_tx)
        set_error_flag = (set_error_flag or rx_get != set_rx)
        set_error_flag = (set_error_flag or alpha_get != set_alpha)
        if (not set_error_flag):
            break
        
    if __is_stop_event_set():
        node_con.close()
        print_utils.print_thread_terminated(script_name, "launch")
        return

    if set_error_flag:
        raise NodeValueError(SnmpCommandCode.WALK, 
                             ScriptRunStatusesEnum.COEF_COHERENCY_LOSS,
                             "wrpcPtpGroup",
                             f"Unable to apply delay coefficients for {IP_ADDRESS}. Current are:",
                             f"TX delay: {tx_get}, RX delay: {rx_get}, alpha: {alpha_get}")
    else:
        print_utils.print_info(
            f"Successfully applied delay coefficients for {IP_ADDRESS}. Current "
            f"TX delay: {tx_get}, RX delay: {rx_get}, alpha: {alpha_get}",
            verbosity=0
        )

    if (RESYNC):
        print_utils.print_info(f"Restart PTP...", 0)
        if (node_con.ptp_resync(timeout=RESYNC_TIMEOUT)):
            print_utils.print_untagged("",0)
            if RESYNC_TIMEOUT:
                print_utils.print_info(f"PTP Synchronized", 0)
    
    if print_utils.logger.is_logging_on():
        print_utils.logger.log(IP_ADDRESS, ScriptRunStatusesEnum.OK)
    
    print_utils.print_info(f"Config {IP_ADDRESS} finished", 0)
    return 0

# handles try-catches for logging into file if enabled
def __x_launch(
        IP_ADDRESS: str,
        TX_DELAY: int,
        RX_DELAY: int,
        ALPHA_COEF: int,
        SFP_PN: str,
        RESYNC: bool,
        RESYNC_TIMEOUT: int
) -> int:
    global remote_config_stop_event
    if not ip_utils.is_ip_valid(IP_ADDRESS):
            err_msg = f"Invalid IP ({IP_ADDRESS}) format. Expected format: 2.25.255.03"
            __print_error(IP_ADDRESS, ScriptRunStatusesEnum.IP_INVALID,
                            err_msg)
            return
    try:
        launch(
            IP_ADDRESS = IP_ADDRESS,
            TX_DELAY = TX_DELAY,
            RX_DELAY = RX_DELAY,
            ALPHA_COEF = ALPHA_COEF,
            SFP_PN = SFP_PN,
            RESYNC=RESYNC,
            RESYNC_TIMEOUT=RESYNC_TIMEOUT
        )

        if __is_stop_event_set():
            print_utils.print_thread_terminated(script_name, "__x_launch")
            return
    except NodeConnectError as ex:
        __print_error(IP_ADDRESS, ex.err_code,
                        f"Connection to {IP_ADDRESS} is failed on {SnmpCommandCode(ex.cmd).name}." + str(ex.args))
    except NodeValueError as ex:
        # Unexpected OK-error
        if (ex.err_code == ScriptRunStatusesEnum.OK):
            __print_error(IP_ADDRESS, ex.err_code,
                            f"Unexpected error with OK ({ScriptRunStatusesEnum.OK:X}) status" + str(ex.args))
        # Every other Exception is printed as-is
        elif (ex.err_code in iter(ScriptRunStatusesEnum)):
            __print_error(IP_ADDRESS, ex.err_code,
                            str(ex.args))
        # If new Exception, write it!
        else:
            __print_error(IP_ADDRESS, ScriptRunStatusesEnum.UNKNOWN_ERROR,
                            "Unspecified error met." + str(ex.args))
    except NodeSyncTimeoutError as ex:
        __print_error(IP_ADDRESS, ScriptRunStatusesEnum.SYNC_TIMEOUT,
                      str(ex.args))

def __print_error(ip: str, err_code: ScriptRunStatusesEnum, msg: str):
    print_utils.print_error(f"{ip}: {ScriptRunStatusesEnum(err_code).name}({err_code:X}). {msg}")
    if print_utils.logger.is_logging_on():
        print_utils.logger.log(ip, err_code)
    return

def __prepare_coef(val: int) -> int:
    global __NODE_MODEL__
    if __NODE_MODEL__=="CUTE_A7":
        return math_utils.round_partial(val, 256) // 256
    return val

def __is_stop_event_set():
    return remote_config_stop_event is not None and remote_config_stop_event.is_set()