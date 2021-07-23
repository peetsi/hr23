# IMPORTS
import glob
import time
import os
# up here old imports
try:
    import pi_conf as oconf
except ImportError:
    raise "error"

#oerr = olog_err()

#old:
#import numpy as np
#import heizkreis_config as hkr_cfg
#import rr_parse as parse


# IDEA:
# EACH pi_log object creates an err object
# As each pi_log object will be included into any function,
# any function will have an err function already and it does
# prolly not have to be included somerwhere else again
# use inner class!


# test of a new log class
class pi_log:
    """pi_log Class
        this is to set custom error codes for each object or function
        therefor pi_log should be inherited 

    Raises:
        error: custom error printing for each object

    Returns:
        pi_log: object
    """
    
# LOG CLASS - TO BE INCLUDED FROM ERR_HANDLER AND OTHER CLASSES WHICH WANT TO LOG
class pi_log:
    """ PI_LOG Class 
        Does include an own pi_err class+object to better handle the information        
    """
    
    class err:
        try:
            import classes.pi_err as o
            o = pi_err()
        except:
            raise
        
    # INIT ERROR HANDLER (create object - every object has its error handler object)
    def __init__(self):
        self.oerr = self.create_error_object()#self.err()
        # init inner class + init oerr class
        # if error -> raise error
        # oErr = oErr.err_handle()
        CONF_USING_ERR_T = t # py_log = 5

        # INSERT FUNCTION NAMES HERE (automatically if somehow possible? pi_conf.names?) [-> should overwrite the default vars]
        oErr.err_a = {  0 : '_init_', \
                        1 : 'cache', \
                        2 : 'ras', \
                        3 : 'case_run', \
                        4 : 'r_sec', \
                        5 : 'cache_conf', \
                        6 : 'r', \
                        7 : 'w', \
                        8 : '', \
                        9 : '', \
                        10: '' }


        # READ Information for LOG module
        CACHE   = oconf.cache(2)

        fhandle = open( CACHE.FULL_PATH, "r", CACHE.ENC) # just to check if the file could be opened
        if fhandle: return 1 # succesfully initialized
        return 0 # error happened 

    def p(str): # console
        print(str)

    def c(str): # console
        console.write_output(str)
    


    # dictionary defining an index from variable names

    val  = {"vIdx":0,
            "vSoW":1,           # d;     summer=1; winter=0
            "vMod":2,           # d;     module number
            "vVlm":3,           # degC;  Vorlauf, measured
            "vRlm":4,           # degC;  Ruecklauf, measured
            "vVle":5,           # degC;  Vorlauf, evaluation base
            "vRle":6,           # degC;  Ruecklauf, evaluation base
            "vSol":7,           # degC;  Solltemperatur, set-temperature
            "vVen":8,           # %;     estimated valve position 0..100%
        }

    #global av
    global heizkreis
    global modules
    global modTVor     # Modul Nr. mit zentraler Vor- unf Ruecklauftemperatur
    global modSendTvor
    global filtFakt


    h = hkr_cfg.get_heizkreis_config()
    (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h


    def select_first_file_index( flist, lastFileIndex, firstSec ):
        err = 0
        idx = lastFileIndex-1
        while idx >= 0 :
            hs = flist[idx].split("_")
            try:
                datum=hs[1]
                zeit =hs[2].split(".")[0]
            except Exception as e:
                print(e)
                err = 3
            else:
                hstr = datum+"_"+zeit

            try:
                sec = time.mktime( time.strptime(hstr,"%Y%m%d_%H%M%S") )
            except Exception as e:
                print(e)
                err = 4

            if sec < firstSec:
                break
            idx -= 1

        if err!=0:
            return -1
        elif idx >= 0 :
            #print( sec, firstSec )
            return idx
        else:
            return 0
        
    def select_logfiles( choice ):
        # list all log-files in "./log/*"
        # choice    "N" <=> ask; 'E' <=> Ende; 'L' <=> Letzter Tag; 'Z' <=> letzte 2 Tage
        err = 0
        flist = glob.glob("log/log*.dat")
        flist.sort()
        fileNr = 0
        for file in flist:
            fileNr += 1
            if (choice=="N" or choice=="n") :
                print("%d  -  %s"%(fileNr, file))
        lastFileIndex = fileNr-1

        if len(flist) == 0:
            print( "Keine Log-Dateien gefunden" )
            return []
        
        # extract date and time from last file in list:
        # "logHZ-RR_20161228_043534.dat"  (typical filename)
        lastFileName = flist[lastFileIndex]
        
        #print("last file nr=%d, name=%s"%(lastFileIndex+1,lastFileName))
        hs = lastFileName.split("_")
        try:
            datum=hs[1]
            zeit =hs[2].split(".")[0]
            #print(datum,zeit)
        except Exception as e:
            print(e)
            err = 1
        else:
            hstr = datum+"_"+zeit
            try:
                lastSec = time.mktime( time.strptime(hstr,"%Y%m%d_%H%M%S") )
            except Exception as e:
                print(e)
                err = 2

        #print("err=",err)
        if err == 0 :
            #print("lastSec=%d"%(lastSec))
            ende = False
            while not ende:
                if choice == "N":
                    print("E)nde; L)etzter Tag; Z)wei letzte Tage; 1,2,3... von Datei")
                    print("Wahl:", end="")
                    w=input()
                else:
                    w=choice

                if w=="E" or w=="e":
                    return[]

                if w=="L" or w=="l":
                    firstSec = lastSec - 3600 * 24
                    firstFileIndex = select_first_file_index( flist, lastFileIndex, firstSec )
                    ende = True

                elif w=="Z" or w=="z":
                    firstSec = lastSec - 3600 * 48
                    firstFileIndex = select_first_file_index( flist, lastFileIndex, firstSec )
                    ende = True

                else:
                    try:
                        w0=int(w)-1
                    except Exception as e:
                        print(e)
                    else:
                        if 0 < w0 <= lastFileIndex+1 :
                            firstFileIndex = w0
                            if w0 != lastFileIndex:
                                w=input("Bis Datei Nr:")
                                try:
                                    w0=int(w)-1
                                except Exception as e:
                                    print(e)
                                else:
                                        if firstFileIndex <= w0 <= lastFileIndex:
                                            lastFileIndex=w0
                            ende = True

            fl = []

            for i in range(firstFileIndex,lastFileIndex+1):
                fl.append(flist[i])
            return fl






    # ----------------
    # ----- main -----
    # ----------------



    # test:
    #
    #flist = select_logfiles("N")
    if __name__ == "__main__" :
        flist = select_logfiles("L")
        print( flist )
        
        