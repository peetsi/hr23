#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pl1_hr23_variables import *
import pl1_modbus_c as mb
import time

'''
# % % '%%' run cell
print("hello")
#
''' 
def parStr2list(pyld):
    ''' split ',' separated values from st.rxCmd in list '''
    if (pyld == ""):
        return 1,[]
    pl = pyld.rxCmd.split(",")
    while pl[0] == '' :      # discard leading empty strings
        pl.pop(0)
    while pl[-1] == '' :     # discard trailing empty strings
        pl.pop()
    return 0,pl


def parse_answer(rxCmdStr):
    ''' @brief  analyze STRING rxCmd and perform required action
        @param  rxCmdStr   received command-string of type 'str'
        @return err     error number
        @return parse   parsed data
        @retrun rxd     global structure with header and payload data
    '''
    global rxd
    err=0

    #vl(3,"parse_answer(): rxCmd=",rxCmdStr)
    # *** remove checksums
    err,rxCmdU = mb.modbus_unwrap(rxCmdStr)
    #vl(3,"err=",err,"; rxCmdU=",rxCmdU)
    if err != 0:
        return err, "err unwrapping received command: "+str(err)

    err,pyld   = mb.parse_command_header(rxCmdU)
    #print("err=",err,"; pyld=",pyld)

    if err != 0:
        return err, "err understanding command header: "+str(err)

    # *** interpret received data by command-number

    modAdr = rxd["sender"]
    rxSubAdr = rxd["subAdr"]
    rxCmdNr= rxd["cmdNr"]
    

    if rxCmdNr == 1 :  # ping command
        if "ACK" in pyld :
            return 0,pyld

    elif rxCmdNr == 2 :  # read status values part 1
        if rxSubAdr == 0 :
            if "ACK" in pyld :   # "ACK" - no data to be sent
                return 0,"ACK"
        elif rxSubAdr in [1,2,3]:
            '''
            # parse a line e.g.:
            // cmd = 2
            // SN:    season, typical S or W; maybe something else e.g. empty like ",,"
            //        discarded in rev2.x of HZ-RR; is forced to '-' from rev. 2.3
            // VM RM: Vl/Rl temp. measured
            // VE RE: Vl/Rl temp. effectively used for regulation
            // RS:    Rl temp. soll
            // PM:    Permille motor-valve setting; 0=closed, 999=open
            // cmd = 4
            // ER:    Error message bits set
            // FX:    fixed position; MOT_STOP (somewhere), MOT_STARTPOS, MOT_CLOSE or MOT_OPEN
            // MT:    total motor-on time
            // NL:    Number of limits reached (higher load to gears)
            //           1         2         3         4         5         6  
            //  1234567890123456789012345678901234567890123456789012345678901234
            // ":00021E1b,W,VM0.0,RM0.0,VE0.0,RE0.0,RS0.0,PM0,09AB01cl0"  // could become a bit longer; OK
            // payload to be parsed:
            // ",W,VM0.0,RM0.0,VE0.0,RE0.0,RS0.0,PM0,09AB01cl0"  // could become a bit longer; OK
            
            '''
            l = pyld.strip().split(",")
            #while(l[0]==''):            # remove leading empty items
            #    l.pop(0) # do not remove
            rst["tic2"] = time.time()
            pos=0
            
            #print("l=",l)
            
            try:
                rst["SN"] = l[pos+0]
            except ValueError as e:
                return 1,"parsing error"+str(e)
            except Exception as e:
                return 2,"other error"+str(e)
    
            try:
                rst["VM"] = float(l[pos+1][2:])
            except ValueError as e:
                return 11,"parsing error"+str(e)
            except Exception as e:
                return 12,"other error"+str(e)

            try:
                rst["RM"] = float(l[pos+2][2:])
            except ValueError as e:
                return 21,"parsing error"+str(e)
            except Exception as e:
                return 22,"other error"+str(e)
            
            try:
                rst["VE"] = float(l[pos+3][2:])
            except ValueError as e:
                return 31,"parsing error"+str(e)
            except Exception as e:
                return 32,"other error"+str(e)
            
            try:
                rst["RE"] = float(l[pos+4][2:])
            except ValueError as e:
                return 41,"parsing error"+str(e)
            except Exception as e:
                return 42,"other error"+str(e)
            
            try:
                rst["RS"] = float(l[pos+5][2:])
            except ValueError as e:
                return 51,"parsing error"+str(e)
            except Exception as e:
                return 52,"other error"+str(e)
            
            try:
                rst["PM"] = int(l[pos+6][2:])
            except ValueError as e:
                print(l)
                return 61,"parsing error"+str(e)
            except Exception as e:
                return 62,"other error"+str(e)
            
            return 0,pyld


    # command 3 not implemented in rev hr2 (was in hr010)
    # sends regulator parameter -> new command

    elif rxCmdNr == 4 :  # read status values part 2
        '''
        // ER:      Error message bits set
        // FX:      fixed position; 
                    MOT_STOP (somewhere), MOT_STARTPOS, MOT_CLOSE or MOT_OPEN
        // MT:      total motor-on time
        // NL:      Number of limits reached (higher load to gears)
        // NB:      Number of boots (TBD)
        //           1         2         3         4         5         6   
        //  1234567890123456789012345678901234567890123456789012345678901234
        // ":0004021b,ER111111,FX22,MT33333.33,NL44444,NB55555,06BA28cl0"
        // payload to be parsed:
        // ",ER111111,FX22,MT33333.33,NL44444,NB55555,06BA28cl0"
        
        '''
        if rxSubAdr == 0 :
            # "ACK" - no data received
            if "ACK" in pyld :
                return 0,"ACK"
        elif rxSubAdr in [1,2,3]:
            l = pyld.strip().split(",")
            while(l[0]==''):
                l.pop(0)
            rst["tic4"] = time.time()
            pos=0
            #print("l=",l)
            try:
                rst["ER"] = int(l[pos+0][2:],16)
                rst["FX"] = int(l[pos+1][2:],10)
                rst["MT"] = float(l[pos+2][2:])
                rst["NL"] = int(l[pos+3][2:],10)
                rst["NB"] = int(l[pos+4][2:],10)
                #rst[""] = l[pos+]
            except ValueError as e:
                return 1,"parsing error: "+str(e)
            except Exception as e:
                return 2,"other error: "+str(e) 
            return 0,pyld

    elif rxCmdNr == 5:  # read parameter: module / reg.part 1
        # make a parameter-list from received string
        err,pl=parStr2list(pyld)
        if err:
            return -2,pyld

        par = pars[modAdr]      # NOTE inex 0 is not used -> modAdr is actual Index
        if rxSubAdr == 0:
            # set values from received string:
            # timer1Tic,tMeas,dtBackLight,
            #   tv0,tv1,tr0,tr1,tVlRxValid,tempZiSoll,tempZiToly
            for n in par:
                if n == "r":
                    break # last value, contains regulator parameters - see below
                par[n]=float(pl.pop(0))
            return 0,pyld

        elif rxSubAdr in [1,2,3]:
            # set values from received string:
            # active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax,
            #   dtOpen, dtClose, dtOffset
            pr = par["r"][rxSubAdr-1]
            start=False
            for n in pr:         # start at begin of directory
                pr[n]=float(pl.pop(0))
                if pl == []:     # last item provided
                    break
            return 0,pyld

    elif rxCmdNr == 6:  # read parameter: module / reg.part 2
        if rxSubAdr == 0:
            # "ACK" - no data available
            if "ACK" in pyld :
                return 0,pyld

        elif rxSubAdr in [1,2,3]:
            # "tMotTotal" and "nMotLimit" are not transferred here
            # they are received with command nr. 4 as "MT" and "NL"
            # set values from received string:
            #   pFakt, iFakt, dFakt, tauTempVl, tauTempRl, tauM
            err,pl=parStr2list(pyld)
            par = pars[modAdr]      # NOTE inex 0 is not used -> modAdr is actual Index
            pr = par["r"][rxSubAdr-1]
            # fill in from a certain parameter on:
            start=False
            for n in pr:
                if n == "pFakt":  # first item to be filled
                    start=True
                if start :
                    pr[n]=float(pl.pop(0))
                    if pl == []:     # last item provided
                        break
            return 0,pyld

    elif rxCmdNr == 7:  # read parameter: module / reg.part 3
        if rxSubAdr == 0:
            # "ACK" - no data available
            if "ACK" in pyld :
                return 0,pyld

        elif rxSubAdr in [1,2,3]:
            # set values from received string:
            #   m2hi, m2lo,
            #   tMotPause, tMotBoost, dtMotBoost, dtMotBoostBack
            err,pl=parStr2list(pyld)
            par = pars[modAdr]      # NOTE inex 0 is not used -> modAdr is actual Index
            pr = par["r"][rxSubAdr-1]
            # fill in from a certain parameter on:
            start = False
            for n in pr:
                if n == "m2hi":  # first item to be filled
                    start=True
                if start :
                    pr[n]=float(pl.pop(0))
                    if pl == []:     # last item provided
                        break
            return 0,pyld

    elif rxCmdNr == 9:   # revision numbers of module 
        return 0,pyld    # TODO: check, separate data, add to _variables.py


    elif rxCmdNr == 0x20 :  # Zentrale Vorlauftemperatur received
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld



    elif rxCmdNr == 0x22 :  # setze parameter
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x23 :  # setze parameter
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld


    elif rxCmdNr == 0x24 :  # setze parameter
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x25 :  # set special parameters
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x30 :  # reset all parameters to factory settings
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x31 :  # move valve; time and direction
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x34 :  # set normal operation
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x35 :  # set regulator active/inactive
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x36 :  # fast mode on/off
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld
 
    elif rxCmdNr == 0x37 :  # get milliseconds timer-tic of module
        err,pl=parStr2list(pyld)
        if err:
            return -1,pyld
        rxMillis = float(pl[0])
        stat["rxMs"]=rxMillis
        return 0,pyld

    elif rxCmdNr == 0x38 :  # copy all parameters from EEPROM to RAM
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x39 :  # write all parameters from RAM to EEPROM
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x3A :  # RESET using watchdog - endless loop
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x3B :  # clear eeprom
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x3C :  # check if motor connected
        err,pl=parStr2list(pyld)
        if err:
            return -1,pyld
        rxMotConn = int(l[0])
        stat["MotConn"]=rxMotConn
        return 0,pyld

    elif rxCmdNr == 0x3D :  # open and close valve to store times
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x3E :  # switch off current motor
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x3F :  # read motor current
        err,pl=parStr2list(pyld)
        if err:
            return -1,pyld
        rxMotImA = float(pl[0])
        stat["MotImA"] = rxMotImA 
        return 0,pyld

    elif rxCmdNr == 0x40 :  # LCD-light on/off
        if "ACK" in pyld :
            return 0,pyld
        elif "NAK" in pyld:
            return -1,pyld

    elif rxCmdNr == 0x41 :  # read jumper settings
        err,pl=parStr2list(pyld)
        if err:
            return -1,pyld
        jumpers = int(l[0], 16)
        stat["jumpers"] = jumpers
        return 0,pyld

    return -1,"function number not available: "+str(rxCmdNr) # values not found while parsing



#pa_to_ser_obj

# ----------------
# ----- test -----
# ----------------


if __name__ == "__main__" :

   # Test functions, Tests


    ''' 
    def prog_header_var():
        print()
        cmdLine=sys.argv
        progPathName = sys.argv[0]
        progFileName = progPathName.split("/")[-1]
        print(60*"=")
        print("ZENTRALE: %s"%(progFileName))
        print(60*"-")
    '''

    prog_header_var()
    # usage examples

    # example 1


