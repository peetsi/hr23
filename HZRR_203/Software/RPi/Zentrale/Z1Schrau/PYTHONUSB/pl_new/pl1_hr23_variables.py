#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# variables combined in classes

import sys
import platform
import time
import configparser
import vorlaut as vor


'''
********************
   system info
********************
'''
'''
SD-card protection information:
-------------------------------
he SD-card cannot stand many writes - wears with time
so data will be logged to a USB-FLASH memory
best is to invoke the RAM-Filesystem on the RPi to protect SD in final installation
Where data has to be stored is defined in the "pl1_hr23_config.ini" file


.ini files:
-----------
Most system relevant data is stored in .ini files:
    hr23_config.ini         for application software (RPi) data
                            this file is in a fixed file, relative to the current
                            directory  "config/pl1_hr23_config.ini"
    heizkreis.ini           for heizkreis configuration, modules etc
'''






'''
***************************************************
Globale Variable, Klassen etc.
***************************************************
'''
progName = "hr2"
progRev = "2.3.0"
PROT_REV = "b"      # protocol revision for hzrr200

# *** configuration parameters in .ini files:
co=configparser.ConfigParser()  # application and implementation data
hk=configparser.ConfigParser()  # Heizkreis specific data

si = {}                         # system information

modules=[]



'''
***************************************************
            ZENTRALE APPLICATION DATA
***************************************************
'''
def hr_init():
    '''initialize global variables for whole application'''
    global co, hk, si
    
    # *** SYSTEM CONFIGURATION
    co.read("config/pl1_hr23_config.ini")

    #hostNameFile = co["system"]["hostNameFile"]

    # *** system information
    si["hostname"]  = get_hostname()              
    si["opsys"]     = platform.system()    # "Linux",

    # *** log-file info
    if si["hostname"]=="testhost":
        si["logpath"]="log/"        # relative to current dir
    elif "True" in co["system"]["logOnUSB"]:
        si["logPath"]=co["system"]["logPath_USB_LINUX"]
    else:
        si["logPath"]=co["system"]["logPath_local_LINUX"]
    
    
    # *** HEIZKREIS CONFIGURATION    
    # read file-name with heizkreis configuration data
    fromUSB = co["system"]["confUSB"]    
    if si["hostname"]=="testhost":
        confHkFile = "config/heizkreis.ini"
    elif "True" in fromUSB:
        confHkFile = co["system"]["confPath_USB_linux"]
    else:
        confHkFile = co["system"]["confPath_local_linux"]
    # read configuration file
    ans=hk.read(confHkFile)
    print(ans)
    print(hk.sections())
    













'''
***************************************************
                    MODULE DATA
***************************************************
'''

'''
Data organization:
==================
1. Module Data
--------------
There are two main types of operation data:
S: Status information which shows state- or measured values
P: Parameter data which can be stored in EEPROM in the modules
S and P are kept in separate data structures in the Modules and here.

Up to 30 modules can be connected in one RS-485 Network.
Each Module contains 3 Regulators 1,2,3 or index 0,1,2; 
- all regulators are normally 'Ruecklaufregler'
- reg1 (idx=0) is always set to active; 
- reg2 or reg3 (idx=1 or =2) may be activated by jumper settings on PCB
- reg2 (idx=1) may be switched to regulate a room-temperature; selected by jumper settings.

The data structures are set accordingly:
A list of up to 30 modules with module-related data, each contains a list with
tree regulator data sets is defined for each S (status) and P (parameters).

1.1. Status data (S)
- - - - - - - - - - -
- can be read from the modules
- are stored in intervals to a log-file
- are diplayed on demand on the screen

1.2. Parameter data (P)
- - - - - - - - - - - -
- handling insinde a module by commands:
  - set to factory settings (data reside in RAM)
  - store actual setting in RAM to EEPROM
  - read from EERPOM to actual setting in RAM
- transfer Parameter between module and Zentrale:
  - read parameter from module RAM to Zentrale
  - write parameter from Zentrale to module RAM
  - store parameter of a module to a file in Zentrale
  - read parameter of a module from file in Zentrale
  - The parameter files ar ein radable form and may be set manually.

1.3. Module parameter data handling:
- - - - - - -- - - - - - -- - - - - -
- After start the module software tries to read parameter data from EEPROM into RAM.
- If this fails, it reads parameter from FLASH memory to RAM and stores them to EEPROM.
- RAM parameter data can be changed from Zentrale with specific commands, e.g. for tests
- another command stores the RAM parameter to EEPROM to make them permanent after a new-start
- another command reads EEPROM data to RAM to recover its original stat
- another command sets RAM-data to factory settings.

1.4. typical parameter data operations
- - - - - - -- - - - - - -- - - - - - -
- reset parameter in module to factory setting
- send changed parameter from Zentrale to Module RAM;
  changed parameter will be lost after a new-start of Module (rest, watchdog, power-dwon)
- copy parameter in Module RAM to Module EEPROM makes changes permanent
NOTE: save data to EEPROM with an explicit command to make changes permanent.


2. Data transfer via RS485 Network
==================================
Another dictionary holds data for sending and receiving via the RS485 network with the modules

'''


