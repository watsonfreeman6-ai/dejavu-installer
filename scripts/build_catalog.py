"""Build Dejavu skill catalog SQLite FTS5 database from source files.

Reads from catalog/ directory (YAML or JSON skill manifests).
Outputs a single catalog.db with FTS5 index.
Uses sqlite3 stdlib only — no dependencies beyond Python.

Usage:
    python scripts/build_catalog.py --output catalog.db
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional


def build_catalog(source_dir: Path, output_path: Path) -> int:
    """Build catalog.db from source files. Returns number of skills indexed."""
    skills = _load_skills(source_dir)
    if not skills:
        print("WARNING: No skills found in", source_dir)
        return 0
    
    conn = sqlite3.connect(str(output_path))
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Create tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            slug TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            category TEXT DEFAULT 'uncategorized',
            grade TEXT DEFAULT 'B',
            source_url TEXT DEFAULT '',
            version TEXT DEFAULT '',
            author TEXT DEFAULT '',
            license TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Create FTS5 index
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts USING fts5(
            slug, name, description, category,
            content='skills',
            content_rowid='rowid'
        )
    """)
    
    # Insert/update skills
    count = 0
    for skill in skills:
        conn.execute("""
            INSERT OR REPLACE INTO skills (slug, name, description, category, grade, source_url, version, author, license, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            skill.get("slug", ""),
            skill.get("name", skill.get("slug", "")),
            skill.get("description", ""),
            skill.get("category", "uncategorized"),
            skill.get("grade", "B"),
            skill.get("source_url", ""),
            skill.get("version", ""),
            skill.get("author", ""),
            skill.get("license", ""),
        ))
        count += 1
    
    # Rebuild FTS5
    conn.execute("INSERT INTO skills_fts(skills_fts) VALUES('rebuild')")
    
    conn.commit()
    conn.close()
    
    print(f"Catalog built: {count} skills → {output_path} ({output_path.stat().st_size} bytes)")
    return count


def _load_skills(source_dir: Path) -> List[Dict]:
    """Load skill manifests from YAML or JSON files in source_dir."""
    skills = []
    
    if not source_dir.exists():
        return skills
    
    for path in source_dir.rglob("*"):
        if path.suffix in (".json",):
            try:
                data = json.loads(path.read_text())
                if isinstance(data, list):
                    skills.extend(data)
                elif isinstance(data, dict):
                    skills.append(data)
            except Exception:
                continue
        elif path.suffix in (".yaml", ".yml"):
            try:
                import yaml
                data = yaml.safe_load(path.read_text())
                if isinstance(data, list):
                    skills.extend(data)
                elif isinstance(data, dict):
                    skills.append(data)
            except Exception:
                continue
    
    return skills


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Dejavu catalog database")
    parser.add_argument("--output", default="catalog.db", help="Output path")
    parser.add_argument("--source", default="catalog", help="Source directory")
    args = parser.parse_args()
    
    source = Path(args.source)
    output = Path(args.output)
    
    count = build_catalog(source, output)
    if count == 0:
        sys.exit(1)
