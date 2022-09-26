import os
import hashlib
import argparse
import shutil

debug_enable = True


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
	filenames=[]
	for root, dirname, fnames in os.walk(dirname) :
		for fname in fnames :
			filenames.append(os.path.join(root, fname))

	hlist = map(get_file_hash, filenames)
#	print(list(hlist))
	hmap={}
	for i in hlist :
		if hmap.get(i[1]) :
			hmap[i[1]].append(i[0])
		else :
			hmap[i[1]] = [i[0]]
#print(hmap)

	for f in hmap.values() :
		if len(f) > 1 :
			print(find_dup(f))
		else :
			dbg("No duplicate for file", f[0])