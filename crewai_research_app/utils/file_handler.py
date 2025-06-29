import os
import zipfile
from gitignore_parser import parse_gitignore

def list_files_in_repo(repo_path: str) -> list[str]:
    """
    Lists all files in a given repository path, respecting .gitignore rules
    found at the root of the repository.

    Args:
        repo_path (str): The absolute path to the root of the repository.

    Returns:
        list[str]: A list of absolute file paths for all files not ignored by .gitignore.
    """
    all_files_details = [] # Stores tuples of (absolute_path, relative_path_to_repo_root)

    gitignore_path = os.path.join(repo_path, ".gitignore")
    matches = None
    if os.path.exists(gitignore_path):
        matches = parse_gitignore(gitignore_path, base_dir=repo_path)

    for root, dirs, files in os.walk(repo_path, topdown=True):
        # Filter out .git directory (and other common VCS dirs if needed)
        dirs[:] = [d for d in dirs if d not in ['.git', '.hg', '.svn']]

        for file_name in files:
            file_abs_path = os.path.join(root, file_name)

            if matches:
                if matches(file_abs_path):
                    # print(f"Ignoring (via .gitignore): {file_abs_path}")
                    continue # Skip ignored files

            # Check if the file is within a directory that itself is ignored.
            # The `matches` function from gitignore_parser should handle this if the
            # directory pattern (e.g., `some_dir/`) is in .gitignore.
            # For explicit check, one might need to check parent paths if `matches` doesn't cover it.
            # However, `gitignore_parser` is generally good at this.

            all_files_details.append(file_abs_path)

    return all_files_details


# Note: Zip extraction logic is currently in main_streamlit_app.py.
# It could be moved here if it needs to be reused or becomes more complex.
# For now, we'll keep it there as it's directly tied to the Streamlit upload flow.

# Example usage (for testing):
if __name__ == '__main__':
    # Create a dummy repo structure for testing
    test_repo_dir = "temp_test_repo"
    os.makedirs(test_repo_dir, exist_ok=True)
    os.makedirs(os.path.join(test_repo_dir, "src"), exist_ok=True)
    os.makedirs(os.path.join(test_repo_dir, "data", "raw"), exist_ok=True)
    os.makedirs(os.path.join(test_repo_dir, ".git"), exist_ok=True) # Ignored dir

    with open(os.path.join(test_repo_dir, ".gitignore"), "w") as f:
        f.write("*.log\n")
        f.write("data/\n")
        f.write("temp_file.txt\n")
        f.write("!important.log\n") # Test negation
        f.write("dist/\n")

    with open(os.path.join(test_repo_dir, "main.py"), "w") as f: f.write("print('hello')")
    with open(os.path.join(test_repo_dir, "src", "module.py"), "w") as f: f.write("# module code")
    with open(os.path.join(test_repo_dir, "error.log"), "w") as f: f.write("error")
    with open(os.path.join(test_repo_dir, "important.log"), "w") as f: f.write("important") # Should be included
    with open(os.path.join(test_repo_dir, "data", "raw", "datafile.csv"), "w") as f: f.write("col1,col2") # Should be ignored
    with open(os.path.join(test_repo_dir, "temp_file.txt"), "w") as f: f.write("temp") # Should be ignored

    # Test the function
    abs_repo_path = os.path.abspath(test_repo_dir)
    print(f"Testing with repository: {abs_repo_path}")

    # Ensure .gitignore is parsed from the correct base
    # The parse_gitignore function needs the base_dir argument if the gitignore_path itself is absolute
    # and contains rules relative to the repo root.
    # If gitignore_path is relative to cwd, and cwd is repo_root, it's fine.
    # Here, gitignore_path is constructed as absolute, so base_dir should be repo_path.

    non_ignored_files = list_files_in_repo(abs_repo_path)
    print("\nNon-ignored files:")
    for f_path in non_ignored_files:
        print(os.path.relpath(f_path, abs_repo_path))

    # Cleanup
    import shutil
    # shutil.rmtree(test_repo_dir) # Keep for manual inspection if needed
    print(f"\nTest repo created at {abs_repo_path}. Manually delete it if desired.")
    # Expected output:
    # .gitignore (usually not ignored by itself unless explicitly listed, gitignore_parser might exclude it by default - need to check its behavior for .gitignore itself)
    # main.py
    # src/module.py
    # important.log
    # The .gitignore file itself is often implicitly included unless specified.
    # `gitignore_parser`'s `matches` function will return `False` for the `.gitignore` file itself
    # if `.gitignore` is not in the ignore rules.
    # The behavior for `.git` directory is handled by `dirs[:]` filtering.
