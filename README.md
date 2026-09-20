# Media tools

Small Python utilities for arranging media files by date and finding duplicate files.

## Requirements

- Python 3 is required.
- Install the project dependency from `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

The current requirements file contains `ExifRead==3.5.1`, which is used by `arrange.py` to read image metadata. `find_dup.py` uses only Python standard-library modules.

### ExifTool

`arrange.py` uses ExifTool as a fallback for formats and files that do not provide usable EXIF dates. The current code expects the executable at:

```text
EXIFTOOL_PATH
```

On Windows, set the `EXIFTOOL_PATH` environment variable to the executable path before running the scripts. The variable is checked by the script entry point and the program exits with an error if it is missing. For example, in Command Prompt:

```bat
set EXIFTOOL_PATH=C:\Tools\exiftool.exe
python arrange.py --srcdir C:\Pictures\inbox --dstdir C:\Pictures\organized
```

The bundled `exiftool.exe` can be used on Windows. On Linux, install `exiftool` and make sure it is available on `PATH`.

## Arrange media by date

`arrange.py` reads dates from media metadata and moves files into this layout:

```text
<destination>/YYYY/YYYY-MM-DD/<filename>
```

Date lookup is format-dependent. It tries EXIF data, dates embedded in names such as `IMG-20150906-WA0007.jpg`, and ExifTool metadata. Supported extensions are `.jpg`, `.heic`, `.png`, `.mov`, `.mp4`, `.3gp`, `.m2ts`, and `.mts` (case-insensitive).

### Usage

```bash
python arrange.py --srcdir /path/to/source --dstdir /path/to/destination
```

Required options:

- `--srcdir DIR`: source directory.
- `--dstdir DIR`: existing destination directory.

Optional options:

- `--recurse`: scan subdirectories recursively. Without it, only files directly in the source directory are scanned.
- `--logonly`: report the planned file operations without changing files. Moves or copies are performed by default.
- `--logfile FILE`: write the log to a file.
- `--d`: enable debug logging.

The global `MOVE_FILE` setting in `arrange.py` controls the operation: its default value, `True`, moves files; set it to `False` to copy files instead. Copying uses `shutil.copy2` and leaves the source files in place. `--logonly` takes precedence over both operations.

Example dry run:

```bash
python arrange.py \
  --srcdir /data/inbox \
  --dstdir /data/organized \
  --recurse \
  --logonly
```

If a destination filename already exists, files with the same SHA-256 hash are skipped. A different file is renamed with a `__1` suffix before moving or copying. Files without a supported extension, or without a usable date, are reported and left untouched.

After processing, the script reports filenames that could not be dated, files skipped because the same content already exists at the destination, and file operations that failed.

## Find duplicate files

`find_dup.py` recursively scans a directory, first grouping files by size and then comparing SHA-256 hashes. Duplicate groups are written as JSON records containing `orig` and `dup` lists.

### Find duplicates

```bash
python find_dup.py --dir /path/to/organized --ojson duplicates.json
```

Options:

- `--dir DIR`: directory to scan recursively.
- `--ojson FILE`: write duplicate information to this JSON file.
- `--mdir DIR`: move duplicate files into this directory after scanning.
- `--debug`: enable debug logging.

When `--mdir` is used without `--ojson`, the script uses a temporary JSON file and removes it after moving files:

```bash
python find_dup.py \
  --dir /data/organized \
  --mdir /data/duplicates
```

Moving duplicates flattens their paths into filenames under `--mdir`; spaces, backslashes, and colons in source paths are replaced with underscores. Review the result carefully before deleting anything.

### Move duplicates from existing JSON

Use `--ijson` to move duplicates described by a previously generated JSON file:

```bash
python find_dup.py \
  --ijson duplicates.json \
  --mdir /data/duplicates
```

`--ijson` cannot be combined with `--dir` or `--ojson`, and it requires `--mdir`.

## Safety notes

- Test `arrange.py` with `--logonly` before allowing it to move files.
- Keep a backup before using `find_dup.py --mdir`; moving files is not reversible by the script.
- Duplicate detection is content-based only after the initial size filter, so files with different sizes are never treated as duplicates.
