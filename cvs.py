import os
import time
import click
import exceptions
from pathlib import Path
from enum import Enum
import utils as ut

MAIN_BRANCH = ".cvs/branches/main"
BRANCHES = ".cvs/branches"
BRANCHES_LOG = ".cvs/branches_log"
STAGING_AREA = ".cvs/staging_area.json"
GITIGNORE = ".cvs/cvsignore.json"
CURRENT_DIR = "."


class FileState(Enum):
    UNTRACKED = 1
    NEW = 2
    UNCHANGED = 3
    MODIFIED = 4
    DELETED = 5


#region Click

@click.group()
def cli():
    """Local Version Control System"""


@cli.command()
def init():
    """Initialize a new VCS repository"""
    _init(console_info=True)


@cli.command()
@click.argument('files', nargs=-1)
def add(files):
    """Add files to the staging area"""
    _add(files, console_info=True)


@cli.command()
def reset():
    """Reset the staging area"""
    _reset()


@cli.command()
@click.argument('message')
def commit(message):
    """Commit changes to the repository"""
    _commit(message, console_info=True)


@cli.command()
def log():
    """Display commit history"""
    _log()


@cli.command()
@click.argument('branch_name')
def branch(branch_name):
    """Create a new branch"""
    _branch(branch_name, console_info=True)


@cli.command()
@click.argument('branch_name')
def checkout(branch_name):
    """Switch to a different branch"""
    _checkout(branch_name, console_info=True)


#endregion

#region Base


def _init(console_info=False):
    """Initialize a new VCS repository"""
    if os.path.exists(MAIN_BRANCH):
        raise exceptions.RepositoryException("Repository has been already initialized")
    else:
        os.makedirs(BRANCHES_LOG, exist_ok=True)
        _create_branch("main", None, None)
        staging_area_obj = {
            "current_branch": "main",
            "staging_files": {
                "UNTRACKED": [],
                "NEW": [],
                "UNCHANGED": [],
                "MODIFIED": [],
                "DELETED": []
            }
        }
        gitignore_obj = {
            "START": [".", "_"],
            "FORMATS": [".md"],
            "FILES": ["cvs.py", "cvs_tests.py", "utils.py", "setup.py",
                      "requirements.txt", "exceptions.py"],
            "DIRECTORIES": ["venv"]
        }
        ut.write_json_file(STAGING_AREA, staging_area_obj)
        ut.write_json_file(GITIGNORE, gitignore_obj)

        staging_area_path = os.path.join(BRANCHES, "main", "staging_area.json")
        with open(staging_area_path, "w"):
            pass

        if console_info:
            click.echo("Repository was initialized\n")


def _add(files, console_info=False):
    """Add files to the staging area"""
    _check_repository_existence()
    staging_area = _update_staging_area()
    untracked = set(staging_area["staging_files"][FileState.UNTRACKED.name])

    files_to_add = []
    if len(files) == 1 and files[0] == ".":
        files_to_add = staging_area["staging_files"][FileState.UNTRACKED.name]
        untracked = set()
    else:
        for file in files:
            if file not in untracked:
                raise exceptions.AddException(f"There is no file '{file}'")
            files_to_add.append(file)
            untracked.remove(file)

    if not files_to_add and console_info:
        click.echo("There are not any files to add\n")

    staging_area["staging_files"][FileState.UNTRACKED.name] = list(untracked)
    staging_area["staging_files"][FileState.NEW.name] += files_to_add

    ut.write_json_file(STAGING_AREA, staging_area)
    if console_info:
        click.echo(f"Added {len(files_to_add)} file(s) to "
                   f"staging area: {', '.join(files_to_add)}\n")


def _reset(console_info=False):
    """Reset the staging area"""
    _check_repository_existence()
    staging_area = ut.read_json_file(STAGING_AREA)
    staging_files = staging_area["staging_files"]
    for key in staging_files.keys():
        staging_files[key] = []

    ut.write_json_file(STAGING_AREA, staging_area)
    if console_info:
        click.echo(f"Staging area was reset\n")


