import sys
class log :
    def __init__(self, debug):
        self.__debug_enabled = debug
        self.__debug_file_name = sys.argv[0] + "_logfile.log"
        self.__debug_file = open(self.__debug_file_name, "w")
    def __del__(self) :
            self.__debug_file.close()
    def err(self, *args) :
        print("ERR : ", *args)
        if self.__debug_file :
            print("ERR : ", *args, file=self.__debug_file)
    def dbg(self, *args):
        print("DBG : ", *args)
        if self.__debug_enabled :
            print("DBG : ", *args, file=self.__debug_file)
