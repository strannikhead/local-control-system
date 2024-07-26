import os
import utils as ut
import pytest

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


class TestStatusCommand(InitDirs):
    def test_status(self):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._commit('commit')
        open(f'{cvs.CURRENT_DIR}/test2.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test2.txt'])
        status = cvs._status()
        staging_area = ut.read_json_file(cvs.STAGING_AREA)
        staging_files = staging_area["staging_files"]
        assert ["Current branch is 'main'\n",
                'NEW FILES:\n',
                f'- {cvs.CURRENT_DIR}/test2.txt\n',
                'UNCHANGED FILES:\n',
                f"- {cvs.CURRENT_DIR}/test1.txt\n"] == status


class TestLogCommand:
    pass


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
