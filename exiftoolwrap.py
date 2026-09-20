import os
import subprocess
import sys
import mlog

EXIFTOOL_PATH = "EXIFTOOL_PATH"

class exiftoolWrap :
    def __init__(self, exiftool = None, debug = False) :
        self.__debug = debug
        l = mlog.log(debug=debug)

        if os.name == "nt" :
            if exiftool is None :
                l.err("exiftool path is required")
                return
            self.__exiftool = exiftool
        elif os.name == "posix" :
            p = subprocess.run(["which", "exiftool"], capture_output=True, text=True)
            if p.returncode != 0 or not p.stdout.strip() :
                l.err("exiftool should be in path")
                return
            self.__exiftool = p.stdout.strip()
    def process_file(self, filename) :
        l = mlog.log(debug=True)
        try :
            p = subprocess.run([self.__exiftool, filename], capture_output=True)
        except :
            l.err("Subprocess[{}] did not execute for file {}".format(self.__exiftool, filename))
            return {}
        if p.returncode != 0 :
            l.err("Subprocess returned failure")
            return {}
        o = {}
        for i in p.stdout.decode().splitlines() :
            j = i.split(":", 1)
            t =  j[1].strip()
            o[j[0].strip()] = t if '+' not in t else t.split('+')[0]
        return o

if __name__ == "__main__" :
    if os.name == "nt" :
        exiftool_path = os.environ.get(EXIFTOOL_PATH)
        l = mlog.log(debug=True)
        if not exiftool_path :
            l.err("EXIFTOOL_PATH environment variable is not set")
            sys.exit(1)
        e = exiftoolWrap(exiftool_path, True)
        print(e.process_file('D:\\Pictures\\IMG-20150830-WA0020.jpg'))
    else :
        e = exiftoolWrap(debug=True)
        print(e.process_file('/home/v/Pictures/DSC02717.jpg'))

