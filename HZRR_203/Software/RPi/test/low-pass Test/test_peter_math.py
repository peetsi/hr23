#!/usr/bin/python3
# -*- coding: utf-8 -*-

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
    #loga_obj = hz_rr_log_analyzer()
    #loga_obj.runme()

    _values     = _rnd_float_range(54,61,3,10000)
    vle         = _values.pop()
    vle1        = vle
    vlZen       = vle
    filtFakt    = 0.25
    print( f'[{len(_values)}](vle:{vle}, vle1:{vle1}, vlZen:{vlZen})' )    #long list to simulate a night

    while (len(_values)>0):
        vle     = _values.pop()
        vle1    = vle      * filtFakt + vle1   *   (1-filtFakt)
        vlZen   = vle1    * filtFakt + vlZen  *   (1-filtFakt)
        print( f'[{len(_values)}](vle:{vle}, vle1:{vle1.__round__(3)}, vlZen:{vlZen.__round__(3)})' )