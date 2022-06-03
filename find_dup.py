import os
import hashlib
import argparse
import shutil

debug_enable = False

def err(*args) :
	print("ERROR : ", *args)

def dbg(*args) :
	global debug_enable
	if debug_enable :
		print("DEBUG : ", *args)

def find_dup_files_in_dir(dir, mdir) :
	files_hash = {}
	if not os.path.isdir(dir) :
		err("Invalid dir : ", dir)
		return False 
	f = os.listdir(dir)
	if not f :
		err("No files in : ", dir)
		return False 
	for i in f :
		filepath = os.path.join(dir,i)
		sinfo = os.stat(filepath)
		if sinfo.st_size > 1024 :
			dbg("Size of file ", filepath, " : ", sinfo.st_size);
		if os.path.isfile(filepath) :
			fh = hashlib.sha256()
			with open(filepath, "rb") as fp:
				while True :
					b = fp.read(20 * 1024 * 1024)
					if b :
						fh.update(b)
					else :
						break
			h = fh.hexdigest()
			dbg("filename : ", filepath, " hash : ", h)
			if files_hash.get(h) :
				orig = ""
				dup = ""
				if filepath.find("(") != -1 :
					dup = filepath
					orig = files_hash[h]
				elif files_hash[h].find("(") != -1 :
					orig = filepath
					dup = files_hash[h]
					files_hash[h] = filepath
				else :
					dup = filepath
					orig = files_hash[h]					
				print()
				print("--------->", "Found duplicate [orig : ", orig, "] [duplicate :", dup, "]")
				dfilename = dup 
				d=dfilename.replace('\\', '_')
				ddir=os.path.join(mdir, d)
				try :
					shutil.move(dup, ddir)
				except :
					print("error in move : ddir : ", ddir, "dfilename : ", dfilename)
					raise
			else :
				files_hash[h] = filepath
		else :
			err("Skipping non-file !!! --> ", filepath)
	
	
if __name__ == '__main__' :
	parser = argparse.ArgumentParser()
	parser.add_argument("--dir", help="provide the basedirectory", required=True)
	parser.add_argument("--mdir", help="provide the directory to move", required=True)
	parser.add_argument("--debug", help="provide the basedirectory")

	args = parser.parse_args()
	dirname=args.dir
	mdirname=args.mdir
	if args.debug :
		debug_enable = True
	alldirs = os.listdir(dirname)
	cnt = 0
	for d in alldirs :
		dbg("Scannin dir ", d)
		print(".", end=" ", flush=True)
		cnt = cnt + 1
		if (cnt % 20) == 0 :
			print("")
		dpath = os.path.join(dirname, d)
		if not os.path.isdir(dpath) :
			err(dpath, "is not a directory - check why it is preset in top dir")
			continue
		find_dup_files_in_dir(dpath, mdirname)