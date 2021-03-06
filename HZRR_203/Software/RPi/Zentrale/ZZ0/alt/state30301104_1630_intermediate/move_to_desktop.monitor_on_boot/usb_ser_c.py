#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import time

import serial

import hr2_parse_answer_b as pan
import modbus_b as mb
import vorlaut as vor
from hr2_variables_b import *


SER_TIMEOUT = 0.5
RX_TIMEOUT  = 2.5
NET_REPEAT  = 3

#serPort = "/dev/ttyUSB0" # USB0 might change
# fixed for the same adapter is always:
#serPort = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A504YCFM-if00-port0"
# has problems if the adapter changes (because of serial number)
# so we use the USB-socket where the adapter is connected:

# RPi 3 Mod. B
# Bottom socket next to Ethernet socket:
#serPort = "/dev/serial/by-path/platform-3f980000.usb-usb-0:1.3:1.0-port0"

# RPi 4 Mod. B
# Bottom USB2-socket next to corner (away from Ethernet socket)
#serPort = "COM8" #"COM5" 
serPort = "/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.4:1.0-port0"
#serPort = "/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0" #3b+

global ser


def ser_instant() :
    global ser
    err=0
    try:
        ser = serial.Serial(
        port=serPort,
        baudrate =115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_TWO,
        bytesize = serial.EIGHTBITS,
        timeout = SER_TIMEOUT)
    except serial.SerialException as e:
        vor.vorlaut( 3,  "01 cannot find: %s"%(serPort))
        vor.vorlaut( 3,  "   exception = %s"%(e))
        err = 1
    except Exception as e:
        vor.vorlaut( 3,  "02 something else is wrong with serial port: %s"%(serPort))
        vor.vorlaut( 3,  "   exception = %s"%(e))
        err = 2
    return err



def ser_open():
  # open USB->RS485 connection
  global ser
  err=0
  try:
    ser.open()
  except serial.SerialException as e:
    vor.vorlaut( 3,  "03 cannot open: %s"%(serPort))
    vor.vorlaut( 3,  "   exception = %s"%(e))
    err = 3
  except  Exception as e:
    vor.vorlaut( 3,  "04 something else is wrong with serial port:"%(serPort))
    vor.vorlaut( 3,  "   exception = %s"%(e))
    err = 4
  return err


def ser_reset_buffer():
  global ser
  err=0
  try:
    ser.flushOutput()  # newer: ser.reset_output_buffer()
    ser.flushInput()   # newer: ser.reset_input_buffer()
  except serial.SerialException:
    err = 5
    vor.vorlaut( 3,  "05 cannot erase serial buffers")
    vor.vorlaut( 3,  "   exception = %s"%(e))
  except Exception as e:
    err = 6
    vor.vorlaut( 3,  "06 something else is wrong with serial port: %s"%(serPort))
    vor.vorlaut( 3,  "   exception = %s"%(e))
  return err



def ser_check():
    global ser
    ser_instant()
    if ser.isOpen() == False :
        print("open network")
        err = 0
        err |= ser_open()
        if( err ) :
            print("rs485 Netz: %d"%(err))
        time.sleep(1.0)
        ser_reset_buffer()
    print("rs485 Netz verbunden")
    return ser






def txrx_command( txCmd ) :
    # send a command and receive answer
    # txCmd      byte-array of command-string
    # return:    string with command
    global ser
    global line
    twait1 = 0.01
    twait2= 0.01
    ser.flushOutput()
    #vor.vorlaut( 2, "\ntx: %s"%(txCmd[:-2]))

    if type(txCmd)==str :
        txCmd = txCmd.encode()
    try:
        ser.write(txCmd)                  # start writing string
    except serial.SerialTimeoutException as e:
        vor.vorlaut( 2, "07 timeout sending string: %s"%(txCmd))
        vor.vorlaut( 2,  "  exception = %s"%(e))
    except serial.SerialException as e:
        vor.vorlaut( 2,  "08 SerialException on write")
        vor.vorlaut( 2,  "   exception = %s"%(e))
        ser.close()
    except   Exception as e:
        vor.vorlaut( 2,  "09 error serial port %s, writing"%(serPort))
        vor.vorlaut( 2,  "   exception = %s"%(e))
        ser.close()

    ser.flush()
    ser.flushInput()
    st.rxCmd = ""
    
    #time.sleep( twait1 )   # maybe not necessary: flush waits unitl all is written
    # using USB-RS485 converter: no echo of sent data !
    # receive answer from module
    et = time.time() + RX_TIMEOUT 
    l0=b""
    while (time.time() < et) and (l0==b""):
        l0 = ser.readline()
    #print("l0=",l0)
    l1 = l0.split(b":")
    #print("rx l1=",(l1))
    if(len(l1)==2):
        line = l1[1]
    else:
        line = b""
    line = line.strip()   # remove white-spaces from either end
    try:
        line = line.decode()     # make string
    except Exception as e:
        # some false byte in byte-array
        vor.vorlaut( 2,  "10 cannot decode line")
        vor.vorlaut( 2,  "   exception = %s"%(e))
        line = ""
        pass

    print("line=",line)
    st.rxCmd = line
    return line