'''
******************
  MODULE STATUS
******************
'''


# *** regulator status data for one regulator
rst = {
    # Values received from command nr.2
    # was cn2{}:
    "tic2": 0,      # sec   time when data cmd 2 was received
    "SN"  : '-',    # 'S'ummer or 'W'inter operation mode (was used in hr1)
    # following temperatures are set to -9.9 if they are not valid; 
    "VM"  : -9.9,  # degC; Vorlauf Temperatur, gemessen
    "RM"  : -9.9,  # degC; Ruecklauf Temperatur, gemessen
    "VE"  : -9.9,  # degC; Vorlauf Tmeperatur effektiv, von Regler verwendet
    "RE"  : -9.9,  # degC; Ruecklauf Temperatur effektiv, von Regler verwendet
    "RS"  : -9.9,  # degC; Ruecklauf Temperatur soll
    "PM"  : -100,  # %0;   Position Motor-Ventil; e {0...999}
    # command nr.3 is skipped - was used in version 1.0 of HZ-RR project
    # Values received from command nr.4
    # was cn4{}
    "tic4":  0,     # sec   time when data cmd 4 was received
    "ER"  :  0,     # 1;    Error-Message Flags
    "FX"  :  0,     # 1;    e {MOT_STOP, MOT_STARTPOS, MOT_CLOSE or MOT_OPEN}
                    #       e {20,       41,           21,          22      } 
                    #       ("last direction");
    "MT"  :  0.0,   # sec;  total motor running time since power on
    "NL"  :  0,     # 1;    number of motor driving to limit
    "NB"  :  0,     # 1;    number of boots TODO tbd
}

# module status data for one module including 3 regulators
stat = {
    "rxMs"      :  0,   # msec; received timestamp from module  
    "MotConn"   :  0,   # 1     motor connected -> 1
    "MotImA"    :  0,   # mA;   last measured motor current 
    "jumpers"   :  0,   # 1     jumper settings
    "r" : [ rst for i in range(3) ], # status of 3 built-in regulators
}

stats = [stat for i in range(31)]   # index 0 is unused -> index = module number

''' 
******************
 MODULE PARAMETER
******************
'''

# *** Parameter for the modules

'''
// calculate Ruecklauf temperature from given Vorlauf temperature
// following a polygon shaped characteristic curve (Kennlinie)
// determined by a lint through the points from (tv0,tr0) to (tv1,tr1) 
//
// tr1|- - - - - - - +-----
//    |             /:
//    |           /  :
//  y |- - - - -+    :
//    |       / :    :
// tr0|----+/   :    :
//    |    :    :    :
//    |    :    :    :
//    +---------+----------
//       tv0   tv   tv1
// 
'''
# *** Parameter for each regulator
# following lines are a shortcut of all dictionary names; copy for easier programming:
    # valve motor
    #"active":"motIMin":"motIMax":"tMotDelay":"tMotMin":"tMotMax":"dtOpen":"dtClose":
    #"dtOffset":"dtOpenBit":"tMotTotal":"nMotLimit":  
    # regulation
    #"pFakt":"iFakt":"dFakt":"tauTempVl":"tauTempRl":"tauM":"m2hi":"m2lo":"tMotPause":
    #"tMotBoost":"dtMotBoost":"dtMotBoostBack":"tempTol":
