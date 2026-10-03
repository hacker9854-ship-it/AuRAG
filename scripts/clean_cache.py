"""Repository Cache and Bytecode Cleaner.

Safely purges __pycache__, .pyc, .pyo, and .pytest_cache directories across
the project tree while preserving virtual environments (.venv).
"""
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {
    ".venv",
    ".venv-broken",
    "venv",
    "node_modules",
    ".git",
}


def clean_project_cache(repo_root: Path = REPO_ROOT) -> dict:
    cleaned_dirs = 0
    cleaned_files = 0
    bytes_freed = 0

    print(f"Scanning for cache and bytecode artifacts in {repo_root}...")

    # First pass: collect files and directories to remove
    dirs_to_remove = []
    files_to_remove = []

    for root, dirs, files in os.walk(repo_root, topdown=True):
        # Prune excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not any(part in EXCLUDED_DIRS for part in Path(root, d).parts)]

        for d in dirs:
            if d in ("__pycache__", ".pytest_cache"):
                dir_path = Path(root, d)
                dirs_to_remove.append(dir_path)

        for f in files:
            if f.endswith((".pyc", ".pyo", ".pyd")):
                file_path = Path(root, f)
                files_to_remove.append(file_path)

    # Remove files
    for file_path in files_to_remove:
        try:
            if file_path.exists():
                size = file_path.stat().st_size
                file_path.unlink()
                cleaned_files += 1
                bytes_freed += size
        except Exception as e:
            print(f"Warning: could not delete file {file_path}: {e}", file=sys.stderr)

    # Remove directories
    for dir_path in dirs_to_remove:
        try:
            if dir_path.exists():
                for p in dir_path.rglob("*"):
                    if p.is_file():
                        bytes_freed += p.stat().st_size
                shutil.rmtree(dir_path, ignore_errors=True)
                cleaned_dirs += 1
        except Exception as e:
            print(f"Warning: could not delete dir {dir_path}: {e}", file=sys.stderr)

    mb_freed = bytes_freed / (1024 * 1024)
    print(f"Cleanup complete:")
    print(f"  - Removed {cleaned_dirs} cache directories (__pycache__, .pytest_cache)")
    print(f"  - Removed {cleaned_files} bytecode files (.pyc, .pyo)")
    print(f"  - Freed approx. {mb_freed:.2f} MB")

    return {
        "cleaned_dirs": cleaned_dirs,
        "cleaned_files": cleaned_files,
        "bytes_freed": bytes_freed,
    }


if __name__ == "__main__":
    clean_project_cache()