def net_dialog( txCmd, info=0 ):
    maxCnt = NET_REPEAT
    st.repeat = 0
    ready  = False
    while st.repeat < maxCnt :
        ser_reset_buffer()
        txrx_command( txCmd )
        #print(pan.parse_answer())
        if pan.parse_answer():
            if info==0:return True
            return True, repeat
        else:
            st.repeat += 1
    if st.repeat >= maxCnt:
        st.repeat=-1
    if info==0: return False
    return False, st.repeat

# *****************************************
# *** module communication commands     ***
# *****************************************

def ping( modAdr ):
    txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )   # cmd==1: send ping
    return net_dialog(txCmd, 1)

def read_stat( modAdr, subAdr ) :
    ''' read all status values from module
        using command 2 and 4
    '''
    # modAdr e {1..31}
    # subAdr e {0..3} for {module, reg0, reg1, reg2}

    # *** first part, scan to cn2
    txCmd = mb.wrap_modbus( modAdr, 2, subAdr, "" )
    if not  net_dialog(txCmd):
        return False
    time.sleep(0.5)
    
    # *** second part, scan to cn4
    txCmd = mb.wrap_modbus( modAdr, 4, subAdr, "" )
    if not  net_dialog(txCmd):
        return False

    #read_stat(mod,reg)     # result is in cn2 and cn4
    get_milisec(modAdr)
    get_jumpers(modAdr)

    # *** print data
    #print("="*40)
    #print("cn2=",cn2)
    #print("cn4=",cn4)
    #print("timestamp ms=",st.rxMillis)
    #print("Jumper settings=%02x"%(st.jumpers))
    #print("-"*40)
  

    # module data:
    cmdHead  = "0002%02X%db "%(modAdr,subAdr)
    tic      = float(st.rxMillis) / 1000.0
    ticStr   = "t%.1f "%(tic)

    #cn2={"SN":0,"VM":0,"RM":0,"VE":0,"RE":0,"RS":0,"PM":0}
    vlMeas   = float(cn2["VM"])
    rlMeas   = float(cn2["RM"])
    vlEff    = float(cn2["VE"])
    rlEff    = float(cn2["RE"])
    rlSoll   = float(cn2["RS"])
    posMot   = float(cn2["PM"])

    #cn4={"ER":0,"FX":0,"MT":0,"NL":0} # command names
    erFlag  = int(cn4["ER"])
    fixPos  = float(cn4["FX"])
    motTime = float(cn4["MT"])
    nLimit  = int(cn4["NL"])


    s1    = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f "%(vlMeas,rlMeas,vlEff,rlEff)
    s2    = "RS%5.1f P%03.0f "%(rlSoll, posMot)
    s3    = "E%04X FX%.0f M%.0f A%d"%(erFlag,fixPos,motTime,nLimit)
    # FX muss noch ??bersetzt werden.
    x = s1 + s2 + s3
    s = str(cmdHead) + str(ticStr) + str(cn2["SN"]) + " " + str(x)
    
    print (s)

    return s
    

def get_param(modAdr,subAdr):
    '''read module-related parameter set from module'''
    if subAdr in [0,1,2,3]:
        txCmd = mb.wrap_modbus( modAdr, 0x05, subAdr,"" )
        if not  net_dialog(txCmd):
            return False
        elif subAdr == 0:
            return True

        txCmd = mb.wrap_modbus( modAdr, 0x06, subAdr,"" )
        if not  net_dialog(txCmd):
            return False
    
        txCmd = mb.wrap_modbus( modAdr, 0x07, subAdr,"" )
        if net_dialog(txCmd):
            return True

    return False


def send_Tvor(modAdr,tempSend):
    '''send Vorlauftemperatur to module'''
    txCmd = mb.wrap_modbus(modAdr,0x20,0,','+str(tempSend)+',')
    if net_dialog(txCmd):
        return True
    return False


