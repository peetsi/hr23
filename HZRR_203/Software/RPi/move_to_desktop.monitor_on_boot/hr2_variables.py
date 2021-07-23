#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hz_rr_debug as dbg
import functools
import platform
import json
import time
import sys
import random
import string
import threading
import copy

pyVers = platform.python_version()
if pyVers < "3.6":
    print("must be at least Python 3.6")
    sys.exit(1)

PROT_REV = "b"      # protocol revision for hzrr200

jumpers =0
rxMillis=0

__x = -1
cn2             =   {"SN":__x,"VM":__x,"RM":__x,"VE":__x,"RE":__x,"RS":__x,"PM":__x} # command names
cn4             =   {"ER":__x,"FX":__x,"MT":__x,"NL":__x} # command names

parReg = {
    # valve motor
    "active":        1,     # uint8_t;   0=inactive; 1=Ruecklauf;
    "motIMin":       6,     # int16_t;   mA;   above: normal operation; below: open circuit
    "motIMax":      71,     # int16_t;   mA;   above: mechanical limit; 2x: short circuit
    "tMotDelay":    81,     # int16_t;   ms;   motor current measure delay; (peak current)
    "tMotMin":     101,     # uint16_t;  ms;   minimum motor-on time; shorter does not move
    "tMotMax":      41,     # uint8_t;   sec:  timeout to reach limit; stop if longer
    "dtOpen":       29,     # uint8_t;   sec;  time from limit close to limit open
    "dtClose":      35,     # uint8_t;   sec;  time from limit open to limit close
    "dtOffset":   3001,     # uint16_t;  ms;   time to open valve a bit when close-limit reached#
    "dtOpenBit":   500,     # uint16_t;  ms;   time to open valve a bit when close-limit reached
    "tMotTotal":   0.1,     # float;     sec;  total motor-on time
    "nMotLimit":     1,     # uint16_t;  1;    count of limit-drives of motor
    # regulation
    "pFakt":       0.11,    # float;     s/K;  P-factor; motor-on time per Kelvin diff.
    "iFakt":       0.01,    # float;     1/K;  I-factor;
    "dFakt":       0.01,    # float;     s^2/K D-factor;
    "tauTempVl":  300.1,    # float;     sec;  reach 1/e; low-pass (LP) filter Vorlauf
    "tauTempRl":  180.1,    # float;     sec;  reach 1/e; LP filter Ruecklauf (RL)<
    "tauM":       120.1,    # float;     sec;  reach 1/e; LP filter slope m
    "m2hi":       40.1,     # float;     mK/s; up-slope; stop motor if above for some time
    "m2lo":       -40.1,    # float;     mK/s; down-slope; open valve a bit
    "tMotPause":  601,      # uint16_t;  sec;  time to stop motor after m2hi
    "tMotBoost":  901,      # uint16_t;  sec;  time to keep motor open after m2lo increase flow
    "dtMotBoost":  2001,    # uint16_t;  ms;   motor-on time to open motor-valve for boost
    "dtMotBoostBack": 2001, # uint16_t;  ms;   motor-on time to close motor-valve after boost
    "tempTol":     2.1,     # float;     K;    temperature tolerance allowed for Ruecklauf
    }

# Parameter for the module

'''
// calculate Ruecklauf temperature from given Vorlauf temperature
// following a polygon shaped characteristic curve (Kennlinie)
// determined by a lint through the points from (tv0,tr0) to (tv1,tr1) 
//
// tr1|- - - - - - - +-----
//    |             /:
//    |           /  :
//  y |- - - - -+    :
//    |       / :    :
// tr0|----+/   :    :
//    |    :    :    :
//    |    :    :    :
//    +---------+----------
//       tv0   tv   tv1
//
'''
#timer1Tic,tMeas,dtBackLight,tv0,tv1,tr0,tr1,tVlRxValid,tempZiSoll,tempZiTol

parameter = {
    "timer1Tic":      11,   # uint16_t; ms;    Interrupt heartbeat of Timer1
    "tMeas":          61,   # uint16_t; sec;   measuring interval
    "dtBackLight":    11,   # uint8_t;  min;   LCD time to switch off backlight
    # characteristic curve (Kennlinie)
    "tv0":          40.1,   # float;    degC;  calculate Ruecklauf temperature
    "tv1":          75.1,   # float;    degC;  from characteristic curve
    "tr0":          32.1,   # float;    degC;  see above
    "tr1":          46.1,   # float;    degC;
    "tVlRxValid":     16,   # uint8_t;  min;    st.tempVlRx is valid this time;
    # regulator 1: special Zimmer temperature if active==2:
    "tempZiSoll":   20.1,   # float; degC;  Zimmer temp. soll; +/-4K with room Thermostat
    "tempZiTol":     0.6,   # float;degC:  toleracne for room-temperature
    "r":           [parReg for i in range(4)] # three sets of regulator parameters
    }

