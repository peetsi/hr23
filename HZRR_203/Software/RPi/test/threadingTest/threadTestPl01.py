# Eine Funktion zur Datenerfassung wird in einen thread ausgelagert
# und erhält Kommandos über eine Queue,
# sie wickelt die serielle Kommunikation ab und sendet die Antwort
# über eine Antwort-Queue zurück; diese wird ebenfalls über die
# Parameter übergeben.
# somit kann die Datenerfassungsfunktion von verschiedenen Threads
# aufgerufen werden. 
#
# in diesem Beispiel ist das aufrufende logger-Programm im Hauptprogramm,
# bei mehreren threads müssen dieses und die anderen in eigenen threads
# laufen.


import time
import queue
from threading import Thread


#------------------------------------------------------------------
# queues zum Datenaustausch mit dem communication-thread definieren
#------------------------------------------------------------------
# NOTE: alle Variablen die vor dem Abspalten von threads
#       definiert werden ist allen threads und dem Hautpprogramm
#       gemeinsam. So vor allem auch cmd_q:

# die command-queue wird von allen threads mit anfragen verwendet:
print("define command queue, input to communication thread:")
cmd_q = queue.Queue(maxsize=0)



#------------------------------------
# serielle Kommunikation - Simulation
#------------------------------------
def comm_module(qi):
    # qi    queue input, enthält Kommandos
    wert=0 # dummy Zaehler
    ende = False
    while not ende:
        cmd=qi.get()
        print("comm: cmd=",cmd)
        if cmd == "stop":
            ende=True
        else:
            aq = cmd[1]   # antwort an diese queue
            
            # *** sende commandstring an Modul,
            #     warte auf Antwort / timeout
            #     gibt emfpangenen String zurück
            
            # z. B.:
            aq.put(":00011E0b123456_%d"%(wert)) # dummy antwort
            wert += 11
            qi.task_done()


# communication in einen separaten thread laufen lassen
comm_th = Thread(target=comm_module, args=(cmd_q,))
comm_th.setDaemon(True)   # kill thread when main program exits
comm_th.start()



#----------------
# logger function
#----------------
# NOTE: ist hier als Hauptprogramm geschrieben. Wenn tatsächlich
#       mehrere Programme laufen sollen, müssen diese auch als
#       eigener thread abgespalten ('spawn') werden.
#       Alle Variablen, die vor dem Abspalten defniert wurden
#       sind allen Threads gemeinsam. Dennoch dürfen Variable
#       in den Threads nicht verändert werden, sonder müssen über
#       die queues an den aufrufenden thread übergeben werden.
#       also: nur EIN THREAD darf VARIBLE ÄNDERN

# *** ab hier können alle Funktionen in einen eigenen thread laufen
#     späteres Beispiel

# Die logger-queue enthält Antworten an den log-thread
print("define logger queue, answer to logging program")
log_q = queue.Queue(maxsize=0)

for modul in [1,2,3,4,5]:
    # fertiger String zu senden
    cmdStr=":%02X010b123456"%(modul)
    cmd_q.put((cmdStr,log_q))
    while log_q.empty():   # wait for answer
        pass
    answer = log_q.get()
    print("log: antw.=",answer)
    


time.sleep(1)


#--------------------------
# Task kann beendet werden:
#--------------------------
cmd_q.put("stop")   # sende nochmal an thread
comm_th.join()



