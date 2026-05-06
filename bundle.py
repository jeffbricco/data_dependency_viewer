#!/usr/bin/env python3
"""
bundle.py — Report Catalog Bundler
===================================
Reads markdown documentation files + dependencies.yaml and generates catalog.js.

Usage:
    python bundle.py           # regenerate catalog.js in same folder
    python bundle.py --check   # validate IDs in dependencies.yaml match known assets

Requirements:
    PyYAML (pip install pyyaml) — falls back to a basic parser if not available.

Folder structure expected:
    source_systems/
        <system_name>.md         ← upstream source system (ERP, CRM, etc.)
    delivery_mechanisms/
        <mechanism_name>.md      ← how data travels (SFTP, Replication, API Pull)
    etl_processes/
        <etl_name>.md            ← process that loads data INTO the data sources
    sources/
        <ServerName>/            ← SQL server group (folder)
            _server.md           ← server documentation (frontmatter + markdown)
            <DatabaseName>/      ← database group (folder)
                _database.md     ← database documentation
                <table_name>.md  ← table/view documentation
        <source-name>.md         ← flat source (API, file, etc.)
    processes/
        <process_name>.md        ← consumer-side process (queries data, feeds reports)
    reports/
        <report_name>.md         ← consumer-side report / dashboard
    dependencies.yaml            ← edge definitions

Markdown frontmatter fields:
    id       (required) unique identifier used in dependencies.yaml
    label    display name (defaults to filename stem)
    subtype  e.g. Table, View, REST API, Python, SSRS, PowerBI (required for leaf nodes)
    owner    team or person responsible
    updated  YYYY-MM-DD of last update
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ─── YAML parsing ─────────────────────────────────────────────────────────────

try:
    import yaml

    def parse_yaml_block(text):
        return yaml.safe_load(text) or {}

    def load_yaml_file(path):
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False

    def parse_yaml_block(text):
        """Minimal YAML scalar parser (no lists, no nested objects)."""
        meta = {}
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, val = line.partition(":")
                val = val.strip().strip("\"'")
                meta[key.strip()] = val
        return meta

    def load_yaml_file(path):
        """Load a YAML file with edge list support (no PyYAML)."""
        with open(path, encoding="utf-8") as f:
            text = f.read()
        # Extract edges manually from the simple format we use
        edges = []
        current = {}
        for line in text.splitlines():
            line_stripped = line.strip()
            if line_stripped.startswith("- source:"):
                current = {"source": line_stripped.split(":", 1)[1].strip()}
            elif line_stripped.startswith("target:") and current:
                current["target"] = line_stripped.split(":", 1)[1].strip()
                edges.append(current)
                current = {}
        return {"edges": edges}


# ─── Frontmatter parser ───────────────────────────────────────────────────────


def parse_frontmatter(text):
    """Split markdown into (meta_dict, body_string)."""
    text = text.strip()
    if not text.startswith("---"):
        return {}, text
    # Find closing ---
    rest = text[3:]
    end = rest.find("\n---")
    if end == -1:
        return {}, text
    yaml_block = rest[:end].strip()
    body = rest[end + 4 :].strip()
    return parse_yaml_block(yaml_block), body


def read_md(path):
    with open(path, encoding="utf-8") as f:
        return parse_frontmatter(f.read())


def make_id(path_stem):
    """Generate a fallback ID from a filename stem."""
    return re.sub(r"[^a-z0-9_]", "_", path_stem.lower())


# ─── Source tree builder ──────────────────────────────────────────────────────


def build_source_tree():
    sources_dir = BASE_DIR / "sources"
    if not sources_dir.exists():
        print("  [warn] sources/ directory not found")
        return []

    result = []

    for item in sorted(sources_dir.iterdir()):
        if item.is_dir():
            result.append(build_server_group(item))
        elif item.suffix == ".md" and not item.name.startswith("_"):
            result.append(build_flat_source(item))

    return result


def build_server_group(server_dir):
    server_md = server_dir / "_server.md"
    meta, docs = ({}, "") if not server_md.exists() else read_md(server_md)

    srv = {
        "id": meta.get("id", make_id(server_dir.name)),
        "type": "server_group",
        "label": meta.get("label", server_dir.name),
        "owner": meta.get("owner", ""),
        "updated": str(meta.get("updated", "")),
        "docs": docs,
        "databases": [],
    }

    for db_dir in sorted(d for d in server_dir.iterdir() if d.is_dir()):
        srv["databases"].append(
            build_database_group(db_dir, default_owner=srv["owner"])
        )

    return srv


def build_database_group(db_dir, default_owner=""):
    db_md = db_dir / "_database.md"
    meta, docs = ({}, "") if not db_md.exists() else read_md(db_md)

    db = {
        "id": meta.get("id", make_id(db_dir.name)),
        "type": "database_group",
        "label": meta.get("label", db_dir.name),
        "owner": meta.get("owner", default_owner),
        "updated": str(meta.get("updated", "")),
        "docs": docs,
        "tables": [],
    }

    for tbl_file in sorted(db_dir.glob("*.md")):
        if tbl_file.name.startswith("_"):
            continue
        meta_t, docs_t = read_md(tbl_file)
        db["tables"].append(
            {
                "id": meta_t.get("id", make_id(tbl_file.stem)),
                "type": "source",
                "subtype": meta_t.get("subtype", "Table"),
                "label": meta_t.get("label", tbl_file.stem),
                "owner": meta_t.get("owner", db["owner"]),
                "updated": str(meta_t.get("updated", "")),
                "docs": docs_t,
            }
        )

    return db


def build_flat_source(md_file):
    meta, docs = read_md(md_file)
    return {
        "id": meta.get("id", make_id(md_file.stem)),
        "type": "source",
        "subtype": meta.get("subtype", "Source"),
        "label": meta.get("label", md_file.stem),
        "owner": meta.get("owner", ""),
        "updated": str(meta.get("updated", "")),
        "docs": docs,
    }


# ─── Process + report readers ─────────────────────────────────────────────────


def read_nodes(folder, default_type):
    directory = BASE_DIR / folder
    if not directory.exists():
        print(f"  [warn] {folder}/ directory not found")
        return []
    nodes = []
    for f in sorted(directory.glob("*.md")):
        meta, docs = read_md(f)
        nodes.append(
            {
                "id": meta.get("id", make_id(f.stem)),
                "type": default_type,
                "subtype": meta.get("subtype", default_type.capitalize()),
                "label": meta.get("label", f.stem),
                "owner": meta.get("owner", ""),
                "updated": str(meta.get("updated", "")),
                "docs": docs,
            }
        )
    return nodes


# ─── Flatten + validate ───────────────────────────────────────────────────────


def flatten_sources(tree):
    """Return all leaf source nodes from the tree."""
    leaves = []
    for item in tree:
        if item["type"] == "server_group":
            for db in item.get("databases", []):
                leaves.extend(db.get("tables", []))
        else:
            leaves.append(item)
    return leaves


def collect_all_ids(
    source_tree,
    processes,
    reports,
    source_systems=None,
    delivery_mechanisms=None,
    etl_processes=None,
):
    ids = set()
    for item in source_tree:
        if item["type"] == "server_group":
            ids.add(item["id"])
            for db in item.get("databases", []):
                ids.add(db["id"])
                for tbl in db.get("tables", []):
                    ids.add(tbl["id"])
        else:
            ids.add(item["id"])
    ids.update(n["id"] for n in processes)
    ids.update(n["id"] for n in reports)
    ids.update(n["id"] for n in (source_systems or []))
    ids.update(n["id"] for n in (delivery_mechanisms or []))
    ids.update(n["id"] for n in (etl_processes or []))
    return ids


def validate(edges, known_ids):
    errors = []
    for e in edges:
        if e.get("source") not in known_ids:
            errors.append(f"  [error] Unknown source ID: '{e.get('source')}'")
        if e.get("target") not in known_ids:
            errors.append(f"  [error] Unknown target ID: '{e.get('target')}'")
    return errors


# ─── Main ─────────────────────────────────────────────────────────────────────


def main():
    check_only = "--check" in sys.argv

    if not HAS_PYYAML:
        print(
            "[warn] PyYAML not found — using fallback parser. Install with: pip install pyyaml"
        )

    print("Reading source systems…")
    source_systems = read_nodes("source_systems", "source_system")

    print("Reading delivery mechanisms…")
    delivery_mechanisms = read_nodes("delivery_mechanisms", "delivery_mechanism")

    print("Reading ETL processes…")
    etl_processes = read_nodes("etl_processes", "etl_process")

    print("Reading sources…")
    source_tree = build_source_tree()
    flat_sources = flatten_sources(source_tree)

    print("Reading processes…")
    processes = read_nodes("processes", "process")

    print("Reading reports…")
    reports = read_nodes("reports", "report")

    print("Reading dependencies…")
    dep_file = BASE_DIR / "dependencies.yaml"
    if dep_file.exists():
        dep_data = load_yaml_file(dep_file)
        edges = dep_data.get("edges", []) if isinstance(dep_data, dict) else []
    else:
        print("  [warn] dependencies.yaml not found — no edges will be set")
        edges = []

    # Validate
    known_ids = collect_all_ids(
        source_tree,
        processes,
        reports,
        source_systems,
        delivery_mechanisms,
        etl_processes,
    )
    errors = validate(edges, known_ids)
    if errors:
        print("\nValidation errors:")
        for e in errors:
            print(e)
        if check_only:
            sys.exit(1)
        print("  [warn] Continuing despite errors — fix IDs in dependencies.yaml\n")
    elif check_only:
        print("✓ All edge IDs are valid")
        return

    # Count leaf sources
    n_source_systems = len(source_systems)
    n_delivery_mechanisms = len(delivery_mechanisms)
    n_etl_processes = len(etl_processes)
    n_sources = len(flat_sources)
    n_processes = len(processes)
    n_reports = len(reports)
    n_edges = len(edges)

    catalog = {
        "meta": {
            "generated": datetime.now().isoformat(timespec="seconds"),
            "counts": {
                "source_systems": n_source_systems,
                "delivery_mechanisms": n_delivery_mechanisms,
                "etl_processes": n_etl_processes,
                "sources": n_sources,
                "processes": n_processes,
                "reports": n_reports,
                "edges": n_edges,
            },
        },
        "sourceSystems": source_systems,
        "deliveryMechanisms": delivery_mechanisms,
        "etlProcesses": etl_processes,
        "sourceTree": source_tree,
        "processes": processes,
        "reports": reports,
        "edges": edges,
    }

    out_path = BASE_DIR / "catalog.js"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("// AUTO-GENERATED by bundle.py — do not edit directly.\n")
        f.write(f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(
            "// Run `python bundle.py` to regenerate after editing markdown files.\n\n"
        )
        f.write("var CATALOG = ")
        f.write(json.dumps(catalog, indent=2, ensure_ascii=False))
        f.write(";\n")

    print(f"\n✓ catalog.js written ({out_path})")
    print(
        f"  {n_source_systems} source systems  |  {n_delivery_mechanisms} delivery mechanisms  |  {n_etl_processes} ETL processes"
    )
    print(
        f"  {n_sources} data sources  |  {n_processes} consumer processes  |  {n_reports} reports  |  {n_edges} edges"
    )

    if errors:
        print(f"\n  ⚠ {len(errors)} validation error(s) — see above")


if __name__ == "__main__":
    main()
