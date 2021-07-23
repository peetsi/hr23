import PySimpleGUI as sg

sg.theme("DarkAmber")

'''
parameter = \
{ variableName :
    [
        active,
        vModul,
        vStore,
        vReset,
        vEnter,
        unit,
        name,
        expl,
        rem,
    ]
}
'''

paraMod = \
    {"timer1Tic": [0,"","",10,"","msec","Takt","Takt im Regler","nicht aendern",] ,
     "tMeas":     [1,"","",120,"","sec","Regel Intervall","Zeitintervall zur Durchführung der Regelung","",],
    }


for var in paraMod:
    print(var)
    v=paraMod[var]
    print(len(v)," - ",v)
    #print(var.keys()[0])



#'''
pm = paraMod

layout= [
        [sg.T("Module Parameters")],
        [sg.T("timer1Tic",size=(10,1)), sg.In()],
        [sg.T("tMeas",size=(10,1)), sg.In(size=(15,1), enable_events=True) ],
        [sg.OK(), sg.Cancel()],
    ]

window = sg.Window("Modul Parameter Eingebe",layout)



while True:
    event, values = window.read()
    print(event, values)
    if event in (sg.WIN_CLOSED, "Cancel"):
        break
#'''
