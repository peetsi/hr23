#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess
from guizero import App, Box, Combo, PushButton, Text
import time
import threading
import os

import heizkreis_config as hkr_cfg

def get_headline():
    hkpar0=hkr_cfg.get_heizkreis_config(0)
    if len( hkpar0 ) == 2:
        # Parameter Datei existiert nicht
        fehlerNr = hkpar0[1]
        heizkreis="NICHT KONFIGURIERT"
    else:
        fehlerNr = 0
        heizkreis, modules, modTRef, modSendTvor, dtLog, filtFakt=hkpar0
    headline = "HZ-RR Servicemenü, Heizkreis %s"%(heizkreis)
    return headline

hkpar0=hkr_cfg.get_heizkreis_config(0)
# on error return e.g.: ('err', 1)

headline = get_headline()
textStatus ="-***-"
runningPs = "-"

app = App(title=headline,width=700,height=400)


def check_running( progName ) :
    cmd = "ps aux"
    p = subprocess.check_output(cmd, shell=True).decode("utf-8")
    if progName in p:
        #print("Programm ",progName," läuft" )
        return True
    else:
        #print("läuft nicht")
        return False
    

def update_status_text():
    global textStatus
    print(textStatus)
    textAction.value=textStatus
    textStatus="<...>"


def show_textLogger( logger ):
    if logger :
        textLogger.value = "  Logger AN  "
        textLogger.bg    = "lightgreen"
        buttLogOn.disable()
        buttLogOff.enable()
        
    else:
        textLogger.value = "  Logger AUS  "
        textLogger.bg    = "yellow"
        buttLogOn.enable()
        buttLogOff.disable()


def set_textLogger():
    completed = subprocess.run(
        ['./hz_rr_log_start2.sh stat'],
        shell=True,
        stdout=subprocess.PIPE
    )
    retv = completed.stdout.decode("utf-8")
    # 5: running; 6: stopped
    if retv[0] == '5':
        logger = True
    if retv[0] == '6':
        logger = False
        
    show_textLogger( logger )
    
    show_the_rest()
    return logger


def show_the_rest():
    global textStatus
    if check_running("hz_rr_plot10.py"):
        textStatus += "."
    else:
        textStatus = ""
    print(textStatus)
    textAction.value=textStatus
        

def thr_textActive():
    runningPs =""
    completed = subprocess.run(
        ['ps aux'],
        shell=True,
        stdout=subprocess.PIPE,
    )
    retv = completed.stdout.decode("utf-8")
    if "hz_rr_plot10.py" in retv:
        runningPs += "evaluate Log-Files, in progress"
    
def set_textActive():
    threading.Thread(target=thr_diagram_all).start()



def thr_log_start():
    global textStatus
    textAction.value = "Starte Logger"
    completed = subprocess.run(
        ['./hz_rr_log_start2.sh startsilent'],
        shell=True,
        stdout=subprocess.PIPE,
    )
    time.sleep(0.5)
    set_textLogger()
    
def but_log_start():
    threading.Thread(target=thr_log_start).start()


def thr_log_stop():
    textAction.value = "Beende Logger"
    time.sleep(0.5)
    completed = subprocess.run(
        ['./hz_rr_log_start2.sh stop'],
        shell=True,
        stdout=subprocess.PIPE,
    )
    set_textLogger()
    
def but_log_stop():
    threading.Thread(target=thr_log_stop).start()


def thr_scan_all():
    global textStatus
    textStatus="scan"
    thr_log_stop()
    textAction.value = "Status aller Module ..."
    # generate lock-file to avoid cron-start of logger once
    lockFileName = "log.lock"
    lf = open(lockFileName,"w+")
    lf.write("hz_rr_log.py will not be executed if this file is present")
    lf.close()
    completed = subprocess.run(
        ['./hz_rr_monitor_direct02.py'],
        shell=True,
        stdout=subprocess.PIPE,
    )
    retv = completed.stdout.decode("utf-8")
    textAction.value = "Status beendet"
    # remove lock-file so logger can be started again
    
    if os.path.isfile(lockFileName):   # falls Dabei existiert
        os.remove(lockFileName)

    thr_log_start()
    time.sleep(0.5)
    textAction.value="---"

def but_scan_all():
    threading.Thread(target=thr_scan_all).start()


def thr_uebersicht():
    global textStatus
    textStatus="Uebersicht"
    buttUeb.disable()
    buttUeb.bg = 'light green'  
    buttDiagAll.disable()
    textAction.value = "Erstelle Übersicht ..."
    p = subprocess.Popen(
        ['./hz_rr_plot10.py', '1', 'Z', 'F', '[]'],
        stdout = subprocess.PIPE,
    )
    for line in iter(p.stdout.readline, b""):
        textAction.value = line
    textAction.value = "Erstelle Übersicht ... fertig"
    time.sleep(1)
    textAction.value="---"
    buttUeb.enable()
    buttUeb.bg = 'light grey' 
    buttDiagAll.enable()

def but_uebersicht():
    threading.Thread(target=thr_uebersicht).start()
    

