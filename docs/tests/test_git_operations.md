# Test Plan for `git_operations.py`

**Module Overview:**
This module provides functions for interacting with Git repositories, including running Git commands, managing files (add, commit, push), analyzing commit history, handling Git operation errors, and managing branches, remotes, tags, and stashes.

**Functionality to Test:**

1. **Git Command Execution:**
    - **`run_git_command(command, config)`**
        - **Description:** Executes a Git command and returns its output.
        - **Test Cases:**
            - Successful execution of valid Git commands.
            - Handling of Git command failures with appropriate error messages.
            - Simulation of various Git errors (e.g., not a git repository, permission denied).
        - **How to Test:**
            - Use `pytest-mock` to mock `subprocess.Popen`, simulating different Git command outputs and errors.
            - Assert that the function returns correct `stdout` and `stderr` for successful commands.
            - Verify that specific Git errors are mapped to user-friendly `GitError` messages.

    - **`get_current_branch(config)`**
        - **Description:** Retrieves the name of the current Git branch.
        - **Test Cases:**
            - Successfully retrieving the current branch in a valid repository.
            - Handling cases where the current branch cannot be determined.
            - Simulating Git errors during branch retrieval.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to return a valid branch name.
            - Simulate empty `stdout` or Git errors and assert that `GitError` is raised with appropriate messages.

2. **Git Operations:**
    - **`git_add(files, config)`**
        - **Description:** Adds specified files or all files to the Git staging area.
        - **Test Cases:**
            - Adding a single file successfully.
            - Adding multiple files with and without spaces in filenames.
            - Handling non-existent files or permission issues.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to simulate successful and failed `git add` operations.
            - Test with various `files` inputs, including quoted filenames.
            - Simulate Git errors and verify that `GitError` is raised appropriately.

    - **`git_commit(message, config)`**
        - **Description:** Commits staged changes with the provided commit message.
        - **Test Cases:**
            - Successful commit with a valid message.
            - Handling empty commit messages.
            - Simulating commit failures (e.g., no staged changes).
        - **How to Test:**
            - Use `pytest-mock` to mock `run_git_command` to simulate successful and failed `git commit` operations.
            - Assert that `GitError` is raised for invalid commit scenarios.

    - **`git_push(branch, config)`**
        - **Description:** Pushes committed changes to the specified branch on the remote repository.
        - **Test Cases:**
            - Successful push to an existing branch.
            - Handling push rejections due to conflicts or permissions.
            - Simulating network failures during push.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to simulate successful and failed `git push` operations.
            - Verify that specific errors (e.g., push rejected) raise `GitError` with informative messages.

3. **Change Management:**
    - **`get_changed_files(config)`**
        - **Description:** Retrieves a set of files that have been changed, excluding patterns defined in `EXCLUDED_PATTERNS`.
        - **Test Cases:**
            - Correctly identifying changed files and excluding specified patterns.
            - Handling cases with no changed files.
            - Managing complex Git status outputs.
        - **How to Test:**
            - Use `pytest-mock` to mock `run_git_command` to return various Git status outputs.
            - Assert that the returned set includes only the expected files.
            - Test exclusion logic by including files that match exclusion patterns.

    - **`unstage_files(config)`**
        - **Description:** Unstages all files from the staging area.
        - **Test Cases:**
            - Successfully unstaging files.
            - Handling cases where there are no files to unstage.
            - Simulating Git errors during unstaging.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to simulate successful and failed `git reset HEAD` operations.
            - Verify that `GitError` is raised appropriately on failures.

    - **`get_recent_commits(num_commits, config)`**
        - **Description:** Retrieves a list of recent commits up to the specified number.
        - **Test Cases:**
            - Correctly retrieving the specified number of recent commits.
            - Handling repositories with fewer commits than requested.
            - Managing malformed commit data.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to return valid and invalid commit logs.
            - Assert that the function returns the correct number of commit dictionaries.
            - Verify error handling for JSON parsing issues.

    - **`find_related_commits(diff_content, num_commits, config)`**
        - **Description:** Identifies commits related to the current changes based on file similarities.
        - **Test Cases:**
            - Accurately identifying related commits based on overlapping files.
            - Handling cases with no related commits.
            - Managing scenarios with multiple related commits.
        - **How to Test:**
            - Mock `get_recent_commits` and `run_git_command` using `pytest-mock` to simulate various commit histories.
            - Assert that related commits are correctly identified and limited to `num_commits`.

    - **`get_diff(diff_type, config)`**
        - **Description:** Retrieves the Git diff output for either staged or unstaged changes.
        - **Test Cases:**
            - Correctly retrieving staged diffs.
            - Correctly retrieving unstaged diffs when staged diffs are empty.
            - Handling cases with no diffs available.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to return different diff outputs based on `diff_type`.
            - Assert that the function returns the expected diff strings.

