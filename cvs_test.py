import os
import time

import utils as ut
import pytest
from pathlib import Path
import cvs
import exceptions


class InitDirs:
    @pytest.fixture(scope='function', autouse=True)
    def test_setup(self, tmp_path):
        temp = tmp_path
        print(temp)
        cvs.MAIN_BRANCH = f"{temp}/.cvs/branches/main"
        cvs.BRANCHES = f"{temp}/.cvs/branches"
        cvs.BRANCHES_LOG = f"{temp}/.cvs/branches_log"
        cvs.STAGING_AREA = f"{temp}/.cvs/staging_area.json"
        cvs.GITIGNORE = f"{temp}/.cvs/cvsignore.json"
        cvs.CURRENT_DIR = f"{temp}"


class TestAdditionalFunctions:
    def test_rep_existence(self):
        with pytest.raises(exceptions.RepositoryException):
            cvs._check_repository_existence()


class TestInitCommand(InitDirs):

    def test_init(self, capsys):
        # Check if the .vcs directory is created
        cvs._init(console_info=True)
        captured = capsys.readouterr()
        assert os.path.exists(os.path.join(cvs.MAIN_BRANCH))
        assert os.path.exists(os.path.join(cvs.STAGING_AREA))
        assert os.path.exists(os.path.join(cvs.GITIGNORE))
        assert 'Repository was initialized' in captured.out

    def test_already_init(self):
        cvs._init(console_info=True)
        with pytest.raises(exceptions.RepositoryException):
            cvs._init()


class TestAddCommand(InitDirs):
    def test_add_no_files(self, capsys):
        cvs._init()
        cvs._add([], console_info=True)
        captured = capsys.readouterr()
        assert "There are not any files to add\n" in captured.out

    def test_add_all_files(self, capsys):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        open(f'{cvs.CURRENT_DIR}/test2.txt', 'a')
        assert os.path.exists(f'{cvs.CURRENT_DIR}/test1.txt')
        assert os.path.exists(f'{cvs.CURRENT_DIR}/test2.txt')
        cvs._add(['.'], console_info=True)
        captured = capsys.readouterr()
        staging_area = ut.read_json_file(cvs.STAGING_AREA)
        assert not staging_area['staging_files'][cvs.FileState.UNTRACKED.name]
        assert f'{cvs.CURRENT_DIR}/test1.txt' in staging_area['staging_files'][cvs.FileState.NEW.name]
        assert f'{cvs.CURRENT_DIR}/test2.txt' in staging_area['staging_files'][cvs.FileState.NEW.name]
        assert f"Added 2 file(s) to staging area: {cvs.CURRENT_DIR}/test1.txt, {cvs.CURRENT_DIR}/test2.txt" in captured.out

    def test_add_one_file(self, capsys):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        open(f'{cvs.CURRENT_DIR}/test2.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'], console_info=True)
        staging_area = ut.read_json_file(cvs.STAGING_AREA)
        assert f'{cvs.CURRENT_DIR}/test1.txt' in staging_area['staging_files'][cvs.FileState.NEW.name]

    def test_add_non_existent_file(self, capsys):
        cvs._init()
        with pytest.raises(exceptions.AddException):
            cvs._add([f'not_exist.txt'], console_info=True)


class TestResetCommand(InitDirs):
    def test_reset(self, capsys):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test.txt'])
        staging_area = ut.read_json_file(cvs.STAGING_AREA)
        assert f'{cvs.CURRENT_DIR}/test.txt' in staging_area['staging_files'][cvs.FileState.NEW.name]
        cvs._reset(console_info=True)
        captured = capsys.readouterr()
        staging_files = ut.read_json_file(cvs.STAGING_AREA)["staging_files"]
        for key in staging_files.keys():
            assert not staging_files[key]
        assert "Staging area was reset\n" in captured.out


class TestCommitCommand(InitDirs):
    def test_empty_commit(self):
        cvs._init()
        with pytest.raises(exceptions.CommitException):
            cvs._commit('empty commit')

    def test_commit(self, capsys):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        open(f'{cvs.CURRENT_DIR}/test2.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt', f'{cvs.CURRENT_DIR}/test2.txt'])
        commit_message = 'commit test'
        cvs._commit(commit_message, console_info=True)
        captured = capsys.readouterr()
        staging_area = ut.read_json_file(cvs.STAGING_AREA)
        staging_files = staging_area["staging_files"]
        assert not staging_files[cvs.FileState.DELETED.name]
        assert not staging_files[cvs.FileState.MODIFIED.name]
        assert not staging_files[cvs.FileState.NEW.name]
        assert f'{cvs.CURRENT_DIR}/test1.txt' in staging_files[cvs.FileState.UNCHANGED.name]
        assert f'{cvs.CURRENT_DIR}/test2.txt' in staging_files[cvs.FileState.UNCHANGED.name]
        assert f"Changes were commited with message: {commit_message}\n" in captured.out

    def test_many_commits(self, capsys):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._commit('commit1')
        open(f'{cvs.CURRENT_DIR}/test2.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test2.txt'])
        cvs._commit('commit2')
        branch_log_path = os.path.join(cvs.BRANCHES_LOG, "main.json")
        branch_log_obj = ut.read_json_file(branch_log_path)
        commit_id = branch_log_obj["head"]
        commit_info_obj = branch_log_obj["commits"][commit_id]
        staging_area = cvs._update_staging_area()
        last_commit = cvs._get_last_commit(staging_area["current_branch"])
        assert commit_info_obj["parent_commit_branch"] == last_commit["branch"]
        assert commit_info_obj["id"] == last_commit["id"]
        assert commit_info_obj["files"] == last_commit["files"]


