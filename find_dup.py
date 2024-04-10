import os
import hashlib
import argparse
import shutil
import time
import mlog
import sys
import json
from datetime import date

TMPJSONFILENAME = "k_o_k_k_a_n_____t_m_p.json"

def find_dup(filelist):
    res = {"orig": [], "dup": []}
    orig = []
    dup = []
    for filename in filelist:
        if "Copy" in filename or "(" in filename:
            dup.append(filename)
        else:
            orig.append(filename)

    if len(orig) > 1:
        # Check for the base directory name and if it is a specific
        # date keep it, else mark as dup
        # for example if base directory is of one file is 2016-12 and another
        # file is 2016-12-18, mark 2016-12-18 as original and 2016-12 as dup
        basedirs = list(map(lambda p: [os.path.basename(os.path.dirname(p)), p], orig))
        year_month_basedirs = list(filter(lambda p: len(p[0].split("-")) == 2, basedirs))
        non_year_month_date_basedirs = list(filter(lambda p: len(p[0].split("-")) != 2, basedirs))
        if len(year_month_basedirs) > 0 and len(non_year_month_date_basedirs) > 0:
            dup.extend(p[1] for p in year_month_basedirs)
            orig = [p[1] for p in non_year_month_date_basedirs]
#                print(f"basedirs = {basedirs}")
#                print(f"year_month_basedirs = {year_month_basedirs}")
#                print(f"non_year_month_date_basedirs = {non_year_month_date_basedirs}")
#                print("dup = ", dup)
#                print("orig = ", orig)
    if len(orig) > 1:
        # keep the file in the oldest base directory as the orig and mark rest as dup
        basedirs = list(map(lambda p: [date.fromisoformat(os.path.basename(os.path.dirname(p))), p], orig))
        oldest = basedirs[0]
        for e in basedirs[1:]:
            if oldest[0] > e[0]:
                oldest = e
            elif oldest[0] == e[0]:
                #consider the first one found as original and rest as duplicate
                dup.append(e[1])
        orig = [oldest[1]]
        dup.extend([e[1] for e in basedirs if e[0] != oldest[0]])
    if len(orig) > 1:
        print("Cant find all dups :", orig)
    res["orig"] = orig
    res["dup"] = dup
    return res


def file_hash(filepath):
    fh = hashlib.sha256()
    with open(filepath, "rb") as fp:
        while True:
            b = fp.read(20 * 1024 * 1024)
            if b:
                fh.update(b)
            else:
                break
    h = fh.hexdigest()
    return h


def get_file_hash(filename):
    return [filename, file_hash(filename)]

def move_dup_files(mdir, json_file_name):
    if not mdir:
        return
    jsondata = None
    with open(jsonfilename, "r") as jf:
        jsondata = json.load(jf)
    def moveone(file):
        tfile = file
        tfile = tfile.replace(' ', '_')
        tfile = tfile.replace('\\', '_')
        tfile = tfile.replace(':', '_')
        tpath = os.path.join(mdir, tfile)
        lg.dbg("Moving file ", file, " to ", tpath, " as ", tfile)
        try:
            shutil.move(file, tpath)
        except:
            lg.err("Moving file ", file, " to ", mdir, " as ", tfile, " failed !!!")
    for e in jsondata:
        print("move duplicate json files : ", e["dup"])
        list(map(moveone, e["dup"]))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", help="provide the base directory to check for duplicate files")
    parser.add_argument("--mdir", help="provide the directory to move duplicate files")
    parser.add_argument("--ojson", help="json file to output the duplicate file information")
    parser.add_argument("--ijson", help="input duplicate file information in json file")
    parser.add_argument("--debug", action="store_true", help="enable debug")

    args = parser.parse_args()
    dirname = args.dir
    mdir = args.mdir
    if args.ijson and args.ojson:
        print("--ijson and --ojson cannot be provided together")
        sys.exit(1)
    if args.ijson and args.dir:
        print("--ijson and --dir cannot be provided together")
        sys.exit(1)
    if args.ijson and not args.mdir:
        print("--ijson requires --mdir")
        sys.exit(1)
    lg = mlog.log("13Jan", args.debug)

    if not args.ijson:

        # Create a list of files
        st = time.time()
        filenames = []
        for root, dirname, fnames in os.walk(dirname):
            for fname in fnames:
                filenames.append(os.path.join(root, fname))
        et = time.time()
        lg.info("Get List of files : ", et - st)

        lg.dbg("number of files : ", len(filenames))
        # Group file based on size and take only files which have equal size
        szmap = {}
        for file in filenames:
            sz = os.stat(file).st_size
            if szmap.get(sz):
                szmap[sz].append(file)
            else:
                szmap[sz] = [file]
        filelist = [j for i in szmap.values() for j in i if len(i) > 1]
        filenames = filelist
        lg.dbg("number of files filtered based on length: ", len(filenames))

        # Calculate the hash of all the files
        st = time.time()
        hlist = list(map(get_file_hash, filenames))
        et = time.time()
        lg.info("Hash of files : ", et - st)

        # Find duplicate from the hashlist (files with same hash)
        st = time.time()
        hmap = {}
        for i in hlist:
            if hmap.get(i[1]):
                hmap[i[1]].append(i[0])
            else:
                hmap[i[1]] = [i[0]]
        duplist = []
        origlist = []
        # separate the list to duplicate (multiple entries for same hash)
        # and original list (only one entry for one hash)
        for f in hmap.values():
            if len(f) > 1:
                duplist.append(find_dup(f))
            else:
                origlist.append(f[0])
        et = time.time()
        lg.info("Finding dup : ", et - st)

        lg.dbg("DUP : ", duplist)
        lg.dbg("ORIG : ", origlist)
        jsonfilename = TMPJSONFILENAME if not args.ojson and mdir else args.ojson
        if jsonfilename:
            with open(jsonfilename, "w") as jf:
                jstr = json.dumps(duplist, indent=4)
                jf.write(jstr)
    if args.ijson:
        jsonfilename = args.ijson
    ########################################################
    # Move the files
    ########################################################
    move_dup_files(mdir, jsonfilename)
    if jsonfilename == TMPJSONFILENAME:
        os.unlink(TMPJSONFILENAME)