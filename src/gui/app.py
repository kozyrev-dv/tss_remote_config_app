import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import tkinter.font as tk_font
import subprocess
import threading
import queue
import sys
import io

from .autocalib_tab import AutocalibTab
from .remote_config_tab import RemoteConfigTab
from ..utils import threading as thread_utils

class App:

    __CONSOLE_UPDATE_PERIOD = 100

    def __init__(self, root):
        self.root = root
        root.title("TSS calibration app")
        root.geometry("1120x700")

        self.output_buffer = None
        self.__create_output_buffer()

        # Create a queue for thread-safe console output        
        self.root.after(App.__CONSOLE_UPDATE_PERIOD, self.process_console_queue) # Start checking the queue

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, expand=True, fill=tk.BOTH)

        # --- Autocalib Tab ---
        self.autocalib_tab_fr = ttk.Frame(self.notebook)
        self.autocalib_tab = AutocalibTab(
            master=self.autocalib_tab_fr)
        self.notebook.add(self.autocalib_tab_fr, text="Autocalib")
        self.autocalib_tab_fr.bind(thread_utils.OnScriptThreadGenerate_Event, self.__enable_terminate_btn)
        self.autocalib_tab_fr.bind(thread_utils.OnScriptThreadTerminate_Event, self.__disable_terminate_btn)

        # --- Remote config Tab ---
        self.remote_config_fr = ttk.Frame(self.notebook)
        self.remote_config_tab = RemoteConfigTab(
            master=self.remote_config_fr)
        self.notebook.add(self.remote_config_fr, text="Remote config")
        self.remote_config_fr.bind(thread_utils.OnScriptThreadGenerate_Event, self.__enable_terminate_btn)
        self.remote_config_fr.bind(thread_utils.OnScriptThreadTerminate_Event, self.__disable_terminate_btn)

        # --- Shared Console Output Field ---
        self.console_output_frame = ttk.LabelFrame(root, text="Console output")
        self.console_output_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True, side=tk.BOTTOM)

        self.terminate_threads_btn = ttk.Button(self.console_output_frame, text="terminate", command=self.__terminate_threads)
        self.terminate_threads_btn.pack(side=tk.TOP, expand=True, padx=5, pady=2)
        self.__disable_terminate_btn()
        self.console_output = scrolledtext.ScrolledText(self.console_output_frame, state=tk.DISABLED, wrap=tk.WORD, height=10)
        self.console_output.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

    def process_console_queue(self):
        """Processes items in the console queue and updates the ScrolledText widget."""
        text = self.output_buffer.getvalue()
        if text != "":
            self.__create_output_buffer()
            self.console_output.config(state='normal') # Temporarily make the field editable
            self.console_output.insert(tk.END, text)
            self.console_output.see(tk.END) # Scroll to the end
            self.console_output.config(state='disabled') # Revert to read-only state
        self.root.after(App.__CONSOLE_UPDATE_PERIOD, self.process_console_queue) # Schedule next check

    def __create_output_buffer(self):
        self.output_buffer = io.StringIO()
        sys.stdout = self.output_buffer
        sys.stderr = self.output_buffer
        return
    
    def __enable_terminate_btn(self, *args):
        if len(self.autocalib_tab.threads) + len (self.remote_config_tab.threads) > 0:
            self.terminate_threads_btn.config(state=tk.NORMAL)
        return

    def __disable_terminate_btn(self, *args):
        if len(self.autocalib_tab.threads) + len (self.remote_config_tab.threads) == 0:
            self.terminate_threads_btn.config(state=tk.DISABLED)
        return

    def __terminate_threads(self, *args):
        self.autocalib_tab.terminate_threads_event.set()
        self.remote_config_tab.terminate_threads_event.set()

        self.autocalib_tab.threads.clear()
        self.remote_config_tab.threads.clear()
        
        self.autocalib_tab_fr.event_generate(thread_utils.OnScriptThreadTerminate_Event)
        self.remote_config_fr.event_generate(thread_utils.OnScriptThreadTerminate_Event)
        return



def launch():
    root = tk.Tk()
    app = App(root)
    root.mainloop()
