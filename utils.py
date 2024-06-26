import hashlib
import json
import os
import shutil
from pathlib import Path


def read_json_file(path):
    with open(path, 'r') as f:
        return json.load(f)


def write_json_file(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def get_all_files(path, ignore, staged_files):
    dirs = [Path(path)]
    while len(dirs) > 0:
        p = dirs.pop()
        for item in p.iterdir():
            if any(str(item).startswith(i) for i in ignore):
                continue
            if item.is_dir():
                dirs.append(item)
            elif str(item) not in staged_files:
                yield str(item)


def get_file_hash(path):
    h = hashlib.new('sha256')
    with open(path, "r") as f:
        for line in f:
            h.update(line.encode())
    return h.hexdigest()


def copy_files(copy_to, files_to_copy):
    """Receives files paths and directory to which files will be copied"""
    for item in files_to_copy:
        shutil.copy2(Path(item), copy_to)


def delete_files(directory, ignore):
    dirs = [Path(directory)]
    while len(dirs) > 0:
        p = dirs.pop()
        for item in p.iterdir():
            if any(str(item).startswith(i) or item.name.startswith(i)
                   for i in ignore):
                continue
            if item.is_dir():
                dirs.append(item)
            else:
                os.remove(item)
