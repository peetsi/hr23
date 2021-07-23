
import PySimpleGUI as sg
import hz_rr_config as cg
import hz_rr_debug as dbg
import hr2_variables as hrv
from hr2_variables import *
import usb_ser_b as us
import copy
import time
import threading


class hz_rr_terminalG():

    def __init__(self):

        sg.ChangeLookAndFeel('Dark')
        self.dbg                    = dbg.Debug(1)
        self._first_run             = True
        self.heizkreis= self.modules= self.modTVor= \
            self.modSendTvor= self.dtLog= self.filtFakt = None
        self._header_line           = 'Terminal mit Grafischer Oberfläche'
        self._dict_watcher_stop     = False
        self.location               = (100,100)
        self.size                   = (800,600)
        self.ende                   = False
        self.hkr                    = self.__load_hkr()
        self._dictionaryread        = cg.terg_obj.rs('dictionary')
        self._cmdlistread           = cg.terg_obj.rs('cmd_list')
        self._liveviewlistread      = cg.terg_obj.rs('live_view')
        self._cmd_list              = [x for x in self._cmdlistread.keys()]
        self._liveview_list         = [x for x in self._liveviewlistread.items()]
        self._dictionary_dict       = [x for x in self._dictionaryread.items()]
        self._module_list           = [x for x in self.modules]
        self._regler_list           = [1,2,3]
        self._e_dict                = dict()
        self.live_view_enabled      = False

        #text keys
        self._text_fields           = dict()
        #clear list
        self._var_list              = dict(self._dictionary_dict)
        for _k, _v in self._var_list.items():
            if (_v.find('{')>=0 and _v.find('}')>=0):
                _v = eval(f'f"{_v}"')
            else: pass

            try: _v = int(_v)
            except: pass
            self._var_list.update({_k:_v})

        self._cmd_and_function_dict = copy.deepcopy(self._cmdlistread)
        self.layout                 = self.__gen_layout(self._cmd_list, self._liveview_list)
        self.gui_terminal_ident     = 'hz_rr_terminalG_request'
        self._dict_watcher          = threading.Thread(target=self._dict_w)
        self._dict_watcher.setDaemon(True)

    def __update_par_list(self):

        for i in range(0,len(self.sg_par_list)):
            #self.sg_par_list[0] = self.sg_par_list[i].GetLabelText()
            pass
            #print("sg_par_list:", self.sg_par_list[i])
        self.form.Refresh()

    def _get_attr(self,mid,atr):
        _id = mid
        _attr = atr
        if (_id[0] == "b"):
            _x_ = _attr['id'][0][1]
            _x2_ = _attr['id'][0][0]
            udict = self._e_dict[_id][_x_]
            udict2 = self._e_dict[_id][_x2_]
            #print("x:", _x_)
            #print("_x2:", _x2_)
        else:
            udict = self._e_dict[_id][_attr['id']]
            udict2 = ""

        _func = udict.get('func', "")
        _call = udict.get('call', "")
        _key = udict.get('key', "")  # if _id[0] != 'b' else eval(udict.get('key', ""))
        _mid = udict.get('id', "t")
        _save_to = udict.get('save_to', "nowhere")
        _repeat = udict.get('repeat', 0)
        _type = udict.get('type', "t")
        _l_run = udict.get('l_run', 0)
        _n_run = udict.get('n_run', 1)
        _f_skip = udict.get('f_skip', False)
        _did_work = getattr(self, _id + '_WORK', False)
        return udict, udict2, _func, _call, _key, _mid, _save_to, _repeat, _type, _l_run, _n_run, _f_skip, _did_work,

    def runme(self):
        self.form                   = sg.Window('HZ_RR Console Terminal', self.layout,  background_color='black', location=self.location, font=("Calibri",12),finalize=True )

        self.form.Refresh()
        self._dict_watcher.start()

        self.__update_par_list()
        self.check_list = copy.copy(self.sg_par_list)
        while not self.ende:
            time.sleep(0.01)
            while not self.ende: # Event Loop
                self.event, self.value = self.form.Read(timeout=100)
                #self.form.Finalize()
                if (self.value != None):
                    try:
                        self._save_var('mod', self.value['cmod'])
                        self._save_var('reg', self.value['creg'])
                        self._save_var('adir', self.value['adir'])
                        self._save_var('adur', self.value['adur'])
                        self._save_var('par_mod', self.value['par_mod'])
                        self._save_var('par_set', self.value['par_set'])

                        self._save_var('par_reg', self.value['par_reg'])
                        self._save_var('parreg_key', self.value['parreg_key'])
                        self._save_var('par_c_val', self.value['par_c_val'])

                        if self.value['par_set'] == 'r':
                            self.par_reg.Update(disabled=False)
                            self.parreg_key.Update(disabled=False)
                            self.bb4.Update(disabled=False)
                            try: _par_text = parameters[self.value['par_mod']][self.value['par_set']][self.value['par_reg']][self.value['parreg_key']]
                            except Exception as e: _par_text = "1 " + e
                        else:
                            self.par_reg.Update(disabled=True)
                            self.parreg_key.Update(disabled=True)
                            self.bb4.Update(disabled=True)
                            try: _par_text = parameters[self.value['par_mod']][self.value['par_set']]
                            except Exception as e: _par_text = "2 " + e

                        self.par_c_val.Update(_par_text)
                    except:
                        pass

                if self.event is None or self.event == 'Zurück':
                    self._dict_watcher_stop = True
                    self.ende = True
                    self.form.Close()
                    continue

                elif self.event == '__TIMEOUT__':
                    continue

                elif self.event == '_set_param':
                    try: self._set_param()
                    except: pass
                    print("set param to selection")
                    continue

                elif self.event == '_set_param_all_mod':
                    try: self._set_param(mod = self.modules)
                    except: pass
                    print("set param all modules")
                    continue
                elif self.event == '_set_param_all_reg':
                    try: self._set_param(reg = [1,2,3])
                    except: pass
                    print("set param all regler")
                    continue

                elif self.event == '_set_param_all_sel':
                    self.setparam_selective_gui()

                combo_list = ("par_mod", "par_set", "par_reg", "parreg_key","par_n_val", "par_c_val", "adur" , "adir" , "cmod", "creg")
                for i in range(0,len(combo_list)):
                    if self.event == combo_list[i]:
                        x = eval(f'self.{combo_list[i]}').update(str(self.value[combo_list[i]]))
                        self.__force_update()

                print(">>event:", self.event, "value:", self.value)
                #self.__force_update()
                for _id, _attr in self._e_dict.items():
                    if (self.value == None): break
                    udict, udict2, _func, _call, _key, _mid, _save_to, _repeat, _type, _l_run, _n_run, _f_skip, _did_work = self._get_attr(_id,_attr)
                    #print(">>event:", self.event, "_id:", _id)
                    if (self.event == 'b1' and _id == 'b1'):
                        togglenow= eval(udict['func'] +'()')
                        _testf   = eval(udict2['func']+'()')
                        _col = ("white", "red") if (_testf == 'STOP') else ("white", "green")
                        updatebut= eval('self.'+ udict2['id']).Update((_testf))
                        updatebut= eval('self.'+ udict2['id']).Update(button_color = _col)
                        print("LIVEVIEW:",self.live_view_enabled)
                        pass

                    if (_type == 'f' and _did_work == True and _repeat == 0):
                        #del udict
                        continue

                    if _f_skip:
                        _cur_id_str = "-1"
                    else:
                        _lc_ = locals()
                        _cur_id_str = f"self.{_id}" if not (_id[0] == 'b') else _func+'()'
                        #print("_cur_id_str:",_cur_id_str)
                        #print("eval(_cur_id_str,globals(),_lc_):", eval(_cur_id_str,globals(),_lc_))

                        if self.event[1] == 'b':

                            if _id[0] != 'b': _cur_id = eval(_cur_id_str,globals(),_lc_)
                            else:             _cur_id = eval('self.'+_id,globals(),_lc_)
                            #print("_cur_id:",_cur_id)

                            if _id[0] == 'b': _cc = udict2.get('func', "")

                            if _id[0] != 'b': self.form[_id].Update(str(self._var_list.get(_save_to,0.0)))
                            else:             self.form[_id].Update(eval(_cc+'()'))
                            print("live_view_status;",self.live_view_enabled )
                            print("self._var_list.get(_save_to,0.0):",self._var_list.get(_save_to,0.0))
                            print("_save_to:",_save_to)

                    if _type == 'f': #function needs to be evaluated
                        if self.live_view_enabled: #  only do functions if live view is enabled
                            #self._dict_w()# this is in worker now
                            pass

                    elif _type == 'b': #button
                        _x_ = eval(udict2.get('func')+'()')
                        if self.event == _x_:
                            _but_text   = eval(_func+'()')
                            _x_         = eval(udict2.get('func') + '()')
                            _btn_id_str = f"self.{_id}"
                            _btn_id     = eval(_btn_id_str)
                            print(f"self.event:{self.event}, udict2.get('func'):{_x_},\n",
                            f"  but_text:{_but_text}, _x_:{_x_}, _btn_id_str:{_btn_id_str}",
                            f"      _btn_id:{_btn_id}")
                            _btn_id.update(_x_)
                            print("live_view_enabled:",self.live_view_enabled)
                        pass
                    else:
                        pass

                for _w in self._cmd_list:
                    if self.event == _w:
                        print("send function comes here")
                        use = ""
                        try:
                            use = self._cmd_and_function_dict[_w]
                            ib = self.__inside_brackets(use,rb=True).split(',')
                            mod = self.value['cmod']
                            reg = self.value['creg']
                            adir = self.value['adir']
                            adur = self.value['adur']
                            for _r in ib:
                                _clean = eval(_r.replace('{','').replace('}',''))
                                use = use.replace(_r,str(_clean))
                        except Exception as e:
                            self.dbg.m("value['txstr']:",e, cdb = -7)
                            txt = "error"
                        _q = use.replace('(',',').replace(')','').split(',')
                        _q.append(self.gui_terminal_ident)
                        print("trying to use:",_q)
                        try: _r, ret, ident = us.ser_add_work(_q, cbt=1)
                        except Exception as e:
                            print("exception:",e)
                        print("_r:",_r)

    def setparam_selective_gui(self):
        sg.theme('Dark')
        layout = [
            [sg.Text(
                'Gib Module oder Regler an.\n\nWenn ein Feld leer ist, wird ein standardwert genommen.\n\n Akzeptierte Schreibweisen, Beispiele:\n\n ] 1-18,19,24,25-30\n ] 1,2,3,4\n ] 3\n ] 3-27')],
            [sg.Text('Module', size=(5, 1)), sg.InputText(key="mod",size=(20,1))],
            [sg.Text('Regler', size=(5, 1)), sg.InputText(key="reg",size=(20,1))],
            [sg.Submit(), sg.Cancel()]
        ]
        window = sg.Window('Simple data entry window', layout)
        event, values = window.read()
        window.close()

        if event is None:
            return

        if event.lower() == "submit":
            _tempcheck = values['mod'].replace(',', '').replace('-', '')
            if not (_tempcheck == ""):
                if _tempcheck.isdigit():
                    pass
                else:
                    sg.Popup('Fehler!',
                             f'Bitte verwende nur Zahlen[0-9], Komma[,] und Bindestrich[-] zum definieren deiner Auswahl\n Modul Auswahl Fehler:[{values["mod"]}]')
                    print("you put some shit in your string")
                    return

            _tempcheck = values['reg'].replace(',', '').replace('-', '')
            if not (_tempcheck == ""):
                if (_tempcheck.isdigit()):
                    pass
                else:
                    sg.Popup('Fehler!',
                             f'Bitte verwende nur Zahlen[0-9], Komma[,] und Bindestrich[-] zum definieren deiner Auswahl\n Regler Auswahl Fehler:[{values["reg"]}]')
                    print("you put some shit in your string")
                    return

            try:
                _m = values['mod']
                _r = values['reg']
            except:
                return

            self._set_param(mod=_m, reg=_r)
            print("set param all")
        else:
            self.dbg.m("set selective param canceld")
        return

    def _set_param(self, mod=None, reg=None):
        _mod = None if (mod == "") else mod
        _reg = None if (reg == "") else reg
        _mod = str(self.value['par_mod'])if (_mod is None) else str(mod)
        _reg = str(self.value['par_reg'])if (_reg is None) else str(reg)

        if not (mod is None or reg is None):
            if not reg is None:
                _r =""
                if (_reg.find(',')>0 and _reg.find('-')>0): # 2 or more + range
                    try:    _sdig = _reg.split(',')# 1,2,3-6,8,16-19
                    except: _sdig = [_reg,]
                    for w in _sdig:
                        try:
                            _rdig = w.split('-')
                            for _w in range(int(_rdig[0]),int(_rdig[1])+1):
                                _r += str(_w) + ","
                        except:
                            _r += str(w) + ','
                elif _reg.find(',')>0:# 2 or more
                    _r = _reg
                elif _reg.find('-')>0: #range
                    _re = _reg.split('-')
                    for w in range(int(_re[0]),int(_re[1])+1):
                        _r += str(w) + ','
                else :
                    _r = str(_reg) + ","
                _reg = _r.split(',')

            if not mod is None:
                _r = ""
                if _mod.find(',') > 0 and _mod.find('-') > 0:  # 2 or more + range
                    try:    _sdig = _mod.split(',')# 1,2,3-6,8,16-19
                    except: _sdig = [_mod,]
                    for w in _sdig:
                        print("_sdig:", w)
                        try:
                            _rdig = w.split('-')
                            print("_rdig:",_rdig)
                            for _w in range(int(_rdig[0]), int(_rdig[1]) + 1):
                                _r += str(_w) + ","
                        except:
                            _r += str(w) + ','
                elif _mod.find(',')>0:# 2 or more
                    _r = _mod
                elif _mod.find('-')>0: #range
                    _ma = _mod.split('-')
                    for w in range(int(_ma[0]), int(_ma[1]) + 1):
                        _r += str(w) + ','
                else:
                    _r = str(_mod) + ","

                _mod = _r.split(',')
        print("_mod:",_mod)
        print("_reg:",_reg)
        try:
            for x in _mod: pass
        except: _mod = [_mod,]
        try:
            for x in _reg: pass
        except: _reg = [_reg,]

        for _m in _mod:
            if _m == "": continue
            _um = int(_m)

            for _ra in _reg:
                if _ra == "": continue
                _ur = int(_ra)

                if self.value['par_set'] == 'r':
                    try:
                        parameters[_um][self.value['par_set']][_ur][self.value['parreg_key']] = self.value['par_n_val']
                    except Exception as e:
                        _par_text = "1 " + str(e)
                else:
                    try:
                        parameters[_um][self.value['par_set']] = self.value['par_n_val']
                    except Exception as e:
                        _par_text = "2 " + str(e)

            _p = parameters[_um][self.value['par_set']][_ur][self.value['parreg_key']] \
                if (self.value['par_set'] == 'r') else \
                parameters[_um][self.value['par_set']]
            print("set param:", _p)

    def __force_update(self):
        for id, val in self._liveviewlistread.items():
            _bb = False
            ban = None
            if id[:len('self.')] == 'self.':
                if (id[:len('self.x')] != "self.b" and id[:len('self.x')] != 'self.f'):
                    if id.find("_") > 0:
                        g_lbl_txt = self._liveviewlistread.get(id, None)
                        g_rpl_txt = self.__inside_brackets(g_lbl_txt, fxret=True)
                        if g_rpl_txt != False:
                            #print("g_lbl_txt:", g_lbl_txt, "g_rpl_txt:", g_rpl_txt)
                            g_rpl_val = str(self._var_list.get(g_rpl_txt, None))
                            if g_rpl_val is not None:
                                rpl = g_lbl_txt.replace('{'+g_rpl_txt+'}', g_rpl_val).replace('"','')
                                _eme = id.split('.')[1]
                                self.form[_eme].Update(rpl)

    def _update_varlist(self, var_dict):
        for _k, _v in var_dict.items():
            if (_v.find('{') >= 0 and _v.find('}') >= 0):
                _v = eval(f'f"{_v}"')
            else:
                pass

            try:
                _v = int(_v)
            except:
                pass
            self._var_list.update({_k: _v})

    def _dict_w(self):
        self.dbg.m(f'_dict_w started')
        while not self._dict_watcher_stop:
            time.sleep(0.05)
            while self.live_view_enabled:
                #self.dbg.m("live_view_enabled!:",self.live_view_enabled,cdb=1)
                time.sleep(0.5)
                _display_time_str = ""
                for _mid, _attr in self._e_dict.items():
                    if not (_mid[0] == "b"):
                        udict = self._e_dict[_mid][_attr['id']]
                        _func       = udict.get('func')
                        _call       = udict.get('call')
                        _key        = udict.get('key')
                        _id         = udict.get('id')
                        _save_to    = udict.get('save_to')
                        _repeat     = udict.get('repeat',-1)
                        _type       = udict.get('type')
                        _l_run      = udict.get('l_run')
                        _n_run      = udict.get('n_run',0)
                        _run_cnt    = udict.get('run_cnt', 0)
                        _did_work   = getattr(self, _id+'_WORK', False)
                        #print(f"_type({_type}); _did_work({_did_work}); _repeat({_repeat})")
                        if (_type=='f' and _func=='bgcol' or _func=='txcol'):
                            if _func == 'bgcol':
                                pass
                            elif _func == 'txcol':
                                pass

                            continue
                        if (_type=='f' and _did_work==True and _repeat==0):   continue

                        _t_left = int(_n_run) - int(time.time())

                        _display_time_str += f"{_func}({_call}); {_t_left}s; c:{_run_cnt}"
                        self.dbg.m(f"in {_t_left}s -> serbus.{_func}({_call}) (i:'{_run_cnt}', _id:'{_id}', _run_cnt:'{_run_cnt}')",cdb=1)
                        if (_t_left<=0):
                            #_did_work   = getattr(self, _id + '_WORK', False)
                            _did_work2  = udict.get('WORK',False)
                            if (_did_work==True and _repeat==0):
                                # give different color to show its inactivity
                                #del udict
                                continue # just continue with next item in list

                            udict.update( {'WORK': False} )
                            _w = _func + ',' + _call + ',' + self.gui_terminal_ident
                            _w = _w.split(",")
                            try: _req, _retv, _mid = us.ser_add_work(_w, cbt=1, cn2cn4=True)
                            except Exception as e: self.dbg.m(f"ser_add_work({_w}, cbt=1, cn2cn4=True) Fail -> _req:{_req}, _retv:{_retv}, _mid:{_mid}, e{e}",cdb=-7)
                            if( _req == False or _req == None): self._save_var(_save_to, 'Fail', _func, _mid)
                            else:                               self._save_var(_save_to, _retv, _func, _mid)
                            udict.update({'l_run'   : time.time()}  )
                            udict.update({'n_run'   : time.time() + _repeat}  )
                            udict.update({'run_cnt' : udict.get('run_cnt', 0) + 1}  )
                            udict.update({'WORK'    : True}  )
                            self.dbg.m("INS:_id:", _id, ",_run_cnt:", _run_cnt,cdb=3)
                            _did_work   = setattr(self, _id + '_WORK', True)
                            self.__force_update()
                            self.dbg.m(f'_req:{_req};_retv{_retv},_mid{_mid}')
                            #if (int(_repeat) == 0):
                            #    del udict
                            #    del self._e_dict[_id]['id']
                            #    br
                self.dbg.m(_display_time_str,cdb=1)

    def __gen_layout(self,_cmd_list, _liveview_list):
        _x1_ = _x2_ = _x3_ = _x4_ = _f4 = _f2 = _f3 = _f0 = _f1 = _ret = ""
        # cmd liste
        _size = (20,1)
        self.cmod = sg.Combo(self._module_list, size=  (5,1), enable_events=True, key='cmod',default_value=self._module_list[0])
        self.creg = sg.Combo(self._regler_list, size=(5,1), enable_events=True, key='creg',default_value=self._regler_list[0])
        _x1_ =    [
                    #[sg.Text('Wähle ein Modul und einen Regler aus.',size=(60,1)),],
                    # [sg.Input(do_not_clear=True, key='_IN_')],
                    [sg.Text('Modul:',size=_size), self.cmod,],
                     [sg.Text('Regler:',size=_size), self.creg,]
        ]
                    #[sg.Text('',size=(60,1)),],]
        # buttons to generate from list
        _x3_  =  [*[[sg.Button(button_text=w.replace('_',' '),key=w,size=(20,1))] for w in _cmd_list],
                    [sg.RButton('Zurück')]]

        # additional options
        _size = (5,1)
        self.adur = sg.Input('5000', key="adur", size=_size)
        self.adir = sg.Combo((0,1), default_value=1, enable_events=True, key='adir', size=_size)
        _size = (20,1)
        _x4_ =    [
                    [sg.Text('Laufzeit (ms):',_size),self.adur,],
                    [sg.Text('Richtung (0=zu/1=auf):',_size), self.adir,],
                    ]
                    #[sg.Text('',size=(60,1))],]

        # access module nr. 30 parameter e.g.:
        #     parameters[30-1]['tMeas']
        # access regulator 0 (subAdr 1) parameter of module nr. 30 e.g.:
        #     parameters[30-1]['r'][0]["tMotTotal"]
        _m = self._var_list.get('mod',1)
        _r = str(int(self._var_list.get('reg',1))-1)
                #           c1   c2   c3
        _parreg = list(parameters[0].keys())#['r'][_r].keys()
        _params = list(parameters[0]['r'][0].keys())
        _val    = parameters[0]['r'][0][_params[0]]
        _size = (13,1)

        self.par_mod = sg.Combo(self._module_list, default_value=self._module_list[0],  size=(5,1),  enable_events=True, key='par_mod')
        self.par_set = sg.Combo(_parreg, default_value=_parreg[0],                      size=(10,1), enable_events=True, key='par_set')
        self.par_reg = sg.Combo(self._regler_list, default_value=self._regler_list[0],  size=(5,1),  enable_events=True, key='par_reg',     disabled=True)
        self.parreg_key = sg.Combo(_params, default_value=_params[0],                   size=(10,1), enable_events=True, key='parreg_key',  disabled=True)
        self.par_n_val = sg.Input("",                                                   size=(10,1), enable_events=True, key='par_n_val',)
        self.par_c_val = sg.Input(default_text=_val,                                    size=(12,1), enable_events=True, key='par_c_val', readonly=True, disabled_readonly_text_color='red', disabled_readonly_background_color='yellow')
        self.sg_par_list = [self.par_mod, self.par_set, self.par_reg, self.parreg_key, self.par_n_val, self.par_c_val]

        #self.ii3 = sg.Input(self.cc3.Get(), key='_par_reg_n_val')
        self.bb2 = sg.RButton('Apply',        key='_set_param')
        self.tt1 = sg.Text('Setze für Alle:')
        self.bb3 = sg.RButton('Module',  key='_set_param_all_mod')
        self.bb4 = sg.RButton('Regler',  key='_set_param_all_reg')
        self.bb5 = sg.RButton('Selektiv',key='_set_param_all_sel')
        _x5_ = [
                    [self.par_mod, self.par_set, self.par_reg, self.parreg_key, sg.Text(' == '), self.par_c_val,],
                    [sg.Text('Neu:'), self.par_n_val, self.bb2, self.tt1, self.bb3, self.bb4, self.bb5 ],
        ]

        #list(map(exec, ("{0}={1}".format(x[0], x[1]) for x in self._var_list.items()))) # set locals from dict
        for key, val in self._var_list.items():
            exec(key + f'={val}')
        _lv_var = locals()
        _x2_ = []

        for _mid, val in _liveview_list:
            #print(f"id({id}, val({val}")
            _id = _mid[0]
            _r = []
            _temp = ""
            _val = val.strip()
            if _id == 't': # plain text
                val = val
                hc_func_call = False
                _sep_call = 0
                _hc_call= False
                if (val.strip()[:len('headline(')] == 'headline('):
                    _col = "black"
                    _va_ = self.__inside_brackets(_val, bo="(", bc=")" )
                    _va_ = "".join(_va_)
                    _vab_ = _va_
                    _te_ = f', justification="center", relief="sunken", border_width=2, background_color="{_col}", font=(\"Calibri\",10)'
                    #print("_va_headline:",_va_)
                    _hc_call = True
                    hc_func_call = True
                elif (val.strip()[:len('seperator(')] =='seperator('):
                    _col = "grey"
                    _va_ = self.__inside_brackets(_val,bo="(",bc=")" )
                    if (_va_[0:1] == 'f,' or _va_[0:1] == 't,'):_vab_ = _va_[0]
                    else:                                       _vab_ = _va_.split(',')[0]
                    #print("tf happening:",_va_)

                    _te_ = f', {_va_.split(",")[1].strip()}, justification="center", relief="sunken", border_width=2, size=(41,1), font=(\"Calibri\",10)'
                    #print("_vab_seperator:",_vab_)
                    hc_func_call = True

                if hc_func_call: #this is done
                    _gg= _va_
                    this_text = []
                    this_text = self._create_dynamic(_mid, _gg, 'txt', va_ = _vab_, te_ = _te_, seperator_call = True, headline_call =  _hc_call)
                    #print("this_textYSEP:", this_text)

                else: # text
                    _col = 'grey'
                    _va_ = _val # self.__inside_brackets(_val, bo="(", bc=")", rb=False,f=True)
                    #print("_va_:",_va_)
                    #exit(0)
                    _vab_ = _va_
                    _te_ = ', relief="sunken", border_width=2, size=(41,1), font=(\"Calibri\",10),'
                        #f', justification="center", relief="sunken", border_width=2, background_color="{_col}", size=(41,1), font=(\"Calibri\",10)'
                    this_text = self._create_dynamic(_mid, _gg, 'txt', va_=_vab_, te_=_te_, seperator_call=False)

                real_ret = []
                #print("this_text:", this_text)
                for w in this_text:
                    #print("w:", w)
                    if (w != ""):
                        try:
                            _al = eval(w)
                            #print("eval:",_al)
                            real_ret.append(_al)
                        except: real_ret.append(w)
                #print('_real_ret:', real_ret)
                _r = real_ret

            elif _id == 'f': #function + text(the return values)
                _exx = ""
                _st = 'bgcol'
                if (val[:len(_st)] == _st or val[:len(_st)] == 'txcol'):
                    _to_color = self.__inside_brackets(val,bo="(",bc=")")
                    _tte = _to_color.split(',')
                    _wtc = 'background_color' if (val[:len(_st)] == _st) else 'text_color'
                    #_exx = f'self.{_tte[0]}.update({_wtc}={_tte[1]})'
                    _exx = f'self.{_tte[0]}.update( {_wtc} = {_tte[1]} )'
                    _gg = val
                else:
                    _gg = self._lv_get_plain_text(val, _lv_var, d=",", f=True)

                _tmp = _gg.split(';')
                _gg = ""
                if len(_tmp)>0:
                    for funcs in _tmp:
                        if (funcs != "" and funcs.find('@:')>0):
                            func, repeat                = funcs.split('@:')[0], int(funcs.split('@:')[1])
                            _func_name_clear            = func.split('(')[0]
                            _func_args_clear            = self.__inside_brackets(func,bo="(",bc=")") #func.split('(')[1].split(")")[0]
                            #print("_func_args_clear:",_func_args_clear)
                            _save_to_var_clear          = func.split("->")[1] if (func.split("->")[1] != "NULL") else _lv_var['nul_var']
                            _time_now                   = time.time()
                            self._e_dict[_mid] = dict()
                            self._e_dict[_mid]['id']             = _func_name_clear
                            self._e_dict[_mid][_func_name_clear] = dict()
                            _sfn            = self._e_dict[_mid][_func_name_clear]
                            _sfn['func']    = _sfn.get('func',  _func_name_clear)
                            _sfn['call']    = _sfn.get('call',  _func_args_clear)
                            _sfn['key']     = _sfn.get('key',   _func_name_clear)
                            _sfn['exec']    = _sfn.get('exec',  _exx)
                            _sfn['id']      = _sfn.get('id',    _mid)
                            _sfn['repeat']  = _sfn.get('repeat',int(repeat))
                            _sfn['type']    = _sfn.get('type',  "f")
                            _sfn['save_to'] = _sfn.get('save_to',_save_to_var_clear)
                            _sfn['l_run']   = _time_now
                            _sfn['n_run']   = _time_now + repeat if (_sfn['repeat'] > 0) else _time_now + 1
                            _t_             = _sfn.get('WORK',     False)
                            _run_cnt_       = _sfn.get('run_cnt',  1)
                            _did_work       = getattr(self,_mid+"_WORK",False)
                            _sfn['run_cnt'] = _run_cnt_
                            #if (_save_to_var_clear != "NULL":)
                            _tleft = str(int(_sfn['n_run']) - int(time.time()))
                            _fo_ = (str, int)
                            _stvc_ = _lv_var[_save_to_var_clear] if _lv_var.get(_save_to_var_clear, None) != None else ""
                            _update_string = f"{_func_name_clear}_{_func_args_clear}_>>" + _tleft + f"s>>{_save_to_var_clear}>>({_stvc_})".strip()

                            _update_string = self._fstr(_update_string,25,4,25,split_key=">>")
                            #print("_update_string:",_update_string)
                            if (_update_string[0] != "" and len(_update_string) > 1):
                                _b = 'self.' + _mid
                                _fname_args = _func_name_clear + ',' + _func_args_clear
                                _fname_tile = str(_sfn['repeat'])+ 's'  #_update_string[1]
                                _fname_svar = _save_to_var_clear #_update_string[2]
                                _fname_tvar = _update_string[3]
                                _gg = [_fname_args, _fname_tile, _fname_svar, _fname_tvar]
                                #print("_update_string_gg:" + '"',_gg)
                            else:
                                _update_string = str(_update_string+"\\n").split("\\n")
                                _update_string = '"' + _update_string[0] + '"' +   _update_string[1][:-2] + ")"
                                _gg += _update_string
                    pass
                #print("_gg:",_gg)
                _skip_functions = 0
                _sfn['f_skip'] = True

                if _skip_functions != 1:
                    _sfn['f_skip'] = False
                    #if (_sfn['repeat'] == 0):
                    _this_text = self._create_dynamic(_mid, _gg, 'txtf')
                    #print("_this_text[TXTF]:", _this_text)
                    _real_ret = []
                    for _w in _this_text:
                        try:
                            if (_w != ""):_real_ret.append(eval(_w))
                        except: _real_ret.append(_w)
                    #print('_real_ret2:',_real_ret)
                    #else:
                    #    _this_text = self._create_dynamic(_mid, _gg, 'txt')
                    _r = _real_ret

            elif _id == 'b':
                _wg = val.replace("(",'').replace(")",'').split(",")
                self._e_dict[_mid]       = dict()
                self._e_dict[_mid]['id'] = list()
                self._e_dict[_mid]['id'].append(_wg)

                first = 1
                for _gg in _wg:
                    self._e_dict[_mid][_gg]   = dict()
                    _sfn                    = self._e_dict[_mid][_gg]
                    _sfn['func']            = _sfn.get('func', 'self.'+_gg)
                    _sfn['call']            = _sfn.get('call', '')
                    _sfn['key']             = _sfn.get('key', eval('self.'+_gg))
                    _sfn['id']              = _sfn.get('id', _mid)
                    _sfn['save_to']         = _sfn.get('save_to', "")
                    _sfn['repeat']          = _sfn.get('repeat', 0)
                    _sfn['type']            = _sfn.get('type', "b")
                    _sfn['l_run']           = _sfn.get('l_run', "")
                    _sfn['n_run']           = _sfn.get('n_run', time.time() + self._e_dict[_mid][_gg]['repeat'])
                    _sfn['run_cnt']         = _sfn.get('run_cnt', 0)
                    #exec(f"self.{_gg} = self.{_gg}()")
                    if first == 1:
                        _rv_ = str(eval(f'self.{_gg}()'))
                        _x_ = "button_text='"+_rv_+"'"
                        _this_text = self._create_dynamic(_mid, _x_, 'btn')
                        #print("_this_text[BTN]:", _this_text[1])

                        _but_ret = _this_text[1]
                        #print("_but_ret[BTN]:", _but_ret)
                        _r += [_but_ret,]
                        first=0

            _x2_.append(_r)



        _size = (100,20)
        _s = 'self.'
        self.frames = [_s+'f0',_s+'f1',_s+'f2',_s+'f3',_s+'f4']
        _f0 = sg.Frame('Modul/Regler Auswahl',  key=self.frames[0] , layout=_x1_)
        #print("f0 done")
        _f1 = sg.Frame('Ventil Einstellungen',  key=self.frames[1]  ,layout=_x4_)
        #print("f1 done")
        _f2 = sg.Frame('Parameter Einstellungen',key=self.frames[2] ,layout=_x5_)
        #print("f2 done")

        _f3 = sg.Frame('Funktionen',            key=self.frames[3] , layout= _x3_, vertical_alignment='top')
        #print("f3 done")

        #print("_x2:",str(_x2_).replace(', ','\n'))
        _f4 = sg.Frame('LIVEVIEW',             key=self.frames[4] ,  layout=_x2_, vertical_alignment='top')
        #print("f4 done")

        _ret = [
                    [sg.Text(background_color='black'),],
                    [
                        _f0,_f1
                    ],
                    [_f2,],
                    [sg.Text(background_color='black'), ],
                    [
                        _f4, _f3,
                    ],
                    [sg.Text(background_color='black'), ],
                ]


        self._first_run = False
        return _ret

    def _fstr(self, s, *block_n_len, split_key=' ', splits=None):
        _t, _c, _sp = "", 0, -1 if (splits==None) else splits
        try: _s = s.split(split_key, _sp)
        except: return ["", s] #cant split, its a 1 liner
        return _s#.strip()

    def _create_dynamic(self, _id, _gg="_gg", w="txt", rep=0, va_ = "", te_="",  seperator_call = False, headline_call = False):
        _iid = f"self.{_id}"
        _x_  = "Text" if (w=="txt" or w=='txtf') else "RButton"
        locals()[_iid] = ""
        if (w == "txtf" or w == 'txt'):

            _base_v = _iid
            _labels = va_.split(", ") if len(va_)>1 else _gg
            #print("_te:",te_)
            #print("_gg:",_gg)
            #print("_labels:",_labels)
            _args   = te_
            _range  = len(_labels)
            #print(f"_labels:{_labels}, args:{_args}, range:{_range}, seperator_call:{seperator_call}")

            if (seperator_call and not headline_call):
                _vac = ('[VALUES]', '[CALL IN]')
                _style = f'relief="sunken", border_width=2, size=(41,1), font=("Calibri",10), justification="center"'
                if (_labels[0] == 't' or _labels[0] == 'f'):
                    if (_labels[0] == 't'):
                        _label = _vac[0]
                        _style += ', background_color="green",'
                    else:
                        _label = _vac[1]
                        _style += ', background_color="red",'

                    _call = f'= sg.{_x_}( "{_label}", {_style} )'  # f'{_base_v} = sg.{_x_}( "{_label}", {_style} )'
                    #print("_c_call:",_call)
                    _sizes = [1, ]
                    _calls = [_call, ]
                    _idvars = [_base_v, ]
                    _styles = [_style, ]

                else:
                    _labels = va_.split(',',1)[0]   if va_.find(',')>0 else [va_,]
                    _args =   te_
                    #print("MEH:",f'"{_id}",| "{_args}",| "{w}",| "{rep}",| "{te_}"')
                    _sizes = self.__sizes(w, _labels, va_)
                    _styles= self.__styles(w, _args, _sizes, seperator_call, headline_call)
                    _idvars, _calls = self.__calls(w, _iid, _sizes, _styles, _labels)
                    #print(f"_call[{seperator_call}]:", _calls)

            elif headline_call:
                _labels = va_.split(',') if va_.find(',') > 0 else [va_, ]
                _args = te_
                #print("headline_call:", f'"{_id}", "{_gg}", "{w}", "{rep}", "{va_}", "{te_}"')
                _sizes = self.__sizes(w, _labels, va_)
                _styles = self.__styles(w, _args, _sizes, seperator_call, headline_call)
                _idvars, _calls = self.__calls(w, _iid, _sizes, _styles, _labels)
                #print(f"_call[{seperator_call}]:", _calls)


            else:
                #print(f"({w} == 'txtf'):",(w == 'txtf'))
                _sizes = self.__sizes(w, _labels, va_)
                _styles= self.__styles(w, _args, _sizes)
                _idvars, _calls = self.__calls(w, _iid, _sizes, _styles, _labels)
            #execute
            _this = []
            _once = 0
            for i in range(0,len(_sizes)):
                vntmp = list(_idvars[i])
                if vntmp[0] == '"': vntmp.pop(0)
                if vntmp[-1]== '"': vntmp.pop(-1)
                varname = "".join(vntmp)
                _v = varname +  _calls[i].replace('%VARNAME%',varname.replace('self.',''))
                #print("varnamevarnamevarname:",varname)
                _lcs_ = locals()
                #print("_v:",_v)
                #_exe = varname + '= ""'
                if _once == 0:
                    try:
                        if varname.find("_")>0: _exec = _v.split('_')[0] + '=' + _v.split('=',1)[1]
                        else:                   _exec = _v.split('=')[0] + '=' + _v.split('=',1)[1]

                        try:    _e = exec(_exec)  # ,globals(),_lcs_)
                        except: print(f"exe fail{_e}:",_e)

                        try:    self._liveviewlistread.update({_v.split('_')[0]: _v.split('=',1)[1]})
                        except: self._liveviewlistread.update({_v.split('=')[0]: _v.split('=',1)[1]})

                    except Exception as e:
                        print(f"_exe({e}):", _exec, " |>>| ", _v)
                    _once = 1
                #try: exec(_exe,globals(),_lcs_)
                #except: print("_exe:", _exe)
                try:    _e = exec(_v)#,globals(),_lcs_)
                except: print("_exe:", _v)
                vn    = eval(varname)
                #print("_v.split('=')[0]: vn:",_v.split('=')[0], "//", vn)
                _cc = _v.split('=')[0]
                _vv = _v.split('=', 1)[1].split('(',1)[1].split(',')[0]
                self._liveviewlistread.update({_cc : _vv})
                #print(f"_set_({_v}):",_v,",eval==",vn)
                _this.append(vn)
            #print("_this:",_this)
            return _this
        #_gg = _gg[1]
        #_gg += ", relief='sunken', border_width=2" if not (_gg.find('size')>0 and w=='btn' and id[0]=='t' )else "" #print(f"_ggggg[{id}]:", _gg) #, background_color="{_col}", ,justification="center"
        #print(f"_gg1.{_id}:",_gg)
        _clean = _gg
        _first = ""
        if (_id[0] != 't'):
            _gg = _gg.replace(',,',',').replace('=',':')
            #print("_gg2:",_gg)
            try: _first = _gg.split(', ',1)[0] + ','
            except: _first = ""
            #print("_first pass:",_first)
            try: _clean = _gg.split(', ',1)[1].replace("'",'"')
            except:
                _clean = _first
                _first = ""
            #print("_clean pass:", _clean)
            if not (_clean == ""):
                _clean = _clean.split(', ')
                _hd,_n = {},''
                for x in _clean:
                    try:
                        _t = x.split(':')
                        _hd[_t[0]] = _t[1]
                    except Exception as e:
                        print("exception:",e)
                for _k, _v in _hd.items():
                    _n += _k + '=' + _v + ", "
                _clean = _n[:-1]
        #print("_clean1:",_clean)
        _clean = list(_clean)
        while (_clean[-1] == ","): _clean.pop()
        #print("_superclean1:", "".join(_clean))
        _clean="".join(_clean)
        _clean = f"{_first}{_clean}"
        #print("_cleanfunc:", "".join(_clean))
        _exe = _iid + f'=sg.{_x_}( {_clean}, key="{_id}")'
        self.dbg.m("_exe:", _exe, cdb=1)
        _test = exec(_exe,globals(),locals())
        _l_ = locals()[_iid]
        _this = eval(f"self.{_id}")

        #print("_id:",_id)
        self._var_list.update({_id: _this})
        self.dbg.m(_this, cdb=9)
        return ["",_this]
        #print('_gg:', _gg)
        #print( f" id {id} - _gg {_gg} - w {w}")
    def __sizes(self, w, _labels, va_):
        if (w == 'txtf'):
            _range = 4
        _mrange = 41
        _size_all = _c = _dbreak = 0
        _sizes = []
        if (w != 'txtf'):
            #print("SIZE:")
            for _lbl in _labels:
                _size = len(_lbl)
                _size_all += _size
                _c += 1
                if (_size_all > _mrange):
                    _dbreak = 1
                    break
                _sizes.append(_size)
                #print( _size, ",", end="")

            if len(_labels) <= 2:
                if (_size_all < _mrange): _sizes[0] = _sizes[0] + _mrange - sum(_sizes) - len(_labels)
            elif len(_labels) <= 4:
                    if (_size_all < _mrange): _sizes[0] = _sizes[0] + _mrange - sum(_sizes) - int(len(_labels) * 1.5)
            elif len(_labels) <= 6:
                if (_size_all < _mrange): _sizes[0] = _sizes[0] + _mrange - sum(_sizes) - int(len(_labels) * 2)
            elif len(_labels) <= 8:
                if (_size_all < _mrange): _sizes[0] = _sizes[0] + _mrange - sum(_sizes) - int(len(_labels) * 2.5)
            elif len(_labels) <= 99:
                if (_size_all < _mrange): _sizes[0] = _sizes[0] + _mrange - sum(_sizes) - int(len(_labels) * 3)
            #print( "SIZE:", _size_all, "_sizes[0]:", sum(_sizes) )

        else:
            _l0 = 30#len(str(_labels[0]))
            _l2 = 15#len(str(_labels[2]))
            #_add_to_0 = _mrange - _l0 - _l2 - 6  # if ((_l0 + _l2 + 6) <= _mrange) else 0
            #_l0 += _add_to_0
            _sizes = [24, 2, 7, 2]
            _size_all = len(va_)
        #print("_sizes:", _sizes)
        return _sizes

    # styles
    def __styles(self, w, _args, _sizes, seperator_call=False, headline_call=False):
        _styles = []
        for i in range(0, len(_sizes)):
            if (w == 'txtf'):
                _styles.append(f"relief='sunken', border_width=1, size=({_sizes[i]},1), font=('Calibri',10), ")
            elif (headline_call == True):
                _styles.append(f"background_color='black', relief='sunken', border_width=1, size=({_sizes[i]},1), font=('Calibri',10), ")
            elif (seperator_call==True):
                _styles.append(_args.strip()[1:])
            else:
                _styles.append(f"relief='sunken', border_width=1, size=({_sizes[i]},1), font=('Calibri',10), ")
        #print("_styles:", _styles)
        return _styles

    def __calls(self, w, _iid, _sizes, _styles, _labels ):
        # build call vars
        _x_  = "Text" if (w=="txt" or w=='txtf') else "RButton"
        _base_v = _iid
        _idvars = []
        for i in range(0, len(_sizes)):
            _idvars.append(_base_v + '_' + str(i))
        #print("_idvars:", _idvars)
        _idvars.append(_base_v)
        # build calls
        _calls = []
        _o = False
        for i in range(0, len(_sizes)):
            _s = str(_labels[i])
            if (_idvars[i][0] != '"'): _idvars[i] = '"' + _idvars[i]
            if (_idvars[i][-1] != '"'): _idvars[i] = _idvars[i] + '"'
            if (_s[0] != '"'): _s = '"' + _s
            if (_s[-1] != '"'): _s = _s + '"'
            _call = f'= sg.{_x_}( {_s}, {_styles[i]}, key="%VARNAME%" )'.replace(', ,',',')
            self._liveviewlistread.update({_idvars[i]: _s})
            # f'{_idvars[i]} = sg.{_x_}( {_labels[i]}, {_styles[i]} )'
            if _o == False:
                self._liveviewlistread.update({_base_v: _s})
                _o = True
            _calls.append(_call)
        #print("_calls:", _calls)
        return _idvars, _calls

    def _save_var(self,k,v,f="",i=""):
        if f == "read_stat":
            _cn2 = hrv.st.str_to_dict(hrv.st.get_parsed_key(i,dt=2,default=None,serbus_call=False))
            time.sleep(0.5)
            _cn4 = hrv.st.str_to_dict(hrv.st.get_parsed_key(i,dt=4,default=None,serbus_call=False))
            if (_cn2 == False):  return -1
            if (_cn4 == False):  return -2
            _cn = {**_cn2, **_cn4}
            _def = -1

            _skr = []
            for _sk in _cn.keys():
                _skr.append(_sk)

            for _k in _skr:
                try: _t  = _cn[_k]
                except Exception as e: _t = str(e)
                self._var_list[_k.lower()] = _t
                self.dbg.m(f"_t:{_t}, _k:{_k}, self._var_list[_k]:{self._var_list[_k.lower()]}")
        else:
            self._var_list[k] = v
        return True

    def _toggle_live_view(self):
        if self.live_view_enabled == True: self.live_view_enabled = False
        else:                              self.live_view_enabled = True
        return self.live_view_enabled

    def live_view_status(self):
        if self.live_view_enabled == True: return 'STOP'
        else:                              return 'START'

    def _lv_get_plain_text(self,val,_lv_var,d=",",f=False):
        _r = ""
        _in_br_list = []
        if (val.find(d) > 0 or val.find(';') > 0):
            if f:
                #print('val:',val)
                try:
                    _in_br_list = self.__inside_brackets(val, f=f)
                except: _in_br_list = list()
                if not _in_br_list.__class__ == list:_in_br_list=_in_br_list.split(',')
                for br in _in_br_list:
                    if (br == ""): break
                    _num_from_var = f'{_lv_var[br]}'
                    val = val.replace( '{'+br+'}', _num_from_var) + " "
                #print("_val:", val)
                return val

            _temp = val.split(d)
            for _text in _temp:
                if not f:
                    _in_br = self.__inside_brackets(_text)
                    if _in_br != None:
                        _in_br_w = self.__inside_brackets(_text, rb=True)
                        _num_from_var = f'{_lv_var[_in_br]}'
                        _r += _text.replace(_in_br_w, _num_from_var) + ","
                    else:
                        _r += _text
            # print("_r:",_r,";_text:",_text,f";_text.replace({self.__inside_brackets(_text)},{_num_from_var}):",_text)
        else:
            _r += val
        #print("_r:",_r)
        return _r

    def __inside_brackets(self, s, bo='{', bc='}', rb=False, f = False, fxret = False):
        if s.find(bo) < 0: return s if fxret == False else False
        #if f:
        _eb_ = []
        _t_ = s.split(bo,1)
        _eb_.append(_t_[1])
        if (rb==False): _eb_ =       str(str("".join(_eb_))[::-1].split(bc,1)[1])[::-1]
        else:           _eb_ =  bo + str(str("".join(_eb_))[::-1].split(bc,1)[1])[::-1] + bc
        _x   = _eb_.replace(bc,'').replace(bo,'') if (f==True) else _eb_
        _eb_ = _x#if len(_x)>1 else _eb_
        return _eb_

    def __load_hkr(self):
        h = cg.hkr_obj.get_heizkreis_config(0)
        if len(h) > 5:
            (self.heizkreis, self.modules, self.modTVor,
            self.modSendTvor, self.dtLog, self.filtFakt) = h
        else:
            self.heizkreis      = 0
            self.modules        = 0
            self.modTVor        = 0
            self.modSendTvor    = []
            self.dtLog          = 180
            self.filtFakt       = 0.1
def _create_buttons():
    (_name, _cmd, _cmd_e, _cmd_all ) = cg.terc_obj.gtb()
    #print("_name:",_name,"_cmd:",_cmd)#,"_cmd_e:",_cmd_e,"_cmd_all:",_cmd_all)




terg_obj = hz_rr_terminalG()






if __name__ == "__main__":
    pass
    terg_obj = hz_rr_terminalG()
    us.ser_obj.ser_check()
    terg_obj.runme()
    _create_buttons()