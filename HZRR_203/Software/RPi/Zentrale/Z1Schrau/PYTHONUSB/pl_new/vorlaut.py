def vorlaut( rang, s="",newline=True):
  # rang: 9 high, 0 low
  # gib nur Werte mit einem mindestrang aus
  rang_min = 0
  if rang >= rang_min:
    if newline:
      print(s)
    else:
      print(s,end="")  
