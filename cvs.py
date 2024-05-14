import os
import time
import click
from pathlib import Path
from utils import _copy_files, _delete_files, _write_json_file, _read_json_file, _get_all_files

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
    if not _try_get_files(files_to_add, files, ignores, staged_files):
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
    # TODO: обновлять информацию о staging_area
    staged_files_obj = _read_json_file(STAGING_AREA)
    if (not staged_files_obj["staging_files"]["add"] and not staged_files_obj["staging_files"]["modified"]
            and not staged_files_obj["staging_files"]["deleted"]):
        click.echo("There is nothing to commit")
        return
    branch_path = os.path.join(BRANCHES, staged_files_obj["current_branch"])
    branch_log_path = os.path.join(BRANCHES_LOG, staged_files_obj["current_branch"])
    branch_log_obj = _read_json_file(branch_log_path)
    #
    #
    #
    # branch_path = _get_branch_path()
    # if not branch_path:
    #     click.echo("Switch to the branch you need to commit")
    #     return
    # staged_files = set(_get_staged_file_paths())
    # if not staged_files:
    #     click.echo("There is nothing to commit")
    #     return
    #
    # commits = os.listdir(branch_path)
    # commit_path = os.path.join(branch_path, str(time.time() * 1000)[:13])
    # commit_info_path = os.path.join(commit_path, "commit_info.txt")
    # _copy_files("", commit_path, *staged_files)
    #
    # if commits:
    #     last_commit = commits[-1]
    #     last_commit_path = os.path.join(branch_path, last_commit)
    #     last_commit_files = set(os.listdir(last_commit_path))
    #     last_commit_files.remove("commit_info.txt")
    #     unstaged_files = last_commit_files.difference(staged_files)
    #     if unstaged_files:
    #         _copy_files(last_commit_path, commit_path, *unstaged_files)
    #
    # with open(commit_info_path, "w+", encoding="UTF-8") as f:
    #     f.write(message)
    # _clear_file(STAGING_AREA, "branch " + branch_path)
    # click.echo(f"Committing changes with message: {message}")


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
#
#
# @cli.command()
# @click.argument('branch_name')
# def branch(branch_name):
#     """Create a new branch"""
#     branch_path = os.path.join(BRANCHES_DIR, branch_name)
#     if os.path.exists(branch_path):
#         click.echo(f"You can't create branch with name '{branch_name}', because it already exists")
#         return
#     current_branch_path = _get_branch_path()
#
#     if len(os.listdir(current_branch_path)) == 0:
#         click.echo(f"`There are no commits on branch '{current_branch_path}'")
#         return
#
#     _copy_files(current_branch_path, branch_path)
#     _clear_file(STAGING_AREA, "branch " + branch_path)
#     click.echo(f"Creating new branch: {branch_name}...")
#
#
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
    branch_info_obj = {
        "branch": name,
        "parent_branch": parent_branch,
        "parent_commit_id": parent_commit_id,
        "head": None,
        "commits": dict()
    }
    branch_path = os.path.join(BRANCHES, name)
    branch_info_path = os.path.join(BRANCHES_LOG, f"{name}.json")
    _write_json_file(branch_info_path, branch_info_obj)
    os.makedirs(branch_path, exist_ok=True)


# def _create_commit(branch_name, commit_id, ):
#     branch_log_path = os.path.join(BRANCHES_LOG, staged_files_obj["current_branch"])
#     branch_log_obj = _read_json_file(branch_log_path)
#     branch_data = read_branch_file(branch_file)
#     branch_data["commits"].append(commit_data)
#     branch_data["current_commit"] = commit_data["commit_id"]
#     write_branch_file(branch_file, branch_data)


def _try_get_files(answer, files,  ignores, staged_files):
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


if __name__ == "__main__":
    cli()