class TestStatusCommand(InitDirs):
    def test_status(self):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._commit('commit')
        open(f'{cvs.CURRENT_DIR}/test2.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test2.txt'])
        status = cvs._status()
        assert ["Current branch is 'main'\n",
                'NEW FILES:\n',
                f'- {cvs.CURRENT_DIR}/test2.txt\n',
                'UNCHANGED FILES:\n',
                f"- {cvs.CURRENT_DIR}/test1.txt\n"] == status


class TestLogCommand(InitDirs):
    def test_log(self, capsys):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._commit('commit1')
        cvs._branch("second_branch")
        open(f'{cvs.CURRENT_DIR}/test2.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test2.txt'])
        cvs._commit('commit2')
        logs = cvs._log()

        log_paths = list(Path(cvs.BRANCHES_LOG).iterdir())
        branch_log_obj1 = ut.read_json_file(os.path.join(cvs.BRANCHES_LOG, log_paths[0].name))
        dummy1 = branch_log_obj1['head']
        date1 = time.strptime(branch_log_obj1["commits"][dummy1]["time"])
        str_date1 = f"{date1.tm_mon:0>2}.{date1.tm_mday:0>2}.{date1.tm_year}"
        message1 = branch_log_obj1["commits"][dummy1]["message"]

        branch_log_obj2 = ut.read_json_file(os.path.join(cvs.BRANCHES_LOG, log_paths[1].name))
        dummy2 = branch_log_obj2['head']
        date2 = time.strptime(branch_log_obj2["commits"][dummy2]["time"])
        str_date2 = f"{date2.tm_mon:0>2}.{date2.tm_mday:0>2}.{date2.tm_year}"
        message2 = branch_log_obj2["commits"][dummy2]["message"]

        assert ("Commit History:\n"
                f"- {branch_log_obj1['branch']}\n"
                f" - {str_date1} {dummy1} '{message1}'\n"
                "- second_branch\n"
                f" - {str_date2} {dummy2} '{message2}'\n") == ''.join(logs)


class TestBranchCommand:
    pass


class TestCheckoutCommand:
    pass

# def test_add_commit_reset(vcs_initialized):
#     # Create test files
#     test_file1 = os.path.join(vcs_initialized, "test_file1.txt")
#     test_file2 = os.path.join(vcs_initialized, "test_file2.txt")
#     with open(test_file1, 'w') as f:
#         f.write("Test file 1 content")
#     with open(test_file2, 'w') as f:
#         f.write("Test file 2 content")
#
#     # Add files to staging area
#     subprocess.run(['python', 'vcs.py', 'add', 'test_file1.txt', 'test_file2.txt'], cwd=vcs_initialized)
#     assert os.path.isfile(os.path.join(vcs_initialized, ".vcs/staging_area/file_list.txt"))
#
#     # Commit changes
#     subprocess.run(['python', 'vcs.py', 'commit', 'Initial commit'], cwd=vcs_initialized)
#     assert os.listdir(os.path.join(vcs_initialized, ".vcs/commits"))
#
#     # Reset staging area
#     subprocess.run(['python', 'vcs.py', 'reset'], cwd=vcs_initialized)
#     assert not os.listdir(os.path.join(vcs_initialized, ".vcs/staging_area"))
#
#
# def test_log(vcs_initialized):
#     # Check log when no commits exist
#     result = subprocess.run(['python', 'vcs.py', 'log'], cwd=vcs_initialized, capture_output=True, text=True)
#     assert "No commits yet." in result.stdout
#
#     # Commit changes
#     subprocess.run(['python', 'vcs.py', 'commit', 'Initial commit'], cwd=vcs_initialized)
#
#     # Check log after commit
#     result = subprocess.run(['python', 'vcs.py', 'log'], cwd=vcs_initialized, capture_output=True, text=True)
#     assert "Commit History" in result.stdout
#
#
# def test_branch_checkout(vcs_initialized):
#     # Create a new branch
#     subprocess.run(['python', 'vcs.py', 'branch', 'new_branch'], cwd=vcs_initialized)
#     assert os.path.isdir(os.path.join(vcs_initialized, ".vcs/branches/new_branch"))
#
#     # Switch to the new branch
#     subprocess.run(['python', 'vcs.py', 'checkout', 'new_branch'], cwd=vcs_initialized)
#     # Implement further checks for branch checkout as needed
