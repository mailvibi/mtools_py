import subprocess
import mlog

class exiftoolWrap :
    def __init__(self, exiftool, debug = False) :
        self.__debug = debug
        self.__exiftool = exiftool
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
    e = exiftoolWrap('D:\Hobbies\mtools\py\exiftool.exe', True)
    print(e.process_file('D:\Pictures\IMG-20150830-WA0020.jpg'))