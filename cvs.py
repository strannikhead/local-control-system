import os
import time
import click
from pathlib import Path
from enum import Enum
from utils import _copy_files, _delete_files, _write_json_file, _read_json_file, _get_all_files, _get_file_hash


MAIN_BRANCH = ".cvs/branches/main"
BRANCHES = ".cvs/branches"
BRANCHES_LOG = ".cvs/branches_log"
STAGING_AREA = ".cvs/staging_area.json"
GITIGNORE = ".cvs/cvsignore.json"
CURRENT_DIR = os.getcwd()


class FileState(Enum):
    Added = 1
    Modified = 2
    Deleted = 3


@click.group()
def cli():
    """Local Version Control System"""


@cli.command()
def init():
    """Initialize a new VCS repository"""
    _init()


@cli.command()
@click.argument('files', nargs=-1)
def add(files):
    """Add files to the staging area"""
    _add(files)


@cli.command()
def reset():
    """Reset the staging area"""
    _reset()


@cli.command()
@click.argument('message')
def commit(message):
    """Commit changes to the repository"""
    _commit(message)


@cli.command()
def log():
    """Display commit history"""
    _log()


@cli.command()
@click.argument('branch_name')
def branch(branch_name):
    """Create a new branch"""
    _branch(branch_name)


@cli.command()
@click.argument('branch_name')
def checkout(branch_name):
    """Switch to a different branch"""
    _checkout(branch_name)


def _init():
    """Initialize a new VCS repository"""
    if os.path.exists(MAIN_BRANCH):
        click.echo("Repository has been already initialized")
    else:
        os.makedirs(BRANCHES_LOG, exist_ok=True)
        _create_branch("main", None, None)
        staging_area_obj = {
            "current_branch": "main",
            "staging_files": []
        }
        _write_json_file(STAGING_AREA, staging_area_obj)
        _write_json_file(GITIGNORE, [".", "_", "cvs.py", "cvs_tests.py",
                                     "utils.py", "setup.py", "README.md",
                                     "requirements.txt"])
        click.echo("Initializing CVS repository...")


def _add(files):
    """Add files to the staging area"""
    if not _check_repository_existence():
        return
    # TODO: обновлять информацию о staging_area
    ignores = _read_json_file(GITIGNORE)
    staged_files_obj = _read_json_file(STAGING_AREA)
    staged_files = set(staged_files_obj["staging_files"])
    files_to_add = []
    if not _try_get_files_for_add(files_to_add, files, ignores, staged_files):
        return
    if not files_to_add:
        return
    staged_files_obj["staging_files"] += files_to_add
    _write_json_file(STAGING_AREA, staged_files_obj)
    click.echo(f"Added {len(files_to_add)} file(s) to staging area: {', '.join(files_to_add)}")


def _reset():
    """Reset the staging area"""
    if not _check_repository_existence():
        return
    staged_files_obj = _read_json_file(STAGING_AREA)
    staged_files_obj["staging_files"] = []
    _write_json_file(STAGING_AREA, staged_files_obj)
    click.echo(f"Reset staging area")


def _commit(message):
    """Commit changes to the repository"""
    if not _check_repository_existence():
        return
    staged_files_obj = _read_json_file(STAGING_AREA)
    if not staged_files_obj["staging_files"]:
        click.echo(f"There are not any files in staging area")
        return
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
        click.echo(f"There are not any changes to commit")
        return

    _write_json_file(STAGING_AREA, staged_files_obj)
    _create_commit(staged_files_obj["current_branch"], commit_id, message,
                   files_to_copy, parent_commit_id, parent_commit_branch)
    click.echo(f"Changes were commited with message: {message}")


def _log():
    """Display commit history"""
    if not _check_repository_existence():
        return
    click.echo("Commit History:")
    log_path = Path(BRANCHES_LOG)
    for branch_log_file in log_path.iterdir():
        p = os.path.join(BRANCHES_LOG, branch_log_file.name)
        branch_log_obj = _read_json_file(p)
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


def _branch(branch_name):
    """Create a new branch"""
    if not _check_repository_existence():
        return
    if os.path.exists(os.path.join(BRANCHES, branch_name)):
        click.echo(f"You can't create branch with name '{branch_name}', because it already exists")
        return
    staged_files_obj = _read_json_file(STAGING_AREA)
    last_commit = _get_last_commit(staged_files_obj["current_branch"])
    if not last_commit:
        click.echo(f"`There are no commits on branch '{staged_files_obj["current_branch"]}'")
        return
    _create_branch(branch_name, last_commit["branch"], last_commit["id"])
    staged_files_obj["current_branch"] = branch_name
    _write_json_file(STAGING_AREA, staged_files_obj)
    click.echo(f"Creating new branch: {branch_name}...")


