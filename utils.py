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


def _item_in_ignore(item, ignore_list):
    item = Path(item)
    name = item.name
    if any(name.startswith(i) for i in ignore_list["START"]):
        return True
    if item.is_dir():
        return name in ignore_list["DIRECTORIES"]
    suffix = item.suffix
    return suffix in ignore_list["FORMATS"] or name in ignore_list["FILES"]


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


def get_files(path, ignore):
    dirs = [Path(path)]
    while len(dirs) > 0:
        p = dirs.pop()
        for item in p.iterdir():
            if _item_in_ignore(item, ignore):
                continue
            if item.is_dir():
                dirs.append(item)
                continue
            yield str(item)


def clear_directory(directory, ignore):
    dirs = [Path(directory)]
    ind = 0
    while ind < len(dirs):
        for item in dirs[ind].iterdir():
            if _item_in_ignore(item, ignore):
                continue
            if item.is_dir():
                dirs.append(item)
                continue
            os.remove(item)
        ind += 1
    for i in range(len(dirs) - 1, 0, -1):
        delete = True
        for _ in dirs[i].iterdir():
            delete = False
            break
        if delete:
            os.rmdir(dirs[i])
