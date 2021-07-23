#from arepl_dump import dump 
from pprint import pprint
import sys

class pi_modbus(object):

    def __init__(self): #(self, *initial_data, **kwargs):
        # init first
        self.output= ""             # active output - doesnt matter if wrap or unwrap
        self.ready       = False     # this will be true when the lrc is calculated and parity byte
        self.len         = 0         # stringlen
        self.adr         = 0
        self.cmd         = ""
        self.m_adr2m     = 0
        self.regler      = 0
        self.version     = 0
        self.data        = ""
        self.checksum    = 0
        self.lrc         = 0         # lrc checksum
        self._wrapped_   = ""
        self._unwrapped_ = ""

    def use(self, _dict): # try else to have only one function
        try:
            self.__dict__.update(_dict) # wrap
        except:
            self.data = _dict # unwrap
            return 0

    def wrap(self):
        tmp = self.data
        _chksm = 0
        wrap_mask = ":{adr}{cmd}{m_adr2m}{regler}{version}{data}".format(adr=self.adr, cmd=self.cmd, m_adr2m=self.m_adr2m, regler=self.regler, version=self.version, data=tmp )
        for k in wrap_mask: 
            if k.isdigit():  # skip the :
                _chksm += int(k) 
        wrap_mask += "{chksm}".format(chksm=int(_chksm)) # get checksum without checksum/lrc
        self.data = wrap_mask
        self._calc_lrc()
        if not(int(self.lrc) >= 0): return 1 # raise error later - calculation mismacht, cant be <= 0
        wrap_mask       += "{lrc}\r\n".format(lrc=self.lrc) + "0" # get checksum without checksum/lrc
        self.output     = wrap_mask
        self._wrapped_  = wrap_mask
        self.len        = len(wrap_mask)
        self.free()

    def _calc_chksm(self):
        pass

    def unwrap(self):
        self.output = ""
        tmp = self.data # using input! very important- output is only a result, not the input.
                            #therefore the unwrap is being set into output aswell
        if not(tmp.find("\r\n0") and tmp[0] == ":"): return 2 # test, works lol
        unwrap_data = tmp
        #print (unwrap_data)
        _ochksm = int(unwrap_data[-7:-5])
        _olrc   = int(unwrap_data[-5:-3])
        _nchksm = 0
        unwrap_data = unwrap_data[:-7] # remove lrc and chksm from string for new calculation
        for k in unwrap_data: #recalculate lrc and chksm
            if k.isdigit():  # skip the :
                _nchksm += int(k) 
        if not(_ochksm==_nchksm):   return 3 #error unwrap checksum error.
        self.data = unwrap_data+str(_nchksm) # add chksm to calc, otherwise wrong
        self._calc_lrc()
        _nlrc = self.lrc
        if not(_olrc==_nlrc):       return 4 #error lrc mismatch
        tmp_msk          = dict({ 'adr':unwrap_data[1:3], 'cmd':unwrap_data[3:5], 'm_adr2m':unwrap_data[6:8], 'regler':unwrap_data[7:9], 'version':unwrap_data[9:11], 'data':unwrap_data[11:] })
        self.output      = tmp_msk#tmp_msk)
        self._unwrapped_ = tmp_msk['data']
        #dump()
        self.free()

    def free(self): # just reset object.
        self.ready      = False     # this will be true when the lrc is calculated and parity byte
        self.adr        = 0
        self.cmd        = ""
        self.m_adr2m    = 0
        self.regler     = 0
        self.version    = 0
        self.data       = ""
        self.checksum   = 0
        self.lrc        = 0         # lrc checksum
        #self.output= ""  
        #self.len       = 0        # stringlen

    def _calc_lrc(self): # internal function - not to be used outside of the object
        tmp = list(self.data)[1:] # skip double dot..
        #print(tmp)
        tmp_lrc = 0
        for b in tmp: #if this does work, it should iterate through the entire string
            tmp_lrc ^= ord(b)
            #print("looooooooop LRC {}".format(tmp_lrc))
        self.lrc = tmp_lrc
        return 0 # lrc_been_set

    def show(self, io='O'): # Input/output/FULLreturn (both)
        if (io.upper() == 'O'):
            return self.output
        elif (io.upper() == 'I'):
            return self.data
        elif (io.upper() == "F"):
            return { 'input' : self.data, 'output' : self.output }
        elif (io.upper() == "L"): # display LRC
            return self.lrc
        elif (io.upper() == "W"): # wrapped text
            return self._wrapped_
        elif (io.upper() == "U"): # unwrapped text
            return self._unwrapped_
        else:
            return print('Error - please call "show" with "I" or "O" or "F" or "W" or "U"')


