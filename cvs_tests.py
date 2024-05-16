import os
import shutil
import subprocess
import tempfile
import utils

import pytest
import cvs


@pytest.fixture
def temp_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_init_command(temp_dir, capsys):
    # Создаем временные файлы или папки, которые требуются для теста
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()

    result = subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)

    assert result.returncode == 0
    assert os.path.exists(os.path.join(temp_dir, '.cvs'))
    assert os.path.exists(os.path.join(temp_dir, cvs.MAIN_BRANCH))
    assert os.path.exists(os.path.join(temp_dir, cvs.BRANCHES))
    assert os.path.exists(os.path.join(temp_dir, cvs.BRANCHES_LOG))
    assert os.path.exists(os.path.join(temp_dir, cvs.STAGING_AREA))
    assert os.path.exists(os.path.join(temp_dir, cvs.GITIGNORE))
    assert 'Initializing CVS repository...' in result.stdout


def test_init_if_already_initialized(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    result = subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    assert "Repository has been already initialized" in result.stdout


def test_add(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    result = subprocess.run(['cvs', 'add', 'example_file.txt'], cwd=temp_dir, capture_output=True, text=True)
    test_for_json = ['"current_branch": "main"', '"staging_files":', 'example_file.txt'][::-1]
    with open(os.path.join(temp_dir, cvs.STAGING_AREA), 'r') as f:
        for line in f:
            print(line)
            if test_for_json and test_for_json[-1] in line:
                test_for_json.pop()
    assert not test_for_json
    assert "Added 1 file(s) to staging area: example_file.txt" in result.stdout


def test_commit(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'add', 'example_file.txt'], cwd=temp_dir, capture_output=True, text=True)
    result = subprocess.run(['cvs', 'commit', 'message'], cwd=temp_dir, capture_output=True, text=True)

    test_for_json = ['"branch": "main"',
                     '"parent_branch": null',
                     '"parent_commit_id": null',
                     'example_file.txt'][::-1]
    with open(os.path.join(temp_dir, cvs.BRANCHES_LOG, 'main.json'), 'r') as f:
        for line in f:
            print(line)
            if test_for_json and test_for_json[-1] in line:
                test_for_json.pop()
    assert not test_for_json
    assert "Changes were commited with message: message" in result.stdout


def test_commit_of_exsisting_files(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'add', 'example_file.txt'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'commit', 'message'], cwd=temp_dir, capture_output=True, text=True)
    result = subprocess.run(['cvs', 'commit', 'message'], cwd=temp_dir, capture_output=True, text=True)

    assert "There are not any changes to commit" in result.stdout


def test_empty_commit(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    result = subprocess.run(['cvs', 'commit', 'message'], cwd=temp_dir, capture_output=True, text=True)

    assert "There are not any files in staging area" in result.stdout


def test_reset(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'add', 'example_file.txt'], cwd=temp_dir, capture_output=True, text=True)
    result = subprocess.run(['cvs', 'reset'], cwd=temp_dir, capture_output=True, text=True)

    is_test_passed = False
    with open(os.path.join(temp_dir, cvs.STAGING_AREA)) as f:
        for line in f:
            if '"staging_files": []' in line:
                is_test_passed = True
                break
    assert is_test_passed
    assert "Reset staging area" in result.stdout


def test_branch_command(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    test_name_for_branch = 'test-branch'
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'add', 'example_file.txt'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'commit', 'message'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'branch', test_name_for_branch], cwd=temp_dir, capture_output=True, text=True)
    assert os.path.exists(os.path.join(temp_dir, cvs.BRANCHES, test_name_for_branch))
    assert os.path.exists(os.path.join(temp_dir, cvs.BRANCHES_LOG, f'{test_name_for_branch}.json'))


def test_create_branch_which_already_exists(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    test_name_for_branch = 'test-branch'
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'add', 'example_file.txt'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'commit', 'message'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'branch', test_name_for_branch], cwd=temp_dir, capture_output=True, text=True)
    result = subprocess.run(['cvs', 'branch', test_name_for_branch], cwd=temp_dir, capture_output=True, text=True)
    assert 'because it already exists' in result.stdout


def test_create_branch_when_last_is_empty(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    test_name_for_branch = 'test-branch'
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    r = subprocess.run(['cvs', 'branch', test_name_for_branch], cwd=temp_dir, capture_output=True, text=True)
    assert f"`There are no commits on branch 'main'" in r.stdout


def test_checkout_changes_in_staging_area(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    test_name_for_branch = 'test-branch'
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'add', 'example_file.txt'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'commit', 'message'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'branch', test_name_for_branch], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'checkout', 'main'], cwd=temp_dir, capture_output=True, text=True)

    is_test_passed = False
    with open(os.path.join(temp_dir, cvs.STAGING_AREA)) as f:
        for line in f:
            if '"current_branch": "main"' in line:
                is_test_passed = True
                break
    assert is_test_passed


def test_checkout_with_test_files(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    test_branch = 'test-branch'
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'add', 'example_file.txt'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'commit', 'message'], cwd=temp_dir, capture_output=True, text=True)

    subprocess.run(['cvs', 'branch', test_branch], cwd=temp_dir, capture_output=True, text=True)
    open(os.path.join(temp_dir, f'{test_branch}.txt'), 'w').close()
    subprocess.run(['cvs', 'add', f'{test_branch}.txt'])
    q = subprocess.run(['cvs', 'commit', 'files'], cwd=temp_dir, capture_output=True)

    log = utils._read_json_file(os.path.join(temp_dir, cvs.BRANCHES_LOG, f'{test_branch}.json'))
    assert log['branch'] == test_branch
    assert os.path.exists(os.path.join(temp_dir, f'{test_branch}.txt'))

    subprocess.run(['cvs', 'checkout', 'main'], cwd=temp_dir, capture_output=True, text=True)
    assert os.path.exists(os.path.join(temp_dir, 'example_file.txt'))
    assert not os.path.exists(os.path.join(temp_dir, f'{test_branch}.txt'))


def test_checkout_to_current_branch(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    test_branch = 'test-branch'
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'add', 'example_file.txt'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'commit', 'message'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'branch', test_branch], cwd=temp_dir, capture_output=True, text=True)
    r = subprocess.run(['cvs', 'checkout', test_branch], cwd=temp_dir, capture_output=True, text=True)

    assert f"You are already on branch '{test_branch}'" in r.stdout



def test_logs(temp_dir):
    open(os.path.join(temp_dir, 'example_file.txt'), 'w').close()
    test_name_for_branch = 'test-branch'
    message_test = 'kmfsokjvdnjdf'
    subprocess.run(['cvs', 'init'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'add', 'example_file.txt'], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'commit', message_test], cwd=temp_dir, capture_output=True, text=True)
    subprocess.run(['cvs', 'branch', test_name_for_branch], cwd=temp_dir, capture_output=True, text=True)
    result = subprocess.run(['cvs', 'log'], cwd=temp_dir, capture_output=True, text=True)

    assert 'Commit History:' in result.stdout
    assert '- main' in result.stdout
    assert '- test-branch' in result.stdout
    assert message_test in result.stdout
