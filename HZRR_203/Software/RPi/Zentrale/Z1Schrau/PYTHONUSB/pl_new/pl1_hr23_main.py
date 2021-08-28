#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO: command 9:  check, separate data, add to _variables.py

import platform
import sys
import time
import configparser
#
from pl1_hr23_variables import *
import vorlaut as vor
import pl1_hr23_parse_answer as par
import pl1_usb_ser_c as us
import pl1_modbus_c as mb
import pl1_hr23_log01 as log




'''
***************************************************
diverse Funktionen
***************************************************
'''



'''
***************************************************
hr23 Funktionen
***************************************************
'''



def show_mod_status(modules,regulators,mode=0):
    ''' read status information from modules and regualtors and display them'''
    us.ser_check()
    print(60*"=")
    print("Mod Reg     VL  VLeff     RL  RLeff   Mot")
    print(" nr  nr   degC   degC   degC   degC   pmill")
    print(60*"-")
    for modAdr in modules:
        mod = modules.index(modAdr)
        for reg in regSel:
            txCmd = mb.modbus_wrap( modAdr, 0x02, reg,"" ) # staus part 1
            err,repeat,rxCmd=us.net_dialog(txCmd)
            time.sleep(0.1)

            txCmd = mb.modbus_wrap( modAdr, 0x04, reg,"" ) # staus part 2
            #err,repeat,rxCmd=us.net_dialog(txCmd)
            time.sleep(0.1)

            if mode==0:
                print(rst)
            if mode==1:
                s1 = " %2d   %1d "%(modAdr,reg)
                VLmess=rst["VM"]
                s2=" Fehlt" if VLmess==-127.0 else "% 6.1f"%(VLmess)
                s3="% 6.1f"%(rst["VE"])
                RLmess=rst["RM"]
                s4=" Fehlt" if RLmess==-127.0 else "% 6.1f"%(RLmess)
                s5="% 6.1f"%(rst["RE"])
                s6="   %3d"%(rst["PM"])
                sg=s1+s2+s3+s4+s5+s6
                print(sg)
                #print(" %2d   %1d % 6.1f % 6.1f % 6.1f % 6.1f   %3d"%\
                #        (modAdr,reg,rst["VM"],rst["VE"],rst["RM"],rst["RE"],rst["PM"],)) 

def send_ping_(modules,mode):
    print(60*"=")
    print("PING-Test ueber alle Module")
    print(60*"-")
    cnt=0
    for modAdr in modules:
        err,repeat,rxCmd = us.ping(modAdr,False)
        cnt+=1
        print("M%02d:% 2dx%d=%s; "%(modAdr,err,repeat,rxCmd), end="; ")
        if cnt%5 == 0:
            print()

    pass

'''
***************************************************
INBETRIEBNAHME MENUE und Fuktionen
***************************************************
'''


modules=[]
modSel = [1]
regSel = [1]

def menu(mpos):
    global modules
    global modSel
    global regSel
    wahl=-1
    while wahl not in mpos:
        print()
        print(60*"=")
        print("0  Ende des Programms")
        print("1  Zeige Daten ausgewählter Module u. Regler",modSel)
        print("2  Zeige Daten aller Module u. ausgewaehlter Regler:")
        print("     ",modules)
        print("3  setze Modul Auswahl",modSel)
        print("4  setze Regler Auswahl",regSel)
        print("5  Sende Vorlauftemperatur von Modul 30 an alle anderen")
        print("6  sende PING Signal an alle Module")
        wahl=int(input("wahl="))
    return wahl



def mod_list_interactive(lsel,lrange ):
    lsel.sort()
    lrange.sort()
    end=False
    while not end:
        print("Liste der Module auswählen; nur Module aus der Liste verwenden:")
        print(lrange)
        print("gewaehlte Module:",lsel)
        a=input("+<nr> zufuegen, -<nr> entfernen, E Ende -> ")
        print()
        if a=="E":
            end=True
        if len(a)<2:
            print("Falsche Eingabe - nochmal:")
        else:
            op=a[0]
            if op not in ["+","-"]:
                print("falscher Operator, verwende +/-")
            else:
                try:
                    nr=int(a[1:])
                except Exception as e:
                    print("Falsche Eingabe; ",e)
                else:
                    if nr not in lrange:
                        print("Zahl ist nicht in der Liste")
                    else:
                        if op=='+' and nr not in lsel:
                            lsel.append(nr)
                            lsel.sort()
                        elif op=='-' and nr in lsel:
                            lsel.remove(nr)
                            lsel.sort()



def inbetriebnahme():
    ''' @brief  einfache Inbetribnahme
        - Einlesen der Werte von den Modulen
        - Anzeige der Messwerte
        - Senden der zentralen Vorlauftemperatur
    '''
    global hk
    global modules
    global modSel
    global regSel

    # *** Einlesen der Heizkreisparameter
    us.ser_check()

    #"Z1Schrau"
    hk.read("config/heizkreis.ini")
    hostname=get_hostname()
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
        wahl=menu([0,1,2,3,4,5,6])
        if wahl==1: # show selected modules
            show_mod_status(modSel,regSel,1)               
        if wahl==2: # show all modules
            show_mod_status(modules,regSel,1)
        if wahl==3: # select modules
            mod_list_interactive(modSel,modules)
        if wahl==4: # select regulators
            mod_list_interactive(regSel,[1,2,3])
        if wahl==5: # send VL temp to modules
            us.send_temp_vorlauf(modSendTvor,30)   # from module 30
        if wahl==6: # send ping to all modules
            send_ping_(modules,1)

        if wahl==0:
            # stop loop
            busy=False


'''
***************************************************
NORMALE FUKTION - infinite loop
***************************************************
'''

def hr_main():
    ''' main-loop for permanent work as Zentrale '''
    log.log()



'''
***************************************************
    START OF THIS MODULE
***************************************************
'''
if __name__ == "__main__":


    def prog_header():
        print()
        cmdLine=sys.argv
        progPathName = sys.argv[0]
        progFileName = progPathName.split("/")[-1]
        print(60*"=")
        print("ZENTRALE: %s main part; rev:%s; %s"%(progName,progRev,progFileName))
        print(60*"-")
        prog_header()
        platform_check()
    

    inbetriebnahme()
    # tests:
    #modules= [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,30]
    # modules=[1,]
    #regulators = [1]
    #us.send_temp_vorlauf([1,2,3,4,5,6,7,8,9],30)
    #show_mod_status(modules,regulators,1)
    

