import hashlib
import os
import shutil

# from cvs import BRANCHES_DIR


def _write_to_file(file_path, prefix, *data):
    """Add files to the staging area"""
    if not os.path.exists(file_path):
        raise ValueError(f"There is no file '{file_path}'")
    with open(file_path, "a") as file:
        for write_data in data:
            file.write(prefix + write_data + '\n')


def _clear_file(file_path, write_data=None):
    """Add files to the staging area"""
    if not os.path.exists(file_path):
        raise ValueError(f"There is no file '{file_path}'")
    if write_data:
        with open(file_path, "w+") as file:
            file.write(write_data + '\n')


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


def _delete_files(directory):
    files = os.listdir(directory)
    for file in files:
        if all(not file.startswith(i) for i in {".", "__"}):
            path = os.path.join(directory, file)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

