import hashlib
import os
import shutil

from cvs import BRANCHES_DIR


def _write_to_file(file_path, *data):
    """Add files to the staging area"""
    if not os.path.exists(file_path):
        raise ValueError(f"There is no file '{file_path}'")
    with open(file_path, "a") as file:
        for write_data in data:
            file.write(write_data + '\n')


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

    if not os.path.exists(copy_from) or not os.path.exists(copy_to):
        raise ValueError(f"This path{' '+copy_from if os.path.exists(copy_from) else ''} "
                         f"{' ' + copy_to if os.path.exists(copy_to) else ''} not exist")

    if not files_to_copy:
        shutil.copy2(copy_from, copy_to)
    else:
        for item in files_to_copy:
            if os.path.isdir(copy_from+f'/{item}'):
                shutil.copy2(copy_from+f'/{item}', copy_to+f'/{item}')
            else:
                shutil.copy2(copy_from+f'/{item}', copy_to)


def commit_changes(staging_area, commit_dir, message):
    """Commit changes to the repository"""
    commit_hash = hashlib.sha1(message.encode()).hexdigest()
    commit_path = os.path.join(commit_dir, commit_hash)

    with open(staging_area, 'r') as f:
        branch = f.readline().strip()
        for filepath in f:
            filepath_split = filepath.split()
            path = ''.join(filepath_split[:-1])
            filename = filepath_split[-1]
            _copy_files(path, commit_path, filename)

    with open(BRANCHES_DIR+'/'+branch+'branch_info.txt', 'w') as f:
        f.write(commit_hash+'\n')


    # Copy files from staging area to commit directory
    # shutil.copytree(staging_area, commit_path)
