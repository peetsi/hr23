# CONFIG MODUL - LOADS/SAVES/WRITES/CACHES CONFIGS/SETTINGS
#import numpy as np

#set this in main.
#pyserver_conf = pi_conf() # wie setzt man initializer? später googlen

# GLOBAL VARIABLES VOR THE OTHER .PY SCRIPTS - CAPSLOCK BECAUSE THOSE __MUST__ BE USED BY THE OTHER SCRIPTS, TO KEEP DYNAMICALLY EXPANDABILITY


# READ Information for GFX module
# ... extend
class pi_parse:
    try:
        import configparser as configparser
        conf_par = configparser.ConfigParser()   
    except ImportError:
        raise ImportError("Config Parser could not be included!")

# ALL THOSE PROPERTIES IN PI_CONF ARE FOR __INTERNAL__ USAGE __ONLY__!!!!! USE THE ABOVE VALUES FOR THE REST OF THE SCRIPT!
class pi_conf(object):

    # IMPORTS - we import them here, as we dont need them anywhere else
    #           this is good for compatibility and also looks clean - i think.
    try:
        #import classes.pi_err as oerr
        #import classes.pi_log as olog
        import pi_err as oerr
        import pi_log as olog
    except ImportError :
        raise ImportError

    # statics
    # INSERT FUNCTION NAMES HERE (automatically if somehow possible? pi_conf.names?) [-> should overwrite the default vars]
    param_a = {  0 : '_init_', \
        1 : 'cache', \
        2 : 'ras', \
        3 : 'case_run', \
        4 : 'r_sec', \
        5 : 'cache_conf', \
        6 : 'r', \
        7 : 'w', \
        8 : '', \
        9 : '', \
        10: '' }
    CONF_USING_ERR_T = 1 # py_conf = 1 param_a,CONF_USING_ERR_T
    conf_err = oerr.pi_err()    # INIT ERROR HANDLER (create object - every object has its error handler object)
    conf_log = olog.pi_log()                            # + init log
    # no error - set data <- automate this process..
    # ERR_STRINGS ---- TEST ------
    conf_err.err_s = { 0 : 'TOO MANY ARGUMENTS'} # maybe implement later or move this into file

    pp = pi_parse()
    conf_par = pp.conf_par
    r = conf_par
    try:
        sections = conf_par.sections() # read all section and key # ['bitbucket.org', 'topsecret.server.com']
    except TypeError:
        raise TypeError("Object Creation in {0:02} has failed. Exiting")
    
    conf_err.s_t()  # 1 = py_conf()
    conf_err.s_a(0) # 0 = TAKES name of function from .oErr.err_a array 

    def __init__(self, NAME_OF_CONFIG_FILE_TO_CREATE="pyServerConf.ini"):
        """
        try:   EXCEPTION HANDLING IN PYTHON
            f()
        except Exception as e:
            print(e)
        """
        # INIT PARSER
        
        
        #[f for f in dir(ClassName) if not f.startswith('_')]
        #method_list = [func for func in dir(Foo) if callable(getattr(Foo, func))]
        #print([ m for m in dir(my_class) if not m.startswith('__')])
        #print (dir(list))
        #import inspect
        #import mymodule
        #method_list = [ func[0] for func in inspect.getmembers(mymodule, predicate=inspect.isroutine) if callable(getattr(mymodule, func[0])) ]
        
        if (NAME_OF_CONFIG_FILE_TO_CREATE == ""): 
            NAME_OF_CONFIG_FILE_TO_CREATE = "pyServer.conf"
            self.conf_err.g( "*WARNING*", 0, "No name given on the initialization of pi_conf() Object." )
            
        # HARDCODED CONSTANTS
        self.__CONF_SEL_INIT_GLOBAL = 1
        self.__CONF_SEL_INIT_LOG = 2
        self.__CONF_SEL_INIT_GFX = 3
        self.__CONF_SEL_INIT_SBUS = 4
        self.__CONF_SEL_INIT_SERVER = 5
        self.__CONF_SEL_INIT_VMON = 6
        self.__CONF_SEL_INIT_COMMHANDLER = 7
        self.__CONF_SEL_INIT_ERRHANDLER = 8
        
        # conf file constants
        self.conf = {  config_section : 'CONFIG_SECTION', \
                        path : 'path', \
                        name :'name', \
                        log_section : 'LOG SETTINGS', \
                        log_path : 'log_path', \
                        log_name : 'name', \
                        log_size : 'max_size' }

        # LOAD LOG CONFIG
        self.cache(1)

        self.conf_file_sec                   = "log_settings" # log file settings >> log settings keys
        
        self.conf_file_key_log_file_path     = "path"         # path "/" local directory (hopfully :P)
        self.conf_file_key_log_file_name     = "name"         # name "pyServer"
        self.conf_file_key_log_file_type     = "type"         # file type ".conf"
        self.conf_file_key_log_file_msize    = "max_size"     # max file size - 100 MB
        self.conf_file_key_log_file_enc      = "encoding"     # set encoding for the file 
        
        self.conf_file_key_log_file_pathD    = "/log/"        # and default value
        self.conf_file_key_log_file_nameD    = "pyServer"     # and default value
        self.conf_file_key_log_file_typeD    = ".conf"        # and default value
        self.conf_file_key_log_file_msizeD   = 1024*100       # max file size - 100 MB
        self.conf_file_key_log_file_encD     = 'utf-8'        # default val for enconding

        self.conf_file_sec_gfx = "gfx_settings" # graphical settings >> log settings keys >> init keys
        # none yet

        self.conf_file_sec_sbus                       = "serial_settings"    # serial bus settings
        self.conf_file_key_sbus_use_multiple_methods  = "use_multiple_connection_methods"
        self.conf_file_key_sbus_use_multiple_methodsD = "false"
        self.conf_file_key_sbus_use_usb               = "use_usb_for_ser_con"
        self.conf_file_key_sbus_use_usbD              = "true" # use usb

        self.conf_file_sec_ser = "server_settings" # server settings (tcp etc.)
        # none yet

        self.conf_file_sec_vmon = "vmon_settings" # vmon file settings
        # none yet

        self.conf_file_sec_comh = "communication_handler" # com handler settings section
        # none yet

        self.conf_file_sec_err = "error_handler" # err file settings
        # none yet

        self.CONF_NAME = self.conf_par.read( self.conf.path,self.conf)      # ['example']
        self.CONF_TYPE = self.conf_par.read( self.conf_file_key_glo_type, self.conf_file_key_glo_typeD)  # ['.conf']
        self.CONF_PATH = self.conf_par.read( self.conf_file_key_glo_type, self.conf_file_key_glo_typeD)  # ['.conf']
        self.CONF_ENC  = self.conf_par.read( self.conf_file_key_glo_type, self.conf_file_key_glo_typeD)  # ['.conf']
        
        self.CONF_FPATH = self.CONF_PATH + self.CONF_NAME + self.CONF_TYPE
        fhandle = open(self.CONF_FPATH, "r", self.CONF_ENC)
        if not (fhandle) :   # check if ini exists
            while not (fhandle):
                self.first_init()
                fhandle = open("config/heizkreis.conf","r",self.CONF_ENC)

    def first_init(self):
        #self.w() create complete configuration file if not present.
        val = "KEY"
        var = "VAL"
        self.ras(val, var)  
        return
    
    def run(self):
        pass

    def cache(self, CONF_SEL_INIT_ID):
        return self.case_run(CONF_SEL_INIT_ID)
    
    def ras(self, val, var): #read AND set value
        _val = self.conf_par.read( val, var )
        return

    def case_run(self, case):   # helper function for cache || not inteded for us to use directly
        if (case == self.__CONF_SEL_INIT_GLOBAL) :
            # do stuff
            return 

        elif (case == self.__CONF_SEL_INIT_LOG) :
            self.PATH    = self.r( self.conf_file_key_log_file_path,  self.conf_file_key_glo_file_pathD )
            self.NAME    = self.r( self.conf_file_key_log_file_name,  self.conf_file_key_glo_file_nameD )
            self.TYPE    = self.r( self.conf_file_key_log_file_type,  self.conf_file_key_glo_file_typeD )
            self.ENC     = self.r( self.conf_file_key_log_file_enc,   self.conf_file_key_log_file_encD )
            self.MFSIZE  = self.r( self.conf_file_key_log_file_msize, self.conf_file_key_log_file_msizeD )
            self.FULL_PATH = PATH + NAME + TYPE
            self.RETURN = { self.PATH, NAME, TYPE  }
            return self.RETURN

        elif (case == self.__CONF_SEL_INIT_GFX) :
            # do stuff
            return 

        elif (case == self.__CONF_SEL_INIT_SBUS) :
            # do stuff
            return 

        elif (case == self.__CONF_SEL_INIT_SERVER) :
            # do stuff
            return 

        elif (case == self.__CONF_SEL_INIT_VMON) :
            # do stuff
            return 

        elif (case == self.__CONF_SEL_INIT_COMMHANDLER) :
            # do stuff
            return 

        elif (case == self.__CONF_SEL_INIT_ERRHANDLER) :
            # do stuff
            return 

        else:
            # log ERROR
            return 

    def r_sec(self, section):
        if (section.lower() == 'a') : return self.conf_par.sections()
        for key in self.conf_par[section]:  
            print(key)

    def cache_conf_all(self):
        return

    def reload_conf(self):
        return self.cache_conf_all()

    def r(self, attr, defaults): # read config setting
        return self.conf_par.read( attr, defaults)

    def w(self, sections, keys, values):  # write config setting
        
        configfile.sections(section)
        configfile.keys(key)
        configfile.values(value)

        with open(NAME, 'w') as configfile:
            configfile.write(configfile)
        return 0

    # ----------------
    # ----- main -----
    # ----------------

# test:
if __name__ == "__main__" :
    config_object = pi_conf()
    
    
    
    