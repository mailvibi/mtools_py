import os
import sys
import argparse
import pathlib
import shutil
import mlog
from datetime import datetime
import exifread

class media_date :
    def __init__(self, y, m ,d ) : 
        self.Year = y
        self.Month = m
        self.Day = d


def get_media_file_creation_date(media_file):
    DATETAGS = ['Image DateTime', 'EXIF DateTimeOriginal', 'EXIF DateTimeDigitized']
    with open(media_file, "rb") as f :
        tags = exifread.process_file(f)
        if not len(tags) :
            #try to find the date from name of the file
            lg.dbg("No tags available for file ->", media_file)
            fname = os.path.basename(media_file)
            return None
        media_date = None
        if 'EXIF DateTimeOriginal' in tags :
            media_date = tags['EXIF DateTimeOriginal']
            lg.dbg("found EXIF DateTimeOriginal tag = ", media_date)
        elif 'Image DateTime' in tags :
            media_date = tags['Image DateTime']
            lg.dbg("found Image DateTime tag = ", media_date)
        else :
            lg.err("No DateTime tags available for file ->", media_file)
            return None
        return datetime.strptime(str(media_date), "%Y:%m:%d %H:%M:%S")
    return None

def arrange_media_file(media_file, dest_dir):
    lg.dbg("Arranging file :", media_file)
    creation_date = get_media_file_creation_date(media_file)
    if not creation_date :
        lg.err("unable to get the creation date for file", media_file)
        return False
    
    year_dir = os.path.join(dest_dir, str(creation_date.year))
    if not os.path.isdir(year_dir) :
        lg.dbg("Year dir {} does not exist, so creating it".format(year_dir))
        os.mkdir(year_dir)
    media_dir = "{:04d}-{:02d}-{:02d}".format(creation_date.year, creation_date.month, creation_date.day)
    media_dir = os.path.join(year_dir,   media_dir)
    if not os.path.isdir(media_dir) :
        lg.dbg("Media dir {} does not exist, so creating it".format(media_dir))
        os.mkdir(media_dir)
    try :
        shutil.move(media_file, media_dir)
    except :
        lg.err("error while moving file {} to directory {}".format(media_file, media_dir))

if __name__ == "__main__" :
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--srcdir", required=True)
    argparser.add_argument("--dstdir", required=True)
    argparser.add_argument("--d")
    args = argparser.parse_args()
    supported_extensions = [".JPG", ".HEIC"]
#    srcdir = pathlib.Path(args.srcdir)
#    dstdir = pathlib.Path(args.dstdir)
    srcdir = args.srcdir
    dstdir = args.dstdir
    lg = mlog.log(True)
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
    list(map(lambda f: arrange_media_file(os.path.join(srcdir, f), dstdir), file_with_supported_extension))
    sys.exit()
    #use filter to check for extensions & then map to arrange_media_files
    for f in files :
        lg.dbg("Starting processing file -> ", f)
        extension = pathlib.Path(f).suffix
        lg.dbg("Extension of file {} -> {}", f, extension)
        # if pathlib.Path(f).suffix in supported_extensions
        #if f.split('.')[1] in supported_extensions :
        if extension in supported_extensions :
            arrange_media_file(f, dstdir)
        else :
            lg.err("Unsupported extension for file -> ", f)
 
