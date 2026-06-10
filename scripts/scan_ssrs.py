#!/usr/bin/env python3
"""scan_ssrs.py — generate report placeholders from a folder of SSRS .rdl files
================================================================================
Points at a directory of SSRS report definitions (.rdl, which are XML) and, for
each report, writes/updates reports/<report-name>.md with:

  * frontmatter: id, label, subtype: SSRS, owner, updated, criticality,
    depends_on (MANUAL — yours to edit) and depends_on_auto (TOOL — inferred)
  * an AUTO body section listing each dataset, its data source/database, and the
    tables/procs referenced in its SQL.

Dependency inference is a FIRST PASS. The tool fills `depends_on_auto` by parsing
each dataset's SQL and matching referenced tables to catalog asset IDs. Your
hand-curated edges live in `depends_on` and are NEVER touched by a re-scan.

Re-running
----------
  * Default: only creates files for reports that don't have a .md yet. Existing
    reports are left completely alone.
  * --refresh: re-derive depends_on_auto and the AUTO body for ALL reports,
    preserving manual depends_on and any prose you added outside the markers.
  * --only "Report Name": refresh just one report (do this when you've tuned one
    by hand and want to re-pull only its auto data).

Examples
--------
    python scripts/scan_ssrs.py --rdl-dir /srv/ssrs/reports
    python scripts/scan_ssrs.py --rdl-dir ./rdl --owner "BI Team"
    python scripts/scan_ssrs.py --rdl-dir ./rdl --refresh
    python scripts/scan_ssrs.py --rdl-dir ./rdl --only "Monthly Sales Report"
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from catalog_lib import (  # noqa: E402
    dump_md,
    parse_md,
    report_id,
    slug,
    upsert_auto_section,
)

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
SOURCES_DIR = BASE_DIR / "sources"
TODAY = date.today().isoformat()


# ─── Namespace-agnostic XML helpers ───────────────────────────────────────────


def local(tag):
    return tag.rsplit("}", 1)[-1]


def findall_local(elem, name):
    return [e for e in elem.iter() if local(e.tag) == name]


def first_child_text(elem, name):
    for child in elem:
        if local(child.tag) == name and child.text:
            return child.text.strip()
    return None


# ─── RDL parsing ──────────────────────────────────────────────────────────────


def parse_rdl(path):
    """Return dict: name, description, datasets[{name, datasource, command}],
    datasource_db {datasource_name: database}."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        print(f"  [error] {path.name}: malformed XML ({exc})")
        return None

    # Map embedded data sources → database (from ConnectString).
    datasource_db = {}
    for ds in findall_local(root, "DataSource"):
        name = ds.get("Name")
        if not name:
            continue
        conn = None
        for cs in findall_local(ds, "ConnectString"):
            conn = cs.text
        if conn:
            m = re.search(r"(?:Initial Catalog|Database)\s*=\s*([^;]+)", conn, re.I)
            if m:
                datasource_db[name] = m.group(1).strip()
        else:
            datasource_db.setdefault(name, None)

    datasets = []
    for dset in findall_local(root, "DataSet"):
        name = dset.get("Name") or "dataset"
        command, datasource = None, None
        for q in findall_local(dset, "Query"):
            command = first_child_text(q, "CommandText") or command
            datasource = first_child_text(q, "DataSourceName") or datasource
        if command is None:  # some RDLs put CommandText directly under DataSet
            for ct in findall_local(dset, "CommandText"):
                command = ct.text
                break
        datasets.append(
            {"name": name, "datasource": datasource, "command": command or ""}
        )

    description = None
    for d in findall_local(root, "Description"):
        if d.text:
            description = d.text.strip()
            break

    return {
        "name": path.stem,
        "description": description,
        "datasets": datasets,
        "datasource_db": datasource_db,
    }


# ─── SQL object extraction ────────────────────────────────────────────────────

