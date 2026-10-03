"""AuRAG Clean Submission Packager.

Packages the AuRAG repository into a production/hackathon submission ZIP artifact,
guaranteeing complete exclusion of:
- __pycache__ / *.pyc / *.pyo / *.pyd bytecode
- .pytest_cache and runtime temp files
- .venv / virtual environments
- frontend/node_modules / .next build caches
- .git repository internals
- Secrets and raw .env files (retaining .env.example)

Validates the final ZIP archive to guarantee zero bytecode leakage.
"""
import argparse
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Top-level and nested directory patterns to ignore
IGNORED_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".venv",
    ".venv-broken",
    "venv",
    ".git",
    "node_modules",
    ".next",
    ".runtime",
    ".claude",
    ".agents",
    "out",
    "coverage",
    "scratch",
    "test-results",
    "playwright-report",
}

# File extensions / names to ignore
IGNORED_FILE_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".tsbuildinfo",
    ".DS_Store",
}

IGNORED_FILE_EXACT = {
    "Thumbs.db",
}


def should_include_path(rel_path: Path) -> bool:
    parts = rel_path.parts
    # Check directory parts
    for part in parts[:-1]:
        if part in IGNORED_DIR_NAMES:
            return False

    name = parts[-1]
    # Check filename / extension
    if name in IGNORED_FILE_EXACT:
        return False
    if any(name.endswith(ext) for ext in IGNORED_FILE_EXTS):
        return False
    if name.startswith(".env") and not name.startswith(".env.example") and not name.startswith(".env.machine-money.example"):
        return False

    return True


def build_submission_zip(output_zip: Path, repo_root: Path = REPO_ROOT) -> int:
    import os
    print(f"Building clean submission ZIP at: {output_zip}")
    print(f"Source root: {repo_root}")

    included_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(repo_root, topdown=True):
            # Prune ignored directory trees upfront
            dirs[:] = [d for d in dirs if d not in IGNORED_DIR_NAMES]

            for fname in files:
                file_path = Path(root, fname)
                # Skip the output zip itself
                if file_path.resolve() == output_zip.resolve():
                    continue

                rel_path = file_path.relative_to(repo_root)
                if not should_include_path(rel_path):
                    continue

                arcname = str(rel_path).replace("\\", "/")
                zf.write(file_path, arcname=arcname)
                included_count += 1
                total_uncompressed_bytes += file_path.stat().st_size

    # Verification phase
    print(f"Verifying archive integrity: {included_count} files packaged...")
    violations = []
    with zipfile.ZipFile(output_zip, "r") as zf:
        for info in zf.infolist():
            filename = info.filename
            if "__pycache__" in filename or filename.endswith((".pyc", ".pyo", ".pyd")):
                violations.append(f"Bytecode leaked: {filename}")
            if filename.startswith(".git/") or "/.git/" in filename:
                violations.append(f"Git internals leaked: {filename}")
            if filename.startswith(".venv/") or "/.venv/" in filename:
                violations.append(f"Virtualenv leaked: {filename}")
            if "node_modules/" in filename:
                violations.append(f"Node modules leaked: {filename}")
            if filename.startswith(".env") and not filename.startswith(".env.example") and not filename.startswith(".env.machine-money.example"):
                violations.append(f"Secret file leaked: {filename}")

    if violations:
        print(f"ERROR: {len(violations)} packaging rule violation(s) found in {output_zip}:", file=sys.stderr)
        for v in violations[:10]:
            print(f"  - {v}", file=sys.stderr)
        output_zip.unlink(missing_ok=True)
        return 1

    zip_size_mb = output_zip.stat().st_size / (1024 * 1024)
    raw_size_mb = total_uncompressed_bytes / (1024 * 1024)
    print(f"SUCCESS: Submission artifact verified completely clean!")
    print(f"  - Files packaged: {included_count}")
    print(f"  - Uncompressed size: {raw_size_mb:.2f} MB")
    print(f"  - ZIP artifact size: {zip_size_mb:.2f} MB")
    print(f"  - Verified zero __pycache__ / .pyc entries.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Package AuRAG into a clean submission ZIP.")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=REPO_ROOT / "AuRAG-Submission.zip",
        help="Target ZIP path (default: AuRAG-Submission.zip)",
    )
    args = parser.parse_args()
    ret = build_submission_zip(args.output.resolve())
    sys.exit(ret)


if __name__ == "__main__":
    main()
