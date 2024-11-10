import hashlib

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
