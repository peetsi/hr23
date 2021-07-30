#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess
from guizero import App, Box, Combo, PushButton, Text
import time
import threading
import os, errno
import glob
import guizero as g0
import heizkreis_config as hkr_cfg

#*****************************
PASSWORT = "ServicE" 
#*****************************


combo = None
pwdBox= None
app   = None

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

def select_config_templates():
    global combo, pwdBox, app
    
    headline = get_headline()
    app = App(title=headline,width=600,height=300)
    # wähle Vorlagen aus vorhandenen Konfigurations-Dateien aus

    configFiles = "config/*.conf"
    flist = glob.glob( configFiles )
    flist.sort()
    try:
        flist.remove("config/heizkreis.conf")
    except:
        pass
    
    #cnt=0
    #for f in flist:
    #    cnt+=1
    #    print(cnt, f)



    boxPwd = g0.Box(app,align="top",border=True)
    txtPwd = g0.Text(boxPwd,text="Service Passwort:", align="left")
    pwdBox = g0.TextBox(boxPwd,text="", hide_text=True, align="left", width="fill")
    butPwd = g0.PushButton(boxPwd,text="Start Service",align="left",command=pwd_check)
    box0  = g0.Box(app,width="fill",align="top", border=True)
    txt01 = g0.Text(box0, text="Vorsicht! Bei falscher Wahl Störung !!!", align="top")
    txt02 = g0.Text(box0, text="Die Konfigurationsdateien können mit einem", align="top")
    txt03 = g0.Text(box0, text="Editor im Verzeichnis 'Desktop/monitor/config' eingestellt werden", align="top")
    box1  = g0.Box(app,width="fill",align="top", border=True)
    txt1  = g0.Text(box1, text="Wähle die Konfigurationsdatei für diese Zentrale", align="top")
    combo = g0.Combo(box1, options=flist, align="top", command=config_file, enabled=False)
    
    app.display()

def config_file(select):
    global app
    print("configFile=",select)
    symlink_force( select, "config/heizkreis.conf")
    headline = get_headline()
    app.title=headline
    
    
def pwd_check():
    global pwdBox, combo
    print(pwdBox.value)
    if pwdBox.value != PASSWORT:
        pwdBox.bg = "red"
        combo.enabled=False
    else:
        pwdBox.bg = "light green"
        combo.enabled=True

def symlink_force(target, link_name):
    currentPath = os.getcwd()
    target = currentPath + "/" + target
    link_name = currentPath +"/" + link_name
    try:
        os.symlink(target, link_name)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)
        else:
            raise e

if __name__ == "__main__" :
    select_config_templates()

