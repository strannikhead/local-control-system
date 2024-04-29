import hashlib
import os
import shutil


def write_to_file(file_path, *data):
    """Add files to the staging area"""
    if not os.path.exists(file_path):
        raise ValueError(f"There is no file '{file_path}'")
    with open(file_path, "a") as file:
        for write_data in data:
            file.write(write_data + '\n')


def clear_file(file_path, write_data=''):
    """Add files to the staging area"""
    if not os.path.exists(file_path):
        raise ValueError(f"There is no file '{file_path}'")
    if write_data == '':
        with open(file_path, "r") as file:
            write_data = file.readline()
    with open(file_path, "w+") as file:
        file.write(write_data + '\n')


def copy_files(copy_from, copy_to, files_to_copy=None):
    """Moves files from the 'copy_from' directory to the 'copy_to' directory
    based on the file paths from the 'files_to_copy' list. If the 'files_to_copy'
    parameter is not specified, the default method moves all files from the 'copy_from'
    directory"""
    pass


def commit_changes(staging_area, commit_dir, message):
    """Commit changes to the repository"""
    commit_hash = hashlib.sha1(message.encode()).hexdigest()
    commit_path = os.path.join(commit_dir, commit_hash)

    # Copy files from staging area to commit directory
    shutil.copytree(staging_area, commit_path)