def _commit(message, console_info=False):
    """Commit changes to the repository"""
    _check_repository_existence()
    staging_area = _update_staging_area()
    staged_files_obj = ut.read_json_file(STAGING_AREA)
    if not staged_files_obj["staging_files"]:
        raise exceptions.CommitException(f"There are not any files in staging area")

    last_commit = _get_last_commit(staged_files_obj["current_branch"])
    commit_id = str(time.time() * 1000)[:13]

    prev_files = dict()
    parent_commit_id = None
    parent_commit_branch = None
    if last_commit:
        parent_commit_id = last_commit["id"]
        parent_commit_branch = last_commit["branch"]
        prev_files = last_commit['files']

    files_data = _get_files_for_commit(prev_files,
                                       staged_files_obj["staging_files"],
                                       staged_files_obj["current_branch"],
                                       commit_id)
    files_to_copy, deleted_files = files_data
    if deleted_files:
        new_staging_area = []
        for file in staged_files_obj["staging_files"]:
            if file not in deleted_files:
                new_staging_area.append(file)
        staged_files_obj["staging_files"] = new_staging_area

    if not files_to_copy:
        raise exceptions.CommitException(f"There are not any changes to commit")

    ut.write_json_file(STAGING_AREA, staged_files_obj)
    _create_commit(staged_files_obj["current_branch"], commit_id, message,
                   files_to_copy, parent_commit_id, parent_commit_branch)
    if console_info:
        click.echo(f"Changes were commited with message: {message}\n")


def _status():
    _check_repository_existence()
    staging_area = _update_staging_area()
    staging_files = staging_area["staging_files"]
    status_list = [f"Current branch is '{staging_area["current_branch"]}'\n"]
    for key, files in staging_files.items():
        if files:
            status_list.append(f"{key} FILES:\n")
            for file in files:
                status_list.append(f"- {file}\n")
    return status_list


def _log():
    """Display commit history"""
    _check_repository_existence()
    staging_area = _update_staging_area()

    click.echo("Commit History:")
    log_path = Path(BRANCHES_LOG)
    for branch_log_file in log_path.iterdir():
        p = os.path.join(BRANCHES_LOG, branch_log_file.name)
        branch_log_obj = ut.read_json_file(p)
        click.echo(f"- {branch_log_obj['branch']}")
        dummy = branch_log_obj['head']
        if not dummy:
            continue
        commits = branch_log_obj["commits"]
        while True:
            date = time.strptime(commits[dummy]["time"])
            str_date = f"{date.tm_mon:0>2}.{date.tm_mday:0>2}.{date.tm_year}"
            click.echo(f" - {str_date} {dummy} '{commits[dummy]["message"]}'")
            if commits[dummy]["parent_commit_branch"] != branch_log_file.stem:
                break
            dummy = commits[dummy]["parent_commit_id"]


def _branch(branch_name, console_info=False):
    """Create a new branch"""
    _check_repository_existence()
    staging_area = _update_staging_area()
    if os.path.exists(os.path.join(BRANCHES, branch_name)):
        raise exceptions.BranchException(
            f"You can't create branch with name '{branch_name}', because it already exists")

    staged_files_obj = ut.read_json_file(STAGING_AREA)
    last_commit = _get_last_commit(staged_files_obj["current_branch"])
    if not last_commit:
        raise exceptions.BranchException(f"`There are no commits on branch '{staged_files_obj["current_branch"]}'")

    _create_branch(branch_name, last_commit["branch"], last_commit["id"])
    staged_files_obj["current_branch"] = branch_name
    ut.write_json_file(STAGING_AREA, staged_files_obj)
    if console_info:
        click.echo(f"Branch '{branch_name}' was created\n")


