#!/usr/bin/env python3
# -*- coding: utf-8 -*-


'''
****************************************************
Functions for serial communication via RS485 network
pl, 25.07.2021
****************************************************
'''

import os
from pl1_modbus_c import modbus_wrap, parse_command_header
import sys
import platform
import time
import configparser
import serial
import traceback

from pl1_hr23_variables import *
import vorlaut as vor
import pl1_hr23_parse_answer as par

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
            vor.vorlaut( 3,  "01 cannot find: %s"%(sp["port"]))
            vor.vorlaut( 3,  "   exception = %s"%(e))
            err = 2
        except Exception as e:
            vor.vorlaut( 3,  "02 other error with serial port: %s"%(sp["port"]))
            vor.vorlaut( 3,  "   exception = %s"%(e))
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
        vor.vorlaut( 3,  "03 cannot open: %s"%(sp["port"]))
        vor.vorlaut( 3,  "   exception = %s"%(e))
        err = 3
    except  Exception as e:
        vor.vorlaut( 3,  "04 something else is wrong with serial port:"%(sp["port"]))
        vor.vorlaut( 3,  "   exception = %s"%(e))
        err = 4
    connected = 0
    time.sleep(0.1)
    return err


def ser_reset_buffer():
    err=0
    try:
        ser.reset_output_buffer()
        ser.reset_input_buffer()
    except serial.SerialException as e:
        err = 5
        vor.vorlaut( 3,  "05 cannot erase serial buffers")
        vor.vorlaut( 3,  "   exception = %s"%(e))
    except Exception as e:
        err = 6
        vor.vorlaut( 3,  "06 error with serial port: %s"%(sp["port"]))
        vor.vorlaut( 3,  "   exception = %s"%(e))
    return err


def ser_check():
    err=0
    global ser

    if ser == None:
        err = ser_instantce()   # define <ser> and <sp>
        if err:
            vor.vorlaut(3,"serial connection could not be installed "+str(err))
    else:
        if not ser.is_open:
            err = ser_open()    # open serial port
            if err:
                vor.vorlaut(3,"serial connection not opened",err)
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
        vor.vorlaut( 2, "10 timeout receiving string RS485")
        vor.vorlaut( 2,  "  exception = %s"%(e))
        err=10
    except serial.SerialException as e:
        vor.vorlaut( 2,  "11 SerialException on read")
        vor.vorlaut( 2,  "   exception = %s"%(e))
        ser.close()
        err=11
    except Exception as e:
        vor.vorlaut( 2,  "12 error serial port while reading")
        vor.vorlaut( 2,  "   exception = %s"%(e))
        ser.close()
        err=12

    # *** check answer for correct format
    # received byte-array looks somehow like:
    #   b"xxx:dddd...dddd<lrc><cr><lf>"
    # the message starts with a ':'
    # there might be trash bytes 'x' before the ':' followed by data 'd'
    # and finally an xor-checksum <lrc> with carr.return-linefeed
    try:
        l0 = lrx.decode()       # make a string    
    except UnicodeDecodeError as e:
        vor.vorlaut(3,"!!! UnicodeDecodeError: "+str(e))
        line=""
    except Exception as e:
        # some false byte in byte-array
        vor.vorlaut( 2,  "10 cannot decode line")
        vor.vorlaut( 2,  "   exception = %s"%(e))
        line = ""
        err=12
    pos=l0.find(":")
    line = l0[pos:]         # take part from and including ':'
    line = line.strip()     # remove white-spaces from either end
    rxd["cmdStr"] = line    # put result to global dict.
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
        vor.vorlaut( 2, "07 timeout sending string: %s"%(txCmd))
        vor.vorlaut( 2,  "  exception = %s"%(e))
        err=1
    except serial.SerialException as e:
        vor.vorlaut( 2,  "08 SerialException on write")
        vor.vorlaut( 2,  "   exception = %s"%(e))
        ser.close()
        err=2
    except Exception as e:
        vor.vorlaut( 2,  "09 error serial port, writing")
        vor.vorlaut( 2,  "   exception = %s"%(e))
        ser.close()
        err=3
    ser.flush()                 # send out whole command
    time.sleep(0.015)
    return err

def net_dialog(txCmd):
    ''' @brief  send txCmd, wait for answer, repeat if needed'''
    txCmdNr = int(txCmd[3:5],16)
    maxCnt = sp["maxRetries"]
    repeat = 0
    try:
        while repeat < maxCnt :
            ser_reset_buffer()
            tx_command( txCmd )
            err,rxCmd  = rx_command()
            if err:
                err,rxCmd = rx_command()    # try reading again
            if len(rxCmd) > 7:
                rxCmdNr = int(rxCmd[3:5],16)
                #print("cmdNrs tx/rx=",txCmdNr,"/",rxCmdNr,end="")
            err,parse = par.parse_answer(rxCmd)
            if err:
                print("repeat=",repeat,"; err=",err,"; parse=",parse)
                repeat += 1
            else:
                return err, repeat, parse
    except Exception as e:
        print("netdialog: error sending / receiving data",e)
        print(traceback.format_exc())
        return -1,repeat,e
    
    if repeat < maxCnt:
        return 0, repeat, parse
    else:
        return -2,repeat,"netdialog: Timeout"





if __name__ == "__main__":
    # Test functions, Tests
    
    def prog_header_var():
        print()
        cmdLine=sys.argv
        progPathName = sys.argv[0]
        progFileName = progPathName.split("/")[-1]
        print(60*"=")
        print("ZENTRALE: %s"%(progFileName))
        print(60*"-")


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

    # test dialog with modules
    print("Test 1. ping-command, echo, directly using txrx_command()")
    modAdr=1
    txCmd = modbus_wrap( modAdr, 0x01, 0,"" )  # ping
    print("txCmd=",txCmd)
    tx_command(txCmd)
    err,rxCmd = rx_command()
    print("rxCmd=",rxCmd)

    print("Test 2. ping-command, echo, using net_dialog()")
    for modAdr in [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,30]:
        txCmd = modbus_wrap( modAdr, 0x01, 0,"" ) # ping
        err,repeat,rxCmd=net_dialog(txCmd)
        print("mod=",modAdr,"; err=",err,"; repeat=",repeat,"; rxCmd=",rxCmd)
        #time.sleep(0.2)

    print("Test 3. read status, using net_dialog()")
    for modAdr in [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,30]:
        #for modAdr in [1,]:
        print("Modul : ",modAdr)
        #for reg in [1,2,3]:
        for reg in [1]:
            print("  regulator: ",reg)
            txCmd = modbus_wrap( modAdr, 0x02, reg,"" ) # staus part 1
            err,repeat,rxCmd=net_dialog(txCmd)
            print("    cmd2; err=",err,"; repeat=",repeat,"; rxCmd=",rxCmd)

            txCmd = modbus_wrap( modAdr, 0x04, reg,"" ) # staus part 2
            err,repeat,rxCmd=net_dialog(txCmd)
            print("    cmd4; err=",err,"; repeat=",repeat,"; rxCmd=",rxCmd)
            #time.sleep(0.2)
            print(rst)
