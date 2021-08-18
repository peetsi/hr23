#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HZ-RR012 log function

Created on 06.12.2016
@author: Peter Loster (pl)

history:
hz_rr_log.py         06.12.2016  pl  initial release
hz_rr_log_Winter.py  14.05.2018  pl  (1) Simulation hoehere VL Temp
                                     fuer ganzjaehrigen Winterbetrieb
                                     send_all_Tvor() geaendert
                     Nur vorlaeufig - Ergebnis beobachten
hz_rr_log.py         27.07.2018  pl/bd  Sende permanent 20 Grad -> Sommerbetrieb
                     NUR VORLAEUFIG !!!
hz_rr_log.py         22.10.2019  pl/bd Winterbetrieb wieder aktiviert
hz_rr_log.py         30.11.2019  pl    Statusausgabe '.' jetzt ohne Zeilenschaltung
pl1_hr23_log01.py    03.11.2021  pl    Neu aufgesetzt; komplett überarbeitet
"""

import os
import sys

from pl1_hr23_variables import *    # including general functions, e,g, vorlaut
import pl1_usb_ser_c as us
import pl1_modbus_c as mb

'''
***************************************************
diverse Funktionen
***************************************************
'''


'''
***************************************************

***************************************************
'''

def get_mod_regs():
    ''' read all modules and active regulators from .ini file'''
    ''' @return modreg     [ 1,[0,1,2], 2,[0], ...]; active modules and regulators'''
    global modules
    # *** get active modules from .ini file

    mods        = hk[si["hostname"]]["modules"]   # ',' separated string with all module numbers
    modules     = [int(i) for i in mods.split(",")] # all active modules as integer list
    # *** get active regulators for each module
    #config.has_option(section, option)

    if hk.has_option(si["hostname"],"regActFlags") :
        # !!! preferred key
        # evaluate active regulator flags from "regActFlags" key in .ini file
        # used from revision 2.3;if available
        mractfl     = hk[si["hostname"]]["regActFlags"]
        regActFlags = [int(i) for i in mractfl.split(",")]# active regulator count for each module
        if len(regActFlags) != len(modules):
            err=1
            vl(3,"'regActFlags' and module count different")
            return []
        regSel=[]
        for x in regActFlags:
            l=[]
            if x & 1:
                l.append(0)
            if x & 2:
                l.append(1)
            if x & 4:
                l.append(2)
            regSel.append(l)
    elif "regActive" in hk[si["hostname"]].keys:
        # evaluate regulator count from "regActive" key in .ini file
        # used before revision 2.3; still available for compatibility
        mract       = hk[si["hostname"]]["regActive"]
        regActive   = [int(i) for i in mract.split(",")]# active regulator count for each module
        if len(regActive) != len(modules):
            err=2
            vl(3,"'regActive' and module count different")
            return[]
        act2list=[[0],[0,1],[0,1,2]] # <=> [1,2,3]
        regSel = [ act2list[regActive[i]-1] for i in len(regActive) ]
    else:
        regSel=[[] for i in regActFlags]
    modRegs=list(zip(modules,regSel))
    return modRegs    




def make_new_logfile(fLog):
    ''' close current log-file if existent and open a new one '''
    # close current file if it exists
    if (fLog!=None) and (fLog.closed == False):
        fLog.close()
    # open new file, e.g. "nlogHZ-RR_ZZ1AKA7u9_20210104_010618.dat"
    # old          new
    # nlog         nlog     prequel
    # HZ-RR_       HR23_    type
    # ZZ1          Z1       Zentrale Nr.
    # AKA7u9_      Schrau_  Hostname
    # 20210104_    -"-      date
    # 010618.dat   -"-      time .dat
    #
    fLogName = si["logpath"] + co["system"]["logHead"]+"_"
    fLogName+= si["hostname"]
    fLogName+= "Z" + hk[si["hostname"]]["heizkreis"]
    fLogName+= time.strftime('_%Y%m%d-%H%M%S.dat')
    if not os.path.exists(si["logpath"]):
        vl(3,"making directory: "+si["logpath"])
        os.mkdir(si["logpath"])
    #os.path.isfile('/etc/dir/name/file.name.to.test')
    vl(3,"open new file fLogName="+fLogName)
    fLog = open(fLogName,"w")
    fLog.write(time.strftime('# new log start: %Y%m%d-%H%M%S\n'))


def save_next_log(fLog):
    ''' read status data from every module with all regulators and save them to logfile'''
    modRegs=get_mod_regs()
    print("modRegs=",modRegs)
    for modReg in modRegs:
        modAdr=modReg[0]
        modIdx=modules.index(modAdr)
        regs=modReg[1]     # active regulators in module
        vl(3,"modReg=%s; modAdr=%d; modIdx=%d; regs=%s"%\
           (str(modReg),modAdr,modIdx,str(regs)))
        for regNr in regs:
            x = us.read_stat(modAdr,regNr)
            # *** generate logfile data-set for one module / regulator
            '''
            20210317_033815 0201 HK0 :0002021b t0.0 0 VM  0.0 RM  0.0 VE  0.0 RE  0.0 RS  0.0 P000 E0000 FX0 M0 A0
            20210317_033815 0202 HK0 :(False,)
            20210317_033816 0203 HK0 :0002023b t0.0 0 VM  0.0 RM  0.0 VE  0.0 RE  0.0 RS  0.0 P000 E0000 FX0 M0 A0
            20210317_033816 1E01 HK0 :00021E1b t0.0 0 VM  0.0 RM  0.0 VE  0.0 RE  0.0 RS  0.0 P000 E0000 FX0 M0 A0
            20210317_033817 1E02 HK0 :00021E1b t0.0 0 VM  0.0 RM  0.0 VE  0.0 RE  0.0 RS  0.0 P000 E0000 FX0 M0 A0
            '''
            #20191016_075934 0901 HK2 :0002091a t4260709.0  S VM 46.0 RM 42.5 VE 20.0 RE 42.5 RS 32.2 P074 E0000 FX0 M2503 A135
            logstr = time.strftime('%Y%m%d_%H%M%S ')

            heizkreis = hk[si["hostname"]]["heizkreis"]
            logstr+= "%02X%02X "%(modAdr,contr) + "HK%d "%(heizkreis) + ":" + str(x)


        


    '''
    '''


def send_next_vlt():
    ''' measure Vorlauf temperature from Zentrale-module and send it to other modules'''
    # *** get active modules from .ini file
    mods        = hk[hostname]["modules"]   # ',' separated string with all module numbers
    modules     = [int(i) for i in mods.split(",")] # all active modules as integer list
    modTvor     = float(hk[hostname]["Modul_Tvor"]) # get central VL Temp. from this module
    mstv        = hk[hostname]["modSendTvor"]       # string with module numbers
    modSendTvor = [int(i) for i in mstv.split(",")] # list send Tvor to these modules
    dtSendTvor  = float(hk[hostname]["interval"])   # sec; interval to send next tVor
    filtFaktTvor= float(hk[hostname]["filterfaktor"]) # factor for low-pass filter
    mract       = hk[hostname]["regActive"]
    regActive   = [int(i) for i in mract.split(",")]# active regulator count for each module
    pass


'''
***************************************************

***************************************************
'''
def log():
    ''' main-loop for permanent work as Zentrale '''
    global co, hk
    hr_init()
    
    tEndFile = time.time()  # endtime when log-file will be closed
    tEndLog  = time.time()  # endtime interval when next log will be performed
    tEndVLT  = time.time()  # endtime interval when next vorlauf temperature is sent
    fLog=None
    endLoop=False
    while(True):
        # *** lies Status aller Module ein und speichere ihn in log-Dateien
        if time.time() >= tEndFile :
            # calculate end-time of current log-file
            # NOTE DO NOT USE eval() - it is unsecure !!!
            xl=co["system"]["logFileTime"].split("*")
            dt=1.0
            for pdt in xl:
                dt *= float(pdt)
            tEndFile = time.time() + dt
            vl(3,"increase end of logfile by %.3f sec to %.3fsec"%(dt,tEndFile))
            make_new_logfile(fLog)

        # *** lies Status aller Module ein und speichere ihn in log-Dateien
        if time.time() > tEndLog :
            tEndLog = time.time() + float(co["system"]["logTime"])
            save_next_log(fLog)

            # TODO DEBUG remove:
            break


        # *** sende zentrale Vorlauftemperatur an alle anderen Module
        if time.time() > tEndVLT :
            tEndVLT = time.time() + float(co["system"]["vorlaufTime"])
            send_next_vlt()
        
        # *** end of infinite loop
        if endLoop:
            fLog.close()
            break




'''
***************************************************

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
    log()
