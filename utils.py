import hashlib
import json
import os
import shutil
from pathlib import Path


def _read_json_file(path):
    with open(path, 'r') as f:
        return json.load(f)


def _write_json_file(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def _get_all_files(path, ignore, staged_files):
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


def _get_file_hash(path):
    h = hashlib.new('sha256')
    with open(path, "r") as f:
        for line in f:
            h.update(line.encode())
    return h.hexdigest()


def _copy_files(copy_to, files_to_copy):
    """Receives files paths and directory to which files will be copied"""
    for item in files_to_copy:
        shutil.copy2(item, copy_to)


def _delete_files(directory, ignore_files):
    files = os.listdir(directory)
    for file in files:
        if all(not file.startswith(i) for i in ignore_files):
            path = os.path.join(directory, file)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
