import os
import subprocess
import pytest


@pytest.fixture
def vcs_initialized(tmp_path):
    # Initialize a VCS repository
    subprocess.run(['python', 'vcs.py', 'init'], cwd=tmp_path)
    return tmp_path


def test_init(vcs_initialized):
    # Check if the .vcs directory is created
    assert os.path.isdir(os.path.join(vcs_initialized, ".vcs"))


def test_add_commit_reset(vcs_initialized):
    # Create test files
    test_file1 = os.path.join(vcs_initialized, "test_file1.txt")
    test_file2 = os.path.join(vcs_initialized, "test_file2.txt")
    with open(test_file1, 'w') as f:
        f.write("Test file 1 content")
    with open(test_file2, 'w') as f:
        f.write("Test file 2 content")

    # Add files to staging area
    subprocess.run(['python', 'vcs.py', 'add', 'test_file1.txt', 'test_file2.txt'], cwd=vcs_initialized)
    assert os.path.isfile(os.path.join(vcs_initialized, ".vcs/staging_area/file_list.txt"))

    # Commit changes
    subprocess.run(['python', 'vcs.py', 'commit', 'Initial commit'], cwd=vcs_initialized)
    assert os.listdir(os.path.join(vcs_initialized, ".vcs/commits"))

    # Reset staging area
    subprocess.run(['python', 'vcs.py', 'reset'], cwd=vcs_initialized)
    assert not os.listdir(os.path.join(vcs_initialized, ".vcs/staging_area"))


def test_log(vcs_initialized):
    # Check log when no commits exist
    result = subprocess.run(['python', 'vcs.py', 'log'], cwd=vcs_initialized, capture_output=True, text=True)
    assert "No commits yet." in result.stdout

    # Commit changes
    subprocess.run(['python', 'vcs.py', 'commit', 'Initial commit'], cwd=vcs_initialized)

    # Check log after commit
    result = subprocess.run(['python', 'vcs.py', 'log'], cwd=vcs_initialized, capture_output=True, text=True)
    assert "Commit History" in result.stdout


def test_branch_checkout(vcs_initialized):
    # Create a new branch
    subprocess.run(['python', 'vcs.py', 'branch', 'new_branch'], cwd=vcs_initialized)
    assert os.path.isdir(os.path.join(vcs_initialized, ".vcs/branches/new_branch"))

    # Switch to the new branch
    subprocess.run(['python', 'vcs.py', 'checkout', 'new_branch'], cwd=vcs_initialized)
    # Implement further checks for branch checkout as needed
