import os
import time
import click
from pathlib import Path
from utils import _copy_files, _delete_files, _write_json_file, _read_json_file, _get_all_files, _get_file_hash

MAIN_BRANCH = ".cvs/branches/main"
BRANCHES = ".cvs/branches"
BRANCHES_LOG = ".cvs/branches_log"
STAGING_AREA = ".cvs/staging_area.json"
GITIGNORE = ".cvs/cvsignore.json"
CURRENT_DIR = os.getcwd()


@click.group()
def cli():
    """Local Version Control System"""


@cli.command()
def init():
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
        _write_json_file(GITIGNORE, [".", "_"])
        click.echo("Initializing CVS repository...")


@cli.command()
@click.argument('files', nargs=-1)
def add(files):
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


@cli.command()
def reset():
    """Reset the staging area"""
    if not _check_repository_existence():
        return
    staged_files_obj = _read_json_file(STAGING_AREA)
    staged_files_obj["staging_files"] = []
    _write_json_file(STAGING_AREA, staged_files_obj)
    click.echo(f"Reset staging area")


@cli.command()
@click.argument('message')
def commit(message):
    """Commit changes to the repository"""
    if not _check_repository_existence():
        return
    staged_files_obj = _read_json_file(STAGING_AREA)
    last_commit = _get_last_commit(staged_files_obj["current_branch"])
    commit_id = str(time.time() * 1000)[:13]

    prev_files = dict()
    parent_commit_id = None
    parent_commit_branch = None
    if last_commit:
        parent_commit_id = last_commit["parent_commit_id"]
        parent_commit_branch = last_commit["parent_commit_branch"]
        prev_files = last_commit['files']

    files_to_copy = _get_files_for_commit(prev_files,
                                          staged_files_obj["staging_files"],
                                          staged_files_obj["current_branch"],
                                          commit_id)

    _create_commit(staged_files_obj["current_branch"], commit_id, message,
                   files_to_copy, parent_commit_id, parent_commit_branch)
    click.echo(f"Changes were commited with message: {message}")


# @cli.command()
# def log():
#     """Display commit history"""
#     branches = os.listdir(BRANCHES_DIR)
#     if not branches:
#         click.echo("No commits yet.")
#         return
#
#     click.echo("Commit History:")
#     for br in branches:
#         click.echo(f"- {br}")
#         branch_path = os.path.join(BRANCHES_DIR, br)
#         for com in os.listdir(branch_path):
#             click.echo(f"  - {com}")


@cli.command()
@click.argument('branch_name')
def branch(branch_name):
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
    _create_branch(branch_name, last_commit["parent_commit_branch"], last_commit["parent_commit_id"])
    click.echo(f"Creating new branch: {branch_name}...")


# @cli.command()
# @click.argument('branch_name')
# def checkout(branch_name):
#     """Switch to a different branch"""
#     branch_path = os.path.join(BRANCHES_DIR, branch_name)
#     if not os.path.exists(branch_path):
#         click.echo(f"Branch '{branch_name}' does not exist.")
#         return
#     ignore = set(_parse_ics_ignore())
#     _delete_files(CURRENT_DIR, ignore)
#     last_commit = os.listdir(branch_path)[-1]
#     last_commit_path = os.path.join(branch_path, last_commit)
#     _copy_files(last_commit_path, CURRENT_DIR)
#     _clear_file(STAGING_AREA, "branch " + branch_path)
#     click.echo(f"Switching to branch: {branch_name}")


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
    _write_json_file(branch_log_path, branch_log_obj)
    commit_path = os.path.join(BRANCHES, branch_name, commit_id)
    os.makedirs(commit_path, exist_ok=True)
    _copy_files(commit_path, files.keys())


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
        prev_files = {file: data for file, data in prev_files.items
                      if os.path.exists(file)}

    for file in staged_files:
        if not os.path.exists(file):
            continue
        file_hash = _get_file_hash(file)
        file_path = os.path.join(BRANCHES, current_branch,
                                 commit_id, Path(file).name)
        if file in prev_files.keys() and file_hash == prev_files[file][1]:
            files_to_copy[file] = prev_files[file]
        else:
            files_to_copy[file] = [file_path, file_hash]

    for file, file_data in prev_files.items():
        if file not in files_to_copy.keys():
            files_to_copy[file] = file_data

    return files_to_copy


def _try_get_parent_commit(current_branch):
    branch_log_path = os.path.join(BRANCHES_LOG, current_branch)
    branch_log_obj = _read_json_file(branch_log_path)
    if branch_log_obj["head"]:
        parent_branch = branch_log_obj["commits"][branch_log_obj["head"]]["parent_commit_branch"]
        parent_commit = branch_log_obj["commits"][branch_log_obj["head"]]["parent_commit_id"]
        branch_log_path = os.path.join(BRANCHES_LOG, parent_branch)
        branch_log_obj = _read_json_file(branch_log_path)
        if parent_commit in branch_log_obj["commits"].keys:
            return branch_log_obj["commits"][parent_commit]
    elif branch_log_obj["parent_branch"] and branch_log_obj["parent_commit_id"]:
        parent_branch = branch_log_obj["parent_branch"]
        parent_commit = branch_log_obj["parent_commit_id"]
        branch_log_path = os.path.join(BRANCHES_LOG, parent_branch)
        branch_log_obj = _read_json_file(branch_log_path)
        if parent_commit in branch_log_obj["commits"].keys:
            return branch_log_obj["commits"][parent_commit]
    return None


def _get_last_commit(current_branch):
    branch_log_path = os.path.join(BRANCHES_LOG, current_branch)
    branch_log_obj = _read_json_file(branch_log_path)
    if branch_log_obj["head"] and branch_log_obj["head"] in branch_log_obj["commits"].keys:
        return branch_log_obj["commits"][branch_log_obj["head"]]
    elif branch_log_obj["parent_branch"] and branch_log_obj["parent_commit_id"]:
        parent_commit = branch_log_obj["parent_commit_id"]
        branch_log_path = os.path.join(BRANCHES_LOG, branch_log_obj["parent_branch"])
        branch_log_obj = _read_json_file(branch_log_path)
        if parent_commit in branch_log_obj["commits"].keys:
            return branch_log_obj["commits"][parent_commit]
    return None


if __name__ == "__main__":
    cli()
