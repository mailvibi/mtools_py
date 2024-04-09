import os
import hashlib
import argparse
import shutil
import time
import mlog
import sys
import json
def find_dup(filelist) :
	res = {"orig": [], "dup": []}
	orig = []
	dup = []
	for f in filelist:
		if "Copy" in f:
			dup.append(f)
		else :
			orig.append(f)
	if len(orig) > 1:
		neworig = []
		for f in orig:
			if "(" in f:
				dup.append(f)
			else:
				neworig.append(f)
		orig = neworig
	res["orig"] = orig
	res["dup"] = dup
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
	lg.dbg("Moving files ", filelist, " to ", mdir)

	def moveone(file) :
		tfile = file
		tfile = tfile.replace('\\', '_')
		tfile = tfile.replace(':', '_')
		tpath=os.path.join(mdir, tfile)
		lg.dbg("Moving file ", file, " to ", tpath)
		try :
			shutil.move(file, tpath)
		except :
			lg.err("Moving file ", file, " to ", mdir, " failed !!!")
	list(map(moveone, filelist))

if __name__ == '__main__' :
	parser = argparse.ArgumentParser()
	parser.add_argument("--dir", help="provide the base directory to check for duplicate files", required=True)
	parser.add_argument("--mdir", help="provide the directory to move duplicate files")
	parser.add_argument("--json", help="json file to output the duplicate file information")
	parser.add_argument("--debug", action="store_true", help="enable debug")

	args = parser.parse_args()
	dirname=args.dir
	mdir=args.mdir

	lg = mlog.log("13Jan", args.debug)

# Create a list of files
	st = time.time()
	filenames=[]
	for root, dirname, fnames in os.walk(dirname) :
		for fname in fnames :
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
	hmap={}
	for i in hlist :
		if hmap.get(i[1]) :
			hmap[i[1]].append(i[0])
		else :
			hmap[i[1]] = [i[0]]
	duplist=[]
	origlist=[]
	#separate the list to duplicate (multiple entries for same hash)
	# and original list (only one entry for one hash)
	for f in hmap.values() :
		if len(f) > 1 :
			duplist.append(find_dup(f))
		else :
			origlist.append(f[0])
	et = time.time()
	lg.info("Finding dup : ", et - st)

	lg.dbg("DUP : ", duplist)
	lg.dbg("ORIG : ", origlist)
	if args.json:
		with open(args.json, "w") as jf:
			jstr = json.dumps(duplist, indent=4)
			jf.write(jstr)
	if mdir is not None:
		st = time.time()
		#flatten the list of lists
		filesToMove=[filename for resultdict in duplist for filename in resultdict["dup"]]
		et = time.time()
		lg.info("Make list of files to move : ", et - st)

		lg.dbg(filesToMove)

		st = time.time()
		movefiles(filesToMove, mdir)
		et = time.time()
		lg.info("Time to move files : ", et - st)
