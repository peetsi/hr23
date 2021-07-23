import PySimpleGUI as sg


'''
parameter = \
{ variableName :
    [
        act,        # active: 0 not changeable; 1 can be changed (input value)
        in,         # input value
        mod,        # from module received
        mem,        # stored in memory on ZZx
        res,        # factory reset value
        unit,       # units
        name,       # long name
        desc,       # description
        rem,        # remark, if necessary
    ]
}
'''
#   0 1 2 3 4 5 6  7  8 9
fw=[8,3,5,5,5,5,4,10,30,30]
#              varNAme, act,  in,     mod,     sto,    res,       unit,   name,  description, remark
paraModHead=["VarName","act","Input","Modul","Store","f.Res.","unit","Name","Beschr","Bemerkung"]
pmh=paraModHead

pmhLayout=[
    sg.T(pmh[0],size=(fw[0],1)),
    sg.T(pmh[1],size=(fw[1],1)),
    sg.T(pmh[2],size=(fw[2],1)),
    sg.T(pmh[3],size=(fw[3],1)),
    sg.T(pmh[4],size=(fw[4],1)),
    sg.T(pmh[5],size=(fw[5],1)),
    sg.T(pmh[6],size=(fw[6],1)),
    sg.T(pmh[7],size=(fw[7],1)),
    #sg.T(pmh[8],size=(fw[8],1)),
    sg.T(pmh[9],size=(fw[9],1))
]

paraMod = \
    {"timer1Tic": [0, "",-999, 11, 12,"msec","Takt","Interner Takt in den Reglern","nicht aendern",] ,
     "tMeas":     [1, "",-999,121,121,"sec","Regel Intervall","Zeitintervall zur Durchführung der Regelung","",],
    }

paraModKeys = \
    { "timer1Tic" : "-t1Tic-",
      "tMeas"     : "-tMeas-",
    }

for var in paraMod:
    print(var)
    v=paraMod[var]
    print(len(v)," - ",v)
    #print(var.keys()[0])


pm = paraMod

sg.theme("DarkAmber")

def text_label(text,ky,sz): 
    return sg.T(text+":",key=ky, enable_events=True, justification="r",size=sz)
    #return sg.T(text+":",justification="r",size=sz)


if pm["timer1Tic"][0] == 0:
    # not active
    infield = sg.T("FIX",key="-t1Tic-", enable_events=True,  size=(fw[2],1))
else:
    infield = sg.In(key="-t1Tic-", enable_events=True, size=(fw[2],1))



line1Layout = [
    text_label("timer1Tic","-t1Tic-",(fw[0],1)), 
    sg.T(pm["timer1Tic"][0],size=(fw[1],1)),
    #sg.In(key="-t1Tic-",    size=(fw[2],1)),
    infield,
    sg.T(pm["timer1Tic"][1],size=(fw[3],1)),
    sg.T(pm["timer1Tic"][2],size=(fw[4],1)),
    sg.T(pm["timer1Tic"][3],size=(fw[5],1)),
    sg.T(pm["timer1Tic"][4],size=(fw[6],1)),
    sg.T(pm["timer1Tic"][5],size=(fw[7],1)),
    #sg.T(pm["timer1Tic"][6],size=(fw[8],1)),
    #sg.T(pm["timer1Tic"][7],size=(fw[9],1)),
]


if pm["tMeas"][0] == 0:
    # not active
    infield = sg.T("FIX",key="-tMeas-", enable_events=True,  size=(fw[2],1))
else:
    infield = sg.In(key="-tMeas-", enable_events=True, size=(fw[2],1))

line2Layout = [
    text_label("tMeas","-tMeas-",(fw[0],1)),     
    sg.T(pm["tMeas"][0],size=(fw[1],1)),
    #sg.In(key="-tMeas-",size=(fw[2],1)),
    infield,
    sg.T(pm["tMeas"][1],size=(fw[3],1)),
    sg.T(pm["tMeas"][2],size=(fw[4],1)),
    sg.T(pm["tMeas"][3],size=(fw[5],1)),
    sg.T(pm["tMeas"][4],size=(fw[6],1)),
    sg.T(pm["tMeas"][5],size=(fw[7],1)),
    #sg.T(pm["tMeas"][6],size=(fw[8],1)),
    #sg.T(pm["tMeas"][7],size=(fw[9],1)),
]

layout = [ 
    pmhLayout,
    line1Layout,
    line2Layout,
    [sg.OK(), sg.Cancel()],
    [sg.T("Beschreibung:",key="-descr-",size=(100,3))],
] 

print("open window")
window = sg.Window("Modul Parameter Eingabe",layout,finalize=True)
'''
print("set input values")
for key in paraModKeys:
    window[paraModKeys[key]].update(value=paraMod[key][0])
'''
print("window loop")
while True:
    event, values = window.read()
    print(event, values)
    if "-t1Tic-" in event:
        window["-descr-"].update( value = pm["timer1Tic"][7] )
    if "-tMeas-" in event:
        window["-descr-"].update( value = pm["tMeas"][7] )
    if event in (sg.WIN_CLOSED, "Cancel"):
        break