def send_param(modAdr,subAdr):
    ''' send module parameters to module nr. modAdr
        0: module, 1,2,3: regulator
    '''
    if subAdr == 0:
        '''
        //           1         2         3         4         5         6  
        //  1234567890123456789012345678901234567890123456789012345678901234
        //  :02200b 111 222 33 44.4 55.5 66.6 77.7 88 99.9 0.5 02634Ccl0"    max. length
           e.g.:    010 060 10 40.0 75.0 32.0 46.0 15 20.0 0.5 
        // with:        typ.value   use    
        //   :02200b    header;     placeholder
        //   111        10 ms;      timer1Tic; 
        //   222        60 sec;     tMeas; measruring interval
        //   33         10 min;     dtBackLight; time for backlight on after keypressed
        //   44.4       degC;       tv0;   Kurve
        //   55.5       degC;       tv1
        //   66.6       degC;       tr0
        //   77.7       degC;       tr1
        //   88         15 min;     tVlRxValid  
        //   99.9       20 degC;    tempZiSoll
        //   0.5        0.5 degC;   tempTolRoom
        //   02634Ccl0  trailer - placeholder; cl0=="\r\n\0" (end of line / string)
        '''
        p = parameters[modAdr]
        print("p=",p)
        time.sleep(1)
        # ATTENTION!!! send  <tVlRxValid> 2x due to error in Nano-Software which needs it twice
        s = ",%03d,%03d,%02d,%4.1f,%4.1f,%4.1f,%4.1f,%02d,%02d,%4.1f,%3.1f,"%( \
            p["timer1Tic"], p["tMeas"], p["dtBackLight"], p["tv0"], \
            p["tv1"], p["tr0"], p["tr1"], p["tVlRxValid"], p["tVlRxValid"], \
            p["tempZiSoll"], p["tempZiTol"] )
        print("*** s=",s)

        txCmd = mb.wrap_modbus( modAdr, 0x22, subAdr, s )
        #print(txCmd)
        if net_dialog(txCmd):
            return True
        return False

    elif subAdr in [1,2,3]: # parameter regulator, part 1,2,3
        # send:
        #   active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax,
        #   dtOpen, dtClose, dtOffset
        time.sleep(0.2)
        ps = parameters[modAdr]["r"][subAdr]
        s = ",%d,%d,%d,%d,%d,%d,%d,%d,%d,"%(\
            ps["active"], ps["motIMin"], ps["motIMax"], ps["tMotDelay"],\
            ps["tMotMin"], ps["tMotMax"],\
            ps["dtOpen"], ps["dtClose"], ps["dtOffset"] )
        #print("s=",s)
        txCmd = mb.wrap_modbus( modAdr, 0x22, subAdr, s )
        #print(txCmd)
        if not net_dialog(txCmd):
            return False

        # send:
        #   pFakt, iFakt, dFakt, tauTempVl, tauTempRl, tauM
        time.sleep(0.2)
        s = ",%5.3f,%5.3f,%5.3f,%6.2f,%6.2f,%6.2f,"%(\
            ps["pFakt"], ps["iFakt"], ps["dFakt"], ps["tauTempVl"],\
            ps["tauTempRl"], ps["tauM"] )
        #print("s=",s)
        txCmd = mb.wrap_modbus( modAdr, 0x23, subAdr, s )
        #print(txCmd)
        if not net_dialog(txCmd):
            return False

        # send:
        #   m2hi, m2lo,
        #   tMotPause, tMotBoost, dtMotBoost, dtMotBoostBack, tempTol
        time.sleep(0.2)
        s = ",%5.3f,%5.3f,%d,%d,%d,%d,%3.1f,"%(\
            ps["m2hi"], ps["m2lo"], ps["tMotPause"], ps["tMotBoost"],\
            ps["dtMotBoost"], ps["dtMotBoostBack"], ps["tempTol"] )
        #print("s=",s)
        txCmd = mb.wrap_modbus( modAdr, 0x24, subAdr, s )
        #print(txCmd)
        if net_dialog(txCmd):
            return True
        return False


def set_motor_lifetime_status(modAdr,subAdr):
    ''' send the regulator motor lifetime status values to module nr. modAdr
        subAdr 1,2,3: regulator 1,2,3, reg-index 0,1,2,
    '''
    if subAdr in [1,2,3]: # parameter regulator
        # send:
        #   tMotTotal, nMotLimit
        ps = parameters[modAdr]["r"][subAdr]
        s = ",%3.1f,%d,"%(ps["tMotTotal"], ps["nMotLimit"] )
        #print("s=",s)
        txCmd = mb.wrap_modbus( modAdr, 0x25, subAdr, s )
        #print(txCmd)
        #print(txCmd)
        if net_dialog(txCmd) :
            return True
        return False


def set_factory_settings(modAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x30, 0, "" )
    print(txCmd)
    if net_dialog(txCmd):
        return True
    return False


def set_regulator_active( modAdr, subAdr, onOff ):
    # onOff     0: switch off,  1: switch on
    if onOff != 0:
        onOff = 1
    s = ",%d,"%( onOff )
    txCmd = mb.wrap_modbus( modAdr, 0x35, subAdr, s )
    if net_dialog(txCmd):
        return True
    return False


    