4. **Branch Management:**
    - **`create_branch(branch_name, config)`**
        - **Description:** Creates a new Git branch with the specified name.
        - **Test Cases:**
            - Successfully creating a new branch.
            - Handling attempts to create a branch that already exists.
            - Managing Git errors during branch creation.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to simulate successful and failed `git checkout -b` operations.
            - Assert that `GitError` is raised for duplicate branch names.

    - **`delete_branch(branch_name, force, config)`**
        - **Description:** Deletes the specified Git branch, with an option to force delete.
        - **Test Cases:**
            - Successfully deleting an existing branch.
            - Handling attempts to delete a non-existent branch.
            - Using the force delete option and verifying its effect.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to simulate successful and failed `git branch -d/-D` operations.
            - Assert that `GitError` is raised appropriately.

    - **`merge_branch(source_branch, config)`**
        - **Description:** Merges the specified source branch into the current branch.
        - **Test Cases:**
            - Successfully merging a branch with no conflicts.
            - Handling merge conflicts and verifying error reporting.
            - Managing Git errors during merging.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to simulate successful and conflicted `git merge` operations.
            - Assert that conflicts raise `GitError` with informative messages.

5. **Remote and Tag Management:**
    - **`manage_remote(operation, remote_name, url, config)`**
        - **Description:** Manages Git remotes by adding, removing, or setting URLs.
        - **Test Cases:**
            - Successfully adding a new remote.
            - Removing an existing remote.
            - Setting the URL of an existing remote.
            - Handling invalid operations or missing parameters.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to simulate `git remote` operations.
            - Assert that appropriate `GitError` is raised for invalid operations.

    - **`manage_tags(operation, tag_name, message, config)`**
        - **Description:** Manages Git tags by creating, deleting, or pushing tags.
        - **Test Cases:**
            - Successfully creating annotated and lightweight tags.
            - Deleting existing tags.
            - Pushing tags to the remote repository.
            - Handling attempts to create duplicate tags or delete non-existent tags.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to simulate `git tag` operations.
            - Assert that `GitError` is raised for invalid tag operations.

    - **`manage_stash(operation, message, stash_id, config)`**
        - **Description:** Manages Git stashes by saving, popping, applying, dropping, or listing stashes.
        - **Test Cases:**
            - Successfully saving a stash with and without a message.
            - Popping, applying, and dropping stashes by ID.
            - Listing existing stashes.
            - Handling operations on non-existent stashes.
        - **How to Test:**
            - Mock `run_git_command` using `pytest-mock` to simulate `git stash` operations.
            - Assert that `GitError` is raised for invalid stash operations.

6. **Commit Pattern Analysis:**
    - **`analyze_commit_patterns(commits, config)`**
        - **Description:** Analyzes commit history to identify patterns in commit types and scopes.
        - **Test Cases:**
            - Correctly counting commit types and scopes from commit history.
            - Handling empty commit histories.
            - Managing commits with unconventional or malformed messages.
        - **How to Test:**
            - Provide mock commit data using `pytest` fixtures and assert that the returned pattern counts are accurate.
            - Test with various commit message formats to ensure robustness.

7. **Signal Handling:**
    - **`setup_signal_handlers()`**
        - **Description:** Sets up signal handlers for graceful interruption of Git operations.
        - **Test Cases:**
            - Verify that interrupt signals (`SIGINT`) trigger the appropriate cleanup (e.g., unstaging files).
            - Ensure that the program exits gracefully upon receiving an interrupt.
        - **How to Test:**
            - Use `pytest` to send signals to the process and assert that cleanup functions are called using `pytest-mock`.
            - Mock `unstage_files` and verify it is invoked upon signal reception.

**Types of Testing:**

- **Unit Testing:** Utilize `pytest` and `pytest-mock` to mock `subprocess.Popen` and other external dependencies, simulating Git command executions and outputs. Test each function's logic independently.
- **Integration Testing:** Employ `pytest` with temporary Git repositories (using `tempfile` and `git init`) to perform real Git operations and verify interactions between functions.
- **Functional Testing:** Simulate complete workflows involving multiple Git operations using `pytest` to ensure end-to-end functionality.
- **Error Handling Testing:** Use `pytest-mock` to simulate various error conditions (e.g., network issues, permission errors) and verify graceful handling and informative error messages. 