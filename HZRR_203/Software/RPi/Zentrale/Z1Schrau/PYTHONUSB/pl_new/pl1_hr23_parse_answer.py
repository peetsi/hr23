#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pl1_hr23_variables import *
import pl1_modbus_c as mb
import time



def parse_answer(rxCmd):
    ''' @brief  analyze STRING rxCmd and perform required action
        @param  rxCmd   received command-string of type 'str'
        @return err     error number
        @return parse   parsed data
        @retrun rxd     global structure with header and payload data
    '''
    global rxd
    err=0

    #print("parse_answer(): rxCmd=",rxCmd)
    # *** remove checksums
    err,rxCmdU = mb.modbus_unwrap(rxCmd)
    #print("err=",err,"; rxCmdU=",rxCmdU)
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
            # "ACK" - no data received
            if "ACK" in pyld :
                return 0,pyld

            '''
            # parse a line e.g.:
            // no winter- or summer operation -> omitted in type b protocol
            // cmd = 2
            // SN:    season, typical S or W; maybe something else e.g. empty like ",,"
            // VM RM: Vl/Rl temp. measured
            // VE RE: Vl/Rl temp. effectively used for regulation
            // RS:    Rl temp. soll
            // PM:     Permille motor-valve setting; 0=closed, 999=open
            // cmd = 4
            // ER:     Error message bits set
            // FX:    fixed position; MOT_STOP (somewhere), MOT_STARTPOS, MOT_CLOSE or MOT_OPEN
            // MT:     total motor-on time
            // NL:     Number of limits reached (higher load to gears)
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
            # "ACK" - no data received
            if "ACK" in pyld :
                return 0,"ACK"

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

    elif rxCmdNr == 0x20 :  # Zentrale Vorlauftemperatur received
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            return 0,pyld



    '''
    elif rxCmdNr == 5:  # read parameter: module / reg.part 1
        #timer1Tic,tMeas,dtBackLight,tv0,tv1,tr0,tr1,
        #tVlRxValid,tempZiSoll,tempTolRoom
        l = get_command_list()
        par = parameters[modAdr-1]
        if rxSubAdr == 0:
            # read timer1Tic,tMeas,dtBackLight,
            #   tv0,tv1,tr0,tr1,tVlRxValid,tempZiSoll,tempZiToly
            for n in par:
                if n == "r":
                    break # last value terminated in dict
                par[n]=float(l.pop(0))
            pa_to_ser_obj.add('READ_PARAM->par = parameters[modAdr-1]: %s'%(str(par)))
            return True

        elif rxSubAdr in [1,2,3]:
            # read:
            #   active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax,
            #   dtOpen, dtClose, dtOffset
            pr = par["r"][rxSubAdr-1]
            start=False
            for n in pr:          # start at begin of directory
                pr[n]=float(l.pop(0))
                if l == []:     # last item provided
                    break
            pa_to_ser_obj.add('READ_PARAM->pr = par["r"][rxSubAdr-1]: %s'%(str(pr)))
            return True

    elif rxCmdNr == 6:  # read parameter: module / reg.part 2
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if rxSubAdr == 0:
            # "ACK" - no data available
            if "ACK" in pyld :
                pa_to_ser_obj.add('READ_PARAM-ACK (rxSubAdr == 0)')
                return True

        elif rxSubAdr in [1,2,3]:
            # "tMotTotal" and "nMotLimit" are not transferred here
            # they are received with command nr. 4 as "MT" and "NL"
            # read:
            #   pFakt, iFakt, dFakt, tauTempVl, tauTempRl, tauM
            l = get_command_list()
            par = parameters[modAdr-1]
            pr = par["r"][rxSubAdr-1]

            start=False
            for n in pr:
                if n == "pFakt":  # first item to be filled
                    start=True
                if start :
                    pr[n]=float(l.pop(0))
                    if l == []:     # last item provided
                        break
            pa_to_ser_obj.add('READ_PARAM->pr = par["r"][rxSubAdr-1]: %s'%(str(pr)))
            return True
            #pr = parameters[modAdr-1]["r"][rxSubAdr-1][n] = number


    elif rxCmdNr == 7:  # read parameter: module / reg.part 3
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if rxSubAdr == 0:
            # "ACK" - no data available
            if "ACK" in pyld :
                pa_to_ser_obj.add('READ_PARAM-ACK (rxSubAdr == 0)')
                return True

        elif rxSubAdr in [1,2,3]:
            # read:
            #   m2hi, m2lo,
            #   tMotPause, tMotBoost, dtMotBoost, dtMotBoostBack
            l = get_command_list()
            par = parameters[modAdr-1]
            pr = par["r"][rxSubAdr-1]
            start = False
            for n in pr:
                if n == "m2hi":  # first item to be filled
                    start=True
                if start :
                    pr[n]=float(l.pop(0))
                    if l == []:     # last item provided
                        break
            #parameter = parameters[modAdr-1]
            pa_to_ser_obj.add('READ_PARAM->pr = par["r"][rxSubAdr-1]: %s'%(str(pr)))
            return True

    elif rxCmdNr == 9:   # revision numbers of module 
        print(rxCmd)
    '''

    '''
    elif rxCmdNr == 0x22 :  # setze parameter
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('set_param(0x22)->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x23 :  # setze parameter
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('set_param(0x23)->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True


    elif rxCmdNr == 0x24 :  # setze parameter
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('set_param(0x24)->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x25 :  # set special parameters
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('set_special_param->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x30 :  # reset all parameters to factory settings
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('factory_reset->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x31 :  # move valve; time and direction
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('move_valve->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x34 :  # set normal operation
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('set_normal_operation->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x35 :  # set regulator active/inactive
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('reg_set->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x36 :  # fast mode on/off
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('fast_mode->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x37 :  # get milliseconds
        l = get_command_list()
        rxMillis = l[0]
        #dbg.m("COMMAND= %02x: rxCmd= %s"%(rxCmdNr,rxCmd),"/ l=",str(l),"/ recv milliseconds:",rxMillis)
        pa_to_ser_obj.add('get_millis->ACK: %s,%s,%s'%(str(rxCmdNr),str(rxCmd),str(rxMillis)))
        return True

    elif rxCmdNr == 0x38 :  # copy all parameters from EEPROM to RAM
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('cpy_eep2ram->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x39 :  # write all parameters from RAM to EEPROM
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('cpy_ram2eep->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x3A :  # RESET using watchdog - endless loop
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('watchdog_reset->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x3B :  # clear eeprom  ??? plpl test eeprom if ram space is left
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('clear_eep->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x3C :  # check if motor connected
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        l = get_command_list()
        #dbg.m("0x3C: l=",l)
        rxMotConn = int(l[0])
        #dbg.m("received motor connected:",rxMotConn)
        pa_to_ser_obj.add('motor_connected->ACK: mot_connected:%s (%s,%s)'%(str(rxMotConn),str(rxCmdNr),str(rxCmd)))
        return True

    elif rxCmdNr == 0x3D :  # open and close valve to store times
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('open_close_valve->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x3E :  # switch off current motor
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('mot_off->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x3F :  # read motor current
        l = get_command_list()
        rxMotImA = float(l[0])
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd),"// l=",l,"// received mA:",rxMotImA)
        pa_to_ser_obj.add('mot_current->ACK: %s (%s,%s)'%(str(rxMotImA),str(rxCmdNr),str(rxCmd)))
        return True

    elif rxCmdNr == 0x40 :  # LCD-light on/off
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd))
        if "ACK" in pyld :
            pa_to_ser_obj.add('lcd_backlight->ACK: %s,%s'%(str(rxCmdNr),str(rxCmd)))
            return True

    elif rxCmdNr == 0x41 :  # read jumper settings
        l = get_command_list()
        jumpers = int(l[0], 16)
        #dbg.m("parse_answer %02x: pyld = %s"%(rxCmdNr,rxCmd),"// jumper setting = %02x:"%(jumpers))
        pa_to_ser_obj.add('get_jumpers->ACK: %s (%s,%s)'%(str(jumpers),str(rxCmdNr),str(rxCmd)))
        return True
    '''
    return -1,"function number not available: "+str(rxCmdNr) # values not found while parsing



#pa_to_ser_obj

# ----------------
# ----- test -----
# ----------------

if __name__ == "__main__" :

   # Test functions, Tests
    
    def prog_header_var():
        print()
        cmdLine=sys.argv
        progPathName = sys.argv[0]
        progFileName = progPathName.split("/")[-1]
        print(60*"=")
        print("ZENTRALE: %s"%(progFileName))
        print(60*"-")

    prog_header_var()
    # usage examples

    # example 1
