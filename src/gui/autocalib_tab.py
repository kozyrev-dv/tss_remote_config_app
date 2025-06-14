import tkinter as tk
from tkinter import ttk 
import threading

from ..scripts import calib_refine
from ..utils import threading as thread_utils
from ..utils import print as print_utils
from .utils import enablement_control
class AutocalibTab(object):
    def __init__(self, master = None, **kwargs):
        self.terminate_threads_event = threading.Event()
        calib_refine.assign_calib_refine_stop_event(self.terminate_threads_event)
        self.threads = []
        # ----------------------Visible Frame-----------------------------
        self.master = master
        self.master.bind(thread_utils.OnScriptStart_Event, lambda x: self.__on_script_start_handler(x))
        self.master.bind(thread_utils.OnScriptFinish_Event, lambda x: self.__on_script_finish_handler(x))
        # ----------------------Visible Frame-----------------------------
        self.visible_fields_fr = ttk.Frame(self.master)
        self.visible_fields_fr.pack(side=tk.TOP, expand=True, pady=3, fill=tk.X)
        self.visible_fields_fr.columnconfigure(index=tuple(range(4)), weight=1)
        self.visible_fields_fr.rowconfigure(index=tuple(range(5)), weight=1)
        # Use grid for flexible element placement
        row = 0

        # Instrument IP
        ttk.Label(self.visible_fields_fr, text="Instrument IP:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.ip_entry = ttk.Entry(self.visible_fields_fr, width=30)
        self.ip_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=2)

        # Instrument model
        ttk.Label(self.visible_fields_fr, text="Instrument model:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        self.instr_model_var = tk.StringVar()
        self.instr_model_combobox = ttk.Combobox(self.visible_fields_fr, textvariable=self.instr_model_var,
                                                     values=["rto2000"], width=27,
                                                     state="readonly")
        self.instr_model_combobox.grid(row=row, column=3, sticky="ew", padx=5, pady=2)
        self.instr_model_combobox.current(0)
        row += 1
        
        # iterations.
        ttk.Label(self.visible_fields_fr, text="iterations:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.iterations_entry = ttk.Entry(self.visible_fields_fr, width=30)
        self.iterations_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        self.iterations_entry.insert(tk.END, "5")

        # time/iteration
        ttk.Label(self.visible_fields_fr, text="time/iteration:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        self.time_iteration_entry = ttk.Entry(self.visible_fields_fr, width=30)
        self.time_iteration_entry.grid(row=row, column=3, sticky="ew", padx=5, pady=2)
        self.time_iteration_entry.insert(tk.END, "300")
        row += 1

        # WR-Node port num
        ttk.Label(self.visible_fields_fr, text="WR-Node port num:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.wr_node_port_entry = ttk.Entry(self.visible_fields_fr, width=30)
        self.wr_node_port_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        self.wr_node_port_entry.insert(tk.END, "0")
        row += 1

        # ttyUSB index (optional)
        ttk.Label(self.visible_fields_fr, text="ttyUSB index (opt.):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.ttyusb_index_entry = ttk.Entry(self.visible_fields_fr, width=30)
        self.ttyusb_index_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        row += 1

        # Oscilloscope WR-Switch ch. (optional)
        ttk.Label(self.visible_fields_fr, text="Oscilloscope ch.: WR-Master (opt.):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.wr_switch_ch_entry = ttk.Entry(self.visible_fields_fr, width=30)
        self.wr_switch_ch_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=2)

        # Oscilloscope WR-Node ch. (optional)
        ttk.Label(self.visible_fields_fr, text="WR-Slave(opt.):").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        self.wr_node_ch_entry = ttk.Entry(self.visible_fields_fr, width=30)
        self.wr_node_ch_entry.grid(row=row, column=3, sticky="ew", padx=5, pady=2)
        row += 1

        # ----------------------Frame end-----------------------------
        # ---------------------- Toggleble crtt Frame-----------------------------
        self.crtt_calib_fr = ttk.Frame(self.master)
        self.crtt_calib_fr.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.crtt_calib_fr.columnconfigure(index=1, weight=1)

        # Enable crtt calibration
        self.enable_crtt_calib_var = tk.BooleanVar()
        self.enable_crtt_calib_checkbox = ttk.Checkbutton(self.crtt_calib_fr, text="Enable crtt calibration",
                                                              command=self.toggle_crtt_fields,
                                                              variable=self.enable_crtt_calib_var)
        self.enable_crtt_calib_checkbox.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=0)

        # crtt calibration time (optional)
        self.crtt_calib_time_label = ttk.Label(self.crtt_calib_fr, text="crtt calibration time:")
        self.crtt_calib_time_entry = ttk.Entry(self.crtt_calib_fr, width=30)
        self.crtt_calib_time_entry.insert(tk.END, "60")
        self.toggle_crtt_fields()

        # ----------------------Frame end-----------------------------
        # ---------------------- Toggleble SSH Frame-----------------------------

        self.ssh_fr = ttk.Frame(self.master)
        self.ssh_fr.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.ssh_fr.columnconfigure(index=1, weight=1)

        # Enable SSH checkbox
        self.enable_ssh_var = tk.BooleanVar()
        self.enable_ssh_checkbox = ttk.Checkbutton(self.ssh_fr, text="Enable SSH",
                                                              command=self.toggle_ssh_fields,
                                                              variable=self.enable_ssh_var)
        self.enable_ssh_checkbox.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=0)

        # SSH fields (initially hidden)
        self.ssh_host_name_label = ttk.Label(self.ssh_fr, text="ssh-host name:")
        self.ssh_host_name_entry = ttk.Entry(self.ssh_fr, width=30)
        self.ssh_password_label = ttk.Label(self.ssh_fr, text="ssh password:")
        self.ssh_password_entry = ttk.Entry(self.ssh_fr, show="*", width=30)
        self.ssh_root_password_label = ttk.Label(self.ssh_fr, text="ssh-host root password:")
        self.ssh_root_password_entry = ttk.Entry(self.ssh_fr, show="*", width=30)

        self.toggle_ssh_fields() # Hide on initialization

        # ----------------------Frame end-----------------------------
        # ----------------------Footer-----------------------------
        # Verbosity
        self.footer = ttk.Frame(self.master)
        self.footer.pack(side=tk.BOTTOM, expand=True, fill=tk.X)

        ttk.Label(self.footer, text="Verbosity:").pack(expand=True, side=tk.LEFT, padx=5, pady=2)
        self.verbosity_var = tk.IntVar()
        self.verbosity_combobox = ttk.Combobox(self.footer, textvariable=self.verbosity_var,
                                                         values=[0, 1, 2], width=27,
                                                         state="readonly")
        self.verbosity_combobox.pack(side=tk.LEFT, expand=True, padx=5, pady=2)
        self.verbosity_combobox.set(1) # Default value

        # Start Button
        self.start_btn = ttk.Button(self.footer, text="Start Autocalib", command=self.start_btn_handler)
        self.start_btn.pack(side=tk.LEFT, expand=True, padx=5, pady=2) # row + 3 to account for hidden SSH fields
        # ----------------------Footer end-----------------------------

    def toggle_crtt_fields(self):
        if self.enable_crtt_calib_var.get():
            self.crtt_calib_time_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
            self.crtt_calib_time_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        else:
            self.crtt_calib_time_label.grid_forget()
            self.crtt_calib_time_entry.grid_forget()
        return
    
    def toggle_ssh_fields(self):
        # Dynamically show/hide SSH fields
        if self.enable_ssh_var.get():
            self.ssh_host_name_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
            self.ssh_host_name_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

            self.ssh_password_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
            self.ssh_password_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

            self.ssh_root_password_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
            self.ssh_root_password_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        else:
            self.ssh_host_name_label.grid_forget()
            self.ssh_host_name_entry.grid_forget()
            self.ssh_password_label.grid_forget()
            self.ssh_password_entry.grid_forget()
            self.ssh_root_password_label.grid_forget()
            self.ssh_root_password_entry.grid_forget()

    def start_btn_handler(self, *args):
        """Handler for the Start button on the Autocalib tab."""
        # Here you will collect data from the fields and form the command to run.
        # For example, we will just print the collected data to the console.
        
        print_utils.print_untagged("\n--- Start Automated Calibration ---", 0)
        
        params = {
            "instrmodel": self.instr_model_var.get(),
            "instrip": self.ip_entry.get(),
            "time": self.time_iteration_entry.get(),
            "iter": self.iterations_entry.get(),
            "wrndsfp": self.wr_node_port_entry.get(),
            "--ttyUSB": self.ttyusb_index_entry.get(),
            "--crtt": self.crtt_calib_time_entry.get(),
            "--wfrchsw": self.wr_switch_ch_entry.get(),
            "--wfrchnode": self.wr_node_ch_entry.get(),
            "-v": self.verbosity_var.get(),
            "-s": self.enable_ssh_var.get()
        }
        calib_args = []
        def add_required(key:str, flagged=False) -> bool:
            """Returns False if error encountered"""
            if params[key] is None or params[key] == "":
                print_utils.print_error(f"Parameter {key} is expected. None set")
                return False
            if (flagged):
                calib_args.append(key)
            calib_args.append(params[key])
            return True
        
        def add_optional(key:str):
            if params[key] != "":
                calib_args.append(key)
                calib_args.append(params[key])
            return
        
        parsing_res = add_required("instrmodel")
        parsing_res &= add_required("instrip")
        parsing_res &= add_required("time")
        parsing_res &= add_required("iter")
        parsing_res &= add_required("wrndsfp")
        if (not self.enable_crtt_calib_var.get()): # disable crtt calib and coef reset 
            params["--crtt"] = "-1" 
        parsing_res &= add_required("--crtt", flagged=True) #I MUST ensure the crtt is set whatever value if Enable crtt on.
                               # Else bug: "" provided -> 60 sec set, which is not obvious

        if params["-v"] > 0:
            calib_args.append(f"-{'v'*params['-v']}")
        add_optional("--ttyUSB")
        add_optional("--wfrchsw")
        add_optional("--wfrchnode")
        if params["-s"]:
            calib_args.append("-s")
            params["--sshhostname"] = self.ssh_host_name_entry.get()
            params["--sshpwd"] = self.ssh_password_entry.get()
            params["--sshhostrootpwd"] = self.ssh_root_password_entry.get()
            parsing_res &= add_required("--sshhostname", flagged=True)
            parsing_res &= add_required("--sshpwd", flagged=True)
            add_optional("--sshhostrootpwd")

        if (not parsing_res):
            return
        # for item in calib_args:
        #     print_utils.print_untagged(item, 2)

        pid = thread_utils.run_script_in_bg(
            func=calib_refine.main,
            args=calib_args,
            gui=self.master,
            stop_event=self.terminate_threads_event
            )
        self.threads.append(pid)

    def __on_script_finish_handler(self, *args):
        enablement_control.enableChildren(self.master)
        self.threads.clear()

    def __on_script_start_handler(self, *args):
        enablement_control.disableChildren(self.master)
        
