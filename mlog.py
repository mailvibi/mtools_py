import sys
class log :
    def __init__(self, logfilename = None, debug = False):
        self.__debug_enabled = debug
        if logfilename :
            self.__debug_file_name = logfilename + "_logfile.log"
            self.__debug_file = open(self.__debug_file_name, "w")
        else :
            self.__debug_file = None
    def __del__(self) :
            if self.__debug_file :
                self.__debug_file.close()
    def err(self, *args) :
        print("ERR : ", *args)
        if self.__debug_file :
            print("ERR : ", *args, file=self.__debug_file)
    def dbg(self, *args):
        if self.__debug_enabled :
            print("DBG : ", *args)
            if self.__debug_file :
                print("DBG : ", *args, file=self.__debug_file)
    def info(self, *args) :
        print("INF : ", *args)
        if self.__debug_file :
            print("INF : ", *args, file=self.__debug_file)