def _checkout(branch_name, console_info=False):
    """Switch to a different branch"""
    _check_repository_existence()
    staging_area = _update_staging_area()

    branch_log_obj = os.path.join(BRANCHES_LOG, f"{branch_name}.json")
    if not os.path.exists(branch_log_obj):
        raise exceptions.CheckoutException(f"Branch '{branch_name}' does not exist.")

    staged_files_obj = ut.read_json_file(STAGING_AREA)
    if branch_name == staged_files_obj["current_branch"]:
        raise exceptions.CheckoutException(f"You are already on branch '{branch_name}'")

    ignores = ut.read_json_file(GITIGNORE)
    staged_files_obj["staging_files"] = []
    staged_files_obj["current_branch"] = branch_name
    ut.write_json_file(STAGING_AREA, staged_files_obj)
    ut.delete_files(".", ignores)
    last_commit = _get_last_commit(branch_name)
    ut.copy_files(".", [val[0] for key, val in last_commit["files"].items()])
    if console_info:
        click.echo(f"Switched to branch '{branch_name}'\n")


#endregion


def _check_repository_existence():
    if not os.path.exists(MAIN_BRANCH):
        raise exceptions.RepositoryException("There is no initialized repository")


def _update_staging_area():
    staging_area = ut.read_json_file(STAGING_AREA)
    ignore = ut.read_json_file(GITIGNORE)
    staging_files = staging_area["staging_files"]

    staging_files[FileState.UNTRACKED.name] = []
    added_files = set(staging_files[FileState.NEW.name])
    unchanged_files = set(staging_files[FileState.UNCHANGED.name])
    modified_files = set(staging_files[FileState.MODIFIED.name])
    deleted_files = set(staging_files[FileState.DELETED.name])

    new_added_files = set()
    new_unchanged_files = set()
    new_modified_files = set()

    for file in ut.get_files(CURRENT_DIR, ignore):
        if file in added_files:
            new_added_files.add(file)
        elif file in unchanged_files:
            new_unchanged_files.add(file)
        elif file in modified_files:
            new_modified_files.add(file)
        else:
            staging_files[FileState.UNTRACKED.name].append(file)

    for file in added_files.difference(new_added_files):
        if file in deleted_files:
            deleted_files.remove(file)
    for file in unchanged_files.difference(new_unchanged_files):
        deleted_files.add(file)
    for file in modified_files.difference(new_modified_files):
        deleted_files.add(file)

    staging_files[FileState.DELETED.name] = list(deleted_files)
    staging_files[FileState.NEW.name] = list(new_added_files)
    staging_files[FileState.UNCHANGED.name] = list(new_unchanged_files)
    staging_files[FileState.MODIFIED.name] = list(new_modified_files)

    _update_changes(staging_area)
    ut.write_json_file(STAGING_AREA, staging_area)
    return staging_area


def _update_changes(staging_area=None):
    if not staging_area:
        staging_area = ut.read_json_file(STAGING_AREA)
    staging_files = staging_area["staging_files"]
    prev_commit = _get_last_commit(staging_area["current_branch"])
    if not prev_commit:
        return

    prev_files = prev_commit["files"]
    new_unchanged_files = set()
    new_modified_files = set()

    for file in staging_files[FileState.UNCHANGED.name]:
        new_hash = ut.get_file_hash(file)
        if new_hash != prev_files[file][1]:
            new_modified_files.add(file)
        else:
            new_unchanged_files.add(file)

    for file in staging_files[FileState.MODIFIED.name]:
        new_hash = ut.get_file_hash(file)
        if new_hash != prev_files[file][1]:
            new_modified_files.add(file)
        else:
            new_unchanged_files.add(file)


def _create_branch(name, parent_branch, parent_commit_id):
    branch_path = os.path.join(BRANCHES, name)
    staging_area_path = os.path.join(branch_path, "staging_area.json")
    branch_log_obj = {
        "branch": name,
        "parent_branch": parent_branch,
        "parent_commit_id": parent_commit_id,
        "staging_area": staging_area_path,
        "head": None,
        "commits": dict()
    }
    branch_log_path = os.path.join(BRANCHES_LOG, f"{name}.json")
    ut.write_json_file(branch_log_path, branch_log_obj)
    os.makedirs(branch_path, exist_ok=True)
    with open(staging_area_path, "w"):
        pass
    # TODO: обновить staging_area текущей ветки