def thr_diagram_all():
    global textStatus
    textStatus="Diagramme"
    buttUeb.disable()
    buttDiagAll.disable()
    buttDiagAll.bg = 'light green'  
    textAction.value = "Erstelle Diagramme ..."
    p = subprocess.Popen(
        ['./hz_rr_plot10.py', '2', 'Z', 'F', '[]' ],
        stdout = subprocess.PIPE,
    )
    for line in iter(p.stdout.readline, b""):
        textAction.value = line
    textAction.value = "Erstelle Diagramme ... fertig"
    time.sleep(1)
    textAction.value="---"
    buttUeb.enable()
    buttDiagAll.enable()
    buttDiagAll.bg = 'light grey' 

def but_diagram_all():
    threading.Thread(target=thr_diagram_all).start()


#buttRunning  = PushButton(app, text="Logger Programm läuft?",
#                          command=log_running,
#                          align="left",
#                          grid=[0,0])
version = "1.0"

fin = open("/etc/hostname","r")
hostname = fin.read().strip()
fin.close()


boxTitle     = Box(app,width="fill",align="top",border=True)
textHeadline = Text(app, text="%s Menü Rücklauf-Reglung Version %s"%(hostname,version), align="top", width="fill")

boxLogger    = Box(app,width="fill",align="top",border=True)
textLogger   = Text(boxLogger, text="-", align="top", width="fill")
buttLogOn    = PushButton(boxLogger, text="Logger starten", command=but_log_start, align="left")
buttLogOn.disable()
buttLogOff   = PushButton(boxLogger, text="Logger beenden", command=but_log_stop,  align="left")
buttLogOff.disable()
txtLogger0   ="Im Normalbetrieb ist der Logger dauernd aktiv (an)"
txtLogger1   ="Während der Statusanzeige wird er vorübergehend ausgeschaltet."
txtLogger2   =""
textLoggerB0 = Text(boxLogger, text=txtLogger0, align="top", size=10, width="fill")
textLoggerB1 = Text(boxLogger, text=txtLogger1, align="top", size=10, width="fill")
textLoggerB2 = Text(boxLogger, text=txtLogger2, align="top", size=10, width="fill")

boxScan      = Box(app,width="fill",align="top",border=True)
buttScan     = PushButton(boxScan, text="Alle Module anzeigen", command=but_scan_all, align="left")
txtScan0     = "Stoppe Logger Betrieb -> zeige Status aller Module an"
txtScan1     = "Nach Ende der Scan-Anzeige -> starte Logger Betrieb"
txtScan2     = ""
textScanB0   = Text(boxScan, text=txtScan0, align="top", size=10, width="fill")
textScanB1   = Text(boxScan, text=txtScan1, align="top", size=10, width="fill")
textScanB2   = Text(boxScan, text=txtScan2, align="top", size=10, width="fill")

boxUeb       = Box(app,width="fill",align="top",border=True)
buttUeb      = PushButton(boxUeb, text="Übersicht erstellen", command=but_uebersicht, align="left")
txtUeb0     = "Erstelle Uebersicht aller Module als .pdf Datei"
txtUeb1     = "im Verzeichnis ~/Desktop/monitor/Bilder"
txtUeb2     = ""
textUebB0   = Text(boxUeb, text=txtUeb0, align="top", size=10, width="fill")
textUebB1   = Text(boxUeb, text=txtUeb1, align="top", size=10, width="fill")
textUebB2   = Text(boxUeb, text=txtUeb2, align="top", size=10, width="fill")

boxDiagAll   = Box(app,width="fill",align="top",border=True)
buttDiagAll  = PushButton(boxDiagAll, text="Diagramme erstellen", command=but_diagram_all, align="left")
txtDiagA0     = "Erstelle Diagramme aller Module über die letzten zwei Tage"
txtDiagA1     = "Für jedes Modul wird eine .pdf Datei in ~/Desktop/monitor/Bilder erstellt"
txtDiagA2     = "ACHTUNG: Dieser Vorgang dauert ziemlich lange; je nach Modulzahl 10 Minuten ++"
textDiagAB0   = Text(boxDiagAll, text=txtDiagA0, align="top", size=10, width="fill")
textDiagAB1   = Text(boxDiagAll, text=txtDiagA1, align="top", size=10, width="fill")
textDiagAB2   = Text(boxDiagAll, text=txtDiagA2, align="top", size=10, width="fill")

def thr_service():
    global textStatus
    global app
    thr_log_stop()
    textAction.value = "Starte Service"
    buttService.disable()
    completed = subprocess.run(
        ['./menueService01.py'],
    )
    time.sleep(0.5)
    buttService.enable()
    headline = get_headline()
    app.title = headline
    thr_log_start()

def but_service():
    threading.Thread(target=thr_service).start()

boxService    = Box(app,width="fill",align="top", border=True)
buttService   = PushButton(boxService, text="Service", command=but_service, align="left")
textService0  = Text(boxService, text="  Passwortgeschützt: Heizkreis Auswahl bei Erstinstalltion", align="left" )

#boxActive    = Box(app,width="fill",align="top",border="True")
#textActive0  = Text(boxActive, text="aktive Programme:",align="left", bg="white")
#textActive   = Text(boxActive, text="",align="left", bg="yellow")
#textActive.repeat(2000,set_textActive)

boxAction    = Box(app,width="fill",align="bottom",border=True)
textAction0  = Text(boxAction, text="Letzte Aktion: ", align="left", bg="white")
textAction   = Text(boxAction, text=textStatus, align="left" )

textLogger.repeat(2000,set_textLogger)

app.display()






