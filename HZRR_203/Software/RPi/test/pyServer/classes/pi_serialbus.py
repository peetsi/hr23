#python -m serial.tools.list_ports

#READ THE RS485 PART with peter!! https://pythonhosted.org/pyserial/pyserial_api.html

class serbus(object):
  """Serial Bus Communication
  
  Raises:
      ImportError: Import error - if "serial" can't be included - fatal error.
  
  Initialise:
      Call init with ADDRESS, TIMEOUT, and BAUD Rate.
  
  Usage:
      s = serbus( usb_address, timout_int, baud_int )
      s.ser is the serial object
      s.recv(bytes, timetolive) <- receives up to X bytes.
      s.send(message) <- sends string
  """
  try:
    import pi_modbus
    import serial
    import io
    import time
  except ImportError:
    raise ImportError('Error: Could not import - Fatal.')
  
  mb = pi_modbus.pi_modbus()
  # SERIAL MODULE CONSTANTS FOR EACH CONNECTION
  ser = serial.Serial() # main init
  ser.port     = '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0' # 
  ser.baudrate = 115200 # 115200  b          change baud rate
  ser.parity   = 'N' # PARITY_NONE, PARITY_EVEN, PARITY_ODD PARITY_MARK, PARITY_SPACE || N E O S M  change parity (None, Even, Odd, Space, Mark)
  ser.stopbits = 2 # STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO || 1 2 3      set stop bits (1, 2, 1.5)
  ser.bytesize = 8 # FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
  ser.timeout  = None # 
  ser.xonxoff  = 0  # x X        disable/enable software flow control
  ser.rtscts   = 0  # r R        disable/enable hardware flow control
  ser.dsrdtr   = 0  # Enable hardware (DSR/DTR) flow control.
  ser._recv_buf= ""
  ser.recv     = ""
  ser.send     = ""

  def __init__(self, port='/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0', baud=115200, parity = 'N', bytesize = 8, stopbits = 2, timeout = None, xonxoff=0, rtscts=0, dsrdtr=0):
    print("Serial Bus initiating\n")         # check which port was really used
    #print("Port: " + self.ser.name)         # check which port was really used
    #self.ser = self.serial.Serial('/dev/ttyUSB0')
    #self.ser.close()             # close port
    #init all the available values - the nthe connection can be opened with "open"
    try:
      self.ser.port     = port
      self.ser.baudrate = baud
      self.ser.parity   = parity
      self.ser.stopbits = stopbits
      self.ser.bytesize = bytesize
      self.ser.timeout  = timeout
      self.ser.xonxoff  = xonxoff
      self.ser.rtscts   = rtscts
      self.ser.dsrdtr   = dsrdtr
      self.ser._recv_buf= ""
      self.ser.recv     = ""
      self.ser.send     = ""
    #except SerialException as e:
    #  raise self.ser.SerialException( "01 cannot find: %s"%(self.ser.port) + "\n   exception = %s"%(e))
    except Exception as e:
      raise Exception("02 Something else is wrong with Serial Port: %s"%(self.ser.port) + "\n exception = %s"%(e))
    print("Serial Bus initiated\n") # no problem - just continue
    #return self

  def close(self):
    if (self.ser.is_open): return self.ser.close()
    print('Error: Serial Connection was not open, therefore could not close handle\n')
  
  def open(self):# port='COM1', baud=115200, parity = 'N', bytesize = 8, stopbits = 1, timeout = 0, xonxoff=0, rtscts=0, dsrdtr=0
    if (self.ser.is_open): return print('Error: Serial Connection could not been opened, it is already open..')
    self.ser.open()

  def unwrap(self, msg, output_level='O'):
    # dict or non dict - both accepted
    # example:
    # msg can be either dict (for wrapping) 
    # :
    # packet_to_arduino =  { "data":'hi - WRAP ME!', "adr": '00', "cmd": '01', "m_adr2m" : '09', "regler" : '02', "version" : '01' } 
    # or a simple string (for unwrapping)
    # :01020902hi im a data stringsendfromversion01ckhsmlrc
    self.mb.use(msg)
    self.mb.unwrap()
    return self.mb.show(output_level) 

  def wrap(self, msg, output_level='O'): 
    # dict or non dict - both accepted
    # example:
    # msg can be either dict (for wrapping) :
    # packet_to_arduino =  { "data":'hi - WRAP ME!', "adr": '00', "cmd": '01', "m_adr2m" : '09', "regler" : '02', "version" : '01' } 
    # or a simple string (for unwrapping)
    # :01020902hi im a data stringsendfromversion01ckhsmlrc
    self.mb.use(msg)
    self.mb.wrap()
    return self.mb.show(output_level) 

  def show(self, output_level='O'):
      return self.mb.show(output_level)

  def send(self, m):
    try:
      self.ser.write(m)
    #except self.ser.SerialTimeoutException as e:
    #  raise self.ser.SerialTimeoutException( 2, "07 [SerialTimeoutException] Write::SerialTimeoutException = %s"%(e))
    #except self.ser.SerialException as e:
    #  raise self.ser.SerialException( 2, "08 [SerialException] Write::Serialexception = %s"%(e))
    except Exception as e:
      raise Exception( 2, "09 [SerialException] Write::exception = %b"%(e))

  def recv(self, bytes = 64, ttl=50):
    self.ser.read(bytes)  # for the  current project, 64 bytes should be max.
                          # maybe 66 - ask peter

  def flush(self, io = 'I'): # 'I' or 'O' or 'F'  (input/output/full flush) [lowercase input is accepted]
    if (io.upper() == 'I'):
      return self.ser.reset_input_buffer()
    elif (io.upper() == 'O'):
      return self.ser.reset_output_buffer()
    elif (io.upper() == 'F'):
      self.ser.reset_input_buffer()
      return self.ser.reset_output_buffer()
    else:
      return print('error - please use I/O/F as parameter.')

  def s(self, set_prop, set_value):
    return setattr(self, set_prop, set_value)

  def cmd(self, cmd):
    return 0


