import sys
import threading
import time as timer
import os, signal

from ..utils import print as print_utils

OnScriptStart_Event = "<<OnScriptStart>>"
OnScriptFinish_Event = "<<OnScriptFinish>>"
OnScriptThreadGenerate_Event = "<<OnScriptThreadGenerate>>"
OnScriptThreadTerminate_Event = "<<OnScriptThreadTerminate>>"

def run_script_in_bg(func, args, gui = None, stop_event=None) -> int:
        """Runs a command in a separate thread"""
        def run(run_func, func_args, stop_event = None, run_gui = None):
            if run_gui is not None:
                run_gui.event_generate(OnScriptStart_Event)
                run_gui.event_generate(OnScriptThreadGenerate_Event)
            try:
                # timer.sleep(10)
                run_func(func_args)
            except Exception as ex:
                # import traceback
                # print_utils.print_error(f"[THREAD] {traceback.format_exc()}")
                print_utils.print_error(f"[THREAD] {ex}")
            if run_gui is not None:
                run_gui.event_generate(OnScriptFinish_Event)
                run_gui.event_generate(OnScriptThreadTerminate_Event)
            stop_event.clear()
            
        thread = threading.Thread(target=run, args=(func, args, stop_event, gui))
        thread.start()
        timer.sleep(1)
        print_utils.print_info(f"Script process id: {thread.ident}", 2)
        return thread.ident

def terminate_thread(pid):
    print_utils.print_info(f"PID to terminate: {pid}", 2)
    os.kill(pid, signal.SIGTERM)