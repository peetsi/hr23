
import PySimpleGUI as sg
import hz_rr_debug as dbg
import copy
import sys

class hz_rr_log_analyzer():

    def __init__(self):

        sg.ChangeLookAndFeel('Dark')
        self.dbg                    = dbg.Debug(1)
        self._header_line           = 'Log Analyzer'
        self.size                   = (800,600)
        self.ende                   = False
        self.datafile               = None
        self.data                   = None
        self.t_fname                = ""
        self.t_time                 = ""
        self.t_func                 = ""
        self.t_text                 = ""
        self.t_thrd                 = ""

        self.active_threads         = self.dbg.used_by()
        self.layout                 = self.__gen_layout()


    def runme(self):
        self.form                   = sg.Window('HZ_RR_Log_Analyzer', self.layout, background_color='black', size=(700,600), location=(200,200), font=("Calibri",12), finalize=True )

        oloc = ""
        while not self.ende:             # Event Loop
            event, value = self.form.Read(timeout=100)

            if value is not None:
                if value['loc'] != oloc:
                    print("event:", event, "; value:", value)
                    oloc = value['loc']
                    try:
                        self.datafile = open(oloc,'r')
                        _dataread = self.datafile.read()
                        self.datafile.close()

                        self.data = _dataread.split('\n')

                        self.format_data()

                        self.form['_listbox_output'].Update(self.data)
                        #self.form['t_fname'].Update(self.t_fname)
                        self.form['t_time'].Update (self.t_time)
                        self.form['t_func'].Update (self.t_func)
                        self.form['t_text'].Update (self.t_text)
                        self.form['t_thrd'].Update (self.t_thrd)

                        self.form(refresh)
                    except Exception as e:
                        pass

            if event is None or event == 'Zurück':
                self.ende = True
                self.form.Close()
                return


            elif event == '__TIMEOUT__':
                continue

            elif event == 'filesel':
                #fs = sg.FilesBrowse()
                pass

    def format_data(self):
        _data = self.data

        _get_header = []

        for _line in _data:

            try:
                _time = _line.split('[')[1].split(']')[0]
                self.t_time = _time
                print("_time:",_time)

                _thrd = _line.split('[')[2].split(']')[0]
                self.t_thrd = _thrd
                print("_thrd:",_thrd)

                _fnme = _line.split('[')[3].split(']')[0]
                self.t_func = _fnme
                print("_fnme:",_fnme)

                _txt = _line.split('[') [4].split(']',1)[1].strip()
                self.t_text = _txt[:50]
                print("_txt:",_txt)

                _get_header.append(_txt)
                #self.t_fname =
            except Exception as e:
                _get_header.append(_line)


        self.data = _get_header
        return



    def __gen_layout(self):
        self.__def_layout()
        self._layout['elements']    = dict()
        for _k in self._layout.keys():
            self._layout['elements'][_k] = dict()
        self.__create_layout()

        _ffh = ('_fh','_fm','_fs')
        _fft = ('_th','_tm','_ts')
        _window = []
        _frame_sel_log      = [[sg.Text('Wähle eine log Datei aus', enable_events=True, key='sel_log',size=(92,1)),],
                                [sg.In(sys.argv[0],key="loc",size=(73,1)) ,sg.FilesBrowse(key='filesel'),]]#sg.Button("Browse",key="filesel"),]]

        _size=(3,1)
        _hours = [x for x in range(1,25)]
        _mins  = [x for x in range(1,61)]
        _secs  = [x for x in range(1,61)]
        _filter_time        = [[sg.Text('... nach Zeit von:'),],
                                [sg.Combo(_hours,default_value=_hours[-1],key=_ffh[0], size=(4,1)), sg.Combo(_mins,default_value=_mins[-1],key=_ffh[1], size=_size), sg.Combo(_mins,default_value=_mins[0],key=_ffh[2],size=_size),],
                                 [sg.Text("bis:"),sg.Checkbox('Activate', key='act_flt_time'),],
                                [sg.Combo(_hours,default_value=_hours[-1],key=_fft[0],  size=(4,1)), sg.Combo(_mins,default_value=_mins[-1],key=_fft[1], size=_size), sg.Combo(_mins,default_value=_mins[0],key=_fft[2],size=_size),],
                               [sg.Text(key='t_time', size=(18,1), justification="center", relief="sunken", border_width=2, text_color='black', background_color='gold'),],]

        _size = (17, 1)
        #self.active_threads = self.dbg.used_by()

        print("_active:",self.active_threads)
        _keys = list(self.active_threads.keys())
        _filter_thread      = [[sg.Text('... nach Threads:'),],
                                [sg.Combo(_keys,default_value=_keys[0],key='_combo_thread', size=_size,),],
                               [sg.Checkbox('Activate', key='act_flt_thread'),],
                               [sg.Text(""),],
                               [sg.Text(key='t_thrd', size=(18,1), justification="center", relief="sunken", border_width=2, text_color='black',  background_color='gold'),],]

        _filter_fname       = [[sg.Text('...nach Dateiname:'),],
                                [sg.Combo('Dateiname',key='_combo_fname',default_value='Dateiname', size=_size,),],
                               [sg.Checkbox('Activate', key='act_flt_fname'),],
                                [sg.Text(""), ],
                               [sg.Text(key='t_fname', size=(18, 1), justification="center", relief="sunken",
                                        border_width=2, text_color='black',  background_color='gold'), ], ]

        _filter_fnc         = [[sg.Text('...nach Funktionsname:'),],
                                [sg.Combo('Funktion',key='_combo_fnc',default_value='Funktion', size=_size,),],
                               [sg.Checkbox('Activate', key='act_flt_fnc'),],
                                [sg.Text(""), ],
                               [sg.Text(key='t_func', size=(18, 1), justification="center", relief="sunken",
                                        border_width=2, text_color='black',  background_color='gold'), ], ]

        _filter_direct      = [[sg.Text('...nach Text:'),],
                                    [sg.InputText('suche',key='_input_txt_direct', size=_size,),],
                                   [sg.Checkbox('Activate', key='act_flt_direct'),],
                                  [sg.Text(""),],
                               [sg.Text(key='t_text', size=(18, 1), justification="center", relief="sunken",
                                        border_width=2, text_color='black',  background_color='gold'), ], ]

        _frame_output       = [[sg.Listbox(["output",], size=(81, 15), key="_listbox_output", default_values='output', background_color="dark green"),]]

        _f0 = sg.Frame('Wähle Logdatei aus', _frame_sel_log , vertical_alignment='top')
        _f1 = sg.Frame('Zeit Filter', _filter_time          , vertical_alignment='top')
        _f2 = sg.Frame('Thread Filter', _filter_thread      , vertical_alignment='top')
        _f3 = sg.Frame('Datei Filter', _filter_fname        , vertical_alignment='top')
        _f3 = sg.Frame('Funktions Filter', _filter_fnc      , vertical_alignment='top')
        _f4 = sg.Frame('Direkt Filter', _filter_direct      , vertical_alignment='top')
        _f5 = sg.Frame('Ausgabe:', _frame_output            , vertical_alignment='top')

        _lay = [
            [_f0,],
            [_f1,_f2,_f3,_f4,],
            [_f5,],
        #    [,],
        #    [_f3,],
        #    [_f4,],
        ]
        return _lay


    #def __init__(self, values, default_values=None, select_mode=None, change_submits=False, enable_events=False,
    #             bind_return_key=False, size=(None, None), disabled=False, auto_size_text=None, font=None, no_scrollbar=False,
    #             background_color=None, text_color=None, key=None, k=None, pad=None, tooltip=None, right_click_menu=None,
    #             visible=True, metadata=None):

        #return   [[sg.Text('Wähle eine Log Datei'),],
        #            # [sg.Input(do_not_clear=True, key='_IN_')],
        #            [],
        #            *[[sg.Button(button_text=w,key=w)] for w in _cmd_list],
        #            [sg.Button('Zurück')]]

    def __create_layout(self):
        _l = copy.deepcopy(self._layout)
        print("test:",_l.keys())
        # get and create them all
        _l['elements'] = dict()
        for _gui_elements, _val in _l.items():
            for _gui_element_name in _val.keys():
                self._layout['elements'][_gui_elements] = dict()
                self._layout['elements'][_gui_elements][_gui_element_name] = dict()
                self._layout['elements'][_gui_elements][_gui_element_name]['pos'] = dict()
                self._layout['elements'][_gui_elements][_gui_element_name]['pos']['x'] = 0.0
                self._layout['elements'][_gui_elements][_gui_element_name]['pos']['y'] = 0.0
                self._layout['elements'][_gui_elements][_gui_element_name]['pos']['z'] = 0.0

        print("_l:",str(self._layout).replace('},','}\n\n,').replace("': {'","':\n\t{'"))
        #[sg.Combo(                  self._layout['combo']['logfilename']['values'],
        #            key=            self._layout['combo']['logfilename']['key'],
        #            default_value=  self._layout['combo']['logfilename']['default_value'],
        #            size=           self._layout['combo']['logfilename']['size'])]


        #return   [[sg.Text('Wähle eine Log Datei'),],
        #            # [sg.Input(do_not_clear=True, key='_IN_')],
        #            [sg.Combo(self._module_list,key=self.layout_key_combo_logfilename,default_value=self._module_list[0],size=(20,40)), sg.Combo(self._regler_list,key='creg',default_value=self._regler_list[0],size=(20,40))],
        #            *[[sg.Button(button_text=w,key=w)] for w in _cmd_list],
        #            [sg.Button('Zurück')]]


    def __def_layout(self):
        self._layout = dict()

        self._layout['combo']= dict()
        self._layout['combo']['DEFAULT_NAME'] = dict()
        self._layout['combo']['DEFAULT_NAME']['values']                 =   None
        self._layout['combo']['DEFAULT_NAME']['default_value']          =   None
        self._layout['combo']['DEFAULT_NAME']['size']                   =   (None, None)
        self._layout['combo']['DEFAULT_NAME']['auto_size_text']         =   None
        self._layout['combo']['DEFAULT_NAME']['background_color']       =   None
        self._layout['combo']['DEFAULT_NAME']['text_color']             =   None
        self._layout['combo']['DEFAULT_NAME']['change_submits']         =   False
        self._layout['combo']['DEFAULT_NAME']['enable_events']          =   False
        self._layout['combo']['DEFAULT_NAME']['disabled']               =   False
        self._layout['combo']['DEFAULT_NAME']['key']                    =   None
        self._layout['combo']['DEFAULT_NAME']['k']                      =   None
        self._layout['combo']['DEFAULT_NAME']['pad']                    =   None
        self._layout['combo']['DEFAULT_NAME']['tooltip']                =   None
        self._layout['combo']['DEFAULT_NAME']['readonly']               =   False
        self._layout['combo']['DEFAULT_NAME']['font']                   =   None
        self._layout['combo']['DEFAULT_NAME']['visible']                =   True
        self._layout['combo']['DEFAULT_NAME']['metadata']               =   None

        self._layout['button']= dict()
        self._layout['button']['DEFAULT_NAME'] = dict()
        self._layout['button']['DEFAULT_NAME']['button_text']           = ''
        self._layout['button']['DEFAULT_NAME']['button_type']           = sg.BUTTON_TYPE_READ_FORM
        self._layout['button']['DEFAULT_NAME']['target']                = (None,None)
        self._layout['button']['DEFAULT_NAME']['tooltip']               = None
        self._layout['button']['DEFAULT_NAME']['file_types']            = ("ALL Files", "*.*")
        self._layout['button']['DEFAULT_NAME']['initial_folder']        = None
        self._layout['button']['DEFAULT_NAME']['disabled']              = False
        self._layout['button']['DEFAULT_NAME']['change_submits']        = False
        self._layout['button']['DEFAULT_NAME']['enable_events']         = False
        self._layout['button']['DEFAULT_NAME']['image_filename']        = None
        self._layout['button']['DEFAULT_NAME']['image_data']            = None
        self._layout['button']['DEFAULT_NAME']['image_size']            = (None,None)
        self._layout['button']['DEFAULT_NAME']['image_subsample']       = None
        self._layout['button']['DEFAULT_NAME']['border_width']          = None
        self._layout['button']['DEFAULT_NAME']['size']                  = (None,None)
        self._layout['button']['DEFAULT_NAME']['auto_size_button']      = None
        self._layout['button']['DEFAULT_NAME']['button_color']          = None
        self._layout['button']['DEFAULT_NAME']['disabled_button_color'] = None
        self._layout['button']['DEFAULT_NAME']['highlight_colors']      = None
        self._layout['button']['DEFAULT_NAME']['use_ttk_buttons']       = None
        self._layout['button']['DEFAULT_NAME']['font']                  = None
        self._layout['button']['DEFAULT_NAME']['bind_return_key']       = False
        self._layout['button']['DEFAULT_NAME']['focus']                 = False
        self._layout['button']['DEFAULT_NAME']['pad']                   = None
        self._layout['button']['DEFAULT_NAME']['key']                   = None
        self._layout['button']['DEFAULT_NAME']['k']                     = None
        self._layout['button']['DEFAULT_NAME']['visible']               = True
        self._layout['button']['DEFAULT_NAME']['metadata']              = None

        self._layout['text']= dict()
        self._layout['text']['DEFAULT_NAME'] = dict()
        self._layout['text']['DEFAULT_NAME']['size']                    = (None, None)
        self._layout['text']['DEFAULT_NAME']['auto_size_text']          = None
        self._layout['text']['DEFAULT_NAME']['click_submits']           = False
        self._layout['text']['DEFAULT_NAME']['enable_events']           = False
        self._layout['text']['DEFAULT_NAME']['relief']                  = None
        self._layout['text']['DEFAULT_NAME']['font']                    = None
        self._layout['text']['DEFAULT_NAME']['text_color']              = None
        self._layout['text']['DEFAULT_NAME']['background_color']        = None
        self._layout['text']['DEFAULT_NAME']['border_width']            = None
        self._layout['text']['DEFAULT_NAME']['justification']           = None
        self._layout['text']['DEFAULT_NAME']['pad']                     = None
        self._layout['text']['DEFAULT_NAME']['key']                     = None
        self._layout['text']['DEFAULT_NAME']['k']                       = None
        self._layout['text']['DEFAULT_NAME']['right_click_menu']        = None
        self._layout['text']['DEFAULT_NAME']['grab']                    = None
        self._layout['text']['DEFAULT_NAME']['tooltip']                 = None
        self._layout['text']['DEFAULT_NAME']['visible']                 = True



loga_obj = hz_rr_log_analyzer()


def _rnd_float_range(f=30, t=60,  l=3,  r=0):
    import random
    _ret=[]
    _r = ""
    _f = False
    for _repeat in range(0,r+1):
        _r = str(random.randint(f,t))+"."
        for _length in range(0,l):
            _r += str(random.randint(0,9))
        _ret.append( float(_r) )
    return _ret


if __name__ == "__main__":
    loga_obj = hz_rr_log_analyzer()
    loga_obj.runme()

    #_values     = _rnd_float_range(54,61,3,10000)
    #vle         = _values.pop()
    #vle1        = vle
    #vlZen       = vle
    #filtFakt    = 0.25
    #print( f'[{len(_values)}](vle:{vle}, vle1:{vle1}, vlZen:{vlZen})' )    #long list to simulate a night
#
    #while (len(_values)>0):
    #    vle     = _values.pop()
    #    vle1    = vle      * filtFakt + vle1   *   (1-filtFakt)
    #    vlZen   = vle1    * filtFakt + vlZen  *   (1-filtFakt)
    #    print( f'[{len(_values)}](vle:{vle}, vle1:{vle1.__round__(3)}, vlZen:{vlZen.__round__(3)})' )