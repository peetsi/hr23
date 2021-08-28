#!/usr/bin/env python3

# 1. script starts
# 2. waits for usb connection from a usb stick with the name "pythonUSB"
# 3. moves files to Desktop/Monitor/pythonUSB
# 4. run files, exits script.

# add this file to startup applications Dashboard > Startup Applications > Add
# this should be perfectly fine with the watchdog, as if he does reset the pi
# the script will itself reboot and then copy all the required files from the usb stick again
# as soon as he does find the "pythonUSB" plugged it.
# he then does start the software and all the required things and then shut down

# MAYBE ADD MAKE A SECOND WATCHDOG OUT OF THIS, WHICH DOES MONITOR ALL THE FILES AND THEIR FUNCTIONALITY..

import os, sys, stat
import shutil
import subprocess
import time
import psutil
from subprocess import Popen

USE_LAST_STABLE_VERSION = False

if os.environ.get('DISPLAY','') == '':
    print('no display found. Using :0.0')
    os.environ.__setitem__('DISPLAY', ':0.0')

#--
# vars
#--
pythonUSBname           = "PYTHONUSB"
target_folder           = "/home/pi/Desktop/Monitor"
pythonUSBpath           = "/media/pi/"+pythonUSBname
if USE_LAST_STABLE_VERSION == False :
    move_to_desktop_folder  = "/move_to_desktop.monitor_on_boot"
else :
    move_to_desktop_folder  = "/move_to_desktop.monitor_on_boot/_fallback_stable_version"
logfolder               = "log"
logfile                 = "loglog.txt"
start_script_path       = target_folder+"/"+pythonUSBname

excluded = ["media_extern"]
# CHANGE TO THE REQUIRED SCRIPTS FOR FIRST BOOT!!
logpath = pythonUSBpath + move_to_desktop_folder + logfolder + logfile
#scripts_to_run = [ "python3 "+target_folder+"/pythonUSB/menue01.py >> " + logpath, target_folder+"/pythonUSB/hz_rr_log_start2.sh" ]

scripts_to_run = [start_script_path + "/main.py", ]
# [ start_script_path +"/menue01.sh", \
 #               start_script_path +"/hz_rr_log_start2.sh" ]
#--
#exit(0)


def get_mountedlist():
    return [(item.split()[0].replace("├─", "").replace("└─", ""),
             item[item.find("/"):]) for item in subprocess.check_output(
            ["/bin/bash", "-c", "lsblk"]).decode("utf-8").split("\n") if "/" in item]

def identify(disk):
    command = "find /dev/disk -ls | grep /"+disk
    output = subprocess.check_output(["/bin/bash", "-c", command]).decode("utf-8")
    if "usb" in output:
        return True
    else:
        return False

def run_bash(file, dopython=0):
    print("starting:", file)
    if (dopython==1):
        return subprocess.Popen("sudo python3 " + file, shell=True)
    #return subprocess.Popen( "sudo /bin/bash " + file, shell=True)
    return os.system("sudo /bin/bash " + file)

def run_cmd(cmd):
    print("executing:", cmd)
    return os.system(cmd)

def set_perm(f):
    ''' *pl* set permissions for file f '''
    try:
        #output = subprocess.check_output("sudo chmod u+rx " + f).decode("utf-8")
        #print("chmod", f, "to", stat.S_IRWXU) # *pl* wrong - octal numbers
        print("chmod %s to %o"%(f, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH))
        output = os.chmod(f, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH )
    except Exception as e:
        print("error setting permissions for file ", f)
        print("error: ",e)
        #print("output: ", output)
    return 0

def init_watchdog():
    # requirements:
    # apt-get install watchdog
    print("init watchdog")
    #run_cmd("sudo modprobe bcm2835_wdt")
    print("trying to install watchdog if not yet installed.")
    run_cmd("sudo apt-get install watchdog")
    print("updating watchdog defaults:", run_cmd("sudo update-rc.d watchdog defaults."))
    print("copying watchdog.conf and replacing the old one.")
    wdog_path="/etc/"
    wdog_conf_old="watchdog.conf"
    wdog_conf_new=targetPath+move_to_desktop_folder+"/"+wdog_conf_old
    print("new file:", wdog_conf_new)
    print("remove old conf file..:", run_cmd("sudo rm -f " + wdog_path + wdog_conf_old))
    print("moving new conf file..:", run_cmd("sudo cp " + wdog_conf_new +" "+wdog_path + wdog_conf_old))
    print("done")

def start_watchdog():
    print("moving on to init whatdog now...")
    print("return=", init_watchdog())
    print("starting watchdog.py - writes to watchdog every 13 seconds.")
    print("return=", run_bash(target_folder+"/"+pythonUSBname+"/watchdog.py",1))

