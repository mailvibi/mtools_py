import os
import hashlib
import argparse
import shutil
import time

debug_enable = False

def instr_prnt(*args) :
	print("INSTR : ", *args)


def err(*args) :
	print("ERROR : ", *args)

def dbg(*args) :
	global debug_enable
	if debug_enable :
		print("DEBUG : ", *args)

def find_dup(filelist) :
	res = {"orig" : [], "dup" : []}
	for file in filelist :
		if "Copy" in file :
			res["dup"].append(file)
		else :
			res["orig"].append(file)
	return res

def file_hash(filepath) :
	fh = hashlib.sha256()
	with open(filepath, "rb") as fp:
		while True :
			b = fp.read(20 * 1024 * 1024)
			if b :
				fh.update(b)
			else :
				break
	h = fh.hexdigest()
	return h

def get_file_hash(filename) :
	return [filename, file_hash(filename)]
	
def movefiles(filelist, mdir) :
	dbg("Moving files ", filelist, " to ", mdir)

	def moveone(file) :
		tfile = file
		tfile = tfile.replace('\\', '_')
		tfile = tfile.replace(':', '_')
		tpath=os.path.join(mdir, tfile)
		dbg("Moving file ", file, " to ", tpath)
		try :
			shutil.move(file, tpath)
		except :
			err("Moving file ", file, " to ", mdir, " failed !!!")
	list(map(moveone, filelist))

if __name__ == '__main__' :
	parser = argparse.ArgumentParser()
	parser.add_argument("--dir", help="provide the basedirectory", required=True)
	parser.add_argument("--mdir", help="provide the directory to move")
	parser.add_argument("--debug", help="enable debug")

	args = parser.parse_args()
	dirname=args.dir
	mdir=args.mdir
	if args.debug :
		debug_enable = True
	filenames=[]

	st = time.time()
	for root, dirname, fnames in os.walk(dirname) :
		for fname in fnames :
			filenames.append(os.path.join(root, fname))
	et = time.time()
	instr_prnt("Get List of files : ", et - st)

	st = time.time()
	hlist = map(get_file_hash, filenames)
	et = time.time()
	instr_prnt("Hash of files : ", et - st)

	st = time.time()
	hmap={}
	for i in hlist :
		if hmap.get(i[1]) :
			hmap[i[1]].append(i[0])
		else :
			hmap[i[1]] = [i[0]]
	duplist=[]
	origlist=[]
	for f in hmap.values() :
		if len(f) > 1 :
			duplist.append(find_dup(f))
		else :
			origlist.append(f[0])
	filesToMove=[filename for resultdict in duplist for filename in resultdict["dup"]]
	et = time.time()
	instr_prnt("Finding dup : ", et - st)

	print("DUP : ", duplist)
	print("ORIG : ", origlist)
	dbg(filesToMove)
	if mdir is not None:
		st = time.time()
		movefiles(filesToMove, mdir)
		et = time.time()
		instr_prnt("Time to move files : ", et - st)