'''
    [
        [text_label("timer1Tic",      (fw[0],1))],
        [sg.In(key="-t1Tic-",    size=(fw[1],1))], 
        sg.T(pm["timer1Tic"][0],size=(fw[2],1)),
        sg.T(pm["timer1Tic"][1],size=(fw[2],1)),
        sg.T(pm["timer1Tic"][2],size=(fw[3],1)),
        sg.T(pm["timer1Tic"][3],size=(fw[4],1)),
        sg.T(pm["timer1Tic"][4],size=(fw[5],1)),
        sg.T(pm["timer1Tic"][5],size=(fw[6],1)),
        sg.T(pm["timer1Tic"][6],size=(fw[7],1)),
        sg.T(pm["timer1Tic"][7],size=(fw[8],1)),
        sg.T(pm["timer1Tic"][8],size=(fw[9],1)),
    ], 
    [
        [text_label("tMeas",      (fw[0],1))],     
        sg.In(key="-tMeas-",size=(fw[1],1)),
        sg.T(pm["tMeas"][0],size=(fw[2],1)),
        sg.T(pm["tMeas"][1],size=(fw[3],1)),
        sg.T(pm["tMeas"][2],size=(fw[4],1)),
        sg.T(pm["tMeas"][3],size=(fw[5],1)),
        sg.T(pm["tMeas"][4],size=(fw[6],1)),
        sg.T(pm["tMeas"][5],size=(fw[7],1)),
        sg.T(pm["tMeas"][6],size=(fw[8],1)),
        sg.T(pm["tMeas"][7],size=(fw[9],1)),
        sg.T(pm["tMeas"][8],size=(fw,1)),
    ] 
'''




'''
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
    "r":           [parReg for i in range(3)] # three sets of regulator parameters


  par.timer1Tic        = 10;      // ms;    Timer1 period
  par.tMeas            =120;      // sec;   measuring interval  plpl
  par.dtBackLight      = 10;      // min;  time to keep backlight on
  par.fastMode         = 0;       // normal operation speed
  // common to all regulators
  
  par.tv0             = 40.0;    // degC; characteristic curve
  par.tv1             = 75.0;    // degC;   see function
  par.tr0             = 32.0;    // degC;   characteristic()
  par.tr1             = 46.0;    // degC;   (Kennlinie)
  par.tVlRxValid      = 30;      // min;  use central Vorlauf temperature until this time
  par.tempZiSoll      = 20.0;    // degC; can be varied +/-4K with Zimmer Thermostat
  par.tempZiTol       =  0.5;    // degC; tolerance

  // for each regulator
  for(i=0;i<3;i++){
    par.r[i].active         =      1;     // ;      see below for Zimmertemperatur Regelung
                                          //        reg-1 (index 0): always active unless 0 here
                                          //        reg.2,3 (index 1,2): only active if jumper is set
    // valve motor
    par.r[i].motIMin        =      5;     // mA;    
    par.r[i].motIMax        =     70;     // mA;    
    par.r[i].tMotDelay      =     80;     // ms;    
    par.r[i].tMotMin        =    100;     // ms;    
    par.r[i].tMotMax        =     40;     // sec;    
    // open- and close times for valves       measured        clock     millis()
                                           // ms;   motor     Auf  Zu   Open   Close
                                           //       1 o.Vent. 30.5 30.2 27579  27577
                                           //       1 LinVen. 31   37   27576  33397
                                           //       1 EckVen. 30.4 38.4 27572  34464  
                                           //       2 o.Vent. 32.0 31.7 28632  28637
                                           //       2 LinVen. 31.2 37.9 28108  33934
                                           //       2 EckVen. 31   36   27577  33873
                                           // valves from "THE"
    par.r[i].dtOpen         =     28;     // sec;
    par.r[i].dtClose        =     34;     // sec;   
    par.r[i].dtOffset       =   3000;     // ms;
    par.r[i].dtOpenBit      =    500;     // ms;
    // regulation
    par.r[i].pFakt          =      0.1;   // s/K;     dT=1K, t=0.1s => 0.1sec motor on time
    par.r[i].iFakt          =      0.0;   // s/(K*s); dT=1K, t= 3h  => ca. 1e-4sec motor on time 
    par.r[i].dFakt          =      0.0;   // s^2/K;   dT=1K, t=50s  => ca. 0.1sec motor on time
    //par.r[i].tauTempVl      = 1.0*60.0;   // sec;   
    //par.r[i].tauTempRl      = 3.0*60.0;   // sec;   
    //par.r[i].tauM           = 2.0*60.0;   // sec;   
    par.r[i].tauTempVl      =        1;   // sec;     if <= par.tMeas: faktor=1; Low-pass switched off 
    par.r[i].tauTempRl      =        1;   // sec;   
    par.r[i].tauM           =        1;   // sec;   
    par.r[i].m2hi           =     50.0;   // mK/s;  
    par.r[i].m2lo           =    -50.0;   // mK/s;  
    par.r[i].tMotPause      =10.0*60;     // sec;   
    par.r[i].tMotBoost      =    900;     // sec; 
    par.r[i].dtMotBoost     =   2000;     // ms; 
    par.r[i].dtMotBoostBack =   2000;     // ms; 
    par.r[i].tempTol        =      2.0;   // K;     
    statist.tMotTotal[i]    =      0.0;   // sec;
    statist.nMotLimit[i]    =      0;     // 1;
  }

'''