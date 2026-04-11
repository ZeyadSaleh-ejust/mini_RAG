"""
Deduplicate islamweb_fatawa.jsonl by fatwa ID.
Keeps the first occurrence of each ID, removes any duplicates.
Overwrites the file in-place.
"""

import json
from pathlib import Path

INPUT_FILE = Path(__file__).parent / "islamweb_fatawa.jsonl"


def deduplicate(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    total = len(lines)

    seen = set()
    unique_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"  ⚠ Skipping malformed line: {e}")
            continue

        fatwa_id = record.get("id")
        if fatwa_id in seen:
            continue
        seen.add(fatwa_id)
        unique_lines.append(line)

    duplicates_removed = total - len(unique_lines)

    path.write_text("\n".join(unique_lines) + "\n", encoding="utf-8")

    print(f"✓ Done.")
    print(f"  Total records read : {total}")
    print(f"  Unique records kept: {len(unique_lines)}")
    print(f"  Duplicates removed : {duplicates_removed}")
    print(f"  File saved → {path.resolve()}")


if __name__ == "__main__":
    print(f"Deduplicating: {INPUT_FILE.resolve()}\n")
    deduplicate(INPUT_FILE)