def valve_move(modAdr, subAdr, duration, direct):
    # duration      ms;    motor-on time
    # dir           1;     0:close, 1:open, 2:startpos
    if subAdr in [1,2,3]:
        s = ",%d,%d,"%(duration,direct)
        txCmd = mb.wrap_modbus( modAdr, 0x31, subAdr, s )
        if net_dialog(txCmd):
            return True
        return False


def set_normal_operation(modAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x34, 0, "" )
    if net_dialog(txCmd):
        return True
    return False


def set_fast_mode( modAdr, mode ):
    # onOff     0: normal mode,  else: fast operation
    s = ",%d,"%( mode )
    txCmd = mb.wrap_modbus( modAdr, 0x36, 0, s )
    if net_dialog(txCmd):
        return True
    return False


def get_milisec(modAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x37, 0, "" )
    if net_dialog(txCmd):
        return True
    return False


def cpy_eep2ram(modAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x38, 0, "" )
    if net_dialog(txCmd):
        return True
    return False

def cpy_ram2eep(modAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x39, 0, "" )
    if net_dialog(txCmd):
        return True
    return False

def wd_halt_reset(modAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x3A, 0, "" )
    if net_dialog(txCmd):
        return True
    return False

def clr_eep(modAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x3B, 0, "" )
    if net_dialog(txCmd):
        return True
    return False

def check_motor(modAdr,subAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x3C, subAdr, "" )
    print("check_motor, txCmd=",txCmd)
    if net_dialog(txCmd):
        return True
    return False

def calib_valve(modAdr,subAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x3D, subAdr, "" )
    if net_dialog(txCmd):
        return True
    return False

def motor_off(modAdr,subAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x3E, subAdr, "" )
    if net_dialog(txCmd):
        return True
    return False

def get_motor_current(modAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x3F, 0, "" )
    if net_dialog(txCmd):
        return True
    return False

def lcd_backlight(modAdr, onOff):
    if onOff:
        s=",1,"
    else:
        s=",0,"
    txCmd = mb.wrap_modbus( modAdr, 0x40, 0, s )
    if net_dialog(txCmd):
        return True
    return False

def get_jumpers(modAdr):
    txCmd = mb.wrap_modbus( modAdr, 0x41, 0, "" )
    if net_dialog(txCmd):
        return True
    return False

def get_version(modAdr):
    # TODO: add function to later Arduino-Nano Firmware
    #       with own command-nr
    # not implemented in Arduino-Nano Version
    # 1.0.b, 2020-09-26, "hr2_reg07pl_Serie01/..."

    # version of modules which do not answer
    st.fwVersion = "1.0.b"
    st.fwDate = "2020-09-26"
    return True


# ---------------------------------------
# interface for logger
# ---------------------------------------

import time


def get_log_data(mod,reg,heizkreis):
    # *** read status if module available
    if not ping(mod):
        print("module not available")
        return False
    else:

        read_stat(mod,reg)     # result is in cn2 and cn4

        get_milisec(mod)
        get_jumpers(mod)

        # *** print data
        print("="*40)
        print("cn2=",cn2)
        print("cn4=",cn4)
        print("timestamp ms=",st.rxMillis)
        print("Jumper settings=%02x"%(st.jumpers))
        print("-"*40)
        
        # *** build a data-set
        # "20191016_075932 0401 HK2 :0002041a t4260659.0  S "
        # "VM 49.5 RM 47.8 VE 20.0 RE 47.8 RS 32.0 P074 E0000 FX0 M2452 A143"
        
        # header:
        dateTime = time.strftime("%Y%m%d_%H%M%S",time.localtime())
        header   ="%s %02X%02X HK%d :"%(dateTime,mod,reg,heizkreis)
        # module data:
        cmdHead  ="0002%02X%db "%(mod,reg)
        tic      = float(st.rxMillis) / 1000.0
        ticStr   ="t%.1f "%(tic)
        vlMeas   = float(cn2["VM"])
        rlMeas   = float(cn2["RM"])
        vlEff    = float(cn2["VE"])
        rlEff    = float(cn2["RE"])
        vlrl     = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f "%(vlMeas,rlMeas,vlEff,rlEff)
        
        s = header + cmdHead + ticStr +cn2["SN"] + " " + vlrl

        '''
        %s VM%5.1f RM%5.1f VE%5.1f RE%5.1f RS%5.1f P%03d "\
                   "E%04X M%d A%d"%\
                   (st.rxMillis/1000.0, cn2["SN"], cn2["VM"], cn2["RM"], \
                    cn2["VE"], cn2["RE"], cn2["RS"], cn2["PM"], \
                    cn2["ER"], cn2["FX"], cn2["MT"], \
                    cn4[""], cn4[""] ) #nL NB ???
        '''
        print(s)
        
        return True