"""

if __name__ == "__main__":
    mb = pi_modbus()

    print('[lets see if this works...]')

    packet_to_arduino =  { "data":'hi - WRAP ME!', "adr": '00', "cmd": '01', "m_adr2m" : '09', "regler" : '02', "version" : '01' } 
    mb.use(packet_to_arduino)

    print( "[wrapping data]" )
    mb.wrap()
    print( mb.show('O') )

    wrapped_packet_to_arduino = mb.show('W')
    print( "[we now gave result from the wrap into var: wrapped_packet_to_arduino, lets unwrap now]")

    mb.use(wrapped_packet_to_arduino) #sets input
    mb.unwrap() # unwrappes
    unwrapped_packet_from_arduino = mb.show('O') # 'U' this only shows UNWRAP as STRING - we want O for dictionary

    print ("[unwrapped packet from arduino]")
    print (unwrapped_packet_from_arduino)
    print(unwrapped_packet_from_arduino['data'])
    print(unwrapped_packet_from_arduino['adr'])
    print(unwrapped_packet_from_arduino['cmd'])
    print(unwrapped_packet_from_arduino['m_adr2m'])
    print(unwrapped_packet_from_arduino['regler'])
    print(unwrapped_packet_from_arduino['version'])
    print(unwrapped_packet_from_arduino['data'])
    print("just the unwrapped data\n")
    print(mb.show('U'))
    #print("\n\ndisplaying in & out vars:\n")
    #print(mb.show( 'F' ))



snprintf( buf, 
                STR_TX_MAXLEN-10, 
                ":00%02X%02X%1X%s %s", 
                st.txCmdNr, 
                get_address(),
                st.txReg, 
                RX_TX_PROTOCOL_VERSION,
                st.txCmd );
// empfangen eines Pakets:
// ":  AA      cc    00        r     21            data_whatever\r\n0; 
// ":|<ADR>|<CMD>|<M_ADR2M>| <R> |<VRS> | <DATA> | <CHKSM>        | <LRC>          | \r        \n      \0"
//  0|1 2  | 3 4 | 5 6     |  7  |8  9  |  10... | len()-6 len()-5| len()-4 len()-3| len()-2 len()-1 len()
// AA = (1-127) target address from master,             - zentrale, wird nicht in eine variable gespeichert, hardcodiert.
// cc = command        to master, "3A"                  - st.rxCmdNr
// 00 = modul address from master,                      - get_address() -> eigenne addresse, wird nicht gespeichert, hardcodiert.
// r  = 0=module, 1=regler0, 2=regler1, 3=regler2,..    - st.rxReg
// V  = <protocol version>,                             - st.rxRecvPtVer
//

byte Hzrr200brd::modbus( byte action,  byte adr, char *s ) {
    if (action == MBWRAP) {
        mPrint("[WRAP]['%s'][c:'%s']\n",s,lrc_calc(s));
        byte lrc = 0;
        byte ls = strlen(s)+2; // Länge LRC Berechnung
        char hs[66];
        //FORMAT : %02X% <- ADDRESSE = AA; %s <- STRING; 
        //:254AB
        //:09TSCHUSS        
        sprintf( hs, ":%02X%s", adr, s);

        for (int i=1; i<ls; i++) {lrc = lrc ^ hs[i];}
            sprintf(hs, ":%02X%s%02X\r\n", adr, s, lrc);
            strcpy(s,hs);       // ich würde das hier gern entfernen und nur noch mit st.modbWrapped arbeiten.. - mit peter besprechen
            strcpy(st.modbWrapped, hs);
            return 0;

    } else if (action == MBUNWRAP) { 
        mPrint("[MODBUS][UNWRAP]['%s']\n",s);
        byte adr = 0;
        byte lrc = 0;
        char cmp_msk[8] = "\r\n";  //8  "\r\n"
        char cmp_in[8];
        byte ls = strlen(s); // Länge LRC Berechnung

        char hs[66];

             // :  ADR  ( DATA  ) (    LRC) \r\n
            //  0|(1>2)|(3>(x-5))|((x-4)>x)| 
        
        if (s[0] != ':')     {  mPrint("s[2]=%c \n",s[2]);      return 1;}
        if (s[ls-2] != '\r') {  mPrint("s[ls-1]=%c \n",s[ls-4]);return 2;}
        if (s[ls-1] != '\n') {  Serial.print(s[ls-3]);          return 3;}



        Serial.println(s[ls-4]);
        Serial.println(s[ls-3]);
        byte blrc = hex2byte(&s[ls-4]);
        byte clrc = lrc_calc(s);

        mPrint( "BLRC: %02X\n", blrc );
        mPrint( "CLRC: %02X\n", clrc );


        //:FEAB42   -> hex 42 = 67 dezimal ||brlc müsste 42 sein und crlc müsste auch 42 sein
        if (blrc != clrc) return 4; //lrc mismatch
        // syntax correct.

        st.cmdAddress = hex2byte(&s[1]);
        if (st.cmdAddress != get_address() && st.cmdAddress != 0) return 5; //kommando abarbeiten

        s[ls-4] = 0;
        s = &s[3]; // string auf den datenbereich reduzieren (den string kürzen)

        return 1;

        Serial.println("BLRC:");
        Serial.println(blrc);

      return 0;
    }
  return 1; // sollte nicht ankommen
}
"""