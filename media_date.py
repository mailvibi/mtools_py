import pathlib
import re
from datetime import datetime

import exifread
import exiftoolwrap


def exiftool_get_creation_date_extened(media_file, logger, exiftool_path):
    logger.dbg("Trying to get date (extended) using exiftool")
    exiftool = exiftoolwrap.exiftoolWrap(exiftool_path, True)
    tags = exiftool.process_file(media_file)
    if len(tags):
        media_date = ""
        if 'File Creation Date/Time' in tags:
            media_date = tags['File Creation Date/Time']
            logger.dbg("found Image - Create Date - tag = ", media_date)
        else:
            logger.dbg("exiftool - extened search too did not find tags in file ->", media_file)
            return None
        media_date = media_date.split(' ')[0].strip()
        logger.dbg("found Image DateTime tag = ", media_date)
        try:
            return datetime.strptime(str(media_date), "%Y:%m:%d")
        except ValueError:
            logger.dbg("unable to get date for file : ", media_file)
            return None
    logger.dbg("exiftool too did not find tags in file ->", media_file)
    return None


def exiftool_get_creation_date(media_file, logger, exiftool_path):
    logger.dbg("Trying to get date using exiftool")
    exiftool = exiftoolwrap.exiftoolWrap(exiftool_path, True)
    tags = exiftool.process_file(media_file)
    if len(tags):
        media_date = ""
        if 'Create Date' in tags:
            media_date = tags['Create Date']
            logger.dbg("found Image - Create Date - tag = ", media_date)
        elif 'Date/Time Original' in tags:
            media_date = tags['Date/Time Original']
            logger.dbg("found Image - Date/Time Original - tag = ", media_date)
        else:
            logger.dbg("exiftool too did not find tags in file ->", media_file)
            return None
        media_date = media_date.split(' ')[0].strip()
        logger.dbg("found Image DateTime tag = ", media_date)
        try:
            return datetime.strptime(str(media_date), "%Y:%m:%d")
        except ValueError:
            logger.dbg("unable to get date for file : ", media_file)
            return None
    logger.dbg("exiftool too did not find tags in file ->", media_file)
    return None


def get_creation_date_from_filename(media_file, logger, exiftool_path=None):
    """Extract a date from names such as 20250724_075334.jpg or IMG-20150906-WA0007.jpg."""
    logger.dbg("Trying to get date from filename")
    filename = pathlib.Path(media_file).name
    match = re.match(r"^(?:\d{8}_\d+|[^-]+-\d{8}(?:-|\.))", filename)
    if not match:
        logger.dbg("filename does not contain a supported date format: ", media_file)
        return None
    date_text = match.group(0).split('_')[0] if '_' in match.group(0) else match.group(0).split('-')[1]
    try:
        return datetime.strptime(date_text, "%Y%m%d")
    except ValueError:
        logger.dbg("unable to parse date from filename: ", media_file)
        return None


def exif_get_creation_date(media_file, logger, exiftool_path=None):
    logger.dbg("Trying to get date from EXIF data")
    datetags = ['Image DateTime', 'EXIF DateTimeOriginal', 'EXIF DateTimeDigitized']
    with open(media_file, "rb") as media_file_handle:
        tags = exifread.process_file(media_file_handle)
        if not len(tags):
            logger.dbg("No tags available for file ->", media_file)
            return None
        media_date = None
        if 'EXIF DateTimeOriginal' in tags:
            media_date = tags['EXIF DateTimeOriginal']
            logger.dbg("found EXIF DateTimeOriginal tag = ", media_date)
        elif 'Image DateTime' in tags:
            media_date = tags['Image DateTime']
            logger.dbg("found Image DateTime tag = ", media_date)
        elif 'EXIF File Modification Date/Time' in tags:
            media_date = tags['EXIF File Modification Date/Time']
            logger.dbg("found Image DateTime tag = ", media_date)
        else:
            logger.dbg("exif_get_creation_date -> No DateTime tags available for file ->", media_file)
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
    ".m2ts": [exiftool_get_creation_date, get_creation_date_from_filename, exiftool_get_creation_date_extened],
    ".mts": [exiftool_get_creation_date, get_creation_date_from_filename, exiftool_get_creation_date_extened],
}


def get_media_file_creation_date(media_file, logger, exiftool_path=None):
    ext = pathlib.Path(media_file).suffix.lower()
    handler_functions = handlers.get(ext)
    if not handler_functions:
        logger.err("No matching handlers for ", media_file)
        return None
    for handler in handler_functions:
        media_date = handler(media_file, logger, exiftool_path)
        if media_date:
            return media_date
    return None