"""
Ungefährer Ablauf:

modul = slave

{ ## ping
master -> modul ping (cmd1)
master(warte auf antwort)
modul -> antwort an master (cmd1+ACK || cmd1+NAK || TTL > maximalwert)
master interpretiert antwort über parser ( ACK = set_flag(vorhanden) || NACK = set_flag(nicht_vorhanden) || TTL > mW  = set_flag(timeout))
}

{ ## broadcast (queue undecided)
master -> alle x(2) min broadcast an alle module "mit zentrale vorlauftemperatur(vlt)"
module -> save(vorlauftemperatur)
module -> set(timeout, zentralevorlauftemperatur (vlt)) timeout==abgelaufen? use(module_vlt) : use(master_vlt)
__MODULE DOES NOT RESPOND TO SERVER - AS BROADCAST COULD BE MULTIPLE DEVICES AT THE SAME TIME__ (no collision detection)
}

{ ## recv()
master.send(cmd, <nr>) ->  modul get_values( <nr> )
modul.send(cmd + ack + values) // has to be defined later -
}

{ ## set_par( property, value )
  while (master.recv() == NAK || tries <= x):
    master.send(cmd, <par>)   -> modul.recv_set_par( <par> ) 
    modul.send( ACK || NAK )  -> master.recv( ACK || NAK || TTL>maxzeit)
}

{ ## LCD/Digital Anzeige per thread
master -> run_Thread(anzeige(answer)
}

{ ## log
master -> log answer (temperaturen,ventilzeiten etc.)

{ date of pi }           : {adr}  {deprecated} {Sommer/Winter}{vorlauf_MODUL}{rücklauf_MODUL}{vorlauf_extern}{deprecated}{deprecated}{deprecated}
20191015_075649 0101 HK2 :0002011a t4174150.2         S           VM 45.6        RM 28.3         VE 20.0        RE 28.3    RS  0.0       P074      E0000 FX0 M2420 A145 


module[1-x] -> "set zentrale vorlauftemperatur"  &&  darf nichts zur bestätigung senden



"""

