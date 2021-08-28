'''
=========================================
RPi4: setup and commandline commands
=========================================

1. general settings
===================
a.  <app> is a dirctory holding software and data files and folders
    it is "move_to_desktop.monitor_on_boot"
b.  <app-path> = "/media/pi/PYTHONUSB/<app>"
c.  the startup script 
    "<app-path>/move_files_from_usb_and_boot_them.py"
    performs the following tasks:

2. startup procedure
====================

2.1. startup script
-------------------
a.  after Raspberry Pi 4 (RPi) boot the startup script is started
b.  NOTE: to estabilish this, copy the following file once when
          installing/setting up the RPi SD-card
    "sudo cp <app-path>/starthzrr.service /etc/systemd/system/"
c.  the startup script finally start ...../main.py which keeps all
    processes running - if they happen to be closed due to e.g. an error
d.  after boot it performs several steps described below:
    
2.2. watchdog control
---------------------
a. sudo copy "<app-path>/watchdog.conf" to "/etc/"
    performed by the startup-script
b. start/stop/status with the commands:
    "sudo systemctl start watchdog" (performed by startup-script)
    to control the watchdog use:
    "sudo systemctl stop watchdog"
    "sudo systemctl status watchdog"
c.  NOTE: before stopping the application task
          make sure to stop the watchdog first
d.  NOTE: the program "watchdog.py" starts the watchdog
          and keeps permanently running feeding it.
          Thus the WD is permanently restarted.
          to avoid ths, change the "watchdog.py"
          by executing a "sys.exit(0)" at top of the program
          (import sys)
e.  NOTE: NOT FORGET removing the above to use WD again

2.2. hzrr application control
-----------------------------
a.  handling the application software:
    sudo systemctl start starthzrr.service
    sudo systemctl stop starthzrr.service
    sudo systemctl status starthzrr.service
b.  NOTE: stop the watchdog (see above) before stopping .service






'''