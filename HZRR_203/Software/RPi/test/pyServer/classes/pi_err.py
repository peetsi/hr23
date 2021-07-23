# IMPORTS
try:
  import pi_log as olog
  import time as oTime
except ImportError:
  raise "Error"
  #error here, we do not want to continue if there is no object creation
  #all of them are required!


# MAIN ERROR HANDLING - WILL BE USED IN THE SPECIFIC HANDLERS TO SHARE BASIC INFORMATION
class pi_err:
  # identify where the error is coming from
  err_t = { 1 : 'py_conf',\
    2 : 'py_err_handler', \
    3 : 'py_gfx', \
    4 : 'py_live_mon', \
    5 : 'py_log', \
    6 : 'py_mail', \
    7 : 'py_serialbus', \
    8 : 'py_initializer', \
    9 : 'pi_vmon' }
  # move those definitions to settings cache later... / could be then also used for language or whatever
  # INSERT FUNCTION NAMES HERE (automatically if somehow possible? pi_conf.names?)
  # this will be changed by the individual function like in pi_conf.py for example
  # i want to automate this procedure if possible
  err_a = { 0 : '_init_', \
    1 : 's_t', \
    2 : 's_a', \
    3 : 'g', \
    4 : 'vorlaut' } # ka was vorlaut it - peter fragen

  def __init__(self):
    # CREATE LOG FILE WRITER/READER OBJECT
    self.ol = olog.pi_log()

  def s_t(self, t ) : # class
    self._errtype = self.err_t[t]
  
  def s_a(self, a ) :  # function
    self._erradr = a 
  
  def g(self, *str ) :  #generate error
    self.s_a(4) # set error function to g()  <- i wanna automate this

    self.pstr = {  1 : '{PARAM}', \
              2 : '{PARAM}', \
              3 : '{PARAM}'} # entire message

    self.ret = ""
    i = 0
    for key in str:
      if i < 3 : 
        i += 1
      
      elif i >= 4 : 
        g( "too many parameters - i > 3",  -1, "g(*str) accepts maximum of 3 parameters, use less.."  )
        return -1  # too many parameters

      self.pstr[i].format(param = key)

    self._errtime  = time.strftime('%Y-%m-%d_%H:%M:%S')
    self._errtype  = self.pstr[i]                                 # FATAL/ C
    self._erradr   = self.err_a[_erradr]                    # set in the beginning of function in class 
    self._errnum   = 0                                 # line number
    self._errdesc  = self.pstr[1]  
    #expand later

    err_fstr  = ""

    err_head  = "[ERROR][{ERR_TYPE}][{ERR_TIME}] >>".format( ERR_TYPE = _errtype, ERR_TIME = _errtime)
    err_adr   = "   >> ADR:     {ERR_ADR}".format( ERR_ADR, _erradr)      # get line and function name on its own if possible
    err_num   = "   >> LINE-NUM:{ERR_LINE}".format( ERR_LINE, _errline ) 
    err_desc  = "   >> DESC:    {ERR_DESC}".format( ERR_DESC, _errdesc)
    err_fix   = "   >> VAL:     {ERR_VAL}".format( ERR_VAL, _errval)
    err_val   = "   >> FIX:     {ERR_FIX}".format( ERR_FIX, _errfix )
    err_end   = "<<"
    # add more if you'd like to
    # function call: .g( err_desc, err_val, err_fix  )

    err_str  = err_head + "\n" + err_adr + "\n" + err_num + "\n" + err_desc + "\n" + err_fix + "\n" + err_val + "\n" + err_end + "\n"

    # print the string in console
    print(err_str)

    # print the string in the VMON later

    # log the string into log file


  def vorlaut(self, rang, s):
    # rang: 9 high, 0 low
    # gib nur Werte mit einem mindestrang aus
    rang_min = 9
    if rang >= rang_min:
      print(s)

