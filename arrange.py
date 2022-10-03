import os
import sys
import argparse
import pathlib
import shutil
import mlog
from datetime import datetime
import exifread
import exiftoolwrap

def exiftool_get_creation_date(media_file) :
    lg.dbg("Trying to get date using exiftool")
    e = exiftoolwrap.exiftoolWrap('D:\Hobbies\mtools\py\exiftool.exe', True)
    tags = e.process_file(media_file)
    if len(tags) and 'Create Date' in tags:
        media_date = tags['Create Date']
        lg.dbg("found Image DateTime tag = ", media_date)
        media_date = media_date.split(' ')[0].strip()
        lg.dbg("found Image DateTime tag = ", media_date)
        try :
            mdate = datetime.strptime(str(media_date), "%Y:%m:%d")
            return mdate
        except :
            lg.dbg("unable to get date for file : ", media_file)
            return None
    else :
        lg.dbg("exiftool too did not find tags in file ->", media_file)
        return None

def get_creation_date_from_filename(media_file) :
    lg.dbg("Trying to get date from filename")
    # break down filename like IMG-20150906-WA0007.jpg
    m = media_file.split('-')
    if len(m) < 2 :
        lg.dbg("length of {} after split is {}".format("media_file", len(m)))
        return None
    if not m[1].isnumeric() :
        lg.dbg("second position of {} is not numeric[{}]".format(media_file, m[1]))
        return None
    return datetime.strptime(m[1], "%Y%m%d")

def exif_get_creation_date(media_file) :
    lg.dbg("Trying to get date from EXIF data")
    DATETAGS = ['Image DateTime', 'EXIF DateTimeOriginal', 'EXIF DateTimeDigitized']
    with open(media_file, "rb") as f :
        tags = exifread.process_file(f)
        if not len(tags) :
            #try to find the date from name of the file
            lg.dbg("No tags available for file ->", media_file)
#            fname = os.path.basename(media_file)
            return None
            #lg.dbg(tags)
        media_date = None
        if 'EXIF DateTimeOriginal' in tags :
            media_date = tags['EXIF DateTimeOriginal']
            lg.dbg("found EXIF DateTimeOriginal tag = ", media_date)
        elif 'Image DateTime' in tags :
            media_date = tags['Image DateTime']
            lg.dbg("found Image DateTime tag = ", media_date)
        elif 'EXIF File Modification Date/Time' in tags :
            media_date = tags['EXIF File Modification Date/Time']
            lg.dbg("found Image DateTime tag = ", media_date)
        else :
            lg.err("No DateTime tags available for file ->", media_file)
            return None
        return datetime.strptime(str(media_date), "%Y:%m:%d %H:%M:%S")
    return None

handlers = {
    ".jpg" : [exif_get_creation_date,get_creation_date_from_filename],
    ".heic" : [exif_get_creation_date,get_creation_date_from_filename],
    ".mov" : [exiftool_get_creation_date, get_creation_date_from_filename],
    ".mp4" : [exiftool_get_creation_date, get_creation_date_from_filename],
}

def get_media_file_creation_date(media_file) :
    ext = pathlib.Path(media_file).suffix.lower()
    hfunc = handlers.get(ext)
    if not hfunc :
        lg.err("No matching handlers for ", media_file)
        return None
    mdate = None
    for func in hfunc :
        mdate = func(media_file)
        if mdate :
            return mdate
    return mdate

def arrange_media_file(media_file, dest_dir, logonly = False):
    lg.dbg("X" * 50)
    lg.dbg("Arranging file :", media_file)
    creation_date = get_media_file_creation_date(media_file)
    if not creation_date :
        lg.err("unable to get the creation date for file", media_file)
        return False
    
    year_dir = os.path.join(dest_dir, str(creation_date.year))
    if not os.path.isdir(year_dir) :
        lg.dbg("Year dir {} does not exist, so creating it".format(year_dir))
        if not logonly :
            os.mkdir(year_dir)
    media_dir = "{:04d}-{:02d}-{:02d}".format(creation_date.year, creation_date.month, creation_date.day)
    media_dir = os.path.join(year_dir,   media_dir)
    if not os.path.isdir(media_dir) :
        lg.dbg("Media dir {} does not exist, so creating it".format(media_dir))
        if not logonly :
            os.mkdir(media_dir)
    try :
        lg.info("[MOVE][{}]-[{}]".format(media_file, media_dir))
        if not logonly :
            shutil.move(media_file, media_dir)
    except :
        lg.err("error while moving file {} to directory {}".format(media_file, media_dir))

if __name__ == "__main__" :
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--srcdir", required=True)
    argparser.add_argument("--dstdir", required=True)
    argparser.add_argument("--logfile")
    argparser.add_argument("--logonly", action="store_true")
    argparser.add_argument("--d", action = "store_true")
    args = argparser.parse_args()
    supported_extensions = [".JPG", ".HEIC", ".MOV", ".MP4"]
#    srcdir = pathlib.Path(args.srcdir)
#    dstdir = pathlib.Path(args.dstdir)
    srcdir = args.srcdir
    dstdir = args.dstdir
    logonly = args.logonly

    lg = mlog.log(args.logfile, args.d)
    #repr(srcdir)
    if not os.path.isdir(srcdir) :
        lg.err("Source directory[{}] Invalid", srcdir)
        sys.exit()
    if not os.path.isdir(dstdir) :
        lg.err("Destination directory[{}] Invalid", dstdir)
        sys.exit()
    files=list(filter( lambda x : os.path.isfile(os.path.join(srcdir, x)) , os.listdir(srcdir)))
#    lg.dbg(files)
    lg.dbg("Found {} files in directory {}".format(len(files), srcdir))
    l_supported_ext=list(map(lambda x : x.lower(), supported_extensions))
    file_with_supported_extension=list(filter(lambda x : pathlib.Path(x).suffix in supported_extensions or pathlib.Path(x).suffix in l_supported_ext, files))
    file_without_supported_extension=list(filter(lambda x : pathlib.Path(x).suffix not in supported_extensions and pathlib.Path(x).suffix not in l_supported_ext, files))
    if len(file_without_supported_extension) :
        lg.err("files with out supported extension :->")
        lg.err(file_without_supported_extension)
        lg.err("These files will not be processed")
    if not len(file_with_supported_extension) :
        lg.err("No files with supported extension to be processed")
        sys.exit()
    lg.dbg("Processing {} files".format(len(file_with_supported_extension)))
    list(map(lambda f: arrange_media_file(os.path.join(srcdir, f), dstdir, logonly), file_with_supported_extension))
    sys.exit()
 
