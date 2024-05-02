import os
import time
import click
from utils import _write_to_file, _clear_file, _copy_files, _delete_files

# Define constants for directories
STAGING_AREA = ".cvs/staging_area.txt"
BRANCHES_DIR = ".cvs/branches"
MAIN_BRANCH = ".cvs/branches/main"
CURRENT_DIR = os.getcwd()
GITIGNORE = ".cvs/icsignore.txt"
gitignore_files = [".", "_", "cvs.py", "cvs_tests.py", "utils.py"]

@click.group()
def cli():
    """Local Version Control System"""


@cli.command()
def init():
    """Initialize a new VCS repository"""
    if os.path.exists(MAIN_BRANCH):
        click.echo("Repository has been already initialized")
    else:
        os.makedirs(MAIN_BRANCH, exist_ok=True)
        with open(STAGING_AREA, 'w+') as f:
            f.write("branch " + MAIN_BRANCH + "\n")
        with open(GITIGNORE, 'w+') as f:
            for file in gitignore_files:
                f.write(file + "\n")
        click.echo("Initializing CVS repository...")


@cli.command()
@click.argument('files', nargs=-1)
def add(files):
    """Add files to the staging area"""
    # TODO: на тесте проверит папку, игнор, добавление существующего и несуществующего файла
    ignores = set(_parse_ics_ignore())
    staged_files = set(_get_staged_file_paths())
    if not _check_repository_existence() or not _check_staging_area_existence():
        return
    for file in files:
        if any(file.startswith(i) for i in ignores):
            click.echo(f"You can't add file '{file}' to staging area, because it is ignored")
            return
        if os.path.isdir(file):
            click.echo(f"You can't add folder ({file}) to staging area")
            return
        if not os.path.exists(file):
            click.echo(f"There is no file '{file}'")
            return
        if file in staged_files:
            click.echo(f"File '{file}' is already in staging area")
            return
    try:
        _write_to_file(STAGING_AREA, "file ", *files)
        click.echo(f"Adding {len(files)} file(s) to staging area: {', '.join(files)}")
    except Exception as e:
        click.echo(e)


@cli.command()
def reset():
    """Reset the staging area"""
    if not _check_repository_existence() or not _check_staging_area_existence():
        return
    _clear_file(STAGING_AREA, "branch " + _get_branch_path())
    click.echo("Resetting staging area...")


@cli.command()
@click.argument('message')
def commit(message):
    """Commit changes to the repository"""
    if not _check_repository_existence() or not _check_staging_area_existence():
        return
    branch_path = _get_branch_path()
    if not branch_path:
        click.echo("Switch to the branch you need to commit")
        return
    staged_files = set(_get_staged_file_paths())
    if not staged_files:
        click.echo("There is nothing to commit")
        return


    commits = os.listdir(branch_path)
    commit_path = os.path.join(branch_path, str(time.time() * 1000)[:13])
    commit_info_path = os.path.join(commit_path, "commit_info.txt")
    _copy_files("", commit_path, *staged_files)

    if commits:
        last_commit = commits[-1]
        last_commit_path = os.path.join(branch_path, last_commit)
        last_commit_files = set(os.listdir(last_commit_path))
        last_commit_files.remove("commit_info.txt")
        unstaged_files = last_commit_files.difference(staged_files)
        if unstaged_files:
            _copy_files(last_commit_path, commit_path, *unstaged_files)

    with open(commit_info_path, "w+", encoding="UTF-8") as f:
        f.write(message)
    _clear_file(STAGING_AREA, "branch " + branch_path)
    click.echo(f"Committing changes with message: {message}")


@cli.command()
def log():
    """Display commit history"""
    branches = os.listdir(BRANCHES_DIR)
    if not branches:
        click.echo("No commits yet.")
        return

    click.echo("Commit History:")
    for br in branches:
        click.echo(f"- {br}")
        branch_path = os.path.join(BRANCHES_DIR, br)
        for com in os.listdir(branch_path):
            click.echo(f"  - {com}")


@cli.command()
@click.argument('branch_name')
def branch(branch_name):
    """Create a new branch"""
    branch_path = os.path.join(BRANCHES_DIR, branch_name)
    if os.path.exists(branch_path):
        click.echo(f"You can't create branch with name '{branch_name}', because it already exists")
        return
    current_branch_path = _get_branch_path()

    if len(os.listdir(current_branch_path)) == 0:
        click.echo(f"`There are no commits on branch '{current_branch_path}'")
        return

    _copy_files(current_branch_path, branch_path)
    _clear_file(STAGING_AREA, "branch " + branch_path)
    click.echo(f"Creating new branch: {branch_name}...")


@cli.command()
@click.argument('branch_name')
def checkout(branch_name):
    """Switch to a different branch"""
    branch_path = os.path.join(BRANCHES_DIR, branch_name)
    if not os.path.exists(branch_path):
        click.echo(f"Branch '{branch_name}' does not exist.")
        return
    _delete_files(CURRENT_DIR)
    last_commit = os.listdir(branch_path)[-1]
    last_commit_path = os.path.join(branch_path, last_commit)
    _copy_files(last_commit_path, CURRENT_DIR)
    _clear_file(STAGING_AREA, "branch " + branch_path)
    click.echo(f"Switching to branch: {branch_name}")


def _check_repository_existence():
    if not os.path.exists(MAIN_BRANCH):
        click.echo("There is no initialized repository")
        return False
    return True


def _check_staging_area_existence():
    if not os.path.exists(STAGING_AREA):
        click.echo("Switch to the branch you need to commit")
        return False
    return True


def _get_branch_path():
    with open(STAGING_AREA, "r") as file:
        branch_name = file.readline().split()
    if len(branch_name) == 2 and branch_name[0] == "branch":
        return branch_name[1]
    return ""


def _get_staged_file_paths():
    paths = []
    with open(STAGING_AREA, "r") as file:
        for line in file:
            data = line.split()
            if len(data) == 2 and data[0] == "file":
                paths.append(data[1])
    return paths


def _parse_ics_ignore():
    ignores = list()
    with open(GITIGNORE, 'r') as file:
        for line in file:
            ignores.append(line.strip())
    return ignores


if __name__ == "__main__":
    cli()