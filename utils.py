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


def _copy_files(copy_from, copy_to, *files_to_copy):
    """Moves files from the 'copy_from' directory to the 'copy_to' directory
    based on the file paths from the 'files_to_copy' list. If the 'files_to_copy'
    parameter is not specified, the default method moves all files from the 'copy_from'
    directory"""
    if copy_from != '' and not os.path.exists(copy_from):
        raise ValueError(f"This path '{copy_from}' does not exist")
    if not files_to_copy:
        shutil.copytree(copy_from, copy_to)

    else:
        if not os.path.exists(copy_to):
            os.makedirs(copy_to, exist_ok=True)
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
