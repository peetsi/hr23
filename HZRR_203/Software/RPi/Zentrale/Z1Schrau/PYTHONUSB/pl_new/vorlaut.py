def vorlaut( rang, s="",nl=True):
  ''' print message if higher 'rang', nl=newline'''
  # rang: 9 high, 0 low
  # gib nur Werte mit einem mindestrang aus
  rang_min = 0
  if rang >= rang_min:
    if nl:
      print(s)
    else:
      print(s,end="")  
