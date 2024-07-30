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


class TestAdditionalFunctions():
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


class TestBranchCommand(InitDirs):
    def test_create_branch_with_existing_name(self):
        cvs._init()
        with pytest.raises(exceptions.BranchException):
            cvs._branch('main')

    def test_create_branch_in_empty_branch(self):
        cvs._init()
        with pytest.raises(exceptions.BranchException):
            cvs._branch('test')

    def test_create_branch(self, capsys):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._commit('commit1')
        cvs._branch('second_branch', console_info=True)
        captured = capsys.readouterr()
        assert os.path.exists(os.path.join(cvs.BRANCHES, 'main'))
        assert os.path.exists(os.path.join(cvs.BRANCHES, 'main', 'staging_area.json'))
        assert os.path.exists(os.path.join(cvs.BRANCHES, 'second_branch'))
        assert os.path.exists(os.path.join(cvs.BRANCHES, 'second_branch', 'staging_area.json'))
        assert f"Branch 'second_branch' was created\n" in captured.out


class TestCheckoutCommand(InitDirs):
    def test_checkout_on_non_existent_branch(self):
        cvs._init()
        with pytest.raises(exceptions.CheckoutException):
            cvs._checkout("non_existent_branch")

    def test_checkout_on_current_branch(self):
        cvs._init()
        with pytest.raises(exceptions.CheckoutException):
            cvs._checkout("main")

    def test_checkout_from_uncommited_branch(self):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._commit('commit1')
        cvs._branch("second_branch")
        open(f'{cvs.CURRENT_DIR}/test2.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test2.txt'])
        with pytest.raises(exceptions.CheckoutException):
            cvs._checkout("main")

    def test_checkout_with_edited_file(self):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._commit('commit1')
        cvs._branch("second_branch")
        with open(f'{cvs.CURRENT_DIR}/test1.txt', 'w') as f:
            f.write("test string")
        cvs._commit('commit2')
        cvs._checkout("main")
        with open(f'{cvs.CURRENT_DIR}/test1.txt', 'r') as f:
            assert not f.readlines()

    def test_checkout(self, capsys):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._commit('commit1')
        cvs._branch("second_branch")
        open(f'{cvs.CURRENT_DIR}/test2.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test2.txt'])
        cvs._commit('commit2')

        assert os.path.exists(os.path.join(cvs.CURRENT_DIR, 'test1.txt'))
        assert os.path.exists(os.path.join(cvs.CURRENT_DIR, 'test2.txt'))

        cvs._checkout("main", console_info=True)
        captured = capsys.readouterr()
        assert os.path.exists(os.path.join(cvs.CURRENT_DIR, 'test1.txt'))
        assert not os.path.exists(os.path.join(cvs.CURRENT_DIR, 'test2.txt'))
        assert "Switched to branch 'main'" in captured.out


class TestUpdateMessageCommand(InitDirs):
    def test_update_message(self, capsys):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._commit('commit1')
        current_branch = ut.read_json_file(os.path.join(cvs.BRANCHES_LOG, 'main.json'))
        commit_id = list(current_branch['commits'].keys())[0]
        cvs._change_commit_message(commit_id, 'new_message', console_info=True)
        captured = capsys.readouterr()
        current_branch = ut.read_json_file(os.path.join(cvs.BRANCHES_LOG, 'main.json'))
        assert current_branch['commits'][commit_id]['message'] == 'new_message'
        assert "Commit message was changed" in captured.out

    def test_update_non_existing_commit(self):
        cvs._init()
        with pytest.raises(FileNotFoundError):
            cvs._change_commit_message('non_existing_commit', 'new_message')



class TestCherryPickCommand(InitDirs):
    def test_cherry_pick(self, capsys):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        with open(f'{cvs.CURRENT_DIR}/test1.txt', 'w') as f:
            f.write("test string1")
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._commit('commit1')
        current_branch = ut.read_json_file(os.path.join(cvs.BRANCHES_LOG, 'main.json'))
        commit_id1 = list(current_branch['commits'].keys())[0]
        with open(f'{cvs.CURRENT_DIR}/test1.txt', 'w') as f:
            f.write("test string2")
        cvs._commit('commit2')
        cvs._branch("second_branch")
        cvs._cherry_pick(commit_id1, console_info=True)
        captured = capsys.readouterr()
        with open(f'{cvs.CURRENT_DIR}/test1.txt', 'r') as f:
            assert f.readlines() == ["test string1"]
        assert "Cherry pick was made successfully" in captured.out

    def test_cherry_pick_last_commit(self):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._commit('commit1')
        current_branch = ut.read_json_file(os.path.join(cvs.BRANCHES_LOG, 'main.json'))
        commit_id1 = list(current_branch['commits'].keys())[0]
        with pytest.raises(exceptions.CherryPickException):
            cvs._cherry_pick(commit_id1)

    def test_cherry_pick_non_existing_commit(self):
        cvs._init()
        with pytest.raises(FileNotFoundError):
            cvs._cherry_pick('non_existing_commit')

    def test_cherry_pick_commit_with_deleted_files(self):
        cvs._init()
        open(f'{cvs.CURRENT_DIR}/test1.txt', 'a')
        open(f'{cvs.CURRENT_DIR}/test2.txt', 'a')
        cvs._add([f'{cvs.CURRENT_DIR}/test1.txt'])
        cvs._add([f'{cvs.CURRENT_DIR}/test2.txt'])
        cvs._commit('commit1')
        current_branch = ut.read_json_file(os.path.join(cvs.BRANCHES_LOG, 'main.json'))
        commit_id1 = list(current_branch['commits'].keys())[0]
        os.remove(f'{cvs.CURRENT_DIR}/test2.txt')
        cvs._commit('commit2')
        cvs._cherry_pick(commit_id1)
        assert os.path.exists(os.path.join(cvs.CURRENT_DIR, 'test2.txt'))