def _create_commit(branch_name, commit_id, message, files: dict,
                   parent_commit_id=None, parent_commit_branch=None):
    branch_log_path = os.path.join(BRANCHES_LOG, f"{branch_name}.json")
    branch_log_obj = ut.read_json_file(branch_log_path)
    commit_info_obj = {
        "time": time.ctime(),
        "parent_commit_branch": parent_commit_branch,
        "parent_commit_id": parent_commit_id,
        "branch": branch_name,
        "id": commit_id,
        "message": message,
        "files": files
    }
    branch_log_obj["commits"][commit_id] = commit_info_obj
    branch_log_obj["head"] = commit_id
    ut.write_json_file(branch_log_path, branch_log_obj)
    commit_path = os.path.join(BRANCHES, branch_name, commit_id)
    files_to_copy = [file for file, data in files.items()
                     if Path(data[0]).parts[-2] == commit_id]
    if files_to_copy:
        os.makedirs(commit_path, exist_ok=True)
        ut.copy_files(commit_path, files_to_copy)


def _get_files_for_commit(prev_files, staged_files,
                          current_branch, commit_id):
    files_to_copy = dict()
    if prev_files:
        prev_files = {file: data for file, data in prev_files.items()
                      if os.path.exists(file)}
    deleted_files = {}
    count_of_new_changes = 0
    for file in staged_files:
        if not os.path.exists(file):
            deleted_files.add(file)
            continue
        file_hash = ut.get_file_hash(file)
        file_path = os.path.join(BRANCHES, current_branch,
                                 commit_id, Path(file).name)
        if file in prev_files.keys() and file_hash == prev_files[file][1]:
            files_to_copy[file] = prev_files[file]
        else:
            files_to_copy[file] = [file_path, file_hash]
            count_of_new_changes += 1
    if count_of_new_changes == 0:
        return dict(), deleted_files

    for file, file_data in prev_files.items():
        if file not in files_to_copy.keys():
            files_to_copy[file] = file_data

    return files_to_copy, deleted_files


def _try_get_parent_commit(current_branch):
    branch_log_path = os.path.join(BRANCHES_LOG, f"{current_branch}.json")
    branch_log_obj = ut.read_json_file(branch_log_path)
    if branch_log_obj["head"]:
        parent_branch = branch_log_obj["commits"][branch_log_obj["head"]]["parent_commit_branch"]
        parent_commit = branch_log_obj["commits"][branch_log_obj["head"]]["parent_commit_id"]
        branch_log_path = os.path.join(BRANCHES_LOG, f"{parent_branch}.json")
        branch_log_obj = ut.read_json_file(branch_log_path)
        if parent_commit in branch_log_obj["commits"].keys:
            return branch_log_obj["commits"][parent_commit]
    elif branch_log_obj["parent_branch"] and branch_log_obj["parent_commit_id"]:
        parent_branch = branch_log_obj["parent_branch"]
        parent_commit = branch_log_obj["parent_commit_id"]
        branch_log_path = os.path.join(BRANCHES_LOG, f"{parent_branch}.json")
        branch_log_obj = ut.read_json_file(branch_log_path)
        if parent_commit in branch_log_obj["commits"].keys:
            return branch_log_obj["commits"][parent_commit]
    return None


def _get_last_commit(current_branch):
    branch_log_path = os.path.join(BRANCHES_LOG, f"{current_branch}.json")
    branch_log_obj = ut.read_json_file(branch_log_path)
    if (branch_log_obj["head"] and
            branch_log_obj["head"] in branch_log_obj["commits"].keys()):
        return branch_log_obj["commits"][branch_log_obj["head"]]
    elif branch_log_obj["parent_branch"] and branch_log_obj["parent_commit_id"]:
        parent_commit = branch_log_obj["parent_commit_id"]
        branch_log_path = os.path.join(BRANCHES_LOG, f"{branch_log_obj["parent_branch"]}.json")
        branch_log_obj = ut.read_json_file(branch_log_path)
        if parent_commit in branch_log_obj["commits"].keys():
            return branch_log_obj["commits"][parent_commit]
    return None


if __name__ == "__main__":
    # cli()
    _init()
    print("".join(_status()))
    _add(["1.txt", "2.txt"], True)
    print("".join(_status()))
    _add(["."], True)
    print("".join(_status()))


