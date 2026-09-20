import os
import sys
import argparse
import pathlib
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
import exifread
import exiftoolwrap
import pprint

import mlog
import file_hash

MOVE_FILE = False
#MOVE_FILE = True

exiftool_path = None

@dataclass
class ProcessingReport:
    unable_to_get_creation_date_files: list[str] = field(default_factory=list)
    same_file_at_target_files: list[str] = field(default_factory=list)
    unable_to_process_files: list[str] = field(default_factory=list)
    show_same_file_at_target_files: bool = False

    def if_anything_to_log(self):
        return bool(self.unable_to_get_creation_date_files or 
                    self.same_file_at_target_files or
                    self.unable_to_process_files)

    def log_unprocessed_files(self, logger):
        if not self.if_anything_to_log():
            logger.info("All files processed successfully.")
            return
        logger.info("#" * 50)
        logger.info("Log of unprocessed files:")
        if self.unable_to_get_creation_date_files:
            logger.err("Unable to get creation date for following files.")
            logger.err(pprint.pformat(self.unable_to_get_creation_date_files))
        if self.show_same_file_at_target_files:
            logger.err("Unable to copy following files as there is already same file at the target location.")
            logger.err(pprint.pformat(self.same_file_at_target_files))
        else:
            logger.info("There are {} files which were not copied as there is already same file at the target location.".format(len(self.same_file_at_target_files)))
        if self.unable_to_process_files:
            logger.err("Unable to process following files.")
            logger.err(pprint.pformat(self.unable_to_process_files))
        logger.info("#" * 50)


def exiftool_get_creation_date_extened(media_file):
    lg.dbg("Trying to get date (extended) using exiftool")
    e = exiftoolwrap.exiftoolWrap(exiftool_path, True)
    tags = e.process_file(media_file)
    if len(tags) :
        media_date = ""
        if 'File Creation Date/Time' in tags:
            media_date = tags['File Creation Date/Time']
            lg.dbg("found Image - Create Date - tag = ", media_date)
        else :
            lg.dbg("exiftool - extened search too did not find tags in file ->", media_file)
            return None
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


def exiftool_get_creation_date(media_file) :
    lg.dbg("Trying to get date using exiftool")
    e = exiftoolwrap.exiftoolWrap(exiftool_path, True)
    tags = e.process_file(media_file)
    if len(tags) :
        media_date = ""
        if 'Create Date' in tags:
            media_date = tags['Create Date']
            lg.dbg("found Image - Create Date - tag = ", media_date)
        elif 'Date/Time Original' in tags :
            media_date = tags['Date/Time Original']
            lg.dbg("found Image - Date/Time Original - tag = ", media_date)
        else :
            lg.dbg("exiftool too did not find tags in file ->", media_file)
            return None
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
    """Extract a date from supported names such as 20250724_075334.jpg or IMG-20150906-WA0007.jpg."""
    lg.dbg("Trying to get date from filename")
    filename = pathlib.Path(media_file).name
    match = re.match(r"^(?:\d{8}_\d+|[^-]+-\d{8}(?:-|\.))", filename)
    if not match :
        lg.dbg("filename does not contain a supported date format: ", media_file)
        return None
    date_text = match.group(0).split('_')[0] if '_' in match.group(0) else match.group(0).split('-')[1]
    try:
        return datetime.strptime(date_text, "%Y%m%d")
    except ValueError:
        lg.dbg("unable to parse date from filename: ", media_file)
        return None

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
            lg.dbg("exif_get_creation_date -> No DateTime tags available for file ->", media_file)
            return None
        return datetime.strptime(str(media_date), "%Y:%m:%d %H:%M:%S")
    return None

