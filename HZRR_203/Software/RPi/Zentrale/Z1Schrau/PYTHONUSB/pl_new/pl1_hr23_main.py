#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
import sys
import time

from pl1_hr23_variables import *
import vorlaut as vor
import pl1_hr23_parse_answer as par
import pl1_usb_ser_c as us
import pl1_modbus_c as mb

progName = "hr2"
progRev = "2.3.0"



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

    modules= [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,30]
    #modules=[1,2]
    regulators = [1]
    show_mod_status(modules,regulators,1)