# --------------------------------------------------------------
parameters = [parameter for i in range(31)]   #up to 31 modules
# --------------------------------------------------------------
# ATTENTION:
# access module nr. 30 parameter e.g.:
#     parameters[30-1]['tMeas']
# access regulator 0 (subAdr 1) parameter of module nr. 30 e.g.:
#     parameters[30-1]['r'][0]["tMotTotal"]
# --------------------------------------------------------------

def parameters_zero():
    for n in range(31):
        par = parameters[n]
        for n in par:
            if n != "r":
                par[n] = 0
            else:
                for i in range(3):
                    spar=par["r"][i]
                    for n in spar:
                        spar[n]=0

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
class Buffer_answer():
    def __init__(self):
        self.__from_terminal  = False
        self.__ser_grab       = ""
    def _get(self):
        x = self.__ser_grab
        self.__rst()
        return x[1:]
    def __rst(self):
        self.__ser_grab = ""
        self._from_term(False)
    def _add(self, x):
        if self.__from_terminal == True:
            self.__ser_grab += "\n" + x
        return True
    def _from_term(self, v=True):
        if v != False:
            self.__from_terminal = True
        else:
            self.__from_terminal = False

buffer_answer_object = Buffer_answer()

@singleton
class Keys():
    def __init__(self,debug):
        self.buf                = buffer_answer_object
        self.dbg                = debug
        self._EXPIRE_DICT_      = dict()
        self._EXPIRE_TIMEOUT_   = 10 # seconds
        self._EXPIRE_THREAD_    = threading.Thread(target=self._check_timeouts)
        self.check_timeouts     = True
        self.check_timeouts_st  = 0.5
        self.error_dict         = dict()
        self.error_dict['len']  = 'Error: Lenght of string too short'
        self.error_dict['key']  = 'Error: Key not found'
        self.error_dict['val']  = 'Error: Value could not be extracted'
        self.error_dict['oth']  = 'Error: Other Error'
        self.result_available   = "_got_result"
        self.res                = ""
        self.res_old            = self.res

        #start timeout daaemon - aka the garbage collector
        self._EXPIRE_THREAD_.setDaemon(True)
        self._EXPIRE_THREAD_.start()
        #rückgabewerte werden hier gespeichert

    def _g_both(self,identifier,dt=False,default="",serbus_call=False):
        identifier              += "_parsed"
        if (dt==2): identifier  +="_cn2"
        oid                     = identifier    #cn2
        if (dt==4): oid         +="_cn4"        #cn4
        _v0 = self._g(oid,default,serbus_call)
        _v1 = self._g(identifier,default,serbus_call)
        return _v0, _v1
        # gives back request + parsed answer

    def _g_parse(self,identifier,dt=False,default="",serbus_call=False):
        identifier              += "_parsed"
        if (dt==2): identifier  +="_cn2"
        if (dt==4): identifier  +="_cn4"
        self.dbg.m(f"identfier: {identifier}, dt: {dt}, default: {default}, serbus_call: {serbus_call}", cdb=8)
        _v = self._g(identifier,default,serbus_call)
        return _v
        # gives back request + parsed answer

    def _s_parse(self,_identifier, val, dt=False, overwrite=True, set_result=True):
        identifier              = _identifier+ "_parsed"
        if (dt==2): identifier  +="_cn2"
        if (dt==4): identifier  +="_cn4"
        self.dbg.m(f'{identifier} = "{val}"', cdb=8)
        _v = True
        try:
            self.dbg.m(f"val={val}", cdb=11)
            try:
                val= list(val.split(":",maxsplit=1)[1].strip())
                val = "".join(val)
            except:
                val = val
            self.dbg.m(f"{identifier} = '{val}'", cdb=7)
            try:
                _v = self._s(identifier,val,overwrite)
                #_v = self._s(identifier+self.result_available,val,overwrite)
                self.dbg.m(f"_s({identifier},{val}) success", cdb=9)
            except Exception as e:
                _v = False
                self.dbg.m(f"_s({identifier},{val}) Exception:", e, cdb=-7)

        finally:
            if set_result:
                self.dbg.m(f"setting result {val} with id {_identifier} dt {dt}",cdb=3)
                if (dt != "" or dt != None): dt = False if (dt == 2) else True
                self._set_result(_identifier,dt)
                #self._s_err_res(identifier) # set only if wanted. (default true)
            return _v

    def _delete_key(self,identifier):
        try:
            delattr(self, identifier)
            self.dbg.m(f'({identifier}): success', cdb=11)
            #if identifier.find(self.result_available)<1:
            #    self._set_result(identifier)

        except Exception as e:
            self.dbg.m(f'({identifier}): Exception({e})',cdb=-6)
            return False
        return True

    def _s_err_res(self,i):
        self._set_result(i,cn="")
        self._set_result(i,cn=True)
        self._set_result(i,cn=False)
        return

    def _set_result(self,identifier,cn=""):
        _cn = ""
        if (type(cn) == bool): _cn = "_cn4" if (cn ==True) else "_cn2"
        si = identifier + '_parsed' + _cn + self.result_available
        self.dbg.m("set:", si, "cn:", cn,cdb=9)
        try:
            _x = self._s(si,True,True)
            if (_x == False):
                self.dbg.m(f"_s({si},True,True) = {_x} -> Fail", cdb=-7)
                return False
        except Exception as e:
            self.dbg.m(f".{si} = True -> Exception:", e, cdb=-7)
            return False
        self.dbg.m(f".{si} = True:", _x, cdb=10)
        return True

    def _got_result(self,identifier,cn=""):
        _cn = ""
        if (type(cn) == bool): _cn = "_cn4" if (cn ==True) else "_cn2"
        si = identifier + '_parsed' + _cn + self.result_available# cn +

        #self.res = si
        #if (self.res_old != self.res):
        #    self.dbg.m(self.res, cdb=3)
        #    self.res_old = self.res
        #else:
        #    self.dbg.m("skipping:",self.res,cdb=3)

        _c = getattr(self, si, None)
        #self.dbg.m(si, "=", (_c == True),cdb=4)
        return (_c == True) # if not true and not false, false.

    def _check_timeouts_dic_exist(self): #garbage collector
        _vars_exist = getattr(self, "_EXPIRE_DICT_", None)
        if ( _vars_exist == None): return False
        return True

    def _check_timeouts(self): #garbage collector
        self.dbg.m('_check_timeouts() thread started', cdb=1)
        try:
            while self.check_timeouts:
                time.sleep(self.check_timeouts_st)
                while self._check_timeouts_dic_exist():
                    time.sleep(0.1)
                    _time = time.time()
                    try:
                        for ident, count in self._EXPIRE_DICT_.items(): # identifier / counter
                            if (_time > count): # remove _entry
                                try:#delattr(self._EXPIRE_DICT_,ident)
                                    _s_ = ident
                                    del self._EXPIRE_DICT_[ident]
                                    self.dbg.m(f"__check_timeouts -> del {_s_} ->: True",cdb = 7)
                                    self._delete_key(_s_)
                                    if (_s_.find('_parsed') < 1):
                                        pass
                                        #self._s_err_res(_s_)
                                    break # avoid list has changed error?
                                except Exception as e:
                                    self.dbg.m(f'__check_timeouts -> del {self._EXPIRE_DICT_[ident]} -> Exception:', e, cdb=-7)
                            time.sleep(0.01)
                    except:
                        pass
                        #self.dbg.m(f'__check_timeouts -> RunTimeError -> Exception:', e, cdb=-7)
        finally:
            self.dbg.m('_check_timeouts() thread ended', cdb=1)

    def _s(self,i,v,ovr=True):#_key = 'self.'+i+'="'+v+'"' #_keyo = 'self.'+i
        if not ovr:
            _g = getattr(self, i,None)
            if (_g != None): return False # key exists and overwrite = 0
        _entry = time.time()+self._EXPIRE_TIMEOUT_
        try:
            #self.dbg.m(f".{i}= {v}", cdb=3)
            setattr(self, i, v)       #_exec = exec(_key)
            _check = self._g(i)
            if (_check != v): self.dbg.m(f"({i,v}) Error: value v({v}) not set, instead: {_check}", cdb=-7)
            self._EXPIRE_DICT_[i] = _entry
        except Exception as e:
            self.dbg.m(f"exec({i,v}) Exception:", e, cdb=-7)
            return False
        self.dbg.m(f".{i} = {v}", cdb=11)
        return True

    def _g(self,i,d=None,serbus_call=False):
        try: #_val = eval(_key) - old
            _val = getattr(self,i,None)
            if _val == None:
                self.dbg.m(f"_g -> getattr(self,{i}):",_val,cdb=4)
                return d
        except Exception as e: _val = d #self.dbg.m("Exception evaluating _key{_key}:",e,cdb=-7)
        
        try:
            if (serbus_call == True): pass#self.d(i)
        except Exception as e: self.dbg.m(f"Exception deleting _key({i}):",e,cdb=-7)
        
        self.dbg.m(f"self.{i}:",_val,cdb=11)
        return _val

    def _e(self,e):
        _val =""
        try:
            _val = self.error_dict.get(e,'NOT FOUND ERR VAL:'+str(e))
        except Exception as e:
            pass # error key not found
        return _val

    def _get_command_list(self,_req):
        ''' split ',' separated values from _req in list '''
        if (_req == ""):
            return 1
        self.buf._add('_req: %s'%(str(_req)))
        l = _req.split(",")
        while (l[0] == ''): l.pop(0)
        while (l[-1] ==''):l.pop()
        return l


