#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pl1_hr23_variables import *
import vorlaut as vor

def checksum16( s ) :
    ''' @brief  calculate checksum over s
        @param  s       type 'str' or 'bytes'
        @note   checksum will always be calcualted as 'bytes'
        @return checksum as 16-bit unsigned integer
    '''
    if type(s)==str:
        s1=s.encode()
    else:
        s1=s
    cs = 0
    for c in s1 :
        cs += c
    cs = cs & 0xFFFF    # make unsigned 16 bit
    return cs


def lrc_parity( s ) :
    ''' @brief  calculate check-byte by xor-ing all bytes of s
        @param  s   'bytes' or 'str'; will be calculated as 'bytes'
    '''
    if type(s)==str:
        s1=s.encode()
    else:
        s1=s
    lrc = 0
    for c in s1 :
       lrc = lrc ^ c
    lrc = lrc & 0x00FF
    return lrc


def modbus_wrap( adr, fnc, contr, pyld ) :
    ''' @brief  generate complete command string from input:
        @param  adr     module address to send command to
        @param  fnc     function number
        @param  contr   0 for module, 1,2,3 for controller
        @param  pyld    payload data string, could be ""
        @return string
    '''
    try:
        cmd="%02X%02X%1X%s%s"%(int(adr),int(fnc),int(contr),PROT_REV,str(pyld))
        cs = checksum16( cmd )
        cmd="%s%04X"%(cmd,cs)           # add checksum
        lrc=lrc_parity( cmd )
        cmd=":%s%02X\r\n"%(cmd, lrc)    # add ':' ancd lrc-xor
    except Exception as e:
        cmd="ERROR_WRAPPING_MODBUS"
        print("wrap_modbus exception:",e)
    return cmd


def modbus_unwrap( line ) :
    '''
    @brief  a modbus string us unwrapped (see below)
    @param  line is a STRING (no byte-array)
    @retrun unwrapped payload
    example is the answer to a status command Nr. 02 to mdule adr.02
    // ":0002021b VM25.7 RM25.8 VE0.0 RE0.0 RS0.0 PM88 0A003F\r\n"
    // pos  chars  description
    //  0   :      lead-in
    //  1   00     master-address of packet (central PC)
    //  3   02     command nr to which was answered
    //  5   02     from-address (own module address)
    //  7   1      sub-address, 0=module, 1,2,3 is regulator 0,1,2
    //  8   b      protocol type b for HZRR200
    //  9...       >>> payload string >>>
    //                 e.g. VM25.7 RM25.8 VE0.0 RE0.0 RS0.0 PM88
    // -3   0A00x  2 byte checksum
    // -1   3F     LRC - XOR checksum
    // \r\n  carriage-return
    @note   \r\n may be not present in <line>
    '''
    err = 0
    s = line.strip()        # remove whitespaces and \r\n
    n = len( s )
    if n==0 :
        err |= 1
        return err, "err: len=0"

    if s[0] != ":" :
        err |= 2
        return err, "err: missing ':'"

    lrc = lrc_parity(s[1:-2])  # note: lrc byte is in 2-byte notation in hex !!!
    clrc = int(s[-2:],16)
    if lrc != clrc:
        err |= 4
        return err,"err: xor parity wrong: %02Xx"%(lrc)

    s0 = s[n-6:n-2]         # hex-checksum
    try:
        rxCsum = int(s0,base=16)
    except Exception as e:
        err |= 8
        return err,"rx-checksum wrong format: "+str(e)
    else:
        calcCsum=checksum16( s[ 1 : n-6 ] ) # omit ':', <csum> and <lrc>

    if rxCsum!=calcCsum :
        err |= 16
        return err, "err_rx=0x%02X: rxCs=%04X != cs=%04X"%(err,rxCsum,calcCsum)
    else:
        return 0, line[ 1 : n-6 ]           # payload ok


def parse_command_header(cmd):
    ''' @brief  extract header information from received payload string
        @param  cmd     string containing payload
        @return err     0 is ok; err-nr else
        @return rxd     global dictionary with parameters set
        // pos     0123456789...                              ...
        // e.g.: ":0002021b VM25.7 RM25.8 VE0.0 RE0.0 RS0.0 PM88"
        //         +-head-+-------payload data-----------------+
    '''
    global rxd
    err=0
    pos=0
    try:
        rxd["adr"]      =  int(cmd[pos+0:pos+2],16)
        rxd["cmdNr"]    =  int(cmd[pos+2:pos+4],16)
        rxd["sender"]   =  int(cmd[pos+4:pos+6],16)
        rxd["subAdr"]   =  int(cmd[pos+6],16)
        rxd["prot"]     =  cmd[pos+7]
        rxd["pyld"]     =  cmd[pos+8:]
    except Exception as e:
        print("parse_modubus exception:",e)

    if rxd["subAdr"] not in [0,1,2,3]:
        err=1
        pyld="wrong sub-address"
    elif cmd[7] != PROT_REV:
        err=2
        pyld="wrong protocol version"+str(cmd[8])
    else:
        pyld=cmd[9:]
    return err,pyld

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

    def show_command_header():
        global rxd
        print("addr to:         ",rxd["adr"] )   
        print("cmd Nr.:         ",rxd["cmdNr"] )   
        print("adr from:        ",rxd["sender"] )  
        print("subadr:          ",rxd["subAdr"] ) 
        print("protocol:        ",rxd["prot"] )
        print("payload:         ",rxd["pyld"] )
        prog_header_var()   # test ok

    # usage examples

    # example 1
    modAdr = 2
    cmd    = 1    # ping-command
    madr   = 0    # address module (not regulator 1,2 or 3
    cmdtxt = ""   # no data needed
    txCmd  = modbus_wrap( modAdr, cmd, 0, cmdtxt )
    print("modbus-string=",txCmd)   
    s = modbus_unwrap( txCmd )
    print("unwrapped    =",s)
    err,pyld=parse_command_header("00"+s[1])    # make a receive string
    if err:
        print("parse_command_header() error Nr.%d"%(err))
    else:
        show_command_header()
    print(40*"- ")

    # example 2
    # send Vorlauf temperature command 0x20
    tempSend = 45.6
    txCmd = modbus_wrap( modAdr, 0x20, 0, ' '+str(tempSend)+' ' )
    print(txCmd)
    s = modbus_unwrap( txCmd )
    print("unwrapped    =",s)
    err,pyld=parse_command_header("00"+s[1])    # make a receive string
    if err:
        print("parse_command_header() error Nr.%d"%(err))
    else:
        show_command_header()
    print(40*"- ")
    
