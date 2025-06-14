# TSS remote configuration GUI application

This Project aims to collect several scripts for automated calibration and confiuration in one UI-based programm.

## Sources

WR-SWITCH-MIB.txt and WR-WRPC-MIB.txt files in ./src/mibs folder are taken from CERN repositories.
- WRPC: [wrpc-sw repo, br. master](https://gitlab.cern.ch/white-rabbit/wrpc-sw)
- SWITCH: [wr-switch-sw, br. master](https://gitlab.com/ohwr/project/wr-switch-sw/)

## To Use

Before executing the script install the packages from requirements.txt file `pip install -r ./requirements.txt`.
For GUI install Tkinter ([](https://docs.python.org/3/library/tk.html)) via: `sudo apt-get install python3-tk`. The project uses version 3.12.3-0ubuntu1 for running the script.

Installing R&S VISA is also required. For Windows VISA or other VISA's distributions installers see: https://www.rohde-schwarz.com/us/applications/r-s-visa-application-note_56280-148812.html. The project uses v7.2.3 of the VISA downloaded with all default settings.

***calib_refine:***
```
usage: calib_refine [-h] [--ttyUSB TTYUSB] [--dtcs DTCS] [--crtt CRTT] [--wfrchsw WFRCHSW] [--wfrchnode WFRCHNODE] [-v] [-s] [--sshhostname SSHHOSTNAME] [--sshpwd SSHPWD] [--sshhostrootpwd SSHHOSTROOTPWD]
                    {rto2000} instrip time iter wrndsfp

refine calibration data of WR-node via dedicated oscilloscope (RTO 2000 supported only) and direct to WR-Node or SSH access to remote server connected to WR-Node

positional arguments:
  {rto2000}             oscilloscope model which API to access
  instrip               oscilloscope's IP to connect to
  time                  time per calibration iteration
  iter                  number of iterations for calibration
  wrndsfp               WR-node SFP port number to use for calibration

options:
  -h, --help            show this help message and exit
  --ttyUSB TTYUSB       ttyUSB port number to connect on the linux-running server
  --dtcs DTCS           Data Transfer Chunk Size to use while sending measurements to controlling device
  --crtt CRTT           crtt calibration time in seconds. Passing -1 disables crtt reset and calibration; 0 resets coefs, but doesn't calibrate crtt. Default: 60 sec
  --wfrchsw WFRCHSW     oscilloscope channel the WR-Switch is connected to
  --wfrchnode WFRCHNODE
                        oscilloscope channel the WR-Node is connected to
  -v, --verbosity       increase output verbosity
  -s, --ssh             Enable SSH connection to PC connected to calibrated WR-Node
  --sshhostname SSHHOSTNAME
                        IP address of remote server the WR Node is connected to. (required if --ssh is set)
  --sshpwd SSHPWD       password to use for connecting via SSH. (required if --ssh is set)
  --sshhostrootpwd SSHHOSTROOTPWD
                        password to use for login as root on host. Default: equals to sshpwd. (required if --ssh is set)
```

***remote_config:***
```
usage: remote_config [-h] [-ip IP | -f FILE] [--sfp SFP] [-v] [-l LOG] [-rs] [--wait WAIT] [-nm NODEMODEL] tx rx alpha

Remote configuration of calibration coefficients of the WR-Node in network via SNMP

positional arguments:
  tx                    tx delay coefficient
  rx                    rx delay coefficient
  alpha                 fiber assymetry coefficient

options:
  -h, --help            show this help message and exit
  -ip IP                target IP-address to config
  -f FILE, --file FILE  file of IP-addresses to config
  --sfp SFP             SFP PN to set the coefficients to. If none supplied, coefficients are applied to the current inserted
  -v, --verbosity       increase output verbosity
  -l LOG, --log LOG     path to output file for logging the application results to
  -rs, --resync         restart PTP with applied coefficients
  --wait WAIT           wait time in secods for resynchronization after PTP restart. Default: 0 sec - wait is turned off
  -nm NODEMODEL, --nodemodel NODEMODEL
                        specify node model for platform specific coefficient calculations
```