def _checkout(branch_name):
    """Switch to a different branch"""
    if not _check_repository_existence():
        return
    branch_log_obj = os.path.join(BRANCHES_LOG, f"{branch_name}.json")
    if not os.path.exists(branch_log_obj):
        click.echo(f"Branch '{branch_name}' does not exist.")
        return
    staged_files_obj = _read_json_file(STAGING_AREA)
    if branch_name == staged_files_obj["current_branch"]:
        click.echo(f"You are already on branch '{branch_name}'")
        return
    ignores = _read_json_file(GITIGNORE)
    staged_files_obj["staging_files"] = []
    staged_files_obj["current_branch"] = branch_name
    _write_json_file(STAGING_AREA, staged_files_obj)
    _delete_files(".", ignores)
    last_commit = _get_last_commit(branch_name)
    _copy_files(".", [val[0] for key, val in last_commit["files"].items()])
    click.echo(f"Switching to branch: {branch_name}")


def _check_repository_existence():
    if not os.path.exists(MAIN_BRANCH):
        click.echo("There is no initialized repository")
        return False
    return True


def _create_branch(name, parent_branch, parent_commit_id):
    branch_log_obj = {
        "branch": name,
        "parent_branch": parent_branch,
        "parent_commit_id": parent_commit_id,
        "head": None,
        "commits": dict()
    }
    branch_path = os.path.join(BRANCHES, name)
    branch_log_path = os.path.join(BRANCHES_LOG, f"{name}.json")
    _write_json_file(branch_log_path, branch_log_obj)
    os.makedirs(branch_path, exist_ok=True)


def _create_commit(branch_name, commit_id, message, files: dict,
                   parent_commit_id=None, parent_commit_branch=None):
    branch_log_path = os.path.join(BRANCHES_LOG, f"{branch_name}.json")
    branch_log_obj = _read_json_file(branch_log_path)
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
    _write_json_file(branch_log_path, branch_log_obj)
    commit_path = os.path.join(BRANCHES, branch_name, commit_id)
    files_to_copy = [file for file, data in files.items()
                     if Path(data[0]).parts[-2] == commit_id]
    if files_to_copy:
        os.makedirs(commit_path, exist_ok=True)
        _copy_files(commit_path, files_to_copy)


def _try_get_files_for_add(answer, files, ignores, staged_files):
    not_found = []
    if len(files) == 1 and files[0] == "*":
        answer += _get_all_files('', ignores, staged_files)
    else:
        for i, file in enumerate(files):
            p = Path(file)
            cur_dir = Path(CURRENT_DIR)
            if p.is_absolute() and any(p.parts[i] != cur_dir.parts[i] for i in range(len(cur_dir.parts))):
                click.echo(f"There is no file '{file}'")
                return False
            elif p.is_absolute():
                files[i] = file = os.path.join(*p.parts[len(cur_dir.parts):])
            if any(file.startswith(i) for i in ignores):
                continue
            if p.is_dir() or not p.exists():
                not_found.append(file)
                continue

            if file not in staged_files:
                answer.append(file)
    if not_found:
        click.echo(f"There is no files : {', '.join(not_found)}")
    return True


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
        file_hash = _get_file_hash(file)
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
    branch_log_obj = _read_json_file(branch_log_path)
    if branch_log_obj["head"]:
        parent_branch = branch_log_obj["commits"][branch_log_obj["head"]]["parent_commit_branch"]
        parent_commit = branch_log_obj["commits"][branch_log_obj["head"]]["parent_commit_id"]
        branch_log_path = os.path.join(BRANCHES_LOG, f"{parent_branch}.json")
        branch_log_obj = _read_json_file(branch_log_path)
        if parent_commit in branch_log_obj["commits"].keys:
            return branch_log_obj["commits"][parent_commit]
    elif branch_log_obj["parent_branch"] and branch_log_obj["parent_commit_id"]:
        parent_branch = branch_log_obj["parent_branch"]
        parent_commit = branch_log_obj["parent_commit_id"]
        branch_log_path = os.path.join(BRANCHES_LOG, f"{parent_branch}.json")
        branch_log_obj = _read_json_file(branch_log_path)
        if parent_commit in branch_log_obj["commits"].keys:
            return branch_log_obj["commits"][parent_commit]
    return None


def _get_last_commit(current_branch):
    branch_log_path = os.path.join(BRANCHES_LOG, f"{current_branch}.json")
    branch_log_obj = _read_json_file(branch_log_path)
    if (branch_log_obj["head"] and
            branch_log_obj["head"] in branch_log_obj["commits"].keys()):
        return branch_log_obj["commits"][branch_log_obj["head"]]
    elif branch_log_obj["parent_branch"] and branch_log_obj["parent_commit_id"]:
        parent_commit = branch_log_obj["parent_commit_id"]
        branch_log_path = os.path.join(BRANCHES_LOG, f"{branch_log_obj["parent_branch"]}.json")
        branch_log_obj = _read_json_file(branch_log_path)
        if parent_commit in branch_log_obj["commits"].keys():
            return branch_log_obj["commits"][parent_commit]
    return None


if __name__ == "__main__":
    cli()