status_keys_object = Keys(dbg.Debug(1))

@singleton
class Status():
    global cn2, cn4#, cn4_ser, cn4_mon, cn4_log, cn4_ter, cn2_ser, cn2_mon, cn2_log, cn2_ter,

    def __init__(self):
        self.dbg            = dbg.Debug(1)
        self._keys           = status_keys_object
        self.rxCmd          = ""      # received command-string
        self.rxAdr          = 0       # fully obsolete soon
        self.rxCmdNr        = 0       # fully obsolete soon
        self.rxSender       = 0       # fully obsolete soon
        self.rxSubAdr       = 0       # fully obsolete soon
        self.rxProt         = 0       # fully obsolete soon
        self.rxMotConn      = 0       # fully obsolete soon

        self.rxMotImA       = 0
        self.rxMillis       = 0
        self.jumpers        = 0
        self.parse_cur_req  =''
        #self._show()

    def g_both(self,identifier,dt=False,default="",serbus_call=False): # returns 2 variables
        #self.parse_key(identifier)
        return self._keys._g_both(identifier,dt=dt,default=default,serbus_call=serbus_call)

    def g_parse(self,identifier,dt=False,default="",serbus_call=False):
        return self._keys._g_parse(identifier,dt=dt,default=default,serbus_call=serbus_call)

    def s_parse(self,identifier, val, dt=False, overwrite=True, set_result=True):
        self.dbg.m(f's_parse({identifier}, set_result={set_result}) = "{val}"', cdb=9)
        return self._keys._s_parse(identifier, val, dt, overwrite, set_result=set_result)

    def g(self,identifier,default=None,serbus_call=False):
        _v = self._keys._g(identifier,default,serbus_call)
        return _v

    def s(self, identifier, value, overwrite=True):
        _v = self._keys._s(identifier,value,overwrite)
        return _v

    def d(self,identifier): #exec(_k) old
        return self._keys._delete_key(identifier)

    def got_res(self,identifier,cn=""):
        return self._keys._got_result(identifier,cn)

    def set_res(self,identifier,cn=""):
        return self._keys._set_result(identifier,cn)

    def set_key(self,i,v,overwrite=True):
        return self.s(i,v,overwrite)

    def get_parsed_key(self,i,dt=False,default=None,serbus_call=False):
        _ret = self.g_parse(i,dt=dt,default=default,serbus_call=serbus_call)
        return _ret

    def _show(self):
        for attrname in dir(self._keys):
            #if not (attrname.find('x.__')<1): self.dbg.m('x.{} = {!r}'.format(attrname, getattr(self._keys, attrname)),cdb=1)
            self.dbg.m('x.{} = {!r}'.format(attrname, getattr(self._keys, attrname)),cdb=1)

    def __pk_pass_check(self, i,_req="",exception=""):
        _req = str(_req)
        _r = (True,True)
        _t = ""
        if (i == 'len_check'):
            if ((_req=="") or (len(_req) < 9)):
                _t = f"parse_key({_req}): received data trash. string too small ({exception})"
        elif (i == 'val_err'):
            _t = f"parse_key({_req}).__pk_set__modul_information(): could not create modul information - bad extraction ({exception})"
        elif (i == 'other_err'):
            _t = f"parse_key({_req}).__pk_set__modul_information(): could not create modul information - other exception ({exception})"

        if (_t != ""): _r = (False,_t)
        return _r

    def __pk_set__modul_information(self,_req):
        _modul_inf = {   # for internal handling, will be send as string in the end
                        'rxAdr'         : '',
                        'rxCmdNr'       : '',
                        'rxSender'      : '',
                        'rxSubAdr'      : '',
                        'rxProt'        : '',
                        'rx_return_val' : ''
                        }
        try:
            _modul_inf['rxAdr']           = int(_req[0:2],16)
            _modul_inf['rxCmdNr']         = int(_req[2:4],16)
            _modul_inf['rxSender']        = int(_req[4:6],16)
            _modul_inf['rxSubAdr']        = int(_req[6:7])
            _modul_inf['rxProt']          = _req[7:8]
            _modul_inf['rx_return_val']   = ('rxAdr:',  _modul_inf['rxAdr'],    'rxCmdNr:', _modul_inf['rxCmdNr'],
                                            'rxSender:',_modul_inf['rxSender'],'rxSubAdr:', _modul_inf['rxSubAdr'],
                                            'rxProt:',  _modul_inf['rxProt'] )
        except ValueError as e:
            self.dbg.m("value_error:", e)
            return self.__pk_pass_check('val_err', _req, e)

        except Exception as e:
            self.dbg.m("error:", e)
            return self.__pk_pass_check('other_err', _req, e)

        return (True,_modul_inf)

    def __strip_rem_ws(self,_req):
        l = _req.strip().split(",")
        while(l[0]==''): l.pop(0)   # remove whitespaces
        while(l[-1]==''):l.pop()    # remove whitespaces
        return l

    def str_to_dict(self,s):
        if (type(s) == bool):   s = "True" if (s == True) else "False"
        if s == None:           s = "None"
        self.dbg.m("s:(", s,") -> s.find(':'):(",(s.find(":")),")",cdb=3)
        if (s.find(":") < 1):                   return False #no dict string..
        if (s.split(':')[0].lower()=='error'):  return False
        try:
            return json.loads(s.replace("'",'"'))
        except json.JSONDecodeError as e:
            self.dbg.m(f"str_to_dict({s}) Exception:", e, cdb=-7)
        except Exception as e:
            self.dbg.m(f"str_to_dict({s}) Exception:", e, cdb=-7)
        return None

    #buf for terminal
    def add(self,value):
        return self._keys.buf._add(value)

    def from_term(self,toggle=True):
        return self._keys.buf._from_term(toggle)

    def get_terminal_buf(self):
        return self._keys.buf._get()

    def _set_err_res(self,i):
        return self._keys._s_err_res(i)

    def parse_key(self,i,cn2_only_flag=False,__x=0,set_result=True): #parses value and sets the correct value to Keys
        _cn2        = {"SN":__x,"VM":__x,"RM":__x,"VE":__x,"RE":__x,"RS":__x,"PM":__x}  # just temporary inside this function
        _cn4        = {"ER":__x,"FX":__x,"MT":__x,"NL":__x}                             # convert to string on return
        _buf        = self._keys.buf
        _rxMillis   = 0
        _rxMotConn  = 0
        _jumpers    = 0
        _rxMotImA   = 0

        _req    = self.g(i,self._keys._e('key'))
        if (_req == self._keys._e('key')):
            self.dbg.m("parse_key Error:",_req,cdb=-6)
            self._save_key_and_buf(i, f'{i}-> Error:'+ _req)
            self._set_err_res(i)
            return False
        self.dbg.m(f'g({i}): {_req}',cdb=9)

        _did_pass_check = self.__pk_pass_check("len_check",_req)
        if not (_did_pass_check[0] and _did_pass_check[1]):
            self.dbg.m("_did_pass_check Error:", _did_pass_check[1],cdb=-6)
            self._save_key_and_buf(i, f'{i}-> Error: '+_did_pass_check[1])
            self._set_err_res(i)
            return False
        self.dbg.m(f'__pk_pass_check("len_check",{_req}): {str(_did_pass_check)}',cdb=9)

        _modul_inf = self.__pk_set__modul_information(_req) # get basic vals
        if _modul_inf[0] != True:
            self.dbg.m("_modul_inf Error:", _modul_inf[1],cdb=-6)
            self._save_key_and_buf(i, f'{i}-> Error:'+ _modul_inf[1])
            self._set_err_res(i)
            return False
        self.dbg.m(f'__pk_set__modul_information({_req}): {str(_modul_inf)}',cdb=10)

        _modul_inf = _modul_inf[1]
        ( _rxAdr,_rxCmdNr,_modAdr,_rxSubAdr,_rxProt,_rx_return_val  )   = (_modul_inf.values())
        self.dbg.m(f'_modul_inf: {str(_modul_inf.values())}',cdb=10)

        _buf._add('parse_answer: %s'%(str(_rx_return_val)))
        try:
            _req        = _req[9:-7]
        except Exception as e:
            self.dbg.m(f' _req[9:-7]: {_req} -> Exeption: {e}',cdb=-7)
            self._save_key_and_buf(i, 'READ_STAT->CN2:%s' % (str(_cn2)), dt=2)
            self._set_err_res(i)
            return False
        self.dbg.m(f' _req: {_req}',cdb=4)

        if ( _rxProt != PROT_REV):
            #self._set_err_res(i)
            self._save_key_and_buf(i, ' _rxProt != PROT_REV->%s != %s' % (str(_rxProt),str(PROT_REV)), dt=2)
            return True
        if      (_rxCmdNr==1 and "ACK" in _req): return self._save_key_and_buf(i,'PING:ACK',set_result=set_result)
        elif    (_rxCmdNr==2):  # read status values part 1
            if ((_rxSubAdr == 0) and ("ACK" in _req)):
                return self._save_key_and_buf(i,'READ_STAT(cn2):ACK  -- (rxSubAdr == 0)',set_result=set_result)
            elif _rxSubAdr in [1,2,3]:
                l = self.__strip_rem_ws(_req)
                for v in l:
                    if (v == "S" or v == "W"): _cn2['SN'] = cn2["SN"] = v
                    else:
                        nm = v[0:2]
                        try: _cn2[nm] = cn2[nm]= float(v[2:])
                        except ValueError as e: self.dbg.m(f"parse_answer({_req}) value_error:", e, cdb = -6)
                        except Exception as e:  self.dbg.m(f"parse_answer({_req}) error:",       e, cdb = -6)
                _dt = 2
                set_result = True if (_dt == 2) else False
                return self._save_key_and_buf(i,'READ_STAT->CN2:%s'%(str(_cn2)), dt=_dt, set_result=True)

        elif (_rxCmdNr == 4):  # read status values part 2
            if (_rxSubAdr == 0 and "ACK" in _req): return self._save_key_and_buf(i,'READ_STAT(cn4):ACK  -- (rxSubAdr == 0)',set_result=set_result)
            elif _rxSubAdr in [1,2,3]:
                l = self.__strip_rem_ws(_req)
                for v in l:
                    nm = v[0:2]     # dictionary name (=index)
                    if (nm == "ER"): _cn4[nm] = cn4[nm] = int(v[2:],16)
                    else:           # other values can be handled as float
                        _cn4 = cn4[nm] = float(v[2:])
                        if (v == "tMotTotal") or (v == "nMotLimit"):
                            # store additionaly in parameters
                            parameters[_modAdr-1]['r'][_rxSubAdr-1][v] = float(v[2:])
                _buf._add('READ_STAT->CN4: %s'%(str(cn4)))
                _buf._add('READ_STAT->PARAMETER: %s'%(str(parameter)))

                #self._save_key_and_buf(i, "EMPTY", dt=2, set_result=True)
                return self._save_key_and_buf(i,'READ_STAT->CN4:%s'%(str(cn4)),dt=4,set_result=True) #set_cn('s')
        elif (_rxCmdNr == 5): #timer1Tic,tMeas,dtBackLight,tv0,tv1,tr0,tr1,tVlRxValid,tempZiSoll,tempTolRoom
            l = self._keys._get_command_list(_req)
            par = parameters[_modAdr-1]
            if (_rxSubAdr == 0): #   tv0,tv1,tr0,tr1,tVlRxValid,tempZiSoll,tempZiToly
                for n in par:
                    if n == "r": break # last value terminated in dict
                    par[n]=float(l.pop(0))
                return self._save_key_and_buf(i,'READ_PARAM->par = parameters[modAdr-1]:%s'%(str(par)),set_result=set_result)
            elif ( _rxSubAdr in [1,2,3]):#   active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax, dtOpen, dtClose, dtOffset
                pr = par["r"][_rxSubAdr-1]
                start=False
                for n in pr:          # start at begin of directory
                    pr[n]=float(l.pop(0))
                    if l == []: break
                return self._save_key_and_buf(i,'READ_PARAM->pr = par["r"][st.rxSubAdr-1]:%s'%(str(pr)),set_result=set_result)
        elif (_rxCmdNr == 6):  # read parameter: module / reg.part 2
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req))
            if (_rxSubAdr == 0): # "ACK" - no data available
                if ("ACK" in _req) :
                    return self._save_key_and_buf(i,'READ_PARAM-ACK (st.rxSubAdr == 0)',set_result=set_result)
            elif (_rxSubAdr in [1,2,3]):  #   pFakt, iFakt, dFakt, tauTempVl, tauTempRl, tauM
                l = self._keys._get_command_list(_req)
                par = parameters[_modAdr-1]
                pr = par["r"][_rxSubAdr-1]
                start=False
                for n in pr:
                    if n == "pFakt":  # first item to be filled
                        start=True
                    if start :
                        pr[n]=float(l.pop(0))
                        if l == []: break
                return self._save_key_and_buf(i,'READ_PARAM->pr = par["r"][st.rxSubAdr-1]:%s'%(str(pr)),set_result=set_result)
        elif (_rxCmdNr == 7):  # read parameter: module / reg.part 3
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req))
            if (_rxSubAdr == 0):  # "ACK" - no data available
                if ("ACK" in _req) :
                    return self._save_key_and_buf(i,'READ_PARAM-ACK (st.rxSubAdr == 0)',set_result=set_result)
            elif (_rxSubAdr in [1,2,3]):  #   tMotPause, tMotBoost, dtMotBoost, dtMotBoostBack
                l = self._keys._get_command_list(_req)
                par = parameters[_modAdr-1]
                pr = par["r"][_rxSubAdr-1]
                start = False
                for n in pr:
                    if n == "m2hi":  # first item to be filled
                        start=True
                    if start :
                        pr[n]=float(l.pop(0))
                        if (l == []): break
                return self._save_key_and_buf(i,'READ_PARAM->pr = par["r"][st.rxSubAdr-1]:%s'%(str(pr)),set_result=set_result)
        elif (_rxCmdNr == 0x20) :  # Zentrale Vorlauftemperatur received
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req), cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'zentrale_vorlauftemp->ACK: %s,%s'%(str(_rxCmdNr),str(_req)),set_result=set_result)
        elif (_rxCmdNr == 0x22) :  # setze parameter
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req), cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'set_param(0x22)->ACK: %s,%s'%(str(_rxCmdNr),str(_req)),set_result=set_result)
        elif (_rxCmdNr == 0x23) :  # setze parameter
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req), cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'set_param(0x23)->ACK: %s,%s'%(str(_rxCmdNr),str(_req)),set_result=set_result)
        elif (_rxCmdNr == 0x24) :  # setze parameter
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req), cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'set_param(0x24)->ACK: %s,%s'%(str(_rxCmdNr),str(_req)),set_result=set_result)
        elif (_rxCmdNr == 0x25) :  # set special parameters
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req), cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'set_special_param->ACK: %s,%s'%(str(_rxCmdNr),str(_req)),set_result=set_result)
        elif (_rxCmdNr == 0x30) :  # reset all parameters to factory settings
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req), cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'factory_reset->ACK: %s,%s'%(str(_rxCmdNr),str(_req)),set_result=set_result)
        elif (_rxCmdNr == 0x31) :  # move valve; time and direction
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req), cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'move_valve->ACK: %s,%s'%(str(_rxCmdNr),str(_req)),set_result=set_result)
        elif (_rxCmdNr == 0x34) :  # set normal operation
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req), cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'set_normal_operation->ACK: %s,%s'%(str(_rxCmdNr),str(_req)),set_result=set_result)
        elif (_rxCmdNr == 0x35) :  # set regulator active/inactive
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req), cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'reg_set->ACK: %s,%s'%(str(_rxCmdNr),str(_req)),set_result=set_result)
        elif (_rxCmdNr == 0x36) :  # fast mode on/off
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req), cdb=3)
            if ("ACK" in _req) : return  self._save_key_and_buf(i,'fast_mode->ACK: ACK',set_result=set_result)
        elif (_rxCmdNr == 0x37) :  # get milliseconds #self._save_key_and_buf(i,'get_millis->ACK: %s,%s,%s'%(str(_rxCmdNr),str(_req),str(_rxMillis)))
            l = self._keys._get_command_list(_req)
            _rxMillis = l[0]
            self.dbg.m("COMMAND= %02x: _req= %s"%(_rxCmdNr,_req),"/ l=",str(l),"/ recv milliseconds:",_rxMillis,cdb=3)
            self.rxMillis = _rxMillis
            return self._save_key_and_buf(i,f'get_millis->ACK:{_rxMillis}',dt="",set_result=set_result)
        elif (_rxCmdNr == 0x38) :  # copy all parameters from EEPROM to RAM
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req),cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'cpy_eep2ram->ACK: ACK',set_result=set_result)
        elif (_rxCmdNr == 0x39) :  # write all parameters from RAM to EEPROM
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req),cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'cpy_ram2eep->ACK: ACK',set_result=set_result)
        elif (_rxCmdNr == 0x3A) :  # RESET using watchdog - endless loop
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req),cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'watchdog_reset->ACK: ACK',set_result=set_result)
        elif (_rxCmdNr == 0x3B) :  # clear eeprom  ??? plpl test eeprom if ram space is left
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req),cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'clear_eep->ACK: ACK',set_result=set_result)
        elif (_rxCmdNr == 0x3C) :  # check if motor connected
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req),set_result=set_result)
            l = self._keys._get_command_list(_req)
            self.dbg.m("0x3C: l=",l,cdb=3)
            _rxMotConn = int(l[0])
            self.dbg.m("received motor connected:",_rxMotConn,cdb=3)
            return self._save_key_and_buf(i,'motor_connected->ACK: %s'%(str(_rxMotConn)),set_result=set_result)
        elif (_rxCmdNr == 0x3D) :  # open and close valve to store times
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req),cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'open_close_valve->ACK: ACK',set_result=set_result)
        elif (_rxCmdNr == 0x3E) :  # switch off current motor
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req),cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'mot_off->ACK: ACK',set_result=set_result)
        elif (_rxCmdNr == 0x3F) :  # read motor current
            l = self._keys._get_command_list(_req)
            self.rxMotImA = _rxMotImA = float(l[0])
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req),"// l=",l,"// received mA:",_rxMotImA,cdb=3)
            return self._save_key_and_buf(i,'mot_current->ACK: %s'%(str(_rxMotImA)),set_result=set_result)
        elif (_rxCmdNr == 0x40) :  # LCD-light on/off
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req),cdb=3)
            if ("ACK" in _req) : return self._save_key_and_buf(i,'lcd_backlight->ACK: ACK',set_result=set_result)
        elif (_rxCmdNr == 0x41) :  # read jumper settings
            l = self._keys._get_command_list(_req)
            _jumpers = int(l[0], 16)
            st.jumpers = _jumpers
            self.dbg.m("parse_answer %02x: _req = %s"%(_rxCmdNr,_req),"// jumper setting = %02x:"%(_jumpers),cdb=3)
            return self._save_key_and_buf(i,'get_jumpers->ACK: %s'%(str(_jumpers)),set_result=set_result)

        self._save_key_and_buf(i,'Error: (%s,%s)'%(str(_rxCmdNr),str(_req)),set_result=set_result)
        return False # values not found while parsing

    def _save_key_and_buf(self,i,r,dt="",set_result=True):
        self._keys.buf._add(r)
        #st.parse_key(ident, cn2_only_flag=dt)
        _w = self.s_parse(i,r,dt=dt,overwrite=True,set_result=set_result)
        return True

    def set_cur_req(self,s='m'):#
        self.dbg.m("set_cur_reg:",s,cdb=3)
        self.parse_cur_req = s

    def get_cur_req(self):
        _x = self.parse_cur_req
        self.dbg.m("get_cur_req:",_x,cdb=3)
        self.parse_cur_req = ""
        return _x