parReg = {
    # valve motor
    "active":        1,     # uint8_t;   0=inactive; 1=Ruecklauf;
    "motIMin":       6,     # int16_t;   mA;   above: normal operation; below: open circuit 
    "motIMax":      70,     # int16_t;   mA;   above: mechanical limit; 2x: short circuit
    "tMotDelay":    80,     # int16_t;   ms;   motor current measure delay; (peak current)
    "tMotMin":     100,     # uint16_t;  ms;   minimum motor-on time; shorter does not move
    "tMotMax":      40,     # uint8_t;   sec:  timeout to reach limit; stop if longer
    "dtOpen":       28,     # uint8_t;   sec;  time from limit close to limit open
    "dtClose":      30,     # uint8_t;   sec;  time from limit open to limit close
    "dtOffset":   3000,     # uint16_t;  ms;   time to open valve a bit when close-limit reached#
    "dtOpenBit":   500,     # uint16_t;  ms;   time to open valve a bit when close-limit reached
    "tMotTotal":   0.0,     # float;     sec;  total motor-on time 
    "nMotLimit":     0,     # uint16_t;  1;    count of limit-drives of motor
    # regulation
    "pFakt":       0.033,   # float;     s/K;  P-factor; motor-on time per Kelvin diff. (*)
    "iFakt":       0.0,     # float;     1/K;  I-factor;
    "dFakt":       0.0,     # float;     s^2/K D-factor; 
    "tauTempVl":  300.0,    # float;     sec;  reach 1/e; low-pass (LP) filter Vorlauf
    "tauTempRl":  180.0,    # float;     sec;  reach 1/e; LP filter Ruecklauf (RL)<
    "tauM":       120.0,    # float;     sec;  reach 1/e; LP filter slope m
    "m2hi":       40.0,     # float;     mK/s; up-slope; stop motor if above for some time
    "m2lo":       -40.0,    # float;     mK/s; down-slope; open valve a bit
    "tMotPause":  600,      # uint16_t;  sec;  time to stop motor after m2hi
    "tMotBoost":  900,      # uint16_t;  sec;  time to keep motor open after m2lo increase flow
    "dtMotBoost":  2000,    # uint16_t;  ms;   motor-on time to open motor-valve for boost
    "dtMotBoostBack": 2000, # uint16_t;  ms;   motor-on time to close motor-valve after boost 
    "tempTol":     2.0,     # float;     K;    temperature tolerance allowed for Ruecklauf (*)
                            # (*) effective plus 0.033s/K * 3K = 0.1s ->min mot.on
                            #     => +/-( 2K + 3K) = +/-5K for valve movement
}

# alternative parameters with small changes for communication tests
parRegAlt = {
    # valve motor
    "active":        1,     # uint8_t;   0=inactive; 1=Ruecklauf;
    "motIMin":       6,     # int16_t;   mA;   above: normal operation; below: open circuit 
    "motIMax":      71,     # int16_t;   mA;   above: mechanical limit; 2x: short circuit
    "tMotDelay":    81,     # int16_t;   ms;   motor current measure delay; (peak current)
    "tMotMin":     101,     # uint16_t;  ms;   minimum motor-on time; shorter does not move
    "tMotMax":      41,     # uint8_t;   sec:  timeout to reach limit; stop if longer
    "dtOpen":       29,     # uint8_t;   sec;  time from limit close to limit open
    "dtClose":      35,     # uint8_t;   sec;  time from limit open to limit close
    "dtOffset":   3001,     # uint16_t;  ms;   time to open valve a bit when close-limit reached#
    "dtOpenBit":   500,     # uint16_t;  ms;   time to open valve a bit when close-limit reached
    "tMotTotal":   0.1,     # float;     sec;  total motor-on time 
    "nMotLimit":     1,     # uint16_t;  1;    count of limit-drives of motor
    # regulation
    "pFakt":       0.033,   # float;     s/K;  P-factor; motor-on time per Kelvin diff.
    "iFakt":       0.0,     # float;     1/K;  I-factor;
    "dFakt":       0.0,     # float;     s^2/K D-factor; 
    "tauTempVl":  300.1,    # float;     sec;  reach 1/e; low-pass (LP) filter Vorlauf
    "tauTempRl":  180.1,    # float;     sec;  reach 1/e; LP filter Ruecklauf (RL)<
    "tauM":       120.1,    # float;     sec;  reach 1/e; LP filter slope m
    "m2hi":       40.1,     # float;     mK/s; up-slope; stop motor if above for some time
    "m2lo":       -40.1,    # float;     mK/s; down-slope; open valve a bit
    "tMotPause":  601,      # uint16_t;  sec;  time to stop motor after m2hi
    "tMotBoost":  901,      # uint16_t;  sec;  time to keep motor open after m2lo increase flow
    "dtMotBoost":  2001,    # uint16_t;  ms;   motor-on time to open motor-valve for boost
    "dtMotBoostBack": 2001, # uint16_t;  ms;   motor-on time to close motor-valve after boost 
    "tempTol":     2.1,     # float;     K;    temperature tolerance allowed for Ruecklauf
}

