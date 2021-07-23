#!/usr/bin/python3
# -*- coding: utf-8 -*-

# low-pass demo, pl2at

import matplotlib.pyplot as plt
import numpy as np 

vle1   = 40.0   # nur als Demo, sonst vle[0] == "first run"
y      = vle1

def low_pass(vle, filtFakt):
    global vle1, y
    vle1  = vle   * filtFakt + vle1  * ( 1 - filtFakt )
    y     = vle1  * filtFakt + y     * ( 1 - filtFakt ) 
    return y

if __name__ == "__main__":
    #loga_obj = hz_rr_log_analyzer()
    #loga_obj.runme()

    vle      = np.random.rand(1000) * 5  + 55   # random array from55.0 - 60.0
    vlZen05    = np.array([low_pass(x,0.05) for x in vle])  # 05% filter Faktor
    vlZen10    = np.array([low_pass(x,0.10) for x in vle])  # 10%
    vlZen25    = np.array([low_pass(x,0.25) for x in vle])  # 25%

    t = range(len(vle))
    plt.plot(t,vle,label="vle")
    plt.plot(t,vlZen05,label="vlZen05")
    plt.plot(t,vlZen10,label="vlZen10")
    plt.plot(t,vlZen25,label="vlZen25")
    plt.legend()
    plt.grid()
    plt.show()