if __name__ == "__main__":
  
  sb = serbus()     #                    platform-3f980000.usb-usb-0:1.1.3:1.0-port0 # rechts ethernet port unten
          
          #   TEMPLATE:
          #   [ETH] [USB] [USB]
          #         [USB] [USB]
          #
          # platform-3f980000.usb-usb-0:1.1.3:1.0-port0
          #   [ETH] [USB] [USB]
          #         [485] [USB]       
          #                              platform-3f980000.usb-usb-0:1.1.3:1.0-port0
  # this is the PI port:
  sb.ser.port     = '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0' # old von peter: '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.3:1.0-port0' #'/dev/ttyUSB0'
  
  # this is the windows "COM" port:
  sb.ser.port     = 'COM9'
  
  sb.ser.baudrate = 115200
  sb.ser.timeout  = 10    # seconds?
  sb.parity       = None  # sb.ser.PARITY_NONE
  sb.stopbits     = 2     # sb.ser.STOPBITS_TWO
  sb.bytesize     = 8     # sb.ser.EIGHTBITS
  sb.timeout      = None  # sb.ser.none
  sb.xonxoff      = False
  sb.rtscts       = False
  sb.dsrdtr       = False
  sb.open()
  
  run = True
  i = 0
  while run == True:
    print( "sending hello to arduino - but wrapped!")
    packet_to_arduino =  { "data":   'hi - WRAP ME!', 
                          "adr":     '00', 
                          "cmd":     '01', 
                          "m_adr2m": '09', 
                          "regler" : '02', 
                          "version": '01' 
                          } 
    sb.wrap(packet_to_arduino)
    msg = sb.show('O')
    print( "[SEND] >> %s"%msg.encode('ascii'))
    sb.send(msg.encode('ascii'))


    #print("[%s] Debug: waiting for a message to arrive.."%sb.time.ctime())
    i = i + 1
    sb.time.sleep(1)
    buf = sb.ser.readline()
    if not(buf == ""):
      print( "[RECV] << " + buf.decode('utf-8') )



  # oder auch:
  #sb = serbus('/dev/ttyUSB0', 115200, 10, sb.ser.PARITY_NONE, sb.ser.STOPBITS_ONE, sb.ser.EIGHTBITS, sb.ser.none, 0, 0, 0  )


