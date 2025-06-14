import tkinter as tk
from tkinter import ttk 
import os 
import threading

from ..scripts import remote_config
from ..utils import print as print_utils
from ..utils import ip as ip_utils
from ..utils import threading as thread_utils
from .utils import enablement_control

class RemoteConfigTab(object):
    def __init__(self, master):
        self.coef_entries = [] # List to store groups of fields
        self.group_frs = []
        self.terminate_threads_event = threading.Event()
        remote_config.assign_remote_config_stop_event(self.terminate_threads_event)
        self.threads = []
        
        self.master = master
        self.master.bind(thread_utils.OnScriptStart_Event, lambda x: self.__on_script_start_handler(x))
        self.master.bind(thread_utils.OnScriptFinish_Event, lambda x: self.__on_script_finish_handler(x))

        self.add_group_btn = ttk.Button(self.master, text="+", command=self.add_group_handler)
        self.add_group_btn.pack(side=tk.TOP, pady=5, padx=5, anchor="w")
        
        # ----------------------Footer-----------------------------
        self.footer = ttk.Frame(self.master)
        self.footer.pack(side=tk.BOTTOM, expand=True, fill=tk.X)

        # Await PTP Resynchronization
        self.await_ptp_restart_var = tk.BooleanVar()
        self.await_ptp_restart_checkbox = ttk.Checkbutton(self.footer, text="Restart PTP",
                                                              command=self.toggle_await_time_visibility,
                                                              variable=self.await_ptp_restart_var)
        self.await_ptp_restart_checkbox.grid(row=0, column=0, padx=5, pady=0)
        self.await_ptp_restart_time_label = ttk.Label(self.footer, text="Resynch timeout:")
        self.await_ptp_restart_time_entry = ttk.Entry(self.footer, width=30)
        self.await_ptp_restart_time_entry.insert(tk.END, "0") # async mode
        self.await_ptp_restart_var.set(1)
        self.toggle_await_time_visibility()

        # Verbosity
        ttk.Label(self.footer, text="Verbosity:").grid(row=0, column=3, padx=5, pady=2)
        self.verbosity_var = tk.IntVar()
        self.verbosity_combobox = ttk.Combobox(self.footer, textvariable=self.verbosity_var,
                                                         values=[0, 1, 2], width=27,
                                                         state="readonly")
        self.verbosity_combobox.grid(row=0, column=4, padx=5, pady=2)
        self.verbosity_combobox.set(1) # Default value

        # Start Button
        self.start_btn = ttk.Button(self.footer, text="Start Remote Config", command=self.start_btn_handler)
        self.start_btn.grid(row=0, column=5, padx=5, pady=2) # row + 3 to account for hidden SSH fields
        # ----------------------Footer end-----------------------------

        self.groups_canvas = tk.Canvas(self.master)
        self.groups_canvas.pack(side=tk.LEFT, expand=1, fill=tk.BOTH)

        self.groups_scrollbar = ttk.Scrollbar(self.master, orient=tk.VERTICAL, command=self.groups_canvas.yview)
        self.groups_scrollbar.pack(side = tk.RIGHT, fill = tk.Y)
        
        self.groups_canvas.config(yscrollcommand=self.groups_scrollbar.set)

        self.groups_fr = ttk.Frame(self.groups_canvas)
        self.groups_canvas.create_window((0, 0), window=self.groups_fr, anchor="nw")
        self.groups_fr.bind("<Configure>", self.__on_group_fr_configure)

        # Bind mouse wheel for scrolling on the canvas
        self.groups_canvas.bind_all("<MouseWheel>", self.__on_canvas_mousewheel) # Windows/macOS
        self.groups_canvas.bind_all("<Button-4>", self.__on_canvas_mousewheel) # Linux (scroll up)
        self.groups_canvas.bind_all("<Button-5>", self.__on_canvas_mousewheel) # Linux (scroll down)
        
        self.add_group_handler()


    def add_group_handler(self):
        group_fr = ttk.LabelFrame(self.groups_fr, text=f"Group {len(self.group_frs) + 1}")
        group_fr.pack(pady=5, padx=5, fill=tk.X)

        coef_entries = {}
        columns = 0
        labels_and_entries = [
            ("Start IP:", "start_ip"),
            ("End IP:", "end_ip"),
            ("tx:", "tx"),
            ("rx:", "rx"),
            ("alpha (opt.):", "alpha"),
            ("SFP module (opt.):", "sfp_module")
        ]

        for index, (label_text, entry_name) in enumerate(labels_and_entries):
            ttk.Label(group_fr, text=label_text).grid(row=0, column=index, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(group_fr, width=25)
            entry.grid(row=1, column=index, sticky="ew", padx=5, pady=2)
            coef_entries[entry_name] = entry
            columns = index + 1

        self.destroy_btn = ttk.Button(group_fr, text="-",
                                      command=(lambda frame=group_fr: self.destroy_btn_handler(frame)))
        self.destroy_btn.grid(row=0, column=columns, rowspan=2, sticky="ew", ipadx=5, ipady=2)

        self.coef_entries.append(coef_entries)
        self.group_frs.append(group_fr)
        group_fr.columnconfigure(tuple(range(6)), weight=1)
        group_fr.rowconfigure(tuple(range(2)), weight=1)

        self.groups_canvas.update_idletasks()
        return

    def destroy_btn_handler(self, frame):
        id = self.group_frs.index(frame)
        self.group_frs[id].destroy()
        del self.group_frs[id]
        del self.coef_entries[id]
        self.__update_group_titles()
        return

    def __update_group_titles(self):
        for index, group in enumerate(self.group_frs):
            group.config(text=f"Group {index + 1}")

    def toggle_await_time_visibility(self, *args):
        if self.await_ptp_restart_var.get():
            self.await_ptp_restart_time_label.grid(row=0, column=1, padx=5, pady=2)
            self.await_ptp_restart_time_entry.grid(row=0, column=2, padx=5, pady=2)
        else:
            self.await_ptp_restart_time_label.grid_forget()
            self.await_ptp_restart_time_entry.grid_forget()

    def start_btn_handler(self):
        """Handler for the Start button on the Remote config tab."""
        print_utils.print_untagged("\n--- Start Remote Configuration ---", 0)
        all_groups_data = []
        for index, entries_group in enumerate(self.coef_entries):
            data_group = {}
            for entry_name, entry_widget in entries_group.items(): # retrieveing values
                data_group[entry_name] = entry_widget.get()
            all_groups_data.append(data_group)

        is_log_cleared = False

        for data_group in all_groups_data:
            ips_file_path = "./temp.ips"
            start_ip = data_group["start_ip"]
            end_ip = data_group["end_ip"]
            tx = data_group["tx"]
            rx = data_group["rx"]
            alpha = data_group["alpha"]
            print_utils.print_info(f"Configuring devices from {start_ip} to {end_ip}", 0)
            if not ip_utils.is_ip_valid(start_ip):
                print_utils.print_error(f"Invalid start IP: {start_ip}. Expected format is 2.22.215.05")
                return
            if not ip_utils.is_ip_valid(end_ip):
                print_utils.print_error(f"Invalid end IP: {end_ip}. Expected format is 2.22.215.05")
                return
            
            if tx == "":
                print_utils.print_error(f"Invalid tx coefficient: {tx}. Expected integer value")
                return
            
            if rx == "":
                print_utils.print_error(f"Invalid rx coefficient: {rx}. Expected integer value")
                return

            with open(ips_file_path, "w") as f:
                for ip in ip_utils.generate_ip_list(start_ip, end_ip):
                    f.write(f"{ip}\n")
            
            args = []
            args.extend(["-f", ips_file_path])
            
            verbosity = self.verbosity_var.get()
            if verbosity> 0:
                args.append(f"-{'v' * verbosity}")
            
            sfp = data_group["sfp_module"]
            if sfp != "":
                args.extend(["--sfp", sfp])
            
            log_file_path = "run.log"
            if not is_log_cleared:
                open(log_file_path, "w").close()
                is_log_cleared = True
            
            args.extend(["-l", log_file_path])

            rs = self.await_ptp_restart_var.get()
            if rs:
                args.append("-rs")
                args.extend(["--wait", self.await_ptp_restart_time_entry.get()])
            args.extend(["-nm", "CUTE_A7"])
            args.append(tx)
            args.append(rx)
            if alpha != "":
                args.append(alpha)
            else:
                args.append("0")

            pid = thread_utils.run_script_in_bg(
                func=remote_config.main,
                args=args,
                gui=self.master,
                stop_event=self.terminate_threads_event
            )
            self.threads.append(pid)
        return

    def __on_group_fr_configure(self, event):
            """Update the scroll region when the inner frame's size changes."""
            self.groups_canvas.configure(scrollregion=self.groups_canvas.bbox("all"))

    def __on_canvas_mousewheel(self, event):
        """Handle mouse wheel scrolling for the canvas."""
        if event.delta: # Windows/macOS
            self.groups_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        else: # Linux
            if event.num == 4:
                self.groups_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.groups_canvas.yview_scroll(1, "units")

    
    def __on_script_finish_handler(self, *args):
        enablement_control.enableChildren(self.master)
        self.threads.clear()

    def __on_script_start_handler(self, *args):
        enablement_control.disableChildren(self.master)