def process_exists(n):
    for process in psutil.process_iter():
        cmdline = process.cmdline()
        if type(cmdline) is list:
            if any(n in s for s in cmdline):
                print("any(n in s for s in cmdline)",any(n in s for s in cmdline))
                return True
        else:
            return (cmdline.find(n))
    return False # not found

def run_and_check_for_scripts(scripts_to_run):
    for process in psutil.process_iter():
        if process_exists("main.py"):
            #print ("found process:\r",process.cmdline())
            #print ("['python3', '/home/pi/Desktop/Monitor/pythonUSB/menue01.py'] == process.cmdline() ? = ",(process.cmdline()==['python3', '/home/pi/Desktop/Monitor/pythonUSB/menue01.py']))
            ##found process
            #print("found process menu01.py already running!")
            return 1

    # not found - restart.. script
    print("could not find menue01.py - restarting it...")
    run_scripts(scripts_to_run)
    return 0

def run_scripts(scripts_to_run):
    for text in scripts_to_run:
        cur_tar = text
        try:
            set_perm(cur_tar)
            #run_bash(cur_tar + " start")
            print("current target:",cur_tar )
            print('[RUN_AS](cur_tar.find(".py") > 0) =', (cur_tar.find(".py") > 0))
            if (cur_tar.find(".py") > 0):
                print("[PY]starting %s as python"%cur_tar)
                run_bash( cur_tar, 1)
            else:
                print("[BASH]starting %s as bash"%cur_tar)
                run_bash( cur_tar + " start")
        except Exception as e:
            print("Error while trying to run script. ", e)

def hotfixing():
    # this is pure hotfixing...
    #adding xhost to the list of allowed hosts
    # *pl* ??? why is this necessary?
    print("adding xhost +local:")
    run_cmd('xhost +local:')
    # yet another hotfix. without this the tinker does crash 
    # becuase of missing permissions.
    #print("creating watch window")
    #run_cmd("watch systemctl status starthzrr.service")
    print("* giving xauthority root permission")
    run_cmd("sudo cp ~/.Xauthority ~root/")
    run_cmd("sudo cp /home/pi/.Xauthority ~root/")
    print("done")


# *pl* made function from inline code
def make_target_dir(targetPath):
    ''' make target directory if it does not exist '''
    print("making target directroy %s ..."%(targetPath),end="")
    cmd = "mkdir -p %s"%(targetPath)
    #print(cmd)
    run_cmd(cmd)
    print("done")

# *pl* made function from inline code
def waitfor_usbstick( pythonUSBname):
    ''' check for USB-stick being present *BLOCKING* '''
    print("waiting for USB-stick %s ... "%(pythonUSBname),end="")
    ready = False
    while (not ready):
        mounted = get_mountedlist()
        print(mounted)
        for mount in mounted:
            if pythonUSBpath in mount[1] :
                valid=mount
                ready=True
                break
        if (not ready):
            print("\nUSB-stick not found.. wait & sleep for 2 seconds")
            time.sleep(2)
    print("found python usb '", valid, "'")

# *pl* made function from inline code
def copy_files2target(targetPath):
    ''' copy files from USB-stick to target directory *BLOCKING* 
         and change owner to user 'pi' '''
    while True:
        print("copying files from usb to target directory, please wait...",end="")
        try:
            shutil.copytree(pythonUSBpath+move_to_desktop_folder, targetPath)
            print("done")
            break
        except Exception as e:
            print("error copying files to target.", e)
            time.sleep(2.0)
    # *pl* added: set owner of copied files to user pi
    cmd = "sudo chown -hR pi:pi " + target_folder
    #print(cmd)
    run_cmd(cmd)
    print("done;")


done = []
ready = False
found_pythonUSB=0
hotfixing()
# *pl* heavily changed and optimized

# *pl* Wait for USB-Stick named "PYTHONUSB" is mounted
#      BLOCKING !!!
waitfor_usbstick( pythonUSBname)

targetPath = target_folder+"/"+pythonUSBname+"/"

# remove all files from target
print("removing old files if available")
cmd="sudo rm -rf " + targetPath
try:
    run_cmd(cmd) 
    print("done")
except FileNotFoundError:
    print("old files not found")

# *pl* added:
# make_target_dir(targetPath) --- performed by "shutil.copytree" below
copy_files2target(targetPath)

#done = mounted
print("settings permission and starting up the required scripts:")
print(scripts_to_run)
run_scripts(scripts_to_run)

print("script seem to have loaded. lets check.. in 10 seconds")
time.sleep(10)
run_and_check_for_scripts(scripts_to_run)
start_watchdog()

print("everything seems to have completed correctly...")
did_work=1
print("going stuck now in an endless loop of pain, watching the menue01.py for its existence - and if it does not exist anymore - it will be forcefully brought back to life.")

#print("starting monitor")
#run_bash(start_script_path +"/hz_rr_monitor_direct02_b.py",1)

#endless looop
while (run_and_check_for_scripts(scripts_to_run) != -1):
    time.sleep(60)

exit(0)