# *** parameter for a module, including 3 regulators
# following line is a shortcut of all dictionary names; copy for easier programming:
#timer1Tic,tMeas,dtBackLight,tv0,tv1,tr0,tr1,tVlRxValid,tempZiSoll,tempZiTol
par = {
    "timer1Tic":      10,   # uint16_t; ms;    Interrupt heartbeat of Timer1
    "tMeas":          60,   # uint16_t; sec;   measuring interval
    "dtBackLight":    10,   # uint8_t;  min;   LCD time to switch off backlight
    # characteristic curve (Kennlinie)
    "tv0":          40.0,   # float;    degC;  calculate Ruecklauf temperature 
    "tv1":          75.0,   # float;    degC;  from characteristic curve
    "tr0":          32.0,   # float;    degC;  see above
    "tr1":          46.0,   # float;    degC;
    "tVlRxValid":     16,   # uint8_t;  min;    st.tempVlRx is valid this time;
    # regulator 1: special Zimmer temperature if active==2:
    "tempZiSoll":   20.0,   # float; degC;  Zimmer temp. soll; +/-4K with room Thermostat
    "tempZiTol":     0.5,   # float;degC:  toleracne for room-temperature
    "r":           [parReg for i in range(3)], # three sets of regulator parameters
}


# *** parameters for all modules
# --------------------------------------------------------------
# NOTE      pars[0] is not used
#           pars[1]...pars[29] are regulating modules
#           pars[30]  is address of central Vorlauf/Ruecklauf 
#                     measuring module
# --------------------------------------------------------------
pars = [par for i in range(31)]


'''
********************
   RX-DATA (receive)
********************
'''

# *** Variables parsed from received data string
#     depending on command only a part might be set
rxd = {
    "cmdStr"    : "",     # whole unwrapped received command-string rsp answer-string
    "adr"       : 0,      # addressee, always 0 for Zentrale
    "cmdNr"     : 0,      # command nr.
    "sender"    : 0,      # nr. of sender module (address)
    "subAdr"    : 0,      # sub-address: 0 for module, 1,2,3 for regulators
    "prot"      : 0,      # protocol ID; 
    "pyld"      : "",     # payload data-string from module
}





# *****************************
# FUNCTIONS
# *****************************

# *** some global functions
vl=vor.vorlaut


# *** system info functions
def get_hostname():
    ''' @brief  read hostname and put it in dict 'sysinfo' 
        @return sysinfo["hostname"]
    '''
    global si   # system information
    err=0
    if platform.system() == "Linux":
        try:
            with open("/etc/hostname","r") as fin:
                #fin = open("/etc/hostname","r")
                si["hostname"] = fin.read().strip()
                #fin.close()
        except Exception as e:
            print("ERR reading hostname; ",e)
            si["hostname"] = "NOTDEF"
            err=1
    else:
        si["hostname"] = "NOTDEF"
        err=2
    # for debugging on other Computers replace hostname:
    if "pl-Jeli" in si["hostname"]:
        # add more names for debugging
        si["hostname"] = "testhost"
    return si["hostname"]





# *** status function
def status_list(modNr):
    stat=stats[modNr]
    for label in stat:
        if label != "r":
            print(label,":",stat[label])
        else:
            for reg in range(3):
                print(par["r"][reg])


# *** parameter function
def param_list(modNr):
    ''' @brief  list parameters of one module
        @param  modNr   module number to be listed
    '''

    p = pars[modNr]
    for label in p:
        if label != "r":
            print(label, ":", p[label])
        else:
            for reg in range(3):
                print(p["r"][reg])


def parameters_zero():
    ''' NOTE    for debug '''
    ''' @brief  set all parameters of all modules in RPi memory to zero for TEST '''
    for mod in range(31):
        par = pars[mod]
        for label in par:
            if label != "r":
                par[label] = 0
            else:
                for reg in range(3):
                    rpar=par["r"][reg]
                    for rlabel in rpar:
                        rpar[rlabel]=0





def platform_check():
    pyVers = platform.python_version()
    print("Python version:", pyVers)
    si["pyrev"] = pyVers
    if pyVers < "3.6":
        print("must be at least Python 3.6")
        sys.exit(1)



if __name__ == "__main__":

    def prog_header_var():
        print()
        cmdLine=sys.argv
        progPathName = sys.argv[0]
        progFileName = progPathName.split("/")[-1]
        print(60*"=")
        print("ZENTRALE: %s"%(progFileName))
        print(60*"-")




    #prog_header_var()   # test ok
    #platform_check()    # test ok
    #parameters_zero()   # test ok
    #param_list(1)       # test ok
    #status_list(3)      # test ok
    #get_hostname()      # test ok
    #  ->print("hostname =",si["hostname"])