def _rnd(length):
    result_str = ""
    for i in range(length):
        letters     = string.ascii_lowercase            if (random.randint(0,1) == 0) else string.ascii_uppercase
        #result_str += ''.join(random.choice(letters))   if (random.randint(0,1) == 0) else ''.join(random.choice("1234567890"))
        result_str += ''.join(random.choice(letters))
    return result_str


st = Status()

if __name__ == "__main__":
    cmd = (1,2,3,4,5,6,7,8,9,0)

    x = f"options({cmd[(3*-1):]})"
    print(x)

    x = str(cmd[1:len(cmd)-3])[1:-1]
    x = f"options({x})"
    print(x)

    comm_current_max_options = 3
    x = ""
    print(x)


    #exit(0)

    _i      = str( _rnd(5) + '_' + _rnd(5) + '_' + _rnd(5) + '_' + _rnd(5)).upper() + '_ret_mon_q'
    _t      = "0002041b,W,VM19.6,RM21.3,VE70.0,RE21.3,RS44.0,PM999,0BB2320"
    st.from_term(True)
    _x = st.set_key(_i, _t )
    print("set_key:",_x)

    _x = st.parse_key(_i)
    print("parse_key:",_x)

    _x = st.get_parsed_key(_i,dt=2)
    print("get_parsed_key:",_x)

    _x = st.str_to_dict(_x)
    print("strtodict:",type(_x))

    _x = st.get_terminal_buf()
    print("get_terminal_buf:",_x)

    print(f"1got_result({_i}):",st.got_res(_i,cn=False))
    print("")
    print(f"set_key({_i}):",    st.set_key(_i, _t ))
    print(f"parse_key({_i}):", st.parse_key(_i))
    #st._show()
    print(f"2got_result({_i}):", st.got_res(_i,cn=False))
    exit(0)
    for i in range(1,15): 
        st.set_key(_rnd(20),i) # create keys
    st._show() # show keysym
    time.sleep(10) # wait 10 seconds check iff garbage collector works
    st._show()

