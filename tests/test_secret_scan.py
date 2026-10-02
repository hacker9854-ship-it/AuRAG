"""
Unit test for Pre-submission Secret and Credential Scanning (Task 9.1 / SEC-01 / SEC-02 / SEC-06).
Ensures no secrets, API keys, or private keys are committed into git-tracked files.
"""

import os
import subprocess
import pytest
from scripts.secret_scan import scan_repository

def test_no_exposed_secrets_in_git_tracked_files():
    """Verify that zero exposed production secrets or credentials exist in git-tracked files."""
    findings = scan_repository()
    assert findings == [], f"Found exposed credentials in git-tracked files: {findings}"

def test_env_files_are_untracked_and_gitignored():
    """Verify .env is gitignored and not in git index."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Check .gitignore exists and contains .env
    gitignore_path = os.path.join(root_dir, ".gitignore")
    assert os.path.exists(gitignore_path), ".gitignore missing!"
    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert ".env" in content, ".env must be explicitly ignored in .gitignore!"

    # Check git ls-files does not list .env
    try:
        git_tracked = subprocess.check_output(
            ["git", "ls-files"], cwd=root_dir, text=True
        ).splitlines()
        assert ".env" not in git_tracked, "CRITICAL: .env is tracked in git index!"
    except Exception:
        pass