_OBJ = r"\[?\w+\]?(?:\.\[?\w+\]?){0,2}"
_FROM_JOIN = re.compile(rf"\b(?:FROM|JOIN)\s+({_OBJ})", re.I)
_EXEC = re.compile(rf"\b(?:EXEC|EXECUTE)\s+({_OBJ})", re.I)


def strip_brackets(s):
    return s.replace("[", "").replace("]", "")


def extract_objects(sql):
    """Return ordered unique list of referenced object names from SQL text."""
    if not sql:
        return []
    found, seen = [], set()
    for m in list(_FROM_JOIN.finditer(sql)) + list(_EXEC.finditer(sql)):
        name = strip_brackets(m.group(1)).strip()
        # skip obvious table aliases / subquery openers
        if name.lower() in ("(", "select"):
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            found.append(name)
    return found


def normalize_ref(name):
    """Normalize a SQL object reference to (database_or_None, schema.table)."""
    parts = name.split(".")
    if len(parts) == 3:
        return parts[0].lower(), f"{parts[1]}.{parts[2]}".lower()
    if len(parts) == 2:
        return None, f"{parts[0]}.{parts[1]}".lower()
    return None, parts[0].lower()  # bare table, schema unknown


# ─── Catalog asset index (for matching) ───────────────────────────────────────


def build_catalog_index():
    """Scan source markdown for table/view assets to match SQL refs against.

    Returns:
        by_qual:  'schema.table' -> id            (may be ambiguous → list)
        by_bare:  'table'        -> id            (may be ambiguous → list)
        by_db_qual: 'db.schema.table' -> id
    """
    by_qual, by_bare, by_db_qual = {}, {}, {}

    def add(d, key, _id):
        d.setdefault(key, [])
        if _id not in d[key]:
            d[key].append(_id)

    for md in SOURCES_DIR.rglob("*.md"):
        if md.name.startswith("_"):
            continue
        fields, _ = parse_md(md.read_text(encoding="utf-8"))
        _id = fields.get("id")
        if not _id:
            continue
        obj = fields.get("object")  # 'schema.table' (set by introspect_db.py)
        label = fields.get("label", "")
        db = (fields.get("database") or "").lower()

        quals = set()
        if isinstance(obj, str) and "." in obj:
            quals.add(obj.lower())
        if isinstance(label, str) and "." in label:
            quals.add(label.lower())  # e.g. "dbo.Orders"
        for q in quals:
            add(by_qual, q, _id)
            bare = q.split(".")[-1]
            add(by_bare, bare, _id)
            if db:
                add(by_db_qual, f"{db}.{q}", _id)
        if not quals:  # label without schema, treat whole as bare table name
            bare = slug(label) if label else None
            if bare:
                add(by_bare, label.lower(), _id)
    return by_qual, by_bare, by_db_qual


def match_ref(ref, dataset_db, index):
    by_qual, by_bare, by_db_qual = index
    db, qual = normalize_ref(ref)
    db = db or (dataset_db or "").lower() or None

    if db and "." in qual and f"{db}.{qual}" in by_db_qual:
        cands = by_db_qual[f"{db}.{qual}"]
        if len(cands) == 1:
            return cands[0]
    if "." in qual and qual in by_qual:
        cands = by_qual[qual]
        if len(cands) == 1:
            return cands[0]
    bare = qual.split(".")[-1]
    if bare in by_bare and len(by_bare[bare]) == 1:
        return by_bare[bare][0]
    return None  # unmatched or ambiguous → left for manual wiring


# ─── Report markdown builder ──────────────────────────────────────────────────


