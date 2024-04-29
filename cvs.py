import os
import click
from utils import write_to_file, clear_file, copy_files

# Define constants for directories
STAGING_AREA = ".cvs/staging_area.txt"
BRANCHES_DIR = ".cvs/branches"
MAIN_BRANCH = ".cvs/branches/main"


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
            f.write(MAIN_BRANCH + "\n")
        click.echo("Initializing VCS repository...")


@cli.command()
@click.argument('files', nargs=-1)
def add(files):
    """Add files to the staging area"""
    if not os.path.exists(MAIN_BRANCH):
        click.echo("There is no initialized repository")
        return
    if not os.path.exists(STAGING_AREA):
        click.echo("Switch to the branch you need to commit")
        return
    for file in files:
        if not os.path.exists(file):  # нужно проверять, наличие файла в репозитории, а file - это просто имя файла
            raise ValueError(f"There is no file {file}")

    write_to_file(STAGING_AREA, *files)
    click.echo(f"Adding {len(files)} file(s) to staging area: {', '.join(files)}")


@cli.command()
def reset():
    """Reset the staging area"""
    if not os.path.exists(MAIN_BRANCH):
        click.echo("There is no initialized repository")
        return
    if not os.path.exists(STAGING_AREA):
        click.echo("Switch to the branch you need to commit")
        return
    clear_file(STAGING_AREA)
    click.echo("Resetting staging area...")


@cli.command()
@click.argument('message')
def commit(message):
    """Commit changes to the repository"""
    if not os.listdir(STAGING_AREA):
        click.echo("Nothing to commit. Staging area is empty.")
        return

    commit_changes(STAGING_AREA, BRANCHES_DIR, message)
    reset_staging_area(STAGING_AREA)
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


if __name__ == "__main__":
    cli()

