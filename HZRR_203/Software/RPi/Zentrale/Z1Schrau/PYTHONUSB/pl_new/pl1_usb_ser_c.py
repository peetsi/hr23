#!/usr/bin/env python3
# -*- coding: utf-8 -*-


'''
****************************************************
Functions for serial communication via RS485 network
pl, 25.07.2021
****************************************************
'''

import os
import sys
import platform
import time
import configparser
import serial
import traceback

from pl1_hr23_variables import *
from pl1_modbus_c import modbus_wrap, parse_command_header
import pl1_hr23_parse_answer as par
import pl1_usb_ser_c as us
import pl1_modbus_c as mb

#  ***************************
#  CONNECT USB-RS485 Interface
#  ***************************

# *** serial parameters
sp = None   # will be defined in ser_instatnce()
# *** handle of serial RS485 USB-Interface
ser= None   # will be assigned in ser_instance()


def sp_init():
    global sp

    err=0
    configFile='config/pl1_hr23_config.ini'
    try:
        hr23Cfg = configparser.ConfigParser()
        hr23Cfg.read(configFile)
        sp = {
            "portWin"     :  hr23Cfg['SerialBus']['serialPort_WIN'],
            "portRPi3"    :  hr23Cfg['SerialBus']['serialPort_PiThree'],
            "portRPi4"    :  hr23Cfg['SerialBus']['serialPort_PiFour'],
            "port"        :  hr23Cfg['SerialBus']['serialPort_PiFour'],  # TODO
            # TODO select automatically from system information RPi or other
            "baudrate"    :  int(hr23Cfg['SerialBus']['ser_bus_baudrate']),
            "timeout"     :  float(hr23Cfg['SerialBus']['ser_bus_timeout']),
            "maxRetries"  :  int(hr23Cfg['SerialBus']['ser_bus_max_try']),
            "connected"   :  0,
        }
    except Exception as e:
        err=1
        print("error reading/assigning configuration from %s: "%(configFile),end="")
        print(e)
    return err


def ser_instantce() :
    global sp
    global ser
    err=0
    err=sp_init()
    if not err:
        sp["port"] = sp['portRPi4']   # TODO change to automatic selection

        try:
            ser = serial.Serial(
                port        = sp["port"],
                baudrate    = sp["baudrate"],
                parity      = serial.PARITY_NONE,
                stopbits    = serial.STOPBITS_TWO,
                bytesize    = serial.EIGHTBITS,
                timeout     = sp["timeout"]
            )
        except serial.SerialException as e:
            vl( 3,  "01 cannot find: %s"%(sp["port"]))
            vl( 3,  "   exception = %s"%(e))
            err = 2
        except Exception as e:
            vl( 3,  "02 other error with serial port: %s"%(sp["port"]))
            vl( 3,  "   exception = %s"%(e))
            err = 3
    time.sleep(0.1)
    return err


def ser_open():
    global ser
    err=0
    try:
        ser.open() # open USB->RS485 connection
        connected = 1
    except serial.SerialException as e:
        vl( 3,  "03 cannot open: %s"%(sp["port"]))
        vl( 3,  "   exception = %s"%(e))
        err = 3
    except  Exception as e:
        vl( 3,  "04 something else is wrong with serial port:"%(sp["port"]))
        vl( 3,  "   exception = %s"%(e))
        err = 4
    connected = 0
    time.sleep(0.1)
    return err




def ser_check():
    err=0
    global ser

    if ser is None:
        err = ser_instantce()   # define <ser> and <sp>
        if err:
            vl(3,"serial connection could not be installed "+str(err))
    elif not ser.is_open:
            err = ser_open()    # open serial port
            if err:
                vl(3,"serial connection not opened: err="+str(err))
    return err

def ser_reset_buffer():
    err=0
    ser_check()
    try:
        ser.reset_output_buffer()
        ser.reset_input_buffer()
    except serial.SerialException as e:
        err = 5
        vl( 3,  "05 cannot erase serial buffers")
        vl( 3,  "   exception = %s"%(e))
    except Exception as e:
        err = 6
        vl( 3,  "06 error with serial port: %s"%(sp["port"]))
        vl( 3,  "   exception = %s"%(e))
    time.sleep(0.01)
    return err

def connect_rs485():
    err=ser_check()
    if not err:
        ser.close()
        print("RS485 Network connection closed")




#  ***************************
#  command dialog with modules
#  ***************************

