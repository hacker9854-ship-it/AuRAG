"""ANSI/ISA-5.1 Industrial Equipment Tag Normalization Engine.

Resolves fragmented, inconsistent legacy plant equipment identifiers (e.g.
"P101", "P_101", "101-PUMP", "P-101-A", "Pump 101") into canonical ANSI/ISA-5.1
standard tags (e.g. "P-101", "P-101A").

Ensures that heterogeneous data from SAP PM, SCADA/PI historians, and engineering
SOPs link deterministically to identical nodes in the Neo4j Knowledge Graph.
"""
import re
from typing import NamedTuple

# Canonical equipment prefix mappings
PREFIX_MAP = {
    "P": "P",
    "PMP": "P",
    "PUMP": "P",
    "TK": "TK",
    "TNK": "TK",
    "TANK": "TK",
    "HEX": "HEX",
    "EXCH": "HEX",
    "E": "HEX",
    "C": "C",
    "CMP": "C",
    "COMP": "C",
    "COMPRESSOR": "C",
    "M": "M",
    "MOT": "M",
    "MOTOR": "M",
    "CV": "CV",
    "FV": "FV",
    "PV": "PV",
    "LV": "LV",
    "TI": "TI",
    "PI": "PI",
    "FI": "FI",
    "LI": "LI",
    "V": "V",
    "VSL": "V",
    "VESSEL": "V",
    "BLR": "BLR",
    "BOILER": "BLR",
}

# Regex pattern matching variations:
# Group 1: Prefix (letters)
# Group 2: Numeric identifier (digits)
# Group 3: Optional sub-train or train suffix (e.g. A, B, -A, /A)
_TAG_PATTERN_A = re.compile(
    r"\b([A-Za-z]{1,10})[-_\s]*0*(\d{1,5})[-_\s/]*([A-Za-z])?\b"
)
# Pattern for reversed prefix e.g. "101-PUMP", "101_P"
_TAG_PATTERN_B = re.compile(
    r"\b0*(\d{1,5})[-_\s]*([A-Za-z]{1,10})[-_\s/]*([A-Za-z])?\b"
)


class ParsedTag(NamedTuple):
    prefix: str
    number: int
    suffix: str
    canonical: str


def normalize_equipment_tag(raw_tag: str) -> str | None:
    """Normalize a raw equipment string into its canonical ISA-5.1 tag format.
    
    Examples:
        'P101'      -> 'P-101'
        'P_101_A'   -> 'P-101A'
        '101-PUMP'  -> 'P-101'
        'Pump 101'  -> 'P-101'
        'TK-0301'   -> 'TK-301'
        'CV-105'    -> 'CV-105'
    """
    if not raw_tag or not isinstance(raw_tag, str):
        return None

    cleaned = raw_tag.strip()

    # Try standard Prefix-Number pattern
    match_a = _TAG_PATTERN_A.match(cleaned)
    if match_a:
        raw_prefix, raw_num, raw_suffix = match_a.groups()
        prefix_key = raw_prefix.upper()
        if prefix_key in PREFIX_MAP:
            canonical_prefix = PREFIX_MAP[prefix_key]
            num = int(raw_num)
            suffix = raw_suffix.upper() if raw_suffix else ""
            return f"{canonical_prefix}-{num}{suffix}"

    # Try Number-Prefix pattern e.g. "101-PUMP"
    match_b = _TAG_PATTERN_B.match(cleaned)
    if match_b:
        raw_num, raw_prefix, raw_suffix = match_b.groups()
        prefix_key = raw_prefix.upper()
        if prefix_key in PREFIX_MAP:
            canonical_prefix = PREFIX_MAP[prefix_key]
            num = int(raw_num)
            suffix = raw_suffix.upper() if raw_suffix else ""
            return f"{canonical_prefix}-{num}{suffix}"

    # Return uppercase alphanumeric if already structured
    if re.match(r"^[A-Z]{1,4}-\d{1,5}[A-Z]?$", cleaned):
        return cleaned

    return None


def extract_canonical_tags(text: str) -> list[str]:
    """Extract all valid, normalized equipment tags from a block of unstructured text."""
    if not text:
        return []

    found = set()
    # Search for all candidate tokens
    for match in _TAG_PATTERN_A.finditer(text):
        raw_prefix, raw_num, raw_suffix = match.groups()
        prefix_key = raw_prefix.upper()
        if prefix_key in PREFIX_MAP:
            canonical_prefix = PREFIX_MAP[prefix_key]
            num = int(raw_num)
            suffix = raw_suffix.upper() if raw_suffix else ""
            found.add(f"{canonical_prefix}-{num}{suffix}")

    for match in _TAG_PATTERN_B.finditer(text):
        raw_num, raw_prefix, raw_suffix = match.groups()
        prefix_key = raw_prefix.upper()
        if prefix_key in PREFIX_MAP:
            canonical_prefix = PREFIX_MAP[prefix_key]
            num = int(raw_num)
            suffix = raw_suffix.upper() if raw_suffix else ""
            found.add(f"{canonical_prefix}-{num}{suffix}")

    return sorted(list(found))
