#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
import sys
import time
import configparser


from pl1_hr23_variables import *
import vorlaut as vor
import pl1_hr23_parse_answer as par
import pl1_usb_ser_c as us
import pl1_modbus_c as mb

progName = "hr2"
progRev = "2.3.0"

hk=configparser.ConfigParser()

def send_temp_vorlauf( vlmodules, modZentrale ):
    ''' @brief  send Vorlauftemperature to modules'''
    us.ser_check()
    # 1. read VL temperature from Zentrale module
    txCmd = mb.modbus_wrap(modZentrale, 0x02, 0, "" ) # request status part 1
    err,repeat,rxCmd=us.net_dialog(txCmd)
    #vlt = 
    pass

def show_mod_status(modules,regulators,mode=0):
    ''' read status information from modules and regualtors and display them'''
    us.ser_check()
    print("Mod Reg     VL   RL   Mot")
    print(" nr  nr   degC degC pmill")
    for mod in modules:
        for reg in regulators:
            txCmd = mb.modbus_wrap( mod, 0x02, reg,"" ) # staus part 1
            err,repeat,rxCmd=us.net_dialog(txCmd)
            time.sleep(0.1)

            txCmd = mb.modbus_wrap( mod, 0x04, reg,"" ) # staus part 2
            #err,repeat,rxCmd=us.net_dialog(txCmd)
            time.sleep(0.1)
            
            if mode==0:
                print(rst)
            if mode==1:
                print(" %2d   %1d % 6.1f % 6.1f %3d"%\
                      (mod,reg,rst["VM"],rst["RM"],rst["PM"],)) 


def inbetriebnahme():
    ''' @brief  einfache Inbetribnahme
        - Einlesen der Werte von den Modulen
        - Anzeige der Messwerte
        - Senden der zentralen Vorlauftemperatur
    '''
    global hk
    # *** Inlesen der Heizkreisparameter
    us.ser_check()

    #"Z1Schrau"
    hk.read("config/heizkreis.ini")
    err,hostname=get_hostname()
    print( hk.sections())
    print( hk[hostname] )
    mods        = hk[hostname]["modules"]
    modules     = [int(i) for i in mods.split(",")] # all active modules
    modTvor     = float(hk[hostname]["Modul_Tvor"]) # get central VL Temp. from this module
    mstv        = hk[hostname]["modSendTvor"]      
    modSendTvor = [int(i) for i in mstv.split(",")] # send Tvor to these modules
    dtSendTvor  = float(hk[hostname]["interval"])   # sec; interval to send next tVor
    filtFaktTvor= float(hk[hostname]["filterfaktor"]) # factor for low-pass filter
    mract       = hk[hostname]["regActive"]
    regActive   = [int(i) for i in mract.split(",")]# regulator count for each module
    ''' TODO for automatic recognition of changes
    =hk[hostname]["TVorlAendWarn"]
    =hk[hostname]["TVorlAendAlarm"]
    =hk[hostname]["TRueckAendWarn"]
    =hk[hostname]["TRueckAendAlarm"]
    =hk[hostname]["TRueckDeltaPlus"]
    =hk[hostname]["TRueckDeltaMinus"]
    =hk[hostname]["venTravelWarn"]
    =hk[hostname]["venTravelAlarm"]
    '''
    print("modules=      ",modules)
    print("modTvor=      ",modTvor)
    print("modSendTvor=  ",modSendTvor)
    print("dtSendTvor=   ",dtSendTvor)
    print("filtFaktTvor= ",filtFaktTvor )
    print("regActive=    ",regActive )
    #print(" =", )
    
    tNextTvor = time.time()     # next time when VL temperature has to be sent
    busy=True
    while busy:
        # *** forever until restart / watchdog (if implemented)

        # *** 1. read all values and display them
        show_mod_status(modules,regActive,1)               

        # *** 2. if interval is ready: send VL temp to modules
        if time.time() > tNextTvor:
            pass
        
        busy=False



def platform_check():
    pyVers = platform.python_version()
    print("Python version:", pyVers)
    if pyVers < "3.6":
        print("must be at least Python 3.6")
        sys.exit(1)


def prog_header():
    print()
    cmdLine=sys.argv
    progPathName = sys.argv[0]
    progFileName = progPathName.split("/")[-1]
    print(60*"=")
    print("ZENTRALE: %s main part; rev:%s; %s"%(progName,progRev,progFileName))
    print(60*"-")

if __name__ == "__main__":
    prog_header()
    platform_check()
    
    send_temp_vorlauf(1,30)

    #inbetriebnahme()
    '''
    modules= [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,30]
    #
    # modules=[1,]
    regulators = [1]
    show_mod_status(modules,regulators,1)
    '''