def rx_command():
    err=0
    try:
        lrx = ser.readline()     # is blocking until line read or timeout
        #print("lrx=",lrx)
    except serial.SerialTimeoutException as e:
        vl( 2, "10 timeout receiving string RS485")
        vl( 2,  "  exception = %s"%(e))
        line="serial timeout"
        err=10
    except serial.SerialException as e:
        vl( 2,  "11 SerialException on read")
        vl( 2,  "   exception = %s"%(e))
        ser.close()
        line="serial exception; "+str(e)
        err=11
    except Exception as e:
        vl( 2,  "12 error serial port while reading")
        vl( 2,  "   exception = %s"%(e))
        ser.close()
        line="other serial exception; "+str(e)
        err=12
    if err:
        return err, line
    if lrx==b"":
        err=13
        return err, "empty rx-packet"
    # *** check answer for correct format
    # received byte-array looks somehow like:
    #   b"xxx:dddd...dddd<lrc><cr><lf>"
    # the message starts with a ':'
    # there might be trash bytes 'x' before the ':' followed by data 'd'
    # and finally an xor-checksum <lrc> with carr.return-linefeed
    try:
        l0 = lrx.decode()       # make a string    
    except UnicodeDecodeError as e:
        #vl(3,"!!! UnicodeDecodeError: "+str(e))
        line="serial packet: unicode error= "+str(e)
        err=20
    except Exception as e:
        # some false byte in byte-array
        #vl( 2,  "10 cannot decode line")
        #vl( 2,  "   exception = %s"%(e))
        line = "serial rx-packet: error= "+str(e)
        err=21
    if err:
        return err,line

    if len(l0)==0:
        err=22
        return err,"rx-string empty"

    pos=l0.find(":")        # in case leading bytes are before ':'
    if pos < 0:
        # ':' missing -> received packet is invalid
        vl(3,"received line has no ':' >%s<"%(l0))
        err=23
        line="rx-string: missing ':'"
        return err,line
    else:
        line = l0[pos:]         # take part from and including ':'
        line = line.strip()     # remove white-spaces from either end
    rxd["cmdStr"] = line        # put result to global dict.

    return err,line    


def tx_command(txCmd) :
    ''' @brief  send a command and receive answer from module'''
    ''' @param  txCmd       string or bytearray with command to send'''
    ''' @return line        received line as string; "" if error'''
    global rxd
    err=0
    ser_check()

    # *** send command
    ser.reset_output_buffer()
    if type(txCmd)==str :
        txCmd = txCmd.encode()  # make byte-array

    ser.reset_input_buffer()    # remove trash before new bytes come in
    try:
        ser.write(txCmd)
    except serial.SerialTimeoutException as e:
        vl( 2, "07 timeout sending string: %s"%(txCmd))
        vl( 2,  "  exception = %s"%(e))
        err=1
    except serial.SerialException as e:
        vl( 2,  "08 SerialException on write")
        vl( 2,  "   exception = %s"%(e))
        ser.close()
        err=2
    except Exception as e:
        vl( 2,  "09 error serial port, writing")
        vl( 2,  "   exception = %s"%(e))
        ser.close()
        err=3
    ser.flush()                 # send out whole command
    time.sleep(0.015)
    return err

def net_dialog(txCmd):
    ''' @brief  send txCmd, wait for answer, repeat if needed'''
    global sp
    txAdr   = int(txCmd[1:3],16)    # module address to which the command is sent
    txCmdNr = int(txCmd[3:5],16)
    maxCnt = sp["maxRetries"]
    repeat = 0
    while repeat < maxCnt :
        ser_reset_buffer()
        tx_command( txCmd )
        err,rxCmd  = rx_command()
        if err:
            repeat+=1
        elif len(rxCmd) > 7:
            rxAdr   = int(rxCmd[5:7],16)    # address from sender module
            rxCmdNr = int(rxCmd[3:5],16)
            if rxCmdNr != txCmdNr:
                repeat+=1
            elif rxAdr != txAdr:
                repeat+=1
            else:
                err,parse = par.parse_answer(rxCmd)
                if err:
                    repeat += 1
                else:
                    # properly parsed answer
                    parse=parse.strip().strip(",")
                    break
        else:
            # too short
            repeat+=1
    if repeat < maxCnt:
        return 0, repeat, parse
    else:
        return -2,repeat,"netdialog: Timeout"




#  ******************************
#  module communication functions
#  ******************************