"""

#usb_ser.py

import serial

import time

import modbus as rmb
import vorlaut as vor




  # serPort = "/dev/ttyUSB0" # USB0 might change
  # fixed for the same adapter is always:
  # serPort = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A504YCFM-if00-port0"
  # has problems if the adapter changes (because of serial number)
  # so we use the USB-socket where the adapter is connected:
  # Bottom socket next to Ethernet socket:


sb = serbus()


class serbus():

  #read serport from conf file
  serPort = "/dev/serial/by-path/platform-3f980000.usb-usb-0:1.3:1.0-port0"

  def __init__(self):
      return 0

  def get(self, var, default_var=""):
      return getattr(self, var, default_var)

  def set(self, var, attr):
      return setattr(self, var, attr)

  def con() :
    global ser
    err=0
    try:
      ser = serial.Serial(
        port=serPort,
        baudrate =19200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_TWO,
        bytesize = serial.EIGHTBITS,
        timeout = 0.2)
    except serial.SerialException as e:
      vor.vorlaut( 3,  "01 cannot find: %s"%(serPort))
      vor.vorlaut( 3,  "   exception = %s"%(e))
      err = 1
    except Exception as e:
      vor.vorlaut( 3,  "02 something else is wrong with serial port: %s"%(serPort))
      vor.vorlaut( 3,  "   exception = %s"%(e))
      err = 2
    return err

  def open():
    # open USB->RS485 connection
    global ser
    err=0
    try:
      ser.open()
    except serial.SerialException as e:
      vor.vorlaut( 3,  "03 cannot open: %s"%(serPort))
      vor.vorlaut( 3,  "   exception = %s"%(e))
      err = 3
    except  Exception as e:
      vor.vorlaut( 3,  "04 something else is wrong with serial port:"%(serPort))
      vor.vorlaut( 3,  "   exception = %s"%(e))
      err = 4
    return err

  def rst_buf():
    global ser
    err=0
    try:
      ser.flushOutput()  # newer: ser.reset_output_buffer()
      ser.flushInput()   # newer: ser.reset_input_buffer()
    except serial.SerialException:
      err = 5
      vor.vorlaut( 3,  "05 cannot erase serial buffers")
      vor.vorlaut( 3,  "   exception = %s"%(e))
    except Exception as e:
      err = 6
      vor.vorlaut( 3,  "06 something else is wrong with serial port: %s"%(serPort))
      vor.vorlaut( 3,  "   exception = %s"%(e))
    return err

  def cmd( txCmd ) : # add TXRX functionality
    global ser
    global line
    twait1 = 0.01
    twait2= 0.01

    ser.flushInput()
    ser.flushOutput()
    vor.vorlaut( 2, "\ntx: %s"%(txCmd[:-2]))
    try:
      ser.write(txCmd)                  # start writing string
    except serial.SerialTimeoutException as e:
      vor.vorlaut( 2, "07 timeout sending string: %s"%(cmd))
      vor.vorlaut( 2,  "  exception = %s"%(e))
    except serial.SerialException:
      vor.vorlaut( 2,  "08 SerialException on write")
      vor.vorlaut( 2,  "   exception = %s"%(e))
      ser.close()
    except   Exception as e:
      vor.vorlaut( 2,  "09 error serial port %s, writing"%(serPort))
      vor.vorlaut( 2,  "   exception = %s"%(e))
      ser.close()
    
    ser.flush()
  #time.sleep( twait1 )   # maybe not necessary: flush waits unitl all is written
  # using USB-RS485 converter: no echo of sent data !
  # receive answer from module
  line = ser.readline()

  try:
    line = line.decode()
  except Exception as e:
    vor.vorlaut( 2,  "10 cannot decode line")
    vor.vorlaut( 2,  "   exception = %s"%(e))
    pass

  rxCmd = rmb.unwrap_modbus( line )
  return rxCmd

  # ------- functions
  # rr_parse.py


  # old log file data set format
  # 20170110_172715 0101 :0002011a t1813989.6  W VM 61.8 RM 47.2 VE 61.8 RE 47.2 RS 41.7 P018 E0000 FX0 M5133 A704

  # new log file data set format
  # change: HKx in front of ':'
  # 20170111_200810 0101 HK1 :0002011a t1910046.5  W VM 56.5 RM 33.7 VE 56.5 RE 33.7 RS 39.6 P020 E0000 FX0 M5394 A706

  # data set structure:
  # ':' defines two parts:
  #     left part:  from 'Zentrale' added data
  #     right part: from module retreived data
  #

  def get_float( token, string, maxlen ) :
      # if maxlen == 0 -> read until next blank
      pos1 = string.find(token) + len(token)
      while string[pos1] == " " :
          # find first character
          pos1 += 1
      pos2 = pos1
      while pos2 < len(string) and string[pos2] != " " :
          # find end of value string
          pos2 += 1
      if pos2 > pos1+maxlen :
          pos2 = pos1+maxlen
      s1 = string[pos1:pos2]
      #if token == " M":
      #    print("pos1=%d; pos2=%d; maxlen=%d; s1=%s;token=%s; in string=%s"%(pos1,pos2,maxlen,s1,token,string))

      return float(s1)

  def get_hex( token, string, maxlen ) :
      # if maxlen == 0 -> read until next blank
      pos1 = string.find(token) + len(token)
      pos2 = pos1
      while pos2 < len(string) and string[pos2] != " " :
          # find end of value string
          pos2 += 1
      if pos2 > pos1+maxlen :
          pos2 = pos1+maxlen
      s1 = string[pos1:pos2]
      #print("pos1=%d; s1=%s; token=%s; in string=%s"%(pos1,s1,token,string))
      return int(s1, base=16)

  # ----- parse one line from hz_rr module -----
  def rr_parse( dataset ) :
      dset0 = dataset.strip()           # remove linefeed etc
      dset1 = dset0.split(":")        # zentrale and module part

      err = 0
      if len(dset0) < 80 :  # too view data
          err = 1
          return (1,err)

      # dZen = typically
      # '20170110_172715 0101 '      (old version)
      # '20170111_200810 0101 HK1 '  (new version)
      dZen0 = dset1[0]  # Zentrale part
      # dMod = typically
      # '0002011a t1813989.6  W VM 61.8 RM 47.2 VE 61.8 RE 47.2 RS 41.7 P018 E0000 FX0 M5133 A704'
      dMod0 = dset1[1]  # module   part
      # parse Zentrale part
      # -------------------

      # ['20170110_172715', '0101', '']          (old)
      # ['20170111_200810', '0101', 'HK1', '']   (new)

      # get date and time of data set (Z-time)
      dZen1 = dZen0.split(" ")
      try:
          hstr = dZen1[0]                 # date and time
          zDateSec = time.mktime( time.strptime(hstr,"%Y%m%d_%H%M%S") )
      except Exception as e:
          err = 2
          print(e)
          return (1,err)

      # '0101' is module number and command; is also contained in module data set
      # is not evaluated here
      # try to retrieve "Heizkreis" number after "HK" string (new)
      try:
          hstr = dZen1[2]
          if hstr != "":
              hkr = int(hstr[2:])
          else :
              hkr = -1
      except Exception as e:
          err = 3
          print(e)
          return (1,err)



      # parse module part
      # -----------------

      # '0002011a t1813989.6  W VM 61.8 RM 47.2 VE 61.8 RE 47.2 RS 41.7 P018 E0000 FX0 M5133 A704'

      # parse first block:
      #   module nr     e  {0x01..0x1E} = {1..30}
      #   command nr    e  {0x01 .. 0xFF}, command and controller number
      #   controller nr e  {0,1,2,3,4},   0: module related; else: controller nr.
      #   protocol vers.e  {a,b,c,...}
      try:
          dMod1 = dMod0[0:8]
          #print(dMod1)
          command  =  int( dMod1[2:4],base=16)
          module   =  int( dMod1[4:6],base=16)
          control  =  int( dMod1[6:7])
          protVer  =  dMod1[7]
      except Exception as e:
          err = 4
          print(e)
          return (1,err)

      # timestamp from module: seconds since last reset or power up of module
      modTStamp = get_value_float( " t", dMod0, 15 )
      #print(modTStamp)

      # find summer / winter mode
      if " W " in dMod0:
          summer = 0
      elif " S " in dMod0:
          summer = 1
      else:
          summer = -1            # error
          err = 5
          return (1,err)

      dMod1 = dMod0[ dMod0.find(" VM") : ]    # use only trailing string to speed up

      # get tmperature values
      try:
          vlm = get_float( " VM", dMod1, 15 )  # Vorlauf, measured
          rlm = get_float( " RM", dMod1, 15 )  # Ruecklauf, measured
          vle = get_float( " VE", dMod1, 15 )  # Vorlauf, evaluation
          rle = get_float( " RE", dMod1, 15 )  # Ruecklauf, evaluation
          rls = get_float( " RS", dMod1, 15 )  # Ruecklauf, set value
          ven = get_float( " P",  dMod1, 15 )  # valve setting, ca. percent
          err = get_hex(   " E",  dMod1,  5 )  # status label (e.g. error)
          fix = get_float( " FX", dMod1, 15 )  # 0:variable; else valve in fixed pos.
          tmo = get_float( " M",  dMod1, 15 )  # sec; motor running time since power up
          tan = get_float( " A",  dMod1, 15 )  # count of limits reached (Anschlag)
      except Exception as e:
          err = 6
          print(e)
          return (1,err)

      #print(zDateSec,hkr,module,command,control,protVer,modTStamp,summer,
      #      vlm,rlm,vle,rle,rls,ven,err,fix,tmo,tan)
      return(zDateSec,hkr,module,command,control,protVer,modTStamp,summer,
            vlm,rlm,vle,rle,rls,ven,err,fix,tmo,tan)


  # ----- main -----


  # test:
  if __name__ == "__main__" :
      dold = "20170110_172715 0101 :0002011a t1813989.6  W VM 61.8 RM 47.2 VE 61.8 RE 47.2 RS 41.7 P018 E0000 FX0 M5133 A704"
      dnew = "20170111_200810 0101 HK1 :0002011a t1910046.5  W VM 56.5 RM 33.7 VE 56.5 RE 33.7 RS 39.6 P020 E0000 FX0 M5394 A706"

      dset = dold
      a1=rr_parse( dset )
      print("a1=",a1)

      dset = dnew
      a2=rr_parse( dset )
      print("a2=",a2)

      a3=rr_parse( "xxx" )
      print("a3=",a3)




  # modbus.py

  from usb_ser import *

  import vorlaut as vor


  def checksum( s ) :
    cs = 0
    for c in s :
      try:
        cs += ord(c)
      except Exception as e :
        cs = 0          # generate wrong checksum intentionally
        # TODO sotre e in logfile
    cs = cs & 0xFFFF    # make unsigned 16 bit
    return cs


  def lrc_parity( s ) :
    # s contains whole string to be wrapped; for
    lrc = 0;
    for c in s :
      # TODO error:"ord() expected string of length 1, but int found"
      #      abfangen
      try:
        lrc = lrc ^ ord(c)
      except Exception as e :
        lrc = 0               # generate wrong lrc inentionally
        # store e in logfile
    lrc = lrc & 0x00FF
    return lrc


  def wrap_modbus( adr, fnc, contr, cmdstr ) :
    # adr      module address
    # fnc      function number
    # contr    regulator number 1,2,3,4 or 0 for module
    # cmdstr   command-string; could be "" empty
    cmd = "%02X%02X%1X%s"%(adr, fnc, contr, cmdstr )
    cs = checksum( cmd )
    cmd = "%s%04X"%(cmd,cs)
    lrc = lrc_parity( cmd )
    cmd = ":%s%02X\r\n"%(cmd, lrc)
    cmd = cmd.encode()
    return cmd


  def unwrap_modbus( line ) :
    # calculate checksum and parity of received line
    calcLrc = 0
    calcCsm = 0
    lineLrc = 0
    lineCsm = 0

    err_rx = 0
    l = len( line )
    if l==0 :
      err_rx |= 1
      return "err: len=0"

    s0 = line[l-4:l-2]
    s0 = s0.upper()           # user only uppercase hex 'A'...'F'
    try:
      lineLrc = int(s0,base=16)
    except Exception as e:
      vor.vorlaut(3,e)
      err_rx |= 2
    else:
      calcLrc  = lrc_parity( line[ 1 : l-4 ] )

    s1 = line[l-8:l-4]
    s1 = s1.upper()           # user only uppercase hex 'A'...'F'
    try:
      lineCsm = int(s1,base=16)
    except Exception as e:
      vor.vorlaut( 3, e)
      err_rx |= 4
      # fliegt raus -> stoppt Programm
    calcCsm  = checksum( line[ 1 : l-8 ] )

    vor.vorlaut( 3,  "cmd=%s"%(line))
    vor.vorlaut( 3,  "%s lineCs =%04X calcCs =%04X"%(s1,lineCsm,calcCsm))
    vor.vorlaut( 3,  "%s lineLrc=%02X calcLrc=%02X"%(s0,lineLrc,calcLrc))
    if lineLrc==calcLrc and lineCsm==calcCsm :
      return line[ 0 : l-8 ]
    else:
      vor.vorlaut( 3, "error %04X in received string"%(err_rx))
      return "err_rx=%04X"%(err_rx)


"""