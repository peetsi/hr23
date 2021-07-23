#!/usr/bin/python3
# -*- coding: utf-8 -*-

# low-pass demo, pl2at

import matplotlib.pyplot as plt
import numpy as np 

vle1   = 30.0   # nur als Demo, sonst vle[0] == "first run"
y      = vle1

def low_pass(vle, filtFakt):
    global vle1, y
    vle1  = vle   * filtFakt + vle1  * ( 1 - filtFakt )
    y     = vle1  * filtFakt + y     * ( 1 - filtFakt ) 
    return y

if __name__ == "__main__":
    #loga_obj = hz_rr_log_analyzer()
    #loga_obj.runme()

    filtFakt    = 0.1
    vle      = np.random.rand(1000) * 5  + 55   # random array from55.0 - 60.0
    vlZen    = np.array([low_pass(x,filtFakt) for x in vle])

    t = range(len(vle))
    plt.plot(t,vle,label="vle")
    plt.plot(t,vlZen,label="vlZen")
    plt.legend()
    plt.grid()
    plt.show()

