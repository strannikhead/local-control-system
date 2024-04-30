import os
import click
from utils import _write_to_file, _clear_file, _copy_files

# Define constants for directories
STAGING_AREA = ".cvs/staging_area.txt"
BRANCHES_DIR = ".cvs/branches"
MAIN_BRANCH = ".cvs/branches/main"
CURRENT_DIR = "./"

@click.group()
def cli():
    """Local Version Control System"""


@cli.command()
def init():
    """Initialize a new VCS repository"""
    ignoreics = open('icsignore.txt', 'x')


    if os.path.exists(MAIN_BRANCH):
        click.echo("Repository has been already initialized")
    else:
        os.makedirs(MAIN_BRANCH, exist_ok=True)
        with open(STAGING_AREA, 'w+') as f:
            f.write(MAIN_BRANCH + "\n")
        click.echo("Initializing CVS repository...")


@cli.command()
@click.argument('files', nargs=-1)
def add(files):
    """Add files to the staging area"""
    # TODO: сверяться с gitignore
    if not check_repository_existence() or not check_staging_area_existence():
        return
    for file in files:
        if not os.path.exists(file):
            raise ValueError(f"There is no file {file}")

    _write_to_file(STAGING_AREA, *files)
    click.echo(f"Adding {len(files)} file(s) to staging area: {', '.join(files)}")


@cli.command()
def reset():
    """Reset the staging area"""
    if not check_repository_existence() or not check_staging_area_existence():
        return
    _clear_file(STAGING_AREA, get_branch_path())
    click.echo("Resetting staging area...")


@cli.command()
@click.argument('message')
def commit(message):
    """Commit changes to the repository"""
    if not check_repository_existence() or not check_staging_area_existence():
        return

    branch_path = get_branch_path()
    if not branch_path:
        click.echo("Switch to the branch you need to commit")
        return



    _copy_files("", branch_path)
    _clear_file(STAGING_AREA, branch_path)
    click.echo(f"Committing changes with message: {message}")


@cli.command()
def log():
    """Display commit history"""
    commit_hashes = os.listdir(BRANCHES_DIR)
    if not commit_hashes:
        click.echo("No commits yet.")
        return

    click.echo("Commit History:")
    for commit_hash in commit_hashes:
        click.echo(f"- {commit_hash}")


@cli.command()
@click.argument('branch_name')
def branch(branch_name):
    """Create a new branch"""
    # Create a directory for the branch
    branch_dir = os.path.join(".vcs/branches", branch_name)
    os.makedirs(branch_dir, exist_ok=True)
    click.echo(f"Creating new branch: {branch_name}")


@cli.command()
@click.argument('branch_name')
def checkout(branch_name):
    """Switch to a different branch"""
    branch_dir = os.path.join(".vcs/branches", branch_name)
    if not os.path.exists(branch_dir):
        click.echo(f"Branch '{branch_name}' does not exist.")
        return

    # Implement checkout logic here
    click.echo(f"Switching to branch: {branch_name}")


def check_repository_existence():
    if not os.path.exists(MAIN_BRANCH):
        click.echo("There is no initialized repository")
        return False
    return True


def check_staging_area_existence():
    if not os.path.exists(STAGING_AREA):
        click.echo("Switch to the branch you need to commit")
        return False
    return True


def get_branch_path():
    with open(STAGING_AREA, "r") as file:
        branch_name = file.readline().split()
    if len(branch_name) == 2 and branch_name[0] == "branch_name":
        return branch_name[1]
    return None


def get_staged_file_paths():
    with open(STAGING_AREA, "r") as file:
        branch_name = file.readline().split()
    if len(branch_name) == 2 and branch_name[0] == "file":
        return branch_name[1]
    return None



if __name__ == "__main__":
    cli()