def ping_direct(modAdr,verbose):
    ''' ping directly using tx- and rx-functions '''
    txCmd = modbus_wrap( modAdr, 0x01, 0,"" )  # ping
    if verbose:
        vl(1,"    test1: txCmd=%s"%(txCmd.strip()))
    ser_reset_buffer()
    tx_command(txCmd)
    err,rxCmd = rx_command()
    if verbose:
        vl(1,"    test1: err=%d; rxCmd=%s"%(err,rxCmd))
    return err, rxCmd


def ping(modAdr,verbose):
    ''' send ping command to modAdr and return ACK/NAK/-1(timeout)'''
    txCmd = modbus_wrap( modAdr, 0x01, 0,"" ) # ping
    err,repeat,rxCmd=net_dialog(txCmd)
    if verbose:
        vl(2,"mod=%d; err=%d; repeat=%d; rxCmd=%s"%(modAdr,err,repeat,rxCmd))
    #time.sleep(0.2)
    return err,repeat,rxCmd


def read_stat(modAdr,subAdr):
    ''' read all status values from module/regulator using command 2 and 4'''
    ''' modAdr e {1,...,30}, subAdr e {0,1,2,3} <=> {mod,reg1,reg2,reg3}  '''
    # read status part 1
    vl(3,"modAdr=%d; subAdr=%d"%(modAdr,subAdr))
    txCmd = mb.modbus_wrap( modAdr, 0x02, subAdr,"" ) # staus part 1
    err,repeat,rxCmd=us.net_dialog(txCmd)
    time.sleep(0.1)
    # read status part 2
    txCmd = mb.modbus_wrap( modAdr, 0x04, subAdr,"" ) # staus part 2
    err,repeat,rxCmd=us.net_dialog(txCmd)
    time.sleep(0.1)


def get_status(modAdr,regNr,verbose=False):
    ''' read status from module modAdr/regNr; verbose'''
    txCmd = modbus_wrap( modAdr, 0x02, regNr,"" ) # staus part 1
    err,repeat,rxCmd=net_dialog(txCmd)
    if err:
        return -1,"err reading part1 of status"
    if verbose:
        print("    cmd2; err=",err,"; repeat=",repeat,"; rxCmd=",rxCmd)

    txCmd = modbus_wrap( modAdr, 0x04, regNr,"" ) # staus part 2
    err,repeat,rxCmd=net_dialog(txCmd)
    if err:
        return -2,"err reading part2 of status"
    if verbose:
        print("    cmd4; err=",err,"; repeat=",repeat,"; rxCmd=",rxCmd)
    #time.sleep(0.2)
    if verbose:
        print("    ",rst)
    return err,rst














if __name__ == "__main__":
    # Test functions, Tests

    def test_config():
        configFile='config/pl1_hr23_config.ini'
        try:
            hr23Cfg = configparser.ConfigParser()
            hr23Cfg.read(configFile)
        except Exception as e:
            err=1
            print("error reading/assigning configuration from %s: "%(configFile),end="")
            print(e)
        for label in hr23Cfg:
            # dict(Config.items('Section'))
            print(label," : ", hr23Cfg[label])
            d = dict(hr23Cfg.items(label))
            print(d)
            for item in d:
                print(item," = ",hr23Cfg[label][item])
        print(40*"- ")
    

    prog_header_var()   # test ok
    #test_config()       # test ok
    #connect_rs485()     # test ok

    sp_init()           # set serial port parameters from .ini file

    
    # Serial test - send a command for check with oszilloscope
    osziTest=0
    if osziTest:
        modAdr=2
        txCmd = modbus_wrap( modAdr, 0x01, 0,"" ) # ping
        while(True):
            tx_command(txCmd)
            time.sleep(0.5)
    
    modules=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,30]
    modules=[1,2,3,30]
    modules=[1,2,30]

    # test dialog with modules
    print("\nTest 1. ping-command, echo, directly using txrx_command()")
    for modAdr in modules:
        ping_direct(modAdr,True)


    print("\nTest 2. ping-command, echo, using net_dialog()")
    for modAdr in modules:
        ping(modAdr,True)


    print("\nTest 3. read status, using net_dialog()")
    for modAdr in modules:
        #for modAdr in [1,]:
        #print("Modul : ",modAdr)
        #for reg in [1,2,3]:
        for regNr in [1]:
            print("Module %d - Regler %d: "%(modAdr,regNr))
            get_status(modAdr,regNr,True)
