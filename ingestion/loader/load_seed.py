"""Phase 1 entry point: apply infra/neo4j/schema.cypher, then every script in
infra/neo4j/seed/ (in filename order) against the AuraDB instance in .env.

Usage: python load_seed.py
"""
import os
import sys
from pathlib import Path

import truststore  # ponytail: certifi's bundle fails chain-building on this
truststore.inject_into_ssl()  # host's SSL.com/Certum cert (OpenSSL 3.x bug); OS store works

from dotenv import load_dotenv
from neo4j import GraphDatabase

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_FILE = REPO_ROOT / "infra" / "neo4j" / "schema.cypher"
SEED_DIR = REPO_ROOT / "infra" / "neo4j" / "seed"


def split_statements(cypher_text: str) -> list[str]:
    """Split a .cypher file into individual statements on ';', respecting
    single-quoted string literals (some seed text itself contains ';') and
    stripping '//' line comments outside of strings."""
    statements = []
    buf = []
    in_string = False
    i = 0
    n = len(cypher_text)
    while i < n:
        ch = cypher_text[i]
        if in_string:
            buf.append(ch)
            if ch == "'":
                in_string = False
        else:
            if ch == "'":
                in_string = True
                buf.append(ch)
            elif ch == "/" and i + 1 < n and cypher_text[i + 1] == "/":
                # skip to end of line
                while i < n and cypher_text[i] != "\n":
                    i += 1
                continue
            elif ch == ";":
                stmt = "".join(buf).strip()
                if stmt:
                    statements.append(stmt)
                buf = []
            else:
                buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def run_file(driver, database: str, path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    statements = split_statements(text)
    print(f"-- {path.relative_to(REPO_ROOT)} ({len(statements)} statement(s))")
    with driver.session(database=database) as session:
        for stmt in statements:
            session.run(stmt)


def main() -> None:
    load_dotenv(REPO_ROOT / ".env")
    uri = os.environ.get("NEO4J_URI")
    username = os.environ.get("NEO4J_USERNAME")
    password = os.environ.get("NEO4J_PASSWORD")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    if not all([uri, username, password]):
        print(
            "Missing NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD. "
            "Copy .env.example to .env in the repo root and fill them in.",
            file=sys.stderr,
        )
        sys.exit(1)

    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    print(f"Connected to {uri} (database={database})")

    try:
        run_file(driver, database, SCHEMA_FILE)
        for seed_file in sorted(SEED_DIR.glob("*.cypher")):
            run_file(driver, database, seed_file)
    finally:
        driver.close()

    print("Done.")


if __name__ == "__main__":
    main()