def build_auto_body(rdl, matched, unmatched):
    lines = ["### Datasets (auto-extracted from RDL)", ""]
    lines.append("| Dataset | Data Source | Database | Referenced Objects |")
    lines.append("|---|---|---|---|")
    for ds in rdl["datasets"]:
        db = rdl["datasource_db"].get(ds["datasource"]) or ""
        objs = ", ".join(f"`{o}`" for o in extract_objects(ds["command"])) or "—"
        lines.append(f"| {ds['name']} | {ds['datasource'] or '—'} | {db or '—'} | {objs} |")
    lines.append("")
    if matched:
        lines.append("**Matched to catalog assets:** "
                     + ", ".join(f"`{m}`" for m in matched))
    if unmatched:
        lines.append("")
        lines.append("**Unmatched references** (wire these manually into "
                     "`depends_on` if they belong in the catalog): "
                     + ", ".join(f"`{u}`" for u in unmatched))
    return "\n".join(lines)


def process_report(rdl, index, owner, dry_run, refresh, only):
    name = rdl["name"]
    if only and name.lower() != only.lower():
        return
    path = REPORTS_DIR / f"{slug(name)}.md"

    # Collect auto-matched dependency IDs + unmatched refs across all datasets.
    auto_ids, unmatched = [], []
    for ds in rdl["datasets"]:
        ds_db = rdl["datasource_db"].get(ds["datasource"])
        for ref in extract_objects(ds["command"]):
            mid = match_ref(ref, ds_db, index)
            if mid:
                if mid not in auto_ids:
                    auto_ids.append(mid)
            elif ref not in unmatched:
                unmatched.append(ref)

    auto_body = build_auto_body(rdl, auto_ids, unmatched)
    rel = path.relative_to(BASE_DIR)

    if path.exists():
        if not (refresh or only):
            print(f"  [skip] {rel} (exists — use --refresh to update auto data)")
            return
        fields, body = parse_md(path.read_text(encoding="utf-8"))
        fields["depends_on_auto"] = auto_ids          # tool-owned → overwrite
        fields.setdefault("depends_on", [])           # manual → keep as-is
        fields["updated"] = TODAY
        new_body = upsert_auto_section(body, "datasets", auto_body)
        _write(path, dump_md(fields, new_body), dry_run, "refresh", rel)
        return

    fields = {
        "id": report_id(name),
        "label": name.replace("_", " "),
        "subtype": "SSRS",
        "owner": owner,
        "updated": TODAY,
        "criticality": "",
        "depends_on": [],
        "depends_on_auto": auto_ids,
    }
    intro = rdl["description"] or "_Placeholder generated by scan_ssrs.py._"
    body = upsert_auto_section(f"## {fields['label']}\n\n{intro}\n", "datasets", auto_body)
    _write(path, dump_md(fields, body), dry_run, "create", rel)


def _write(path, text, dry_run, action, rel):
    if dry_run:
        print(f"  [dry-run:{action}] {rel}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  [{action}] {rel}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rdl-dir", required=True,
                    help="Directory containing .rdl files (searched recursively)")
    ap.add_argument("--owner", default="",
                    help="Default owner to stamp on newly created report files")
    ap.add_argument("--refresh", action="store_true",
                    help="Re-derive auto deps + AUTO body for existing reports "
                         "(manual depends_on and prose are preserved)")
    ap.add_argument("--only", default=None,
                    help="Refresh just the report with this name")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would change without writing files")
    args = ap.parse_args()

    rdl_dir = Path(args.rdl_dir).expanduser()
    if not rdl_dir.is_dir():
        sys.exit(f"ERROR: --rdl-dir not found: {rdl_dir}")

    rdl_files = sorted(rdl_dir.rglob("*.rdl"))
    if not rdl_files:
        sys.exit(f"ERROR: no .rdl files found under {rdl_dir}")

    print(f"Indexing catalog source assets for dependency matching…")
    index = build_catalog_index()
    print(f"Found {len(rdl_files)} .rdl file(s) under {rdl_dir}\n")

    for rdl_path in rdl_files:
        rdl = parse_rdl(rdl_path)
        if rdl is None:
            continue
        process_report(rdl, index, args.owner, args.dry_run, args.refresh, args.only)

    print("\nDone. Next: run `python bundle.py` to regenerate the catalog.")
    if args.dry_run:
        print("(dry-run — no files were written)")


if __name__ == "__main__":
    main()
