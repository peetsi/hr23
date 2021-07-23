import numpy as np
from graphics import *
import usb_ser as us
import modbus  as mb
import heizkreis_config as hkr_cfg
import rr_parse as parse








class lmon():

    def __init__(self):


    def get(self, var, default_var=""):
        return getattr(self, var, default_var)

    def set(self, var, attr):
        return setattr(self, var, attr)







  # ATTENTION:
  # insert connected modules in array below
  # TODO: read from file if available
  #connected_modules = np.array([1,3,8])    # addresses e {1,..,30}
  connected_modules = np.array(range(1,21) )   # addresses e {1,..,30}
  modules = connected_modules - 1

  clickPoint = 0
  endButtonCoord=[0,0,0,0]

  scrW  = 1000    # pixel; width of whole screen (window)
  scrH  =  700    # pixel; height of whole screen (window)
  bottom=   30    # pixel; bottom range for legend and button
  nboxx =    6    # number of fields horizontally
  nboxy =    5    # number of fields vertically
  frame =   10    # pixel; external frame to border
  dist  =    5    # pixel; distance between fields
  nfldx =    4    # number of fields in a box, horizontally
  nfldy =    4    # number of fields in a box, vertically

  boxW = (scrW - 2*frame - (nboxx - 1)*dist ) / nboxx  # pixel
  boxH = (scrH-bottom - 2*frame - (nboxy - 1)*dist ) / nboxy  # pixel

  fldW = boxW / nfldx
  fldH = boxH / (nfldy+2)  # two for headlines

  color_winter = '#d0ffff'
  color_summer = '#ffe000'
  color_error  = '#8f4fcf'
  color_noEcho = 'grey'
  color_echo   = '#00ff00'
  color_ping   = 'orange'

  win = GraphWin("HZ-RR_Monitor", scrW, scrH )

  boxP0 = []
  boxP1 = []
  boxPt = []
  box = []
  boxTxt = []
  flRec  = []
  flVal  = []
  val=np.ones((30,4,4))        # values to be diaplayed
  val=val*(-99.9)              # stands for 'no vlaue'
  #for i in range(30):
  #  for j in range(4):
  #    for k in range(4):
  #      val[i][j][k] = k + j*4 + i*4*4 # TEST !!!
  val[0][0][0]= 55.5



  pval=np.zeros((30,4,4,2))    # text coordinates x/y for values

  def display_all():
    global endButtonCoord
    for spalte in range(nboxx) :
      for zeile in range(nboxy) :
        boxIdx = spalte * nboxy + zeile
        x0 = frame + spalte * (boxW + dist)
        y0 = frame + zeile  * (boxH + dist)
        x1 = x0 + boxW
        y1 = y0 + fldH
        boxP0.append( [x0,y0] )
        boxP1.append( [x1,y1] )
        p0 = Point(x0,y0)
        p1 = Point(x1,y1)
        #print("box von (%d,%d) bis (%d,%d), index=%d"%(x0,y0,x1,y1,boxIdx))
        box.append( Rectangle( p0, p1))
        box[boxIdx].setFill('white')
        box[boxIdx].draw(win)

        # frame around whole box
        y1 = y0 + boxH
        p1 = Point( x1, y1 )
        r = Rectangle( p0, p1 )
        r.setWidth(3)
        r.draw(win)

        # box header with module number
        xt = x0 + 2*fldW
        yt = y0 + 0.5*fldH
        pt = Point(xt,yt)
        boxPt.append([xt,yt])
        txt = Text( pt,"Adr.:%s       "%(str(boxIdx+1)) )
        txt.setSize(12)
        txt.setStyle('bold')
        txt.draw(win)
        boxTxt.append(txt)
        # column names
        xt = x0 + 2*fldW
        yt = y0 + 1.5*fldH
        pt = Point(xt,yt)
        txt = Text( pt,"T-Vor Rueck    Soll  V.auf")
        txt.setSize(10)
        #txt.setStyle('bold')
        txt.draw(win)
    #print (boxP0)

    inBox = []
    boxIdx = 0
    for b in box :
      # draw interior of a box
      for sp in range(nfldx) :
        for ze in range(nfldy) :
          #flIdx = boxIdx * nboxx * nboxy * sp * nfldy + ze
          flIdx = ze + sp*nfldy + boxIdx*nfldy*nfldx
          x0 = boxP0[boxIdx][0] + sp * fldW
          y0 = boxP0[boxIdx][1] + ze * fldH + 2*fldH
          x1 = x0 + fldW
          y1 = y0 + fldH
          p0 = Point(x0,y0)
          p1 = Point(x1,y1)
          #print("field von (%d,%d) bis (%d,%d), index=%d"%(x0,y0,x1,y1,boxIdx))
          r=Rectangle(p0,p1)
          r.setFill('grey')
          r.draw(win)
          flRec.append(r)
          # display values
          pvx = 0.5*(x0+x1)
          pvy = 0.5*(y0+y1)
          pval[boxIdx][ze][0] = np.array([pvx,pvy])
          pv  = Point(pvx,pvy)
          v=val[boxIdx][ze][sp]
          if v == -99.9 :
            txt = Text( pv, "     " )
          else:
            txt = Text( pv, "%5.1f"%(val[boxIdx][ze][sp]) )
          txt.setSize(10)
          txt.draw(win)
          flVal.append(txt)
          #print("flIdx=%d, sp=%f, ze=%f, box=%d, p=(%d,%d), val=%f"%(flIdx,sp,ze,boxIdx, pvx,pvy,val[boxIdx][ze-1][sp]))
      boxIdx += 1

    # draw end-button
    ep0x = frame
    ep0y = scrH-frame
    ep0 = Point( ep0x, ep0y )
    ep1x = frame + boxW
    ep1y = scrH-bottom
    endButtonCoord=[ep0x, ep0y, ep1x, ep1y]
    ep1 = Point( ep1x, ep1y )
    endButton = Rectangle( ep0, ep1 )
    endButton.setFill('red')
    endButton.draw(win)
    ept = Point(0.5*(ep0x+ep1x),0.5*(ep0y+ep1y) )
    endButtonText = Text( ept,"ENDE")
    endButtonText.setSize(12)
    endButtonText.setStyle('bold')
    endButtonText.draw(win)

    # draw legend
    lXstart = ep1x + dist
    dxPix = boxW / 2
    dyPix = bottom - frame

    legTxt=[ "Winter","Sommer","kein Sensor","Ping","Echo OK",
            "kein Echo","kein Ping","","","","",]
    legCol=[ color_winter, color_summer,color_error,color_ping,color_echo,
            color_noEcho,'white','grey','grey','grey','grey']
    lX0=np.array([])
    nLegBox = 10
    for ix in range(nLegBox):
      xnxt = np.array( [lXstart + ix*(dxPix+dist*0.5)] )
      lX0=np.concatenate([lX0,xnxt])
    lX1=lX0 + dxPix
    legBoxes = []
    legTexts = []
    for ix in range(nLegBox):
      p0 = Point(lX0[ix],ep0y)
      p1 = Point(lX1[ix],ep1y)
      legBoxes.append( Rectangle(p0,p1))
      legBoxes[ix].setFill( legCol[ix])
      legBoxes[ix].draw(win)
      pt = Point( lX0[ix]+dxPix*0.5, ep0y - dyPix*0.5)
      legTexts.append( Text( pt, legTxt[ix]))
      legTexts[ix].setSize(10)
      legTexts[ix].draw(win)


  def ping( modAdr ):
    # TODO: repeat up to 3 times; return number of tries
    maxCnt = 3
    repeat = 0
    ready  = 0
    while not ready and repeat < maxCnt :
      txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )   # send ping
      #print("*** sende: ",txCmd)
      rxCmd = us.txrx_command( txCmd )
      #print('*** empfange: %s'%( rxCmd ) )
      if "ACK" in rxCmd :
        ready = 1
      else:
        repeat += 1
    if repeat < maxCnt :
      return True, repeat
    else :
      return False, repeat


  summer      =   9
  vlm0        = -99.9
  rlm0        = -99.9
  vle0        = -99.9
  rle0        = -99.9
  rls0        = -99.9
  ven0        = -99.9
  err0        =   0
  fix0        = -99.9
  tmo0        = -99.9
  tan0        =   0
  modFwVersion = ""


  def get_parameter( modAdr, controller ) :
    # read parameter data
    global modFwVersion
    txCmd = mb.wrap_modbus( modAdr, 3, controller, "" )
    rxCmd = us.txrx_command( txCmd )
    pos = rxCmd.find("HZ-RR")  
    modFwVersion=rxCmd[pos+5:pos+9]


  def status( modAdr, controller ):
    # get status information from module modAdr and
    # controller; 0 = module status information
    global zDateSec,hkr,modnr,command,control,protVer,modTStamp,summer
    global vlm0,rlm0,vle0,rle0,rls0,ven0,err0,fix0,tmo0,tan0
    #global summer
    
    hs = ""

    fehler = 0
    txCmd = mb.wrap_modbus( modAdr, 2, controller, "" )
    # b':0102400F746\r\n'
    #print("---sende: ",txCmd)
    rxCmd = us.txrx_command( txCmd )
    # ':0002011a t28968.1  W VM999.9 RM999.9 VE  0.0 RE-99.9 RS  0.0 P050 E0002 FX0 M0 A0 '
    #print ("---empfange: ",rxCmd)
    #if "HZ-RR" in rxCmd :
    #  pass
    #else:
    #  fehler += 1
    if len(rxCmd) < 80 :
      fehler |= 0x0001
    else:
      # rr_parse needs date-time before the ":" -> '20170111_200810 0101 HK1 '
      # so a dummy date-time string is added in front
      l0 = time.strftime('%Y%m%d_%H%M%S ')
      l0+= "%02X%02X "%(modAdr,controller) + "HK%d "%(9) + rxCmd.strip()
      # l0 = 20000101_010101 0000 HK9 :00020A4a t602524.9  W VM999.9 RM999.9 VE 55.5 RE-99.9 RS  0.0 P050 E0000 FX0 M0 A0
      # from log-file (typical data line)
      # l0 = 20170131_134820 0303 HK1 :0002033a t592419.9  W VM999.9 RM999.9 VE 55.1 RE-99.9 RS  0.0 P050 E0000 FX0 M0 A0 
      #print("parse: ", l0 )
      p = parse.rr_parse(l0)
      if len(p) > 2 :         # no error
          try:
              (zDateSec,hkr,modnr,command,control,protVer,modTStamp,summer,
              vlm0,rlm0,vle0,rle0,rls0,ven0,err0,fix0,tmo0,tan0) = p
          except Exception as e:
              print(file,lineCnt,e)
              fehler |= 0x0002
              
    return fehler

  '''
    if not fehler :
      if ' W ' in rxCmd :
        summer = 0
      elif ' S ' in rxCmd :
        summer = 1
      else:
        summer = 99
        fehler |= 0x0002
    if not fehler:
      von = rxCmd.find(' VM') + 3
      bis = rxCmd.find(' RM')
      try:
        hs = rxCmd[von:bis]
        vlm0 = float( hs )
      except Exception as e:
        fehler |= 0x0004
        pass
    if not fehler:
      von = bis+3
      bis = rxCmd.find(' VE' )
      try:
        hs = rxCmd[von:bis]
        rlm0 = float( hs )
      except Exception as e:
        fehler |= 0x0008
        pass
    if not fehler:
      von = bis+3
      bis = rxCmd.find(' RE')
      try:
        hs=rxCmd[von:bis]
        vle0 = float( hs )
      except Exception as e:
        fehler |= 0x0010
        pass
    if not fehler:
      von = bis+3
      bis = rxCmd.find(' RS')
      try:
        hs=rxCmd[von:bis]
        rle0 = float( hs )
      except Exception as e:
        fehler |= 0x0020
        pass
    if not fehler:
      von = bis+3
      bis = rxCmd.find(' P')
      try:
        hs=rxCmd[von:bis]
        rls0 = float( hs )
      except Exception as e:
        fehler |= 0x0040
        pass
    if not fehler:
      von = bis+2
      bis = rxCmd.find(' E')
      try:
        ven0 = float(rxCmd[von:bis])
      except Exception as e:
        fehler |= 0x0080
        pass
    if not fehler:
      von = bis+2
      bis = rxCmd.find(' FX')
      try:
        err0 = int(rxCmd[von:bis])
      except Exception as e:
        fehler |= 0x0100
        pass
    if not fehler:
      von = bis+3
      bis = rxCmd.find(' M')
      try:
        fix0 = int(rxCmd[von:bis])
      except Exception as e:
        fehler |= 0x0200
        pass
    if not fehler:
      von = bis+2
      bis = rxCmd.find(' A')
      try:
        hs=rxCmd[von:bis]
        tmo0 = float(hs)
      except Exception as e:
        fehler |= 0x0400
        pass
    if not fehler:
      von = bis+2
      try:
        hs=rxCmd[von:]
        tan0 = int(hs)
      except Exception as e:
        fehler |= 0x0020
        pass
  '''




  def scan_all():
    global modFwVersion
    ende = False
    # plpl for modIdx in range(20):
    for modIdx1 in modules:
      modIdx = modIdx1 - 1
      if ende == True:
        break
      modAdr = modIdx+1
      box[modIdx].setFill('orange')                # mark box as active
      err = us.ser_reset_buffer()
      answer, repeat = ping(modAdr)
      if answer == True :
        # ping echo received
        box[modIdx].setFill(color_echo)   # light green
        # get version information; read from parameters of controller 1
        get_parameter( modAdr, 1 )         # read global modFwVersion


        boxTxt[modIdx].setText("Adr.:%s, V.%s"%(str(modIdx+1),modFwVersion))

        
        # fetch status information and display it
        for controller in [1,2,3,4] :
          conIdx = controller-1
          conAbsIdx = modIdx*4*4 + conIdx
          repeat = 0
          ende = False
          while repeat < 3 and not ende:
            e = status( modAdr, controller )
            if e > 0 :
              repeat += 1
            else:
              ende = True

          for feld in range(4):
            flIdx = conAbsIdx + feld*4
            if e > 0 :
              # no valid data received - set all grey and blank
              flRec[flIdx].setFill(color_noEcho)
              flVal[flIdx].setText('      ')
            else:
              # values received - set background color and show values
              if summer == 0:
                # winter mode
                flVal[conAbsIdx+0*4].setText("%5.1f"%(vle0) )
                flVal[conAbsIdx+1*4].setText("%5.1f"%(rle0) )
                flVal[conAbsIdx+2*4].setText("%5.1f"%(rls0) )
                flVal[conAbsIdx+3*4].setText("%3.0f%%"%(ven0) )
                if((err0!=0) or (vle0==0.0) or (rlm0==999.9)) :
                  flRec[conAbsIdx+0*4].setFill(color_error)
                  flRec[conAbsIdx+1*4].setFill(color_error)
                  flRec[conAbsIdx+2*4].setFill(color_error)
                  flRec[conAbsIdx+3*4].setFill(color_error)
                else:
                  flRec[conAbsIdx+0*4].setFill(color_winter)
                  flRec[conAbsIdx+1*4].setFill(color_winter)
                  flRec[conAbsIdx+2*4].setFill(color_winter)
                  flRec[conAbsIdx+3*4].setFill(color_winter)
              elif summer == 1:
                # summer mode
                flVal[conAbsIdx+0*4].setText("%5.1f"%(vle0) )
                flVal[conAbsIdx+1*4].setText("%5.1f"%(0.0) )
                flVal[conAbsIdx+2*4].setText("%5.1f"%(0.0) )
                flVal[conAbsIdx+3*4].setText("%3.0f%%"%(ven0) )
                if((err0!=0) or (vle0==0.0) or (rlm0==999.9)) :
                  flRec[conAbsIdx+0*4].setFill(color_error)
                  flRec[conAbsIdx+1*4].setFill(color_error)
                  flRec[conAbsIdx+2*4].setFill(color_error)
                  flRec[conAbsIdx+3*4].setFill(color_error)
                else:
                  flRec[conAbsIdx+0*4].setFill(color_summer)
                  flRec[conAbsIdx+1*4].setFill(color_summer)
                  flRec[conAbsIdx+2*4].setFill(color_summer)
                  flRec[conAbsIdx+3*4].setFill(color_summer)

      else:
        # no echo
        box[modIdx].setFill(color_noEcho)
        boxTxt[modIdx].setText("Adr.:%s         "%(str(modIdx+1)))
        for controller in [1,2,3,4] :
          conIdx = controller-1
          conAbsIdx = modIdx*4*4 + conIdx
          for feld in range(4):
            flIdx = conAbsIdx + feld*4
            # no valid data received - set all grey and blank
            flRec[flIdx].setFill(color_noEcho)
            flVal[flIdx].setText('      ')

      ende = 0
      global cp
      cp = win.checkMouse()    # clickPoint
      key= win.checkKey()      # key pressed

      if cp != None :
        print("clickPoint=",cp)
        cpx = cp.getX()
        cpy = cp.getY()
        epc=endButtonCoord
        print("epc=",epc)
        if( (epc[0] < cpx < epc[2]) and epc[3] < cpy < epc[1] ) :
          ende = True
      if key != "" :
        # Taste beendet den Screen
        ende = True
    return ende


  global heizkreis 
  #global modules 
  global modTVor 
  global modSendTvor 
  global dtLog 
  global filtFakt

  us.serial_connect()
  us.ser_open()

  # get Heizkreis setup data
  h = hkr_cfg.get_heizkreis_config()
  if len(h) > 5:
      (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
  else:
      # some default values
      heizkreis   = 0
      modules     = []
      modTVor     = 0
      modSendTvor = []
      dtLog       = 180    # time interval to log a data set
      filtFakt    = 0.1

  try:
    display_all()
  except Exception as e:
    print("Fehler %s"%(e))
    #win.getMouse() # Pause to view result
    #win.close()
  else:
    pass
    # TODO remove
    #win.getMouse() # Pause to view result
    #win.close()    # Close window when done



  ende = 0
  while not ende:
    ende = scan_all()


  win.close()
  us.ser.close()



  # hzrr_inst.py

  from graphics import *
  import usb_ser as us
  import modbus  as mb


  clickPoint = 0

  def display_all():





      bw = 80
      bh= 80
      frame    =  20
      dist     =  10
      txoff    =  50
      tyoff    =  50
      ww       = 2*frame + 5*dist + 6*bw
      wh       = 2*frame + 5*dist + 6*bh
      rad      = 10

      win = GraphWin("HZ-RR_Install", ww, wh)

      # draw number field 6x5 with numbers from 1...30
      re = []
      txt= []
      ci = []
      for i in range(6) :
        for j in range(5) :
          idx = i*5 + j
          p1x = frame + i*(bw+dist)
          p1y = frame + j*(bh+dist)
          p1 = Point( p1x, p1y )
          p2x = frame + bw + i*(bw+dist)
          p2y = frame + bh + j*(bh+dist)
          p2 = Point( p2x, p2y )
          #print(idx,p1,p2)
          re.append(  Rectangle( p1, p2 ) )
          re[idx].setFill('grey')
          re[idx].draw(win)
          pt = Point(0.5*(p1x+p2x)+rad,0.5*(p1y+p2y)+rad)
          txt.append( Text(pt,str(idx+1)))
          txt[idx].setSize(22)
          txt[idx].setStyle('bold')
          txt[idx].draw(win)
          pc = Point( p1.getX()+20, p1.getY() + 20)
          ci.append( Circle( pc, rad ))
          ci[idx].setFill('grey2')
          ci[idx].draw(win)

      # draw end-button
      ep0x = frame
      ep0y = 5*(bh + dist) + frame
      ep0 = Point( ep0x, ep0y )
      ep1x = frame + bw
      ep1y = frame + 5*dist + 6*bh
      ep1 = Point( ep1x, ep1y )
      endButton = Rectangle( ep0, ep1 )
      endButton.setFill('red')
      endButton.draw(win)
      ept = Point(0.5*(ep0x+ep1x),0.5*(ep0y+ep1y) )
      endButtonText = Text( ept,"ENDE")
      #endButtonText.setSize(22)
      endButtonText.setStyle('bold')
      endButtonText.draw(win)

      # draw legend
      mx = ep1x + dist + rad
      m1 =  Point(mx, ep0y + rad)
      c1 = Circle( m1, rad )
      c1.setFill('cyan')
      c1.draw(win)
      m2 = Point(mx, (ep0y+ep1y)/2 )
      c2 = Circle( m2, rad )
      c2.setFill('grey2')
      c2.draw(win)
      m3 = Point(mx, ep1y - rad)
      c3 = Circle( m3, rad )
      c3.setFill('red')
      c3.draw(win)
      tx = mx + 2*rad + bw/2
      t1s = Point(tx, ep0y + rad)
      t1  = Text( t1s,"long xfer  ok" )
      t1.draw(win)
      t2s = Point(tx, (ep0y+ep1y)/2 )
      t2  = Text( t2s,"not available" )
      t2.draw(win)
      t3s = Point( tx, ep1y - rad)
      t3  = Text( t3s,"long xfer fail" )
      t3.draw(win)

      p1x = frame + 3*(bw+dist)
      p1y = frame + 5*(bh+dist)
      p1 = Point( p1x, p1y )
      p2x = frame + bw + 3*(bw+dist)
      p2y = frame + bh + 5*(bh+dist)
      p2 = Point( p2x, p2y )
      ra = Rectangle( p1, p2 )
      ra.setFill('grey')
      ra.draw(win)
      tap = Point( 0.5*(p1x+p2x),0.5*(p1y+p2y))
      ta = Text( tap,'no echo')
      ta.draw(win)

      p1x = frame + 4*(bw+dist)
      p1y = frame + 5*(bh+dist)
      p1 = Point( p1x, p1y )
      p2x = frame + bw + 4*(bw+dist)
      p2y = frame + bh + 5*(bh+dist)
      p2 = Point( p2x, p2y )
      rb = Rectangle( p1, p2 )
      rb.setFill('orange')
      rb.draw(win)
      tbp = Point( 0.5*(p1x+p2x),0.5*(p1y+p2y))
      tb = Text( tbp,'ping...')
      tb.draw(win)

      p1x = frame + 5*(bw+dist)
      p1y = frame + 5*(bh+dist)
      p1 = Point( p1x, p1y )
      p2x = frame + bw + 5*(bw+dist)
      p2y = frame + bh + 5*(bh+dist)
      p2 = Point( p2x, p2y )
      rc = Rectangle( p1, p2 )
      rc.setFill('green2')
      rc.draw(win)
      tcp = Point( 0.5*(p1x+p2x),0.5*(p1y+p2y))
      tc = Text( tcp,'echo')
      tc.draw(win)



      # scan all modules and change color if active
      modAdr = 1
      ende = False
      while( not ende) :
        modIdx = modAdr-1
        re[modIdx].setFill('orange')
        err = us.ser_reset_buffer()
        txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )
        #print("*** sende: ",txCmd)
        rxCmd = us.txrx_command( txCmd )
        #print('*** empfange: %s'%( rxCmd ) )
        try:
          rxTab = rxCmd.split()
          if rxTab[2] == 'ACK' :
            # fetch a very long message of all controllers
            fehler = 0
            for controller in [1,2,3,4] :
              txCmd = mb.wrap_modbus( modAdr, 3, controller, "" )
              # ??? sende:  b':0103000F440\r\n'
              #print("---sende: ",txCmd)
              rxCmd = us.txrx_command( txCmd )
              #print ("---empfange: ",rxCmd)
              if "HZ-RR" in rxCmd :
                pass
              else:
                fehler += 1
            if fehler == 0 :
              ci[modIdx].setFill('cyan')
            else:
              ci[modIdx].setFill('red')

            re[modIdx].setFill('green2')


          else:
            re[modIdx].setFill('grey')
            ci[modIdx].setFill('grey2')

        except:
          re[modIdx].setFill('grey')
          ci[modIdx].setFill('grey2')
          pass


        modAdr += 1
        if modAdr > 30 :
          modAdr = 1

        global cp
        cp = win.checkMouse()    # clickPoint
        key= win.checkKey()      # key pressed
        if cp != None :
          print("clickPoint=",cp)
          cpx = cp.getX()
          cpy = cp.getY()
          print(ep0x,ep1x,ep0y,ep1y)
          if( ep0x < cpx < ep1x and ep0y < cpy < ep1y ) :
            ende = True
        if key != "" :
          # Taste beendet den Screen
          ende = True

      # end of loop
      win.close()    # Close window when done

  us.serial_connect()
  us.ser_open()


  # hzrr_dialog3.py

  import sys
  import time
  import numpy       as np
  import usb_ser     as us
  import modbus      as mb
  import param_11c   as par_c
  import param_11d   as par_d
  import heizkreis_config as hkr_cfg

  #import RPi.GPIO   as GPIO


  # *** global variables
  par = par_d
  err = 0
  err |= us.serial_connect()
  err |= us.ser_open()
  print("Fehler=%d"%(err))

  # *** voreingestellte Werte modAdr = 1
  reg    = 0
  intSec = 10           # intervall zum Abruf der Statusanzeige
  modAdr = 1
  wdh    = 300/intSec   # wiederhole 5 Minuten lang die anzeige
  vers = ['HZ-RR11c', 'HZ-RR11d']
  versTxt= ['(vom 12.12.2016)', '(vom 19.12.2016)']
  modFwVersion = vers[1]


  def read_heizkreis_config() :
      global heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt
      
      h = hkr_cfg.get_heizkreis_config()
      if len(h) > 5:
          (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
      else:
          # some default values
          heizkreis   = 0
          modules     = []
          modTVor     = 0
          modSendTvor = []
          dtLog       = 180    # time interval to log a data set
          filtFakt    = 0.1



  def menu(x):
    # x=0: zeige Menü für Auswahl
    print('Modul Adresse = %d; Firmware Version=%s'%(modAdr,modFwVersion))
    print(' 0   Ende')
    print(' A   Modul Adresse                   V   Modul Firmware Version')
    print(' 1   Teste Modul-Adresse (ping)')
    print(' 2   Staus: anzeigen;                3   alle %dsec anzeigen'%intSec)
    print(' 4   Parameter lesen                 5   alle Param.-> Werkseinst.')
    print(' 6   Ventil dauerhaft auf            7   Ventil dauerhaft zu')
    print(' 8   Ventil regeln (Ende dauerhaft)')
    print(' 9   Regler inaktiv setzen          10   Regler aktiv setzen')
    print('11   schneller Ablauf fuer Test     12   normale Geschwindigkeit')
    print('20   sende Vorlauftemperatur von Zentrale')
    print('21   neue Parameter senden          31   alle Parameter ins EEPROM')
    print('39   neue Parameter an alle Module senden und ins EEPROM speichern')
    print('40   Parameter aller Module abholen und in Datei speichern')
    print(60*"-")
    print('Vorsicht: 49   Reset ueber Watchdog')
    print('Vorsicht: 50   jede Minute status abspeichern'  )
    print('')
    a = input('Wahl? ')
    if a=='a' or a=='A' :
      return 99
    if a=='v' or a=='V' :
      return 98
    return int(a)


  def select_controller():
    fertig = False
    while not fertig :
      a = input( 'module=0; regler=1,2,3,4; alle=5; Ende=9; wahl? ')
      try:
        reg = int(a)
        if reg == 5 :
          return[1,2,3,4]
        elif reg <= 4 :
          return [reg]
        elif reg == 9 :
          return []
      except:
        pass


  def perform_command( controllers, command ) :
    for reg in controllers:
      cmd = mb.wrap_modbus( modAdr, command, reg, "" )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )


  def select_version() :
    global par
    global vers
    global versTxt
    i=0
    for ver in range( len(vers) ) :
      print('%d   %s  %s'%(i+1,vers[i],versTxt[i]))
      i += 1
    wahl=0
    while not wahl :
      a = input("Wahl ?")
      try:
        wahl = int(a)
      except:
        wahl = 0
        pass
      if wahl < 0         :  wahl = 0
      if wahl > len(vers) :  wahl = 0 
    print('wahl=%d, version %s'%(wahl, vers[wahl-1]))
    if wahl == 1:
      par = par_c
    if wahl == 2:
      par = par_d
    return vers[wahl-1]




  def doit( wahl ):
    global modAdr
    global index
    global par
    global modFwVersion

    if wahl == 1 :  # Teste Modul-Adresse (ping)
      err = us.ser_reset_buffer()
      txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )
      print(txCmd)
      rxCmd = us.txrx_command( txCmd )
      print('empfange: %s'%( rxCmd ) )

    if wahl == 2 :  # Staus: anzeigen;
      err = us.ser_reset_buffer()
      controllers = select_controller()
      perform_command( controllers, 0x02 )

    if wahl == 3 :  # alle %dsec anzeigen
      w = wdh
      while( w ) :
        for reg in [1,2,3,4]:
          txCmd = mb.wrap_modbus( modAdr, 2, reg, "" )
          print('sende:  %s'%(txCmd))
          rxCmd = us.txrx_command( txCmd )
          print('empfange: %s'%( rxCmd ) )
        time.sleep(intSec)
        w -= 1
        print()

    if wahl == 4 :  # Parameter lesen 
      tbl=[]
      for regler in [0,1,2,3,4]:
        txCmd = mb.wrap_modbus( modAdr, 3, regler, "" )
        print('sende:  %s'%(txCmd))
        rxCmd = us.txrx_command( txCmd )
        cmdList = rxCmd
        print(rxCmd)
        tbl1 = cmdList.split()
        tbl.append( tbl1 )
        #print('empfange: %s'%( rxCmd ) )
      # sort as a table:
      spalten = len(tbl)
      zeilen  = len(tbl[0])
      print(zeilen,spalten)
      for x in range(zeilen):
        zs=[]
        for y in range(spalten):
          zs.append(tbl[y][x])

        print("%10s  %5s %5s %5s %5s"%(zs[0],zs[1],zs[2],zs[3],zs[4]))

    if wahl == 5 :  # alle Parameter auf Werkseinstellung setzen
      perform_command( [0], 0x30 )

    if wahl == 6 :  # Ventil dauerhaft auf
      controllers = select_controller()
      perform_command( controllers, 0x31 )

    if wahl == 7 :  # Ventil dauerhaft zu
      controllers = select_controller()
      perform_command( controllers, 0x32 )

    if wahl == 8 :  # Ventil regeln (Ende dauerhaft)
      controllers = select_controller()
      perform_command( controllers, 0x33 )

    if wahl == 9 :  # Regler inaktiv setzen 
      controllers = select_controller()
      perform_command( controllers, 0x34 )

    if wahl == 10 :  # controller active
      controllers = select_controller()
      perform_command( controllers, 0x35 )

    if wahl == 11 :  # fast
      controllers = select_controller()
      perform_command( controllers, 0x36 )


    if wahl == 12 :  # end fast -> normal speed
      controllers = select_controller()
      perform_command( controllers, 0x37 )

    if wahl == 20 :  # sende Vorlauftemperatur von Zentrale
      vtzstr = input("Zentrale Vorlauftemperatur:")
      cmd = mb.wrap_modbus( modAdr, 0x20, 0, ' '+vtzstr+' ' )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )
      

    if wahl == 21 :  # parameter senden
      controllers = select_controller()
      for reg in controllers:
        cmd=modFwVersion
        for i in par.index:
          cmd += ' ' + par.valFst[i]%( par.valDef[i] )
        cmd += ' '
        txCmd = mb.wrap_modbus( modAdr, 0x21, reg, cmd )
        print( 'sende: %dbyte, cmd=%s'%(len(txCmd), txCmd ))
        rxCmd = us.txrx_command( txCmd )
        print('empfange: %s'%( rxCmd.strip() ) )
        dtEeprom = 0.2
        print('warte %d sec bis Befehl ausgeführt ist ...'%(dtEeprom))
        print("-"*40)
        time.sleep(dtEeprom)

    if wahl == 31 :  # parameter ins eeprom speichern
      reg=0
      cmd = mb.wrap_modbus( modAdr, 0x39, reg, "" )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )

    if wahl == 39 :  # parameter aller module setzen und ins EEPROM speichern
      print()
      print("-"*60)
      print('ACHTUNG: GROSSE AENDERUNG - LOG-Programm vorher beenden !!!')
      print("-"*60)
      antwort = input("wirklich durchführen? J/n :")
      if antwort == "J":
        fehler = 0
        fehlermod = []
        
        for modAdr in modules :
          for reg in [1,2,3,4] :

            # build command
            cmd=modFwVersion
            for i in par.index:
              cmd += ' ' + par.valFst[i]%( par.valDef[i] )
            cmd += ' '
            txCmd = mb.wrap_modbus( modAdr, 0x21, reg, cmd )
            #print( 'sende: %dbyte, cmd=%s'%(len(txCmd), txCmd ))
            rxCmd = us.txrx_command( txCmd )
            #print('empfange: %s'%( rxCmd.strip() ) )
            print("modul %d; Regler %d; "%(modAdr,reg), end="")
            if "ACK" in rxCmd :
              print("ACK")
            else:
              print("---")
              fehler += 1
              fehlermod.append([modAdr,reg])
              #print('warte %d sec bis Befehl ausgeführt ist ...'%(dtEeprom))
            #print("-"*40)

          # fixiere im EEPROM
          dtEeprom = 1.5
          time.sleep(dtEeprom)
          reg=0
          cmd = mb.wrap_modbus( modAdr, 0x39, reg, "" )
          # print('sende:  %s'%(cmd))
          rxCmd = us.txrx_command( cmd )
          # print('empfange: %s'%( rxCmd ) )
          if "ACK" in rxCmd :
            print("  EEPROM ACK")
          else:
            print("  EEPROM --- Schreibfehler")
            fehler += 1
            fehlermod.append([modAdr, reg])
        if fehler == 0:
          print("Parameter aller Module erfolgreich übertragen")
        else:
          print("%d Fehler; Fehlerliste:"%(fehler))
          for f in fehlermod:
            print("    Modul:%d;  Regler %d;"%(f[0],f[1]))

    if wahl == 40 :  # parameter aller module abholen und abspeichern
        pass
        dateTime = time.strftime( "%Y%m%d_%H%M%S", time.localtime())
        datName = "log/par_hk%d_%s.dat"%(heizkreis, dateTime)
        print("Schreibe Datei: %s"%(datName))
        fout = open(datName,"w")
        
        print("Modul:",end="")
        for moduleAdr in modules:
            print(moduleAdr," ", end="")
            for regler in [0,1,2,3,4]:
                txCmd = mb.wrap_modbus( moduleAdr, 3, regler, "" )
                #print('sende:  %s'%(txCmd))
                rxCmd = us.txrx_command( txCmd )
                hs = "Mod%d Reg%d %s\r\n"%( moduleAdr, regler, rxCmd )
                fout.write(hs)
        print(" fertig")
        fout.close()

    if wahl == 49:  # reset ueber Watchdog auslösen
      print('Modul Adresse ist %d'%(modAdr))
      cmd = mb.wrap_modbus( modAdr, 0x3A, 0, "" )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )


    if wahl == 50:  # jede Minute status einlesen und speichern
      print('Modul Adresse ist %d'%(modAdr))

      dateiName = 'log/log_HZ-RR012_'+time.strftime('%Y-%M-%d_%H:%M:%S.dat')
      odat = open( dateiName, 'w' )
      while True :
        for regler in [1,2,3,4]:
          txCmd = mb.wrap_modbus( modAdr, 2, regler, "" )
          #print('sende:  %s'%(cmd))
          rxCmd = us.txrx_command( txCmd )
          logstr = time.strftime('%Y-%M-%d_%H:%M:%S ') + rxCmd
          print('store: %s'%( logstr ) )
          odat.write( logstr + '\r\n' )
        odat.flush()
        time.sleep(60.0)
        print()

    if wahl == 98 :
      modFwVersion = select_version()

    if wahl == 99 :
      a=0
      while a<1 or a >31 :
        a = int( input( 'Modul Adresse 1..30; wahl? ') )
      modAdr = a
    print()


  wahl = 1
  while wahl > 0 :
      read_heizkreis_config()
      wahl = menu(0)
      print( "----------------wahl=%d-------------"%(wahl) )
      doit(wahl)

    
  # hzrr dialog2.py

  import sys
  import time
  import numpy       as np
  import usb_ser     as us
  import modbus      as mb
  import param_11c   as par_c
  import param_11d   as par_d
  import heizkreis_config as hkr_cfg

  #import RPi.GPIO   as GPIO


  # *** global variables
  par = par_d
  err = 0
  err |= us.serial_connect()
  err |= us.ser_open()
  print("Fehler=%d"%(err))

  # *** voreingestellte Werte modAdr = 1
  reg    = 0
  intSec = 10           # intervall zum Abruf der Statusanzeige
  modAdr = 1
  wdh    = 300/intSec   # wiederhole 5 Minuten lang die anzeige
  vers = ['HZ-RR11c', 'HZ-RR11d']
  versTxt= ['(vom 12.12.2016)', '(vom 19.12.2016)']
  modFwVersion = vers[1]


  def read_heizkreis_config() :
      global heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt
      
      h = hkr_cfg.get_heizkreis_config()
      if len(h) > 5:
          (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
      else:
          # some default values
          heizkreis   = 0
          modules     = []
          modTVor     = 0
          modSendTvor = []
          dtLog       = 180    # time interval to log a data set
          filtFakt    = 0.1



  def menu(x):
    # x=0: zeige Menü für Auswahl
    print('Modul Adresse = %d; Firmware Version=%s'%(modAdr,modFwVersion))
    print(' 0   Ende')
    print(' A   Modul Adresse                   V   Modul Firmware Version')
    print(' 1   Teste Modul-Adresse (ping)')
    print(' 2   Staus: anzeigen;                3   alle %dsec anzeigen'%intSec)
    print(' 4   Parameter lesen                 5   alle Param.-> Werkseinst.')
    print(' 6   Ventil dauerhaft auf            7   Ventil dauerhaft zu')
    print(' 8   Ventil regeln (Ende dauerhaft)')
    print(' 9   Regler inaktiv setzen          10   Regler aktiv setzen')
    print('11   schneller Ablauf fuer Test     12   normale Geschwindigkeit')
    print('20   sende Vorlauftemperatur von Zentrale')
    print('21   neue Parameter senden          31   alle Parameter ins EEPROM')
    print('39   neue Parameter an alle Module senden und ins EEPROM speichern')
    print('40   Parameter aller Module abholen und in Datei speichern')
    print(60*"-")
    print('Vorsicht: 49   Reset ueber Watchdog')
    print('Vorsicht: 50   jede Minute status abspeichern'  )
    print('')
    a = input('Wahl? ')
    if a=='a' or a=='A' :
      return 99
    if a=='v' or a=='V' :
      return 98
    return int(a)


  def select_controller():
    fertig = False
    while not fertig :
      a = input( 'module=0; regler=1,2,3,4; alle=5; Ende=9; wahl? ')
      try:
        reg = int(a)
        if reg == 5 :
          return[1,2,3,4]
        elif reg <= 4 :
          return [reg]
        elif reg == 9 :
          return []
      except:
        pass


  def perform_command( controllers, command ) :
    for reg in controllers:
      cmd = mb.wrap_modbus( modAdr, command, reg, "" )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )


  def select_version() :
    global par
    global vers
    global versTxt
    i=0
    for ver in range( len(vers) ) :
      print('%d   %s  %s'%(i+1,vers[i],versTxt[i]))
      i += 1
    wahl=0
    while not wahl :
      a = input("Wahl ?")
      try:
        wahl = int(a)
      except:
        wahl = 0
        pass
      if wahl < 0         :  wahl = 0
      if wahl > len(vers) :  wahl = 0 
    print('wahl=%d, version %s'%(wahl, vers[wahl-1]))
    if wahl == 1:
      par = par_c
    if wahl == 2:
      par = par_d
    return vers[wahl-1]




  def doit( wahl ):
    global modAdr
    global index
    global par
    global modFwVersion

    if wahl == 1 :  # Teste Modul-Adresse (ping)
      err = us.ser_reset_buffer()
      txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )
      print(txCmd)
      rxCmd = us.txrx_command( txCmd )
      print('empfange: %s'%( rxCmd ) )

    if wahl == 2 :  # Staus: anzeigen;
      err = us.ser_reset_buffer()
      controllers = select_controller()
      perform_command( controllers, 0x02 )

    if wahl == 3 :  # alle %dsec anzeigen
      w = wdh
      while( w ) :
        for reg in [1,2,3,4]:
          txCmd = mb.wrap_modbus( modAdr, 2, reg, "" )
          print('sende:  %s'%(txCmd))
          rxCmd = us.txrx_command( txCmd )
          print('empfange: %s'%( rxCmd ) )
        time.sleep(intSec)
        w -= 1
        print()

    if wahl == 4 :  # Parameter lesen 
      tbl=[]
      for regler in [0,1,2,3,4]:
        txCmd = mb.wrap_modbus( modAdr, 3, regler, "" )
        print('sende:  %s'%(txCmd))
        rxCmd = us.txrx_command( txCmd )
        cmdList = rxCmd
        print(rxCmd)
        tbl1 = cmdList.split()
        tbl.append( tbl1 )
        #print('empfange: %s'%( rxCmd ) )
      # sort as a table:
      spalten = len(tbl)
      zeilen  = len(tbl[0])
      print(zeilen,spalten)
      for x in range(zeilen):
        zs=[]
        for y in range(spalten):
          zs.append(tbl[y][x])

        print("%10s  %5s %5s %5s %5s"%(zs[0],zs[1],zs[2],zs[3],zs[4]))

    if wahl == 5 :  # alle Parameter auf Werkseinstellung setzen
      perform_command( [0], 0x30 )

    if wahl == 6 :  # Ventil dauerhaft auf
      controllers = select_controller()
      perform_command( controllers, 0x31 )

    if wahl == 7 :  # Ventil dauerhaft zu
      controllers = select_controller()
      perform_command( controllers, 0x32 )

    if wahl == 8 :  # Ventil regeln (Ende dauerhaft)
      controllers = select_controller()
      perform_command( controllers, 0x33 )

    if wahl == 9 :  # Regler inaktiv setzen 
      controllers = select_controller()
      perform_command( controllers, 0x34 )

    if wahl == 10 :  # controller active
      controllers = select_controller()
      perform_command( controllers, 0x35 )

    if wahl == 11 :  # fast
      controllers = select_controller()
      perform_command( controllers, 0x36 )


    if wahl == 12 :  # end fast -> normal speed
      controllers = select_controller()
      perform_command( controllers, 0x37 )

    if wahl == 20 :  # sende Vorlauftemperatur von Zentrale
      vtzstr = input("Zentrale Vorlauftemperatur:")
      cmd = mb.wrap_modbus( modAdr, 0x20, 0, ' '+vtzstr+' ' )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )
      

    if wahl == 21 :  # parameter senden
      controllers = select_controller()
      for reg in controllers:
        cmd=modFwVersion
        for i in par.index:
          cmd += ' ' + par.valFst[i]%( par.valDef[i] )
        cmd += ' '
        txCmd = mb.wrap_modbus( modAdr, 0x21, reg, cmd )
        print( 'sende: %dbyte, cmd=%s'%(len(txCmd), txCmd ))
        rxCmd = us.txrx_command( txCmd )
        print('empfange: %s'%( rxCmd.strip() ) )
        dtEeprom = 0.2
        print('warte %d sec bis Befehl ausgeführt ist ...'%(dtEeprom))
        print("-"*40)
        time.sleep(dtEeprom)

    if wahl == 31 :  # parameter ins eeprom speichern
      reg=0
      cmd = mb.wrap_modbus( modAdr, 0x39, reg, "" )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )

    if wahl == 39 :  # parameter aller module setzen und ins EEPROM speichern
      print()
      print("-"*60)
      print('ACHTUNG: GROSSE AENDERUNG - LOG-Programm vorher beenden !!!')
      print("-"*60)
      antwort = input("wirklich durchführen? J/n :")
      if antwort == "J":
        for modAdr in modules :
          for reg in [1,2,3,4] :

            # build command
            cmd=modFwVersion
            for i in par.index:
              cmd += ' ' + par.valFst[i]%( par.valDef[i] )
            cmd += ' '
            txCmd = mb.wrap_modbus( modAdr, 0x21, reg, cmd )
            #print( 'sende: %dbyte, cmd=%s'%(len(txCmd), txCmd ))
            rxCmd = us.txrx_command( txCmd )
            print('empfange: %s'%( rxCmd.strip() ) )
            print("modul %d; Regler %d; "%(modAdr,reg), end="")
            if "ACK" in rxCmd :
              print("ACK")
            else:
              print("---")
            #print('warte %d sec bis Befehl ausgeführt ist ...'%(dtEeprom))
            #print("-"*40)

          # fixiere im EEPROM
          dtEeprom = 1.5
          time.sleep(dtEeprom)
          reg=0
          cmd = mb.wrap_modbus( modAdr, 0x39, reg, "" )
          # print('sende:  %s'%(cmd))
          rxCmd = us.txrx_command( cmd )
          # print('empfange: %s'%( rxCmd ) )
          if "ACK" in rxCmd :
            print("  EEPROM ACK")
          else:
            print("  EEPROM --- Schreibfehler")

    if wahl == 40 :  # parameter aller module abholen und abspeichern
        pass
        dateTime = time.strftime( "%Y%m%d_%H%M%S", time.localtime())
        datName = "log/par_hk%d_%s.dat"%(heizkreis, dateTime)
        print("Schreibe Datei: %s"%(datName))
        fout = open(datName,"w")
        
        print("Modul:",end="")
        for moduleAdr in modules:
            print(moduleAdr," ", end="")
            for regler in [0,1,2,3,4]:
                txCmd = mb.wrap_modbus( moduleAdr, 3, regler, "" )
                #print('sende:  %s'%(txCmd))
                rxCmd = us.txrx_command( txCmd )
                hs = "Mod%d Reg%d %s\r\n"%( moduleAdr, regler, rxCmd )
                fout.write(hs)
        print(" fertig")
        fout.close()

    if wahl == 49:  # reset ueber Watchdog auslösen
      print('Modul Adresse ist %d'%(modAdr))
      cmd = mb.wrap_modbus( modAdr, 0x3A, 0, "" )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )


    if wahl == 50:  # jede Minute status einlesen und speichern
      print('Modul Adresse ist %d'%(modAdr))

      dateiName = 'log/log_HZ-RR012_'+time.strftime('%Y-%M-%d_%H:%M:%S.dat')
      odat = open( dateiName, 'w' )
      while True :
        for regler in [1,2,3,4]:
          txCmd = mb.wrap_modbus( modAdr, 2, regler, "" )
          #print('sende:  %s'%(cmd))
          rxCmd = us.txrx_command( txCmd )
          logstr = time.strftime('%Y-%M-%d_%H:%M:%S ') + rxCmd
          print('store: %s'%( logstr ) )
          odat.write( logstr + '\r\n' )
        odat.flush()
        time.sleep(60.0)
        print()

    if wahl == 98 :
      modFwVersion = select_version()

    if wahl == 99 :
      a=0
      while a<1 or a >31 :
        a = int( input( 'Modul Adresse 1..30; wahl? ') )
      modAdr = a
    print()


  wahl = 1
  while wahl > 0 :
      read_heizkreis_config()
      wahl = menu(0)
      print( "----------------wahl=%d-------------"%(wahl) )
      doit(wahl)


  # hzrr_dialog.py

  import sys
  import time
  import numpy       as np
  import usb_ser     as us
  import modbus      as mb
  import param_11c   as par_c
  import param_11d   as par_d
  import heizkreis_config as hkr_cfg

  #import RPi.GPIO   as GPIO


  # *** global variables
  par = par_d
  err = 0
  err |= us.serial_connect()
  err |= us.ser_open()
  print("Fehler=%d"%(err))

  # *** voreingestellte Werte modAdr = 1
  reg    = 0
  intSec = 10           # intervall zum Abruf der Statusanzeige
  modAdr = 1
  wdh    = 300/intSec   # wiederhole 5 Minuten lang die anzeige
  vers = ['HZ-RR11c', 'HZ-RR11d']
  versTxt= ['(vom 12.12.2016)', '(vom 19.12.2016)']
  modFwVersion = vers[1]


  def read_heizkreis_config() :
      global heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt
      
      h = hkr_cfg.get_heizkreis_config()
      if len(h) > 5:
          (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
      else:
          # some default values
          heizkreis   = 0
          modules     = []
          modTVor     = 0
          modSendTvor = []
          dtLog       = 180    # time interval to log a data set
          filtFakt    = 0.1



  def menu(x):
    # x=0: zeige Menü für Auswahl
    print('Modul Adresse = %d; Firmware Version=%s'%(modAdr,modFwVersion))
    print(' 0   Ende')
    print(' A   Modul Adresse                   V   Modul Firmware Version')
    print(' 1   Teste Modul-Adresse (ping)')
    print(' 2   Staus: anzeigen;                3   alle %dsec anzeigen'%intSec)
    print(' 4   Parameter lesen                 5   alle Param.-> Werkseinst.')
    print(' 6   Ventil dauerhaft auf            7   Ventil dauerhaft zu')
    print(' 8   Ventil regeln (Ende dauerhaft)')
    print(' 9   Regler inaktiv setzen          10   Regler aktiv setzen')
    print('11   schneller Ablauf fuer Test     12   normale Geschwindigkeit')
    print('20   sende Vorlauftemperatur von Zentrale')
    print('21   neue Parameter senden          31   alle Parameter ins EEPROM')
    print('40   Parameter aller Module abholen und in Datei speichern')
    print(60*"-")
    print('Vorsicht: 49   Reset ueber Watchdog')
    print('Vorsicht: 50   jede Minute status abspeichern'  )
    print('')
    a = input('Wahl? ')
    if a=='a' or a=='A' :
      return 99
    if a=='v' or a=='V' :
      return 98
    return int(a)


  def select_controller():
    fertig = False
    while not fertig :
      a = input( 'module=0; regler=1,2,3,4; alle=5; Ende=9; wahl? ')
      try:
        reg = int(a)
        if reg == 5 :
          return[1,2,3,4]
        elif reg <= 4 :
          return [reg]
        elif reg == 9 :
          return []
      except:
        pass


  def perform_command( controllers, command ) :
    for reg in controllers:
      cmd = mb.wrap_modbus( modAdr, command, reg, "" )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )


  def select_version() :
    global par
    global vers
    global versTxt
    i=0
    for ver in range( len(vers) ) :
      print('%d   %s  %s'%(i+1,vers[i],versTxt[i]))
      i += 1
    wahl=0
    while not wahl :
      a = input("Wahl ?")
      try:
        wahl = int(a)
      except:
        wahl = 0
        pass
      if wahl < 0         :  wahl = 0
      if wahl > len(vers) :  wahl = 0 
    print('wahl=%d, version %s'%(wahl, vers[wahl-1]))
    if wahl == 1:
      par = par_c
    if wahl == 2:
      par = par_d
    return vers[wahl-1]




  def doit( wahl ):
    global modAdr
    global index
    global par
    global modFwVersion

    if wahl == 1 :  # Teste Modul-Adresse (ping)
      err = us.ser_reset_buffer()
      txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )
      print(txCmd)
      rxCmd = us.txrx_command( txCmd )
      print('empfange: %s'%( rxCmd ) )

    if wahl == 2 :  # Staus: anzeigen;
      err = us.ser_reset_buffer()
      controllers = select_controller()
      perform_command( controllers, 0x02 )

    if wahl == 3 :  # alle %dsec anzeigen
      w = wdh
      while( w ) :
        for reg in [1,2,3,4]:
          txCmd = mb.wrap_modbus( modAdr, 2, reg, "" )
          print('sende:  %s'%(txCmd))
          rxCmd = us.txrx_command( txCmd )
          print('empfange: %s'%( rxCmd ) )
        time.sleep(intSec)
        w -= 1
        print()

    if wahl == 4 :  # Parameter lesen 
      tbl=[]
      for regler in [0,1,2,3,4]:
        txCmd = mb.wrap_modbus( modAdr, 3, regler, "" )
        print('sende:  %s'%(txCmd))
        rxCmd = us.txrx_command( txCmd )
        cmdList = rxCmd
        print(rxCmd)
        tbl1 = cmdList.split()
        tbl.append( tbl1 )
        #print('empfange: %s'%( rxCmd ) )
      # sort as a table:
      spalten = len(tbl)
      zeilen  = len(tbl[0])
      print(zeilen,spalten)
      for x in range(zeilen):
        zs=[]
        for y in range(spalten):
          zs.append(tbl[y][x])

        print("%10s  %5s %5s %5s %5s"%(zs[0],zs[1],zs[2],zs[3],zs[4]))

    if wahl == 5 :  # alle Parameter auf Werkseinstellung setzen
      perform_command( [0], 0x30 )

    if wahl == 6 :  # Ventil dauerhaft auf
      controllers = select_controller()
      perform_command( controllers, 0x31 )

    if wahl == 7 :  # Ventil dauerhaft zu
      controllers = select_controller()
      perform_command( controllers, 0x32 )

    if wahl == 8 :  # Ventil regeln (Ende dauerhaft)
      controllers = select_controller()
      perform_command( controllers, 0x33 )

    if wahl == 9 :  # Regler inaktiv setzen 
      controllers = select_controller()
      perform_command( controllers, 0x34 )

    if wahl == 10 :  # controller active
      controllers = select_controller()
      perform_command( controllers, 0x35 )

    if wahl == 11 :  # fast
      controllers = select_controller()
      perform_command( controllers, 0x36 )


    if wahl == 12 :  # end fast -> normal speed
      controllers = select_controller()
      perform_command( controllers, 0x37 )

    if wahl == 20 :  # sende Vorlauftemperatur von Zentrale
      vtzstr = input("Zentrale Vorlauftemperatur:")
      cmd = mb.wrap_modbus( modAdr, 0x20, 0, ' '+vtzstr+' ' )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )
      

    if wahl == 21 :  # parameter senden
      controllers = select_controller()
      for reg in controllers:
        cmd=modFwVersion
        for i in par.index:
          cmd += ' ' + par.valFst[i]%( par.valDef[i] )
        cmd += ' '
        txCmd = mb.wrap_modbus( modAdr, 0x21, reg, cmd )
        print( 'sende: %dbyte, cmd=%s'%(len(txCmd), txCmd ))
        rxCmd = us.txrx_command( txCmd )
        print('empfange: %s'%( rxCmd.strip() ) )
        dtEeprom = 0.2
        print('warte %d sec bis Befehl ausgeführt ist ...'%(dtEeprom))
        print("-"*40)
        time.sleep(dtEeprom)

    if wahl == 31 :  # parameter ins eeprom speichern
      reg=0
      cmd = mb.wrap_modbus( modAdr, 0x39, reg, "" )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )

    if wahl == 40 :  # parameter aller module abholen und abspeichern
        pass
        dateTime = time.strftime( "%Y%m%d_%H%M%S", time.localtime())
        datName = "log/par_hk%d_%s.dat"%(heizkreis, dateTime)
        print("Schreibe Datei: %s"%(datName))
        fout = open(datName,"w")
        
        print("Modul:",end="")
        for moduleAdr in modules:
            print(moduleAdr," ", end="")
            for regler in [0,1,2,3,4]:
                txCmd = mb.wrap_modbus( moduleAdr, 3, regler, "" )
                #print('sende:  %s'%(txCmd))
                rxCmd = us.txrx_command( txCmd )
                hs = "Mod%d Reg%d %s\r\n"%( moduleAdr, regler, rxCmd )
                fout.write(hs)
        print(" fertig")
        fout.close()

    if wahl == 49:  # reset ueber Watchdog auslösen
      print('Modul Adresse ist %d'%(modAdr))
      cmd = mb.wrap_modbus( modAdr, 0x3A, 0, "" )
      print('sende:  %s'%(cmd))
      rxCmd = us.txrx_command( cmd )
      print('empfange: %s'%( rxCmd ) )


    if wahl == 50:  # jede Minute status einlesen und speichern
      print('Modul Adresse ist %d'%(modAdr))

      dateiName = 'log/log_HZ-RR012_'+time.strftime('%Y-%M-%d_%H:%M:%S.dat')
      odat = open( dateiName, 'w' )
      while True :
        for regler in [1,2,3,4]:
          txCmd = mb.wrap_modbus( modAdr, 2, regler, "" )
          #print('sende:  %s'%(cmd))
          rxCmd = us.txrx_command( txCmd )
          logstr = time.strftime('%Y-%M-%d_%H:%M:%S ') + rxCmd
          print('store: %s'%( logstr ) )
          odat.write( logstr + '\r\n' )
        odat.flush()
        time.sleep(60.0)
        print()

    if wahl == 98 :
      modFwVersion = select_version()

    if wahl == 99 :
      a=0
      while a<1 or a >31 :
        a = int( input( 'Modul Adresse 1..30; wahl? ') )
      modAdr = a
    print()


  wahl = 1
  while wahl > 0 :
      read_heizkreis_config()
      wahl = menu(0)
      print( "----------------wahl=%d-------------"%(wahl) )
      doit(wahl)