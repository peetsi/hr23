#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#from __future__ import absolute_import

import copy
import functools
import os
import random
import string
import threading as th
import time
import traceback
import serial

import hz_rr_config as cg
import hz_rr_debug as dg
import modbus_b as mb
import hr2_variables as st
from hr2_variables import *


def singleton(cls):
    """Make a class a Singleton class (only one instance)"""
    @functools.wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if not wrapper_singleton.instance:
            wrapper_singleton.instance = cls(*args, **kwargs)
        return wrapper_singleton.instance
    wrapper_singleton.instance = None
    return wrapper_singleton

@singleton
class Serbus(th.Thread):
    ser=port=baudrate=parity=stopbits=bytesize=timeout= \
        cmdHead=tic=ticStr=vlMeas=rlMeas=vlEff=rlEff=vlrl=dateTime=header= \
            txCmd=ps=p=read_stat_str=rxCmd=rxCmdLast=connected= None

    def __init__(self,serT=0.5,rxT=1,netR=3):
        h = cg.hkr_obj.get_heizkreis_config(0)
        if len(h) > 5:                    (self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, self.filtFakt) = h
        else:                             (self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, self.filtFakt) = (self.default_values)
        self.threadID                   = th.Thread.__init__(self)
        self.dbg                        = dg.Debug(1)
        self.comm_req                   = []
        self.comm_rsp                   = ""
        self.comm_working               = False
        self.comm_rspTo                 = ""
        self.comm_rspListDict           = list()# [{'':''},]
        self.comm_ttl_count_dct         = dict()
        self.comm_ttl_count_max         = 7                 # retries before dumping the answer from the response queue
        self.comm_current_max_options   = 3
        self.comm_TTL                   = int(cg.conf_obj.r('SerialBus', 'queue_handler_max_ttl', 7)) # second maximum until queue force-ends
        self.comm_TTL_timer_end         = None
        self.comm_TTL_timer             = None
        self.comm_TTL_timer_s_end       = None
        self.comm_TTL_timer_s           = None
        self.comm_getdone               = True # init value!
        self.comm_firstrun              = True
        self.logger_pause               = False
        self.terminal_running           = False
        self.tries_last_ping            = 0
        self.__rx_response              = None
        self.__rx_called_by_terminal    = False
        self.block_log_until_TTL        = 0
        self.logger_run                 = 0
        self.menu_run                   = 0
        self.erFlag                     = 0
        self.fixPos                     = 0
        self.motTime                    = 0
        self.nLimit                     = 0
        self.serPortWin                 = str(cg.conf_obj.r('system','serialPort_WIN' ))
        self.serPortPithr               = str(cg.conf_obj.r('system','serialPort_PIthree' ))
        self.serPortPifou               = str(cg.conf_obj.r('system','serialPort_PIfour' ))
        self.MAX_READ_STAT_RETRIES      = int(cg.conf_obj.r('SerialBus', 'max_read_stat_retry_count', 3))
        self.ser_bus_to                 = float(cg.conf_obj.r('SerialBus','ser_bus_timeout', '-1' ))
        self.ser_bus_rx_to              = float(cg.conf_obj.r('SerialBus','ser_bus_rx_timeout', '-1' ))
        self.ser_bus_netdiag_max_try    = int(cg.conf_obj.r('SerialBus','ser_bus_netdiag_max_try', '-1' ))
        self.ser_bus_baud_rate          = int(cg.conf_obj.r('SerialBus','ser_bus_baud_rate', '-1' ))
        self.SER_TIMEOUT                = serT   if self.ser_bus_to                 == -1 else self.ser_bus_to
        self.RX_TIMEOUT                 = rxT    if self.ser_bus_rx_to              == -1 else self.ser_bus_rx_to
        self.NET_REPEAT                 = netR   if self.ser_bus_netdiag_max_try    == -1 else self.ser_bus_netdiag_max_try
        self.baudrate                   = 115200 if self.ser_bus_baud_rate          == -1 else self.ser_bus_baud_rate
        self.serPort                    = self.serPortWin if not cg.conf_obj._tbl.islinux() else self.serPortPifou
        self.queue_failsafe_counter     = 0
        self.queue_failsafe_counter_max = 6
        self.running                    = True
        self.spam_debug_level           = 11
        self._this_response_request_by  = ""
        self.default_values             = (None,None,None,None,None,None,)
        self.__cn_flag                  = 4
        self._THIS_IDENTIFIER_          = ""
        self._THIS_IDENTIFIER_LAST      = ""
        self._SERBUS_RUNNING_RXCMD      = "LAST_RXCMD_SEND"
        self._SERBUS_RUNNING_TXCMD      = "LAST_TXCMD_DECODED"

        if cg.conf_obj._tbl.islinux(): self.device_model = os.system('cat /proc/device-tree/model')#('cat /sys/firmware/devicetree/base/model')
        super().setDaemon(True)
        super().start()
        self.dbg.m("Serbus communication handler started", cdb = 1)

    def __del__(self):
        self.running = False

    def __call__(self):
        pass

    def run(self):
        while True:
            time.sleep(0.01)
            # work on the list
            if not self.comm_firstrun == True: 
                while (not self.__work_available()): time.sleep(0.01)# just wait  until work is done
            else: self.dbg.m("skipping the blockade on the first run. to avoid wrong debug messages.", cdb = 1)
            if (self.comm_working == False):
                self.dbg.m("comm handle request start. waiting for request.", cdb=3)
                self.comm_handle_requests()

    def request(self, request_tuple, cbt=0):
        self.dbg.m("adding request_BEFORE:",request_tuple,cdb=11)
        self.__addRequest(request_tuple, cbt)

    def __comm_handle_exec_list_has_elements(self):
        print("(len(self.comm_req)):",(len(self.comm_req)))
        return (len(self.comm_req))

    def __comm_handle_pre_check(self,dir=0) -> None:
        pass

    def __comm_handle_build_call(self,cmd) -> str: #_args = [f"{_x}" for _x in cmd if (_x != cmd[0] and _x != cmd[-1])]
        #pre check command...:
        avail_cmds = dir(self)
        #print(avail_cmds)
        if not cmd[0] in avail_cmds:
            #print(f"FAIL! cmd:{cmd[0]}; not in {avail_cmds}")
            return False, False, False, False
        #print(f"FOUND! cmd:{cmd[0]}; in {avail_cmds}")
        cmd = list(cmd)

        for i in range(1,len(cmd)-self.comm_current_max_options): cmd[i] = int(cmd[i]) #hotfix
        _r = str(cmd[1:len(cmd)-self.comm_current_max_options]).strip()[1:-1]
        if (len(_r)<3): _r = _r.replace(',','') # 1,
        retVal = ""
        _locals = locals()
        _exec = f"retVal = self.{cmd[0]}( {_r} )"
        _e = _exec
        self._THIS_IDENTIFIER_ = _identifier = cmd[-1]
        _c = 4 if (cmd[-2] == True) else 2
        self._set_cn_flag(_c)
        _options = cmd[(self.comm_current_max_options*-1):]#cmd[(len(cmd)-self.comm_current_max_options)*-1::]
        self.dbg.m(f"_r({_r}), call({_e}), ident({self._THIS_IDENTIFIER_}), _options({_options[-2]}) _c({_c})",cdb=3)
        return _exec, _locals, _identifier, _options

    def __comm_handle_call_func(self, cmd, tries = 0) -> tuple:
        _exec, _locals, _ident, _options = self.__comm_handle_build_call(cmd)
        #print("_exec:",_exec)
        if _exec == False:
            return self.__setResponse((False, self._THIS_IDENTIFIER_)), False
        #exec(_exec, globals(), _locals )
        #print("_exec:",_exec)
        #print("_locals:",_locals)
        try: exec(_exec, globals(), _locals )
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.dbg.m(f"(_e:{_exec}, _e:{_ident}, e:{e}), tries={tries}", cdb=-7)
            traceback.print_tb(exc_traceback, limit=100)
            if tries < 3:
                return self.__comm_handle_call_func(cmd,tries+1)
            return self.__setResponse((False,self._THIS_IDENTIFIER_)), False
        _vals, _i = _locals['retVal'], self._THIS_IDENTIFIER_
        self.dbg.m(f"(tries: {tries}, _e:{_exec},_i:{_ident}), _o({_options}), _vals:", _vals, "//_i:", _i,cdb=4)
        if len(_options) > 1: st.parse_key(_i,_options[-2])
        return _vals, _i

    def __comm_handle_debug_incoming_cmd(self,cmd):
        self.dbg.m(f"({cmd})",cdb=5)
        self.dbg.m(f"command({cmd[0]}),args({cmd[1:(len(cmd)-self.comm_current_max_options)]})," \
                     f"options({cmd[(self.comm_current_max_options*-1)+1:]})",cdb=5)

    def __comm_handle_reset_working_state(self):
        self.dbg.m('__comm_handle_reset_working_state: resetting',cdb=9)
        self.comm_working = False
        self.comm_getdone = False

    def __comm_handle_request_TTL_passed(self):
        self.dbg.m('TTL Fail of comm handler Entry',cdb=1)
        return self.__setResponse((False,'TTL has been exceeded'))


    def comm_handle_requests(self,dir = 0,reent=False):
        self.comm_firstrun      = False
        list_size               = len(self.comm_req)
        if dir != 0:              self.dbg.m("comm_handle_request recursive entry -dir:",dir,cdb=3)
        if reent != True:         self.dbg.m("list size:",list_size,";data:",self.comm_req,cdb=2)
        _did_pop, __mstr = False, 'comm_handle_requests: begin work with a ttl of '+ str(self.comm_TTL) +' seconds'
        if (list_size > 0):
            self.comm_working = True
            try:
                self.__comm_handle_pre_check(dir)
                cmd, _did_pop   = self.comm_req.pop(dir), True
                self.__comm_handle_debug_incoming_cmd(cmd)
                x,y         = self. __comm_handle_call_func(cmd)
                return self.__setResponse((x,y))
            finally:
                self.__comm_handle_reset_working_state()
        if _did_pop and self.__passedTTL(intern_ttl=True):
            return self.__comm_handle_request_TTL_passed()

    def __work_available(self):
        self.dbg.m("is work available:", (True if len(self.comm_req)>0 else False), cdb=self.spam_debug_level)
        return True if len(self.comm_req) > 0 else False

    def __addRequest(self,request_tuple,cbt=0):#,identifier=""):
        self.dbg.m(f"__addReqest(request_tuple:{request_tuple},cbt:{cbt}", cdb=3)
        if (cbt == 1):
            self.set_called_by_terminal()
            self.dbg.from_term(True)
        return self.comm_req.append(request_tuple)#gc.disable()#gc.enable()

    def __passedTTL(self, intern_ttl=False) -> bool:
        self.dbg.m("__passedTTL: entering", cdb = self.spam_debug_level)
        if (self.comm_TTL_timer_s == None   or self.comm_TTL_timer_s_end    == None): return True
        if intern_ttl != True:
            pass
        else:  #intern ttl manager, to finish a request.
            self.comm_TTL_timer_s = time.time()
            _r = (self.comm_TTL_timer_s > self.comm_TTL_timer_s_end)
            self.dbg.m("__passedTTL:TTL > TTL END - (self.comm_TTL_timer_s > self.comm_TTL_timer_s_end)", _r, cdb=3)#cdb = self.spam_debug_level)
            return _r

    # RX receiver functions
    def get_rx_response(self):
        x   = "\n"+("-"*30)+"[TERMINAL OUTPUT]:" + self.__rx_response
        x  += "\n\n"+("-"*30)+"[CONSOLE LOG]:\n" + str(st.get_terminal_buf())# self.__set_rx_response(self.dbg.get())
        if x != None:
            self.dbg.m("__get_rx_response:",x,cdb=3)
            self.__reset_rx_response()
            return x
        else:
            self.__reset_rx_response()
            self.dbg.m("__get_rx_response: 'None' (empty)", cdb=3)
            return ""

    def __append_rx_response(self,val,cbt=False):
        if cbt == False:
            return #self.dbg.m("__append_tx_response: not called by terminal",cdb=11)
        if self.__rx_response == None: self.__rx_response = ""
        self.__rx_response += "\n" + str(val)
        self.dbg.m("__append_tx_response:",self.__rx_response,cdb=9)

    def __set_rx_response(self,val):
        self.__append_rx_response( str(val), self.__rx_called_by_terminal )

    def set_called_by_terminal(self,v=True):
        if v == True:
            self.__set_called_by_terminal(True)
        else:
            self.__set_called_by_terminal(False)

    def __set_called_by_terminal(self, v=True):
        self.__rx_called_by_terminal = True
        st.from_term(True)

    def __reset_rx_response(self):
        self.__rx_called_by_terminal = False
        self.__rx_response = None
        st.from_term(False)

    def __resetTTL(self, intern_ttl=False):
        if intern_ttl != True:
            pass
        else:  #intern ttl manager, to finish a request.
            self.dbg.m("__resetTTL: entering [SEND QUEUE TTL]", cdb = 10)
            self.comm_TTL_timer_s     = None
            self.comm_TTL_timer_s_end = None
            self.dbg.m("__resetTTL:comm_TTL_timer", self.comm_TTL_timer, "//comm_TTL_timer:",self.comm_TTL_timer, cdb = self.spam_debug_level)

    def __setResponse(self,response):
        self._THIS_IDENTIFIER_LAST = self._THIS_IDENTIFIER_
        self.dbg.m(f"__setResponse({response}) entering..", cdb = 10)

        if (type(self.comm_rsp)==type(bool)):
            _x = 'True' if (type(self.comm_rsp)==type(bool) and self.comm_rsp==True) else 'False'
            _t = _x[:50]#self.comm_rsp[:50] # cut lenght..
        self.__resetTTL(intern_ttl=True) # removee serbus working on TTL

        try:    self.__set_rx_response( '%s -> %s'%(str(response[0]),str(response[1])) )
        except: self.__set_rx_response( '%s -> %s'%(str(self.comm_rsp),str(self.comm_rspTo)) )
        #print("response:", response, "\nself.comm_rspTo:", self.comm_rspTo)

        if (type(response[0]) != bool):
            _x_ = str(response[1]) if type(response[1]) != str else response[1]
            _s = _x_ + "_ser_rsp"
            st.s(_s,str(response[0]))
        self.comm_working   = False
        self.comm_getdone   = False

    def __response_gathered(self,ttl_pass=False):
        self.comm_working   = False
        self.comm_firstrun  = False

    def ser_instant(self, err=0) :
        try:
            self.ser = serial.Serial(
                port     = self.serPort,
                baudrate = self.baudrate,
                parity   = serial.PARITY_NONE,
                stopbits = serial.STOPBITS_TWO,
                bytesize = serial.EIGHTBITS,
                timeout  = self.SER_TIMEOUT)
            self.dbg.m(f"ser_instant(p:{self.serPort},baud:{self.baudrate},"+ \
                    f"par:{serial.PARITY_NONE},stopb:{serial.STOPBITS_TWO},bsize:{serial.EIGHTBITS},"+ \
                        f"ttl:{self.SER_TIMEOUT})",cdb=1)
        except serial.SerialException as e:
            self.dbg.m(f"ser_instant() SerialException:", e,cdb=-7)
            err = 1
        except Exception as e:
            self.dbg.m(f"ser_instant() Exception:", e,cdb=-7)
            err = 2
        return err

    def ser_open(self, err=0):
        try:
            self.ser.open() # open USB->RS485 connection
            self.connected = 1
        except serial.SerialException as e:
            self.dbg.m(f"ser_open() SerialException:", e,cdb=-7)
            err = 3
        except  Exception as e:
            self.dbg.m(f"ser_open() Exception:", e,cdb=-7)
            err = 4
        self.connected = 0
        return err

    def ser_reset_buffer(self, err=0):
        try:
            self.ser.flushOutput()  # newer: ser.reset_output_buffer()
            self.ser.flushInput()   # newer: ser.reset_input_buffer()
        except serial.SerialException as e:
            err = 5
            self.dbg.m(f"ser_open() SerialException:", e,cdb=-7)
        except Exception as e:
            err = 6
            self.dbg.m(f"ser_open() Exception:", e,cdb=-7)
        return err

    def ser_check(self, err = 0):
        self.ser_instant()
        if self.ser.isOpen() == False :
            self.connected=0
            self.dbg.m("open network",cdb=1)
            err |= self.ser_open()
            if( err ) : self.dbg.m("rs485 Netz: %d"%(err),cdb=1)
            time.sleep(1.0)
            self.ser_reset_buffer()
        self.dbg.m("rs485 Netz verbunden",cdb=1)
        self.connected=1
        return

    def _txrx_command_send(self, txCmd, retries = 0):
        _btxCmd=txCmd
        if (type(self.txCmd)==str):
            self.txCmd = self.txCmd.encode()
        try:
            self.ser.write(self.txCmd)                  # start writing string
        except serial.SerialTimeoutException as e:
            self.dbg.m(f"_txrx_command_send({txCmd}) SerialTimeoutException:", e,cdb=-7)
            self.ser.close()
            if retries <= 3: return self._txrx_command_send(_btxCmd,retries+1)
            return False
        except serial.SerialException as e:
            self.dbg.m(f"_txrx_command_send({txCmd}) SerialException:", e,cdb=-7)
            self.ser.close()
            if retries <= 3: return self._txrx_command_send(_btxCmd,retries+1)
            return False
        except Exception as e:
            self.dbg.m(f"_txrx_command_send({txCmd}) Exception:", e,cdb=-7)
            self.ser.close()
            if retries <= 3: return self._txrx_command_send(_btxCmd,retries+1)
            return False
        return True

    def _txrx_command_recv_decode(self):
        l0=b""
        et = time.time() + self.RX_TIMEOUT
        while (time.time() < et) and (l0==b""): l0 = self.ser.readline()
        l1 = l0.split(b":")
        if(len(l1)==2): line = l1[1]
        else:           line = b""
        self.dbg.m('l0', l0, 'line:', line, cdb=3)
        #print("line1:",line)
        line = line.strip()             # remove white-spaces from either end
        try: line = line.decode()       # make string
        except UnicodeDecodeError as e:
            self.dbg.m(f"_txrx_command_recv_decode() UnicodeDecodeError:", e,cdb=-7)
            return False
        except Exception as e:
            self.dbg.m(f"_txrx_command_recv_decode() Exception:", e,cdb=-7)
            return False

        return line

    def txrx_command(self, txCmd, retries=0) :
        st.add('txrx_command: ' + str(txCmd))
        self.ser.reset_output_buffer()
        _r = self._txrx_command_send(txCmd)
        if (_r == False or _r == ""): return False
        self.dbg.m("_txrx_command_send('",self.txCmd,"'):", _r, cdb=3)

        self.ser.flush()
        self.ser.reset_input_buffer()   # newer:
        self.rxCmdLast  = self.rxCmd    # st.rxCmd = ""
        self.rxCmd      = ""

        time.sleep(0.01)
        line = self._txrx_command_recv_decode()
        if (line == False):               return False
        if (line == "" and retries <= 3): return self.txrx_command(txCmd,retries+1)
        if (line == ""): self.dbg.m(f'WARNING: txrx_command failed {retries} in a row.', cdb=1)
        self.dbg.m(f"_txrx_command_recv_decode():", line, "//txCmd:", self.txCmd, cdb=3)

        self.rxCmd      = line #reset after read?        #st.rxCmd        = line
        st.add('txrx_command -> self.rxCmd: ' + str(self.rxCmd))
        st.set_key(self._SERBUS_RUNNING_TXCMD, line)
        return line

    def net_dialog(self, txCmd, info=0, cn2_only_flag = False, repeat = 0 ):
        _t = str(txCmd)
        _i = str(info)
        _c = str(cn2_only_flag)
        self.dbg.m(f"net_dialog(txCmd:{_t}, info:{_i}, cn2_only_flag:{_c}). __rx_called_by_terminal:",self.__rx_called_by_terminal, cdb=4)
        st.from_term(self.__rx_called_by_terminal)
        st.add('net_dialog: ' + str(txCmd))
        self.txCmd  = txCmd
        self.tries_last_ping = repeat
        try:
            while repeat < self.NET_REPEAT :
                self.dbg.m("net_dialog.ser_reset_buffer()", cdb=9)
                self.ser_reset_buffer()
                self.dbg.m("txrx_command():", txCmd.replace('\n',''), cdb=9)
                _r = self.txrx_command( txCmd )
                _ident = self._THIS_IDENTIFIER_
                st.set_key(_ident,_r)
                self.dbg.m(f"set_key({_ident}, '{_r}'):", txCmd.replace('\n',''), cdb=4)
                _r = st.parse_key(_ident, cn2_only_flag="")
                self.dbg.m(f"parse_key({_ident}, '{_r}'):", txCmd.replace('\n',''), cdb=4)
                st.set_key(self._SERBUS_RUNNING_RXCMD, _r)
                self.__set_rx_response(st.get_terminal_buf())
                if (_r != False):
                    if info==0:
                        return _ident
                    return _ident, repeat
                else:
                    repeat += 1
                    self.tries_last_ping = repeat
                    self.dbg.m("txrx_command() ELSE occured! - did txcmd change:",txCmd,"//",self.txCmd,cdb=9)

            st._set_err_res(_ident)

            if info == 0:
                return False
            return False, repeat

        finally:
            st.from_term(False)
            st._set_err_res(_ident)

    # *****************************************
    # *** module communication commands     ***
    # *****************************************

    def ping(self, modAdr ):
        self.txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )   # cmd==1: send ping
        x, y = self.net_dialog(self.txCmd, info=1)
        return (x,y)

    #def cnget(self,c=0):
    #    x,y = st.get_cn('')
    #    return x if (c == 0) else y
    #    #return self._cn2 if (c == 0) else self._cn4

    def _get_cn_flag(self):
        return self.__cn_flag

    def _set_cn_flag(self,v=4):
        self.dbg.m([f"scanning: cn{v}" if (v == 2) else f"scanning: cn2 and cn{v}"],cdb=3)
        self.__cn_flag = v

    def __ser_serbus_call(self,ident):
        se = ("ret_mon_q", "ret_log_q", "TERMINAL", "ret_mon_valve_failback")
        for wo in se:
            _l = len(wo)*-1
            if( ident[_l:] == wo): return wo
        return True

    def read_cn2(self, modAdr, subAdr):
        _ident = self._THIS_IDENTIFIER_
        #st.set_key(_ident + "_read_stat_str", "Beginning..")
        if (st.rxMillis == ""): self.get_milisec(modAdr)
        if (modAdr == self.modTVor and subAdr > 1):
            self.dbg.m(f'read_cn2: skipping ({modAdr},{subAdr} -> ((', (modAdr == self.modTVor), f')({modAdr} == {self.modTVor}) && (subAdr > 1)(',(subAdr>1),'))')
            return False

        self.txCmd = mb.wrap_modbus( modAdr, 2, subAdr, "" )
        ident = self.net_dialog(self.txCmd)
        if not ident:
            #print("_ident:",_ident)
            #st.set_key(_ident + "_read_stat_str", f"Failed at cn2 {retry_count} times")
            if retry_count <= 3: return self.read_stat(modAdr,subAdr, retry_count +1 )
            self.__set_rx_response('read_cn2(mod=%s,sub=%s) Failed' % (str(modAdr), str(subAdr)))
            return False
        self.__set_rx_response('read_cn2(mod=%s,sub=%s) Success'%(str(modAdr),str(subAdr)))
        f=3
        _key = st.get_parsed_key(_ident, dt=2)
        self.dbg.m("buildcn with key:", _key, cdb=3)
        return self.build_cn(_ident, modAdr, subAdr, cn2str=_key, cn4str=None)

    def read_cn4(self, modAdr, subAdr):
        _ident = self._THIS_IDENTIFIER_
        _whos_dis = self.__ser_serbus_call(_ident)
        #st.set_key(_ident + "_read_stat_str", "Beginning..")
        if (st.rxMillis == ""): self.get_milisec(modAdr)

        self.txCmd = mb.wrap_modbus(modAdr, 4, subAdr, "")
        ident = self.net_dialog(self.txCmd)
        if not ident:
            #st.set_key(_ident + "_read_stat_str", f"Failed at cn4 {retry_count} times")
            if retry_count <= 3: return self.read_stat(modAdr, subAdr, retry_count + 1, skip_first=1)
            self.__set_rx_response('read_cn4(mod=%s,sub=%s) Failed' % (str(modAdr), str(subAdr)))
            return False
        self.__set_rx_response('read_cn4(mod=%s,sub=%s) Success'%(str(modAdr),str(subAdr)))

        _key = st.get_parsed_key(_ident, dt=4)
        self.dbg.m("buildcn with key:", _key, cdb=3)
        return self.build_cn(_ident, modAdr, subAdr, cn2str=None, cn4str=_key)

    def build_read_stat_str(self, modAdr, subAdr, cn2, cn4):
        _cn2 = cn2
        _cn4 = cn4
        self.cmdHead = "0002%02X%db " % (int(modAdr), int(subAdr))
        try:
            self.tic = float(st.rxMillis) / 1000.0
            self.ticStr = "t%.1f " % (self.tic)
            # cn2={"SN":0,"VM":0,"RM":0,"VE":0,"RE":0,"RS":0,"PM":0}
            self.vlMeas = float(_cn2["VM"])
            self.rlMeas = float(_cn2["RM"])
            self.vlEff = float(_cn2["VE"])
            self.rlEff = float(_cn2["RE"])
            self.rlSoll = float(_cn2["RS"])
            self.posMot = float(_cn2["PM"])
            self.erFlag = int(_cn4["ER"])
            self.fixPos = float(_cn4["FX"])
            self.motTime = float(_cn4["MT"])
            self.nLimit = int(_cn4["NL"])
        except:
            pass
        # cn4={"ER":0,"FX":0,"MT":0,"NL":0} # command names
        s1 = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f " % (self.vlMeas, self.rlMeas, self.vlEff, self.rlEff)
        s2 = "RS%5.1f P%03.0f " % (self.rlSoll, self.posMot)
        s3 = "E%04X FX%.0f M%.0f A%d" % (self.erFlag, self.fixPos, self.motTime, self.nLimit)
        # FX muss noch übersetzt werden.
        x = s1 + s2 + s3
        read_stat_str = str(self.cmdHead) + str(self.ticStr) + \
                             str(_cn2['SN']) + " " + str(x)
        self.dbg.m("read_stat_str: ", read_stat_str, cdb=9)
        #st.set_key(_ident + "_read_stat_str", read_stat_str)
        return read_stat_str

        return

    def build_cn(self, _ident, modAdr, subAdr, cn2str=None, cn4str=None):
        _whos_dis = self.__ser_serbus_call(_ident)

        if (cn2str is not None and cn4str is not None):
            _cn4 = self.build_cn(_ident, modAdr, subAdr, _cn2 ,cn4str)
            return _cn4

        elif (cn2str is None and cn4str is not None):
            q_ = cn4str#st.get_parsed_key(_ident, dt=4, serbus_call=_whos_dis)
            _cn4 = st.str_to_dict(q_)
            if _cn4 == False:
                return False
            self.dbg.m(f"serbus.read_stat(cn4).str_to_dict({type(_cn4)}):", _cn4, cdb=3)
            self.erFlag  = int(_cn4["ER"])
            self.fixPos  = float(_cn4["FX"])
            self.motTime = float(_cn4["MT"])
            self.nLimit  = int(_cn4["NL"])
            # cn4={"ER":0,"FX":0,"MT":0,"NL":0} # command names
            s1 = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f " % (self.vlMeas, self.rlMeas, self.vlEff, self.rlEff)
            s2 = "RS%5.1f P%03.0f " % (self.rlSoll, self.posMot)
            s3 = "E%04X FX%.0f M%.0f A%d" % (self.erFlag, self.fixPos, self.motTime, self.nLimit)
            # FX muss noch übersetzt werden.
            x = s1 + s2 + s3
            self.read_stat_str = str(self.cmdHead) + str(self.ticStr) + \
                                 str(self.last_env_val) + " " + str(x)
            self.dbg.m("read_stat_str: ", self.read_stat_str, cdb=9)
            st.set_key(_ident + "_read_stat_str", self.read_stat_str)
            self.last_env_val= ""
            return self.read_stat_str

        elif (cn2str is not None and cn4str is None):
            _q = cn2str#st.get_parsed_key(_ident, dt=2, serbus_call=_whos_dis)
            _cn2 = st.str_to_dict(_q)
            if _cn2 == False: #                st.set_key(_ident + "_read_stat_str", "Couldnt parse cn2 from dictionary")
                return False
            self.dbg.m(f"cn2.str_to_dict({type(_cn2)}, serbus_call:{_whos_dis}, ident:{_ident}):", _cn2, cdb=3)
            # module data:
            self.last_env_val = _cn2["SN"]
            self.cmdHead = "0002%02X%db " % (int(modAdr), int(subAdr))
            try:
                self.tic = float(st.rxMillis) / 1000.0
                self.ticStr = "t%.1f " % (self.tic)
                # cn2={"SN":0,"VM":0,"RM":0,"VE":0,"RE":0,"RS":0,"PM":0}
                self.vlMeas = float(_cn2["VM"])
                self.rlMeas = float(_cn2["RM"])
                self.vlEff = float(_cn2["VE"])
                self.rlEff = float(_cn2["RE"])
                self.rlSoll = float(_cn2["RS"])
                self.posMot = float(_cn2["PM"])
            except Exception as e:
                st.set_key(_ident + "_read_stat_str", "Exception while setting values: " + str(e))
            return _cn2
        else:
            pass
            #should not arrive here
            return False

    def read_stat(self, modAdr, subAdr, retry_count=0, skip_first=0 ) :
        _ident = self._THIS_IDENTIFIER_
        #st.set_key(_ident + "_read_stat_str", "Beginning..")
        if (st.rxMillis == ""): self.get_milisec(modAdr)
        if (modAdr == self.modTVor and subAdr > 1):
            self.dbg.m(f'read_stat: skipping ({modAdr},{subAdr} -> ((', (modAdr == self.modTVor), f')({modAdr} == {self.modTVor}) && (subAdr > 1)(',(subAdr>1),'))')
            return False
        self.__set_rx_response('read_stat(mod=%s,sub=%s)'%(str(modAdr),str(subAdr)))

        if not skip_first:
            self.txCmd = mb.wrap_modbus( modAdr, 2, subAdr, "" )
            ident = self.net_dialog(self.txCmd)
            if not ident:
                #print("_ident:",_ident)
                #st.set_key(_ident + "_read_stat_str", f"Failed at cn2 {retry_count} times")
                if retry_count <= 3: return self.read_stat(modAdr,subAdr, retry_count +1 )
                return False
            skip_first = True
            time.sleep(0.2)

        if self._get_cn_flag() == 4:
            time.sleep(0.01)
            self.txCmd = mb.wrap_modbus( modAdr, 4, subAdr, "" )
            ident = self.net_dialog(self.txCmd)
            if not ident:
                #st.set_key(_ident + "_read_stat_str", f"Failed at cn4 {retry_count} times")
                if retry_count <= 3: return self.read_stat(modAdr,subAdr, retry_count + 1, skip_first=1)
                return False
            st.parse_key(_ident,cn2_only_flag=True,set_result=True) #parse cn4
        f=3
        _whos_dis = self.__ser_serbus_call(ident)
        _cn2 = st.str_to_dict(st.get_parsed_key(ident, dt=2,serbus_call = _whos_dis))
        if _cn2 == False:
            #st.set_key(ident + "_read_stat_str", "Couldnt parse cn2 from dictionary")
            return False
        self.dbg.m(f"cn2.str_to_dict({type(_cn2)}, serbus_call:{_whos_dis}, ident:{ident}):",_cn2,cdb=3)
        # module data:
        self.cmdHead  = "0002%02X%db "%(int(modAdr),int(subAdr))
        try:
            self.tic      = float(st.rxMillis) / 1000.0
            self.ticStr   = "t%.1f "%(self.tic)
            #cn2={"SN":0,"VM":0,"RM":0,"VE":0,"RE":0,"RS":0,"PM":0}
            self.vlMeas   = float(_cn2["VM"])
            self.rlMeas   = float(_cn2["RM"])
            self.vlEff    = float(_cn2["VE"])
            self.rlEff    = float(_cn2["RE"])
            self.rlSoll   = float(_cn2["RS"])
            self.posMot   = float(_cn2["PM"])
        except Exception as e:
            st.set_key(ident + "_read_stat_str", "Exception while setting values: " + str(e))

        if (_whos_dis != 'ret_mon_q'):
            _cn4 = st.str_to_dict(st.get_parsed_key(ident, dt=4,serbus_call =_whos_dis))
            self.dbg.m(f"serbus.read_stat(cn4).str_to_dict({type(_cn4)}):",_cn4,cdb=3)
            self.erFlag  = int(  _cn4["ER"])
            self.fixPos  = float(_cn4["FX"])
            self.motTime = float(_cn4["MT"])
            self.nLimit  = int(  _cn4["NL"])
        #cn4={"ER":0,"FX":0,"MT":0,"NL":0} # command names
        s1    = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f "%(self.vlMeas,self.rlMeas,self.vlEff,self.rlEff)
        s2    = "RS%5.1f P%03.0f "%(self.rlSoll, self.posMot)
        s3    = "E%04X FX%.0f M%.0f A%d"%(self.erFlag,self.fixPos,self.motTime,self.nLimit)
        # FX muss noch übersetzt werden.
        x = s1 + s2 + s3
        self.read_stat_str = str(self.cmdHead) + str(self.ticStr) + \
                                str(_cn2["SN"]) + " " + str(x)
        self.dbg.m("read_stat_str: ", self.read_stat_str, cdb=9)
        st.set_key(ident+"_read_stat_str", self.read_stat_str)
        return self.read_stat_str

    def get_param(self, modAdr,subAdr):
        modAdr = int(modAdr)
        subAdr = int(subAdr)
        '''read module-related parameter set from module'''
        if subAdr in [0,1,2,3]:
            self.txCmd = mb.wrap_modbus( modAdr, 0x05, subAdr,"" )
            if not  self.net_dialog(self.txCmd):
                return False
            elif subAdr == 0:
                return True

            self.txCmd = mb.wrap_modbus( modAdr, 0x06, subAdr,"" )
            if not  self.net_dialog(self.txCmd):
                return False

            self.txCmd = mb.wrap_modbus( modAdr, 0x07, subAdr,"" )
            if self.net_dialog(self.txCmd):
                return True

    def send_Tvor(self, modAdr,tempSend):
        '''send Vorlauftemperatur to module'''
        self.txCmd = mb.wrap_modbus(modAdr,0x20,0,','+"%.1f"%(float(tempSend))+',')
        if self.net_dialog(self.txCmd):
            return True
        return False

    def send_param(self, modAdr,subAdr):
        try:
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
                self.p = parameters[modAdr]
                s = ",%03d,%03d,%02d,%4.1f,%4.1f,%4.1f,%4.1f,%02d,%02d,%4.1f,%3.1f,"%( \
                    self.p["timer1Tic"], self.p["tMeas"], self.p["dtBackLight"], self.p["tv0"], \
                    self.p["tv1"], self.p["tr0"], self.p["tr1"], self.p["tVlRxValid"], self.p["tVlRxValid"], \
                    self.p["tempZiSoll"], self.p["tempZiTol"] )
                #print("s=",s)
                self.txCmd = mb.wrap_modbus( modAdr, 0x22, subAdr, s )
                #self.txCmd = mb.wrap_modbus( modAdr, 0x22, subAdr, "" )
                #print(txCmd)
                if self.net_dialog(self.txCmd):
                    return True
                return False

            elif subAdr in [1,2,3]: # parameter regulator, part 1,2,3
                # send:
                #   active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax,
                #   dtOpen, dtClose, dtOffset
                #time.sleep(0.2)
                self.ps = parameters[modAdr]["r"][subAdr]
                s = ",%d,%d,%d,%d,%d,%d,%d,%d,%d,"%(\
                    self.ps["active"], self.ps["motIMin"], self.ps["motIMax"], self.ps["tMotDelay"],\
                    self.ps["tMotMin"], self.ps["tMotMax"],\
                    self.ps["dtOpen"], self.ps["dtClose"], self.ps["dtOffset"] )
                #print("s=",s)
                self.txCmd = mb.wrap_modbus( modAdr, 0x22, subAdr, s )
                #print(txCmd)
                if not self.net_dialog(self.txCmd):
                    return False

                # send:
                #   pFakt, iFakt, dFakt, tauTempVl, tauTempRl, tauM
                #time.sleep(0.2)
                s = ",%5.3f,%5.3f,%5.3f,%6.2f,%6.2f,%6.2f,"%(\
                    self.ps["pFakt"], self.ps["iFakt"], self.ps["dFakt"], self.ps["tauTempVl"],\
                    self.ps["tauTempRl"], self.ps["tauM"] )
                #print("s=",s)
                self.txCmd = mb.wrap_modbus( modAdr, 0x23, subAdr, s )
                #print(txCmd)
                if not self.net_dialog(self.txCmd):
                    return False

                # send:
                #   m2hi, m2lo,
                #   tMotPause, tMotBoost, dtMotBoost, dtMotBoostBack, tempTol
                time.sleep(0.2)
                s = ",%5.3f,%5.3f,%d,%d,%d,%d,%3.1f,"%(\
                    self.ps["m2hi"], self.ps["m2lo"], self.ps["tMotPause"], self.ps["tMotBoost"],\
                    self.ps["dtMotBoost"], self.ps["dtMotBoostBack"], self.ps["tempTol"] )
                #print("s=",s)
                self.txCmd = mb.wrap_modbus( modAdr, 0x24, subAdr, s )
                #print(txCmd)
                if self.net_dialog(self.txCmd):
                    return True
                return False
        finally:
            pass


    def set_motor_lifetime_status(self,modAdr,subAdr):
        ''' send the regulator motor lifetime status values to module nr. modAdr
            subAdr 1,2,3: regulator 1,2,3, reg-index 0,1,2,
        '''
        if subAdr in [1,2,3]: # parameter regulator
            # send:
            #   tMotTotal, nMotLimit
            self.ps = parameters[modAdr]["r"][subAdr]
            s = ",%3.1f,%d,"%(self.ps["tMotTotal"], self.ps["nMotLimit"] )
            #print("s=",s)
            self.txCmd = mb.wrap_modbus( modAdr, 0x25, subAdr, s )
            #print(txCmd)
            #print(txCmd)
            if self.net_dialog(self.txCmd) :
                return True
            return False

    def set_factory_settings(self,modAdr):
        self.txCmd = mb.wrap_modbus( modAdr, 0x30, 0, "" )
        self.dbg.m(self.txCmd,cdb=1)
        if self.net_dialog(self.txCmd):
            return True
        return False


    def set_regulator_active(self, modAdr, subAdr, onOff ):
        # onOff     0: switch off,  1: switch on
        if onOff != 0:
            onOff = 1
        s = ",%d,"%( onOff )
        self.txCmd = mb.wrap_modbus( modAdr, 0x35, subAdr, s )
        if self.net_dialog(self.txCmd):
            return True
        return False



    def valve_move(self, modAdr, subAdr, duration, direct):
        # duration      ms;    motor-on time
        # dir           1;     0:close, 1:open, 2:startpos
        if subAdr in [1,2,3]:
            s = ",%d,%d,"%(duration,direct)
            self.txCmd = mb.wrap_modbus( modAdr, 0x31, subAdr, s )
            if self.net_dialog(self.txCmd):
                return True
            return False


    def set_normal_operation(self, modAdr):
        self.txCmd = mb.wrap_modbus( modAdr, 0x34, 0, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False


    def set_fast_mode(self, modAdr, mode ):
        # onOff     0: normal mode,  else: fast operation
        s = ",%d,"%( mode )
        self.txCmd = mb.wrap_modbus( modAdr, 0x36, 0, s )
        if self.net_dialog(self.txCmd):
            return True
        return False


    def get_milisec(self, modAdr, retry = 3):
        self.txCmd = mb.wrap_modbus( modAdr, 0x37, 0, "" )
        if self.net_dialog(self.txCmd):
            return True
        if retry <= 3: self.get_milisec(modAdr,retry)
        return False


    def cpy_eep2ram(self, modAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x38, 0, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def cpy_ram2eep(self, modAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x39, 0, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def wd_halt_reset(self, modAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3A, 0, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def clr_eep(self ,modAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3B, 0, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def check_motor(self, modAdr,subAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3C, subAdr, "" )
            self.dbg.m("check_motor, txCmd=",self.txCmd,cdb=1)
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def calib_valve(self, modAdr,subAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3D, subAdr, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def motor_off(self, modAdr,subAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3E, subAdr, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def get_motor_current(self, modAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3F, 0, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def lcd_backlight(self, modAdr, onOff):
        try:
            if onOff:
                s=",1,"
            else:
                s=",0,"
            self.txCmd = mb.wrap_modbus( modAdr, 0x40, 0, s )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def get_jumpers(self, modAdr):
        self.txCmd = mb.wrap_modbus( modAdr, 0x41, 0, "" )
        if self.net_dialog(self.txCmd):
            #self.__set_rx_response('get_jumpers:%s'%(st.jumpers))
            return True
        #self.__set_rx_response('get_jumpers:%s'%("fail"))
        return False

    def get_version(self, modAdr):
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


    def get_log_data(self, mod, reg, heizkreis):
        # *** read status if module available
        x,y = self.ping(mod)
        if not x:
            self.dbg.m("module {%s} not available"%(mod),cdb=1)
            #return False
        else:

            self.read_stat(mod,reg)     # result is in cn2 and cn4
            #if (type(self.cn2))
            #self.get_milisec(mod)
            #self.get_jumpers(mod)

            # *** print data
            self.dbg.m("="*120,cdb=1)
            self.dbg.m("cn2=",str(self._cn2),cdb=1)
            self.dbg.m("cn4=",str(self._cn4),cdb=1)
            self.dbg.m("timestamp ms=",st.rxMillis,cdb=1)
            self.dbg.m("Jumper settings=%02x"%(st.jumpers),cdb=1)
            self.dbg.m("-"*120,cdb=1)

            # *** build a data-set
            # "20191016_075932 0401 HK2 :0002041a t4260659.0  S "
            # "VM 49.5 RM 47.8 VE 20.0 RE 47.8 RS 32.0 P074 E0000 FX0 M2452 A143"

            # header:
            dateTime = time.strftime("%Y%m%d_%H%M%S",time.localtime())
            self.header   ="%s %02X%02X HK%d :"%(dateTime,mod,reg,heizkreis)
            # module data:
            self.cmdHead  ="0002%02X%db "%(mod,reg)
            self.tic      = float(st.rxMillis) / 1000.0
            self.ticStr   ="t%.1f "%(self.tic)
            self.vlMeas   = float(self._cn2["VM"])
            self.rlMeas   = float(self._cn2["RM"])
            self.vlEff    = float(self._cn2["VE"])
            self.rlEff    = float(self._cn2["RE"])
            self.vlrl     = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f "%(self.vlMeas,self.rlMeas,self.vlEff,self.rlEff)
            self.log_data_string = self.header + self.cmdHead + self.ticStr + str(self._cn2["SN"]) + " " + self.vlrl
            self.log_data_string = self.read_stat_str
            '''
            %s VM%5.1f RM%5.1f VE%5.1f RE%5.1f RS%5.1f P%03d "\
                    "E%04X M%d A%d"%\
                    (st.rxMillis/1000.0, cn2["SN"], cn2["VM"], cn2["RM"], \
                        cn2["VE"], cn2["RE"], cn2["RS"], cn2["PM"], \
                        cn2["ER"], cn2["FX"], cn2["MT"], \
                        cn4[""], cn4[""] ) #nL NB ???
            '''
            self.dbg.m("LOGDATA:",self.log_data_string,cdb=1)
            #self.unblock()
            return True


global ser_obj
ser_obj = Serbus()
#pa = pan.pa_to_ser_obj
#ser_obj.ser_check()

def ser_get_work( q, ttl = 3 ):
    global ser_obj
    _ttlm       = time.time() + ttl
    while True:
        _rsp, _val  = ser_obj.response_available()
        print("_rsp:",_rsp)
        print("(time.time() > _ttlm):", (time.time() > _ttlm))
        if (time.time() > _ttlm):
            return False, ("TTL of 3 seconds passed.")
        if _rsp:
            break
        time.sleep(0.01)

    if _rsp:
        try:
            return ser_obj.get_response(q)
        except Exception as e:
            ser_obj.dbg.m("ser_get_work Exception:", e, cdb=-7)
        return False, ('No values found for:', q)

    return False, ("No response available for:",q)

def add_options_to_ser_add_work_request(t, cbt=False, logger_r=False, mon_r=False, cn2cn4=True):
    global ser_obj
    #if (cbt == 0 and logger_r == False and mon_r == False):    #un and repack old requests until the rest of the code is aligned
    _IDENTIFIER_ = str( _rnd(5) + '_' + _rnd(5) + '_' + _rnd(5) + '_' + _rnd(5)).upper() + '_' + t[-1] \
                                    if (cbt or logger_r or mon_r) else  \
                    str( _rnd(5) + '_' + _rnd(5) + '_' + _rnd(5) + '_' + _rnd(5)).upper()
    t = list(t)
    t.append( cn2cn4 )
    t.append( _IDENTIFIER_ )
    t = tuple(t)
    ser_obj.dbg.m("request:",t,cdb=2)
    return t

def ser_add_work( t:tuple, blocking=True, cbt=0, logger_r = False, mon_r = False, cn2cn4=True):
    global ser_obj
    _ttl_break, _err,_IDENTIFIER_ = False, "", ""
    t = add_options_to_ser_add_work_request(t, cbt, logger_r, mon_r, cn2cn4)
    _IDENTIFIER_ = t[-1]
    if blocking != True:
        ser_obj.request(t,cbt)
        return "GET_DATA","WITH_IDENTIFIER:",_IDENTIFIER_                   # give back identifier on non blocking mode
    _req = ser_obj.request(t,cbt)
    _l_internal_receival_timer_end = time.time() + ser_obj.comm_TTL         # maximum wait for response time...
    cn2cn4 = cn2cn4 if (t[0]=='read_stat' or t[0]=='read_cn2' or t[0]=='read_cn4') else ""
    while st.got_res(_IDENTIFIER_,cn2cn4) == False :   # wait for answer             # in response_available has to be added a TTL value.
        #ser_obj.dbg.m(f"waiting st.got_res({_IDENTIFIER_},cn2cn4)",st.got_res(_IDENTIFIER_,cn2cn4),cdb=9)
        if (time.time() > _l_internal_receival_timer_end):
            _err = f'TTL of {ser_obj.comm_TTL}s passed for request ({_IDENTIFIER_})'#; _msg_tuple: ({_msg_tuple[0]}/{_msg_tuple[1]})'
            ser_obj.dbg.m(_err,cdb=1)
            _ttl_break = True
        if _ttl_break: break
        time.sleep(0.1)
    #ser_obj.dbg.m(f"st.got_res({_IDENTIFIER_},{cn2cn4}):",st.got_res(_IDENTIFIER_,cn2cn4),cdb=2)

    if (t[0] == 'read_stat' or t[0] == 'read_cn2' or t[0] == 'read_cn4'):
        if (t[0] == 'read_cn2' or t[0] == 'read_cn4'):
            _req = t
            _rsp = st.str_to_dict(st.get_parsed_key(_IDENTIFIER_, dt=2)) if (t[0] == 'read_cn2') else st.str_to_dict(st.get_parsed_key(_IDENTIFIER_, dt=4))
        else:
            _req, _rsp = st.str_to_dict(st.get_parsed_key(_IDENTIFIER_, dt=2)), \
                         st.str_to_dict(st.get_parsed_key(_IDENTIFIER_, dt=4)) if (
                                     cn2cn4 == True) else "[CN4 NOT_SCANNED]"
        ser_obj.dbg.m("read stat!",cdb=9)

    else:
        _req, _rsp = t,st.get_parsed_key(_IDENTIFIER_,"")
        ser_obj.dbg.m("no read stat",cdb=9)

    ser_obj.dbg.m(f'{_IDENTIFIER_}_req = {_req}',cdb=4)
    ser_obj.dbg.m(f'{_IDENTIFIER_}_rsp = {_rsp}',cdb=4)
    if _ttl_break: return False, _err, _IDENTIFIER_
    if _req == False:
        _err = f'st.g_both({_IDENTIFIER_}): error running ({str(t)}) return: ({str(_rsp)})'
        #ser_obj.dbg.m(f'st._THIS_IDENTIFIER_({ser_obj._THIS_IDENTIFIER_})',cdb=1)
        #ser_obj.dbg.m(f'st._SERBUS_RUNNING_TXCMD({ser_obj._SERBUS_RUNNING_TXCMD})',cdb=1)
        ser_obj.dbg.m(_err,cdb=1)
        return False, _err, _IDENTIFIER_
    ser_obj.__rx_called_be2y_terminal = False
#
    #_s = _IDENTIFIER_+"_ser_rsp"
    #_req = st.g(_s)
    #_rsp = _rsp if (_rsp != "") else st.g(_s)
    #ser_obj.dbg.m(f'{_IDENTIFIER_}_req = {_req}',cdb=4)
    #ser_obj.dbg.m(f'{_IDENTIFIER_}_rsp = {_rsp}',cdb=4)

    return _req, _rsp, _IDENTIFIER_

def _rnd(length):
    result_str = ""
    for i in range(length):
        letters     = string.ascii_lowercase            if (random.randint(0,1) == 0) else string.ascii_uppercase
        #result_str += ''.join(random.choice(letters))   if (random.randint(0,1) == 0) else ''.join(random.choice("1234567890"))
        result_str += ''.join(random.choice(letters))
    return result_str

def ser_add_work_test(t:tuple, blocking=True, cbt=0):
    _w, _v, _i = ser_add_work(t, blocking, cbt)
    print("ser_add_work_test:",_w,"//",_v)
    return _v
    eval('self.'+key+'()')

if __name__ == "__main__":
    ser_obj.ser_check()

    x= "SERBUS_MAIN_IDENTIFIER"
    modAdr = 4
    subAdr = 1

    r = ("read_stat",modAdr,1,x)
    er = ser_add_work( r, cn2cn4=True )
    print("ser_obj.comm_rspListDict:",er)
    exit(0)

    r = ("read_stat",modAdr,3,x)
    e = ser_add_work( r  )
    print("ser_obj.comm_rspListDict:",er)
    if not r == False:
        pass
    else:
        ser_obj.dbg.m("error getting cn2 and cn4",cdb=2)

    pass
    exit(0)

    os.system('cls')
    ser_ident = [1,2,3]
    mods = [*range(1,5)]
    work = [("read_stat",e,z,str(z*e)) for z in ser_ident for e in mods]
    print("WORK:",work)
    #produce error, cause we dont get the queue response:
    er = ser_add_work(('read_stat',1,1,'1'), blocking =False)
    _lw = []
    print("STARTING WORKERS")
    for x in work:
        # create workers:
        #print("x:",x)
        _w = th.Thread(target=ser_add_work_test, args=((x),True,0))
        _w.setDaemon(True)
        _lw.append(_w)
        #print ('_lw',_lw)
        try:
            _w.start()
        except Exception as e:
            print("Exception:",e)

    while len(_lw)>0:
        for threads in _lw:
            if not threads.is_alive(): _lw.remove(threads)
        time.sleep(0.01)

    while True:
        time.sleep(0.25)
        pass
    print("DONE")