handlers = {
    ".jpg": [
                exif_get_creation_date, get_creation_date_from_filename,
                exiftool_get_creation_date_extened
            ],
    ".jpeg": [
                exif_get_creation_date, get_creation_date_from_filename,
                exiftool_get_creation_date_extened
            ],
    ".heic": [
                exif_get_creation_date, get_creation_date_from_filename,
                exiftool_get_creation_date, exiftool_get_creation_date_extened
            ],
    ".png": [exiftool_get_creation_date, get_creation_date_from_filename, exiftool_get_creation_date_extened],
    ".mov": [exiftool_get_creation_date, get_creation_date_from_filename, exiftool_get_creation_date_extened],
    ".mp4": [exiftool_get_creation_date, get_creation_date_from_filename, exiftool_get_creation_date_extened],
    ".3gp": [exiftool_get_creation_date, get_creation_date_from_filename, exiftool_get_creation_date_extened],
    ".m2ts": [exiftool_get_creation_date, get_creation_date_from_filename,  exiftool_get_creation_date_extened],
    ".mts": [exiftool_get_creation_date, get_creation_date_from_filename, exiftool_get_creation_date_extened],
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

def arrange_media_file(media_file, dest_dir, report, logonly = True):
    lg.dbg("X" * 50)
    lg.dbg("Arranging file :", media_file)
    creation_date = get_media_file_creation_date(media_file)
    if not creation_date :
        lg.err("unable to get the creation date for file", media_file)
        report.unable_to_get_creation_date_files.append(media_file)
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
        if not logonly:
            os.mkdir(media_dir)
    else:
        targetfile = os.path.join(media_dir, os.path.basename(media_file))
        if os.path.exists(targetfile):
            lg.dbg("file ", targetfile, " exists. Checking if they are same")
            thash = file_hash.get_file_hash(targetfile)
            shash = file_hash.get_file_hash(media_file)
            if thash[1] == shash[1]:
                lg.dbg("target file {} and source file {} seems to be same. Skipping copying...".format(targetfile, media_file))
                report.same_file_at_target_files.append(media_file)
                return
            #append __1 to the file name & hope this file does not exist"
            tmp_media_file = os.path.basename(media_file).split(".")
            tmp_target_media_file_name = tmp_media_file[:-1] + ["__1."] + tmp_media_file[-1:]
            newtargetfile = os.path.join(media_dir,"".join(tmp_target_media_file_name))
            lg.info("target file {} already exists, changing name to {}".format(targetfile, newtargetfile))
            media_dir = newtargetfile
    try:
        operation = "MOVE" if MOVE_FILE else "COPY"
        lg.info("[{}][{}]-[{}]".format(operation, media_file, media_dir))
        if not logonly:
            if MOVE_FILE:
                shutil.move(media_file, media_dir)
            else:
                shutil.copy2(media_file, media_dir)
    except Exception as e:
        lg.err("error -> {} - while moving file {} to directory {}".format(repr(e), media_file, media_dir))
        report.unable_to_process_files.append(media_file)

if __name__ == "__main__" :
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--srcdir", required=True)
    argparser.add_argument("--dstdir", required=True)
    argparser.add_argument("--logfile")
    argparser.add_argument("--recurse", action="store_true")
    argparser.add_argument("--logonly", action="store_true")
    argparser.add_argument("--d", action = "store_true")
    args = argparser.parse_args()
#    supported_extensions = [".JPG", ".HEIC", ".MOV", ".MP4", ".3gp", ".m2ts", ".MTS"]
    supported_extensions = handlers.keys()
    u_supported_ext=list(map(lambda x : x.upper(), supported_extensions))

#    srcdir = pathlib.Path(args.srcdir)
#    dstdir = pathlib.Path(args.dstdir)
    srcdir = args.srcdir
    dstdir = args.dstdir
    logonly = args.logonly
    recurse = args.recurse

    lg = mlog.log(args.logfile, args.d)
    if os.name == "nt" :
        exiftool_path = os.environ.get(exiftoolwrap.EXIFTOOL_PATH)
        if not exiftool_path :
            lg.err("EXIFTOOL_PATH environment variable is not set")
            sys.exit(1)
    #repr(srcdir)
    if not os.path.isdir(srcdir) :
        lg.err("Source directory[{}] Invalid", srcdir)
        sys.exit()
    if not os.path.isdir(dstdir) :
        lg.err("Destination directory[{}] Invalid", dstdir)
        sys.exit()
    
    files = []
    if recurse:
        for root, dirname, fnames in os.walk(srcdir) :
            for fname in fnames :
                files.append(os.path.join(root, fname))
    else:
        files = list(filter(lambda x: os.path.isfile(os.path.join(srcdir, x)), os.listdir(srcdir)))
    lg.dbg(f"srcdir = {srcdir}, dstdir = {dstdir}, logonly = {logonly}, recurse = {recurse}")
    #lg.dbg(f"files = {files}")
    lg.dbg("supported extensions : {}", supported_extensions)
    lg.dbg("Found {} files in directory {}".format(len(files), srcdir))
    file_with_supported_extension=list(filter(lambda x : pathlib.Path(x).suffix in supported_extensions or pathlib.Path(x).suffix in u_supported_ext, files))
    file_without_supported_extension=list(filter(lambda x : pathlib.Path(x).suffix not in supported_extensions and pathlib.Path(x).suffix not in u_supported_ext, files))
    if len(file_without_supported_extension):
        lg.err("files with out supported extension (These files will not be processed) :->")
        lg.err(file_without_supported_extension)
        lg.err("-" * 30)
    if not len(file_with_supported_extension) :
        lg.err("No files with supported extension to be processed")
        sys.exit()
    report = ProcessingReport()
    lg.dbg("Processing {} files".format(len(file_with_supported_extension)))
    list(map(lambda f: arrange_media_file(os.path.join(srcdir, f), dstdir, report, logonly), file_with_supported_extension))
    lg.info("#" * 50)
    lg.info("Processing completed.")
    report.log_unprocessed_files(lg)
    sys.exit()
 
