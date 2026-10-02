#!/usr/bin/env python3
"""
Pre-submission Secret and Credential Scanner for AuRAG.
Verifies SEC-01 and Task 9.1:
- Scans source code, config files, and tests for exposed production credentials.
- Checks git status for any untracked or accidentally tracked .env files.
"""

import os
import re
import sys
import subprocess

PATTERNS = {
    "Google API Key": re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    "GitHub Token": re.compile(r"(?:ghp_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{82})"),
    "Groq API Key": re.compile(r"gsk_[0-9A-Za-z]{48}"),
    "OpenAI API Key": re.compile(r"sk-[a-zA-Z0-9]{48}"),
    "Private Key Block": re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY-----"),
    "Hardcoded Admin Key Assignment": re.compile(r"(?i)(?:ADMIN_KEY|INVOICE_KEY|PRIVATE_KEY)\s*=\s*['\"][a-f0-9]{32,}['\"]"),
}

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "__pycache__",
    ".next",
    ".pytest_cache",
    "artifacts",
}

EXCLUDE_FILES = {
    "package-lock.json",
    ".env.example",
    ".env.machine-money.example",
}

def scan_repository():
    findings = []
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    print(f"Scanning git-tracked files at: {root_dir}")

    # 1. Get all git-tracked files
    try:
        git_tracked = subprocess.check_output(
            ["git", "ls-files"], cwd=root_dir, text=True
        ).splitlines()
    except Exception as e:
        print(f"Warning: git ls-files failed: {e}")
        git_tracked = []

    # Verify .env is NOT tracked
    for f in git_tracked:
        if f == ".env" or f.endswith("/.env"):
            findings.append({
                "type": "TRACKED_ENV_FILE",
                "file": f,
                "line": 0,
                "content": "CRITICAL: Production .env file is tracked in git!"
            })

    # Verify .gitignore contains .env
    gitignore_path = os.path.join(root_dir, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            gitignore_content = f.read()
            if ".env" not in gitignore_content:
                findings.append({
                    "type": "GITIGNORE_MISSING_ENV",
                    "file": ".gitignore",
                    "line": 0,
                    "content": ".env is missing from .gitignore!"
                })

    # 2. Scan content of all git-tracked files
    scanned_files = 0
    for relpath in git_tracked:
        if any(relpath.startswith(ex) for ex in EXCLUDE_DIRS):
            continue
        if os.path.basename(relpath) in EXCLUDE_FILES:
            continue

        filepath = os.path.join(root_dir, relpath)
        if not os.path.isfile(filepath):
            continue

        scanned_files += 1
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f, 1):
                    for label, pattern in PATTERNS.items():
                        match = pattern.search(line)
                        if match:
                            snippet = line.strip()
                            if "placeholder" in snippet.lower() or "example" in snippet.lower():
                                continue
                            findings.append({
                                "type": label,
                                "file": relpath,
                                "line": line_idx,
                                "content": snippet[:100]
                            })
        except Exception:
            pass

    print(f"Scanned {scanned_files} git-tracked files.")
    return findings

if __name__ == "__main__":
    findings = scan_repository()
    if findings:
        print(f"\n[ALERT] Found {len(findings)} potential secret(s):")
        for finding in findings:
            print(f" - [{finding['type']}] {finding['file']}:{finding['line']}: {finding['content']}")
        sys.exit(1)
    else:
        print("\n[PASS] No exposed secrets or tracked credentials found! Clean scan.")
        sys.exit(0)
