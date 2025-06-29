import os
import shutil
import pytest
from utils.file_handler import list_files_in_repo # Assuming utils is in PYTHONPATH

# Define a fixture to create a temporary test repository structure
@pytest.fixture
def temp_repo(tmp_path):
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    (repo_dir / ".git").mkdir() # VCS directory to be ignored by os.walk filter
    (repo_dir / "src").mkdir()
    (repo_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (repo_dir / "dist").mkdir()

    with open(repo_dir / ".gitignore", "w") as f:
        f.write("*.log\n")
        f.write("data/\n")      # Ignore whole data directory
        f.write("temp_file.txt\n")
        f.write("!important.log\n") # Keep this specific log file
        f.write("dist/\n")      # Ignore dist directory

    # Files that should be included
    (repo_dir / "main.py").write_text("print('hello')")
    (repo_dir / "src" / "module.py").write_text("# module code")
    (repo_dir / "important.log").write_text("important stuff") # Should be kept due to negation
    (repo_dir / ".gitignore").write_text("*.log\n") # .gitignore itself is usually not ignored

    # Files that should be ignored
    (repo_dir / "error.log").write_text("error")
    (repo_dir / "data" / "raw" / "datafile.csv").write_text("col1,col2")
    (repo_dir / "temp_file.txt").write_text("temp content")
    (repo_dir / "dist" / "output.bin").write_text("binary")

    return str(repo_dir)

def test_list_files_in_repo_with_gitignore(temp_repo):
    expected_files_relative = {
        ".gitignore", # .gitignore itself is not ignored by default
        "main.py",
        "src/module.py",
        "important.log"
    }

    non_ignored_files_abs = list_files_in_repo(temp_repo)
    non_ignored_files_relative = {os.path.relpath(f, temp_repo) for f in non_ignored_files_abs}

    # Normalize path separators for comparison, especially on Windows
    normalized_expected_files = {p.replace("/", os.sep) for p in expected_files_relative}

    assert non_ignored_files_relative == normalized_expected_files

def test_list_files_in_repo_no_gitignore(tmp_path):
    repo_dir = tmp_path / "test_repo_no_gitgnore"
    repo_dir.mkdir()
    (repo_dir / "file1.txt").write_text("content1")
    (repo_dir / "file2.txt").write_text("content2")
    (repo_dir / ".git").mkdir() # Should still be skipped

    expected_files_relative = {"file1.txt", "file2.txt"}

    non_ignored_files_abs = list_files_in_repo(str(repo_dir))
    non_ignored_files_relative = {os.path.relpath(f, str(repo_dir)) for f in non_ignored_files_abs}

    normalized_expected_files = {p.replace("/", os.sep) for p in expected_files_relative}

    assert non_ignored_files_relative == normalized_expected_files

def test_list_files_in_repo_empty_repo(tmp_path):
    repo_dir = tmp_path / "empty_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    non_ignored_files_abs = list_files_in_repo(str(repo_dir))
    assert len(non_ignored_files_abs) == 0

def test_list_files_in_repo_gitignore_ignores_all(tmp_path):
    repo_dir = tmp_path / "ignore_all_repo"
    repo_dir.mkdir()
    (repo_dir / "file1.txt").write_text("content1")
    (repo_dir / ".gitignore").write_text("*\n!*.c") # Ignore all, but keep .c

    (repo_dir / "test.c").write_text("hello c")


    expected_files_relative = {".gitignore", "test.c"} # .gitignore itself is not matched by '*' in this context by gitignore_parser
                                                 # and test.c is explicitly un-ignored.

    non_ignored_files_abs = list_files_in_repo(str(repo_dir))
    non_ignored_files_relative = {os.path.relpath(f, str(repo_dir)) for f in non_ignored_files_abs}

    normalized_expected_files = {p.replace("/", os.sep) for p in expected_files_relative}

    assert non_ignored_files_relative == normalized_expected_files
