#!/usr/bin/env python3
"""introspect_db.py — one-time SQL Server placeholder generator
================================================================
Connects to one or more databases on a SQL Server, reads table/view metadata
from the system catalog, and writes placeholder markdown files into the catalog
folder tree:

    sources/<Server>/_server.md
    sources/<Server>/<Database>/_database.md
    sources/<Server>/<Database>/<schema>_<object>.md   (one per table/view)

It is SAFE TO RE-RUN: existing files are left untouched (so your hand-written
docs are never lost) unless you pass --refresh, which rewrites only the
tool-owned AUTO section of the body and leaves your prose + frontmatter alone.

Connection
----------
Uses pyodbc with the Microsoft ODBC Driver and Windows / Integrated auth by
default (Trusted_Connection). For SQL logins, pass --sql-auth and set the
CATALOG_DB_USER / CATALOG_DB_PASSWORD environment variables.

    pip install pyodbc          # plus the "ODBC Driver 18 for SQL Server"

Examples
--------
    # Windows auth, two databases on the named instance
    python scripts/introspect_db.py --server PROD-SQL-01 \
        --databases SalesOLTP HumanResources

    # Different network host than the catalog folder name, include views
    python scripts/introspect_db.py --server PROD-SQL-01 \
        --host prod-sql-01.internal.corp --databases SalesOLTP --include-views

    # Preview what would be written, touch nothing
    python scripts/introspect_db.py --server PROD-SQL-01 --databases SalesOLTP --dry-run
"""
import argparse
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from catalog_lib import (  # noqa: E402
    dump_md,
    parse_md,
    slug,
    table_id,
    upsert_auto_section,
    view_id,
)

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_DIR = BASE_DIR / "sources"
TODAY = date.today().isoformat()


# ─── SQL queries ──────────────────────────────────────────────────────────────

OBJECTS_SQL = """
SELECT s.name AS schema_name,
       t.name AS object_name,
       CASE WHEN t.type = 'V' THEN 'View' ELSE 'Table' END AS object_type,
       CAST(ISNULL(p.row_count, 0) AS BIGINT) AS row_count,
       CAST(ep.value AS NVARCHAR(MAX)) AS description
FROM (
    SELECT object_id, name, schema_id, 'U' AS type FROM sys.tables
    UNION ALL
    SELECT object_id, name, schema_id, 'V' AS type FROM sys.views
) t
JOIN sys.schemas s ON s.schema_id = t.schema_id
OUTER APPLY (
    SELECT SUM(row_count) AS row_count
    FROM sys.dm_db_partition_stats ps
    WHERE ps.object_id = t.object_id AND ps.index_id IN (0, 1)
) p
LEFT JOIN sys.extended_properties ep
    ON ep.major_id = t.object_id AND ep.minor_id = 0 AND ep.name = 'MS_Description'
ORDER BY object_type, s.name, t.name
"""

COLUMNS_SQL = """
SELECT s.name AS schema_name,
       t.name AS object_name,
       c.name AS column_name,
       ty.name AS data_type,
       c.max_length, c.precision, c.scale, c.is_nullable,
       CASE WHEN pk.column_id IS NOT NULL THEN 1 ELSE 0 END AS is_pk
FROM sys.columns c
JOIN sys.objects t ON t.object_id = c.object_id AND t.type IN ('U', 'V')
JOIN sys.schemas s ON s.schema_id = t.schema_id
JOIN sys.types ty ON ty.user_type_id = c.user_type_id
LEFT JOIN (
    SELECT ic.object_id, ic.column_id
    FROM sys.index_columns ic
    JOIN sys.indexes i ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    WHERE i.is_primary_key = 1
) pk ON pk.object_id = c.object_id AND pk.column_id = c.column_id
ORDER BY s.name, t.name, c.column_id
"""


def connect(host, database, driver, sql_auth):
    try:
        import pyodbc
    except ImportError:
        sys.exit(
            "ERROR: pyodbc is not installed. Run: pip install pyodbc\n"
            "       and install the Microsoft 'ODBC Driver 18 for SQL Server'."
        )
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={host}",
        f"DATABASE={database}",
        "TrustServerCertificate=yes",
        "Encrypt=yes",
    ]
    if sql_auth:
        user = os.environ.get("CATALOG_DB_USER")
        pwd = os.environ.get("CATALOG_DB_PASSWORD")
        if not user or not pwd:
            sys.exit(
                "ERROR: --sql-auth requires CATALOG_DB_USER and "
                "CATALOG_DB_PASSWORD environment variables."
            )
        parts += [f"UID={user}", f"PWD={pwd}"]
    else:
        parts.append("Trusted_Connection=yes")
    return pyodbc.connect(";".join(parts))


# ─── Type formatting ──────────────────────────────────────────────────────────

_LEN_TYPES = {"varchar", "nvarchar", "char", "nchar", "varbinary", "binary"}
_PREC_TYPES = {"decimal", "numeric"}


def fmt_type(data_type, max_length, precision, scale):
    t = data_type.lower()
    if t in _LEN_TYPES:
        if max_length == -1:
            return f"{data_type}(MAX)"
        length = max_length // 2 if t.startswith("n") else max_length
        return f"{data_type}({length})"
    if t in _PREC_TYPES:
        return f"{data_type}({precision},{scale})"
    return data_type


# ─── File builders ────────────────────────────────────────────────────────────


def write_file(path, text, dry_run, action):
    rel = path.relative_to(BASE_DIR)
    if dry_run:
        print(f"  [dry-run:{action}] {rel}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  [{action}] {rel}")


def ensure_server_md(server_dir, server_name, dry_run):
    path = server_dir / "_server.md"
    if path.exists():
        return
    fields = {
        "id": "srv_" + slug(server_name),
        "label": server_name,
        "owner": "",
        "updated": TODAY,
        "criticality": "",
    }
    body = (
        f"## {server_name}\n\n"
        "_Placeholder generated by introspect_db.py — add server notes here._\n"
    )
    write_file(path, dump_md(fields, body), dry_run, "create")


def ensure_database_md(db_dir, database, server_name, dry_run):
    path = db_dir / "_database.md"
    if path.exists():
        return
    fields = {
        "id": "db_" + slug(database),
        "label": database,
        "owner": "",
        "updated": TODAY,
        "criticality": "",
    }
    body = (
        f"## {database}\n\n"
        f"_Placeholder generated by introspect_db.py from `{server_name}`._\n"
    )
    write_file(path, dump_md(fields, body), dry_run, "create")


def build_object_body(obj, columns):
    """The AUTO section content: row count + column grid."""
    lines = []
    rc = obj["row_count"]
    lines.append(f"**Object:** `{obj['schema']}.{obj['name']}`  ·  "
                 f"**Type:** {obj['type']}  ·  **Approx rows:** {rc:,}")
    lines.append("")
    lines.append("| Column | Type | Null | Key |")
    lines.append("|---|---|---|---|")
    for c in columns:
        key = "PK" if c["is_pk"] else ""
        null = "NULL" if c["is_nullable"] else "NOT NULL"
        lines.append(f"| `{c['name']}` | {c['type']} | {null} | {key} |")
    return "\n".join(lines)


def ensure_object_md(db_dir, database, obj, columns, dry_run, force, refresh):
    fname = f"{slug(obj['schema'])}_{slug(obj['name'])}.md"
    path = db_dir / fname
    oid = (view_id if obj["type"] == "View" else table_id)(
        database, obj["schema"], obj["name"]
    )
    auto = build_object_body(obj, columns)

    if path.exists():
        if not (force or refresh):
            print(f"  [skip] {path.relative_to(BASE_DIR)} (exists)")
            return
        # Refresh: keep frontmatter + prose, replace only the AUTO column grid.
        fields, body = parse_md(path.read_text(encoding="utf-8"))
        fields.setdefault("id", oid)
        fields["updated"] = TODAY
        new_body = upsert_auto_section(body, "schema", auto)
        write_file(path, dump_md(fields, new_body), dry_run, "refresh")
        return

    fields = {
        "id": oid,
        "label": f"{obj['schema']}.{obj['name']}",
        "subtype": obj["type"],
        "owner": "",
        "updated": TODAY,
        "criticality": "",
        # extra hints used by scan_ssrs.py to match report SQL → this asset:
        "database": database,
        "object": f"{obj['schema']}.{obj['name']}",
        "depends_on": [],
    }
    heading = f"## {obj['schema']}.{obj['name']}"
    desc = (obj.get("description") or "").strip()
    intro = desc if desc else "_Placeholder generated by introspect_db.py._"
    body = upsert_auto_section(f"{heading}\n\n{intro}\n", "schema", auto)
    write_file(path, dump_md(fields, body), dry_run, "create")


# ─── Per-database driver ──────────────────────────────────────────────────────


def process_database(conn, server_dir, database, server_name, args):
    cur = conn.cursor()
    cur.execute(OBJECTS_SQL)
    objects = []
    for row in cur.fetchall():
        if row.object_type == "View" and not args.include_views:
            continue
        objects.append(
            {
                "schema": row.schema_name,
                "name": row.object_name,
                "type": row.object_type,
                "row_count": int(row.row_count or 0),
                "description": row.description,
            }
        )

    cur.execute(COLUMNS_SQL)
    cols_by_obj = {}
    for row in cur.fetchall():
        cols_by_obj.setdefault((row.schema_name, row.object_name), []).append(
            {
                "name": row.column_name,
                "type": fmt_type(row.data_type, row.max_length, row.precision, row.scale),
                "is_nullable": bool(row.is_nullable),
                "is_pk": bool(row.is_pk),
            }
        )

    db_dir = server_dir / database
    ensure_database_md(db_dir, database, server_name, args.dry_run)
    for obj in objects:
        cols = cols_by_obj.get((obj["schema"], obj["name"]), [])
        ensure_object_md(
            db_dir, database, obj, cols, args.dry_run, args.force, args.refresh
        )
    print(f"  → {database}: {len(objects)} object(s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", required=True,
                    help="Server name — also the sources/<Server>/ folder name")
    ap.add_argument("--databases", required=True, nargs="+",
                    help="One or more database names to introspect")
    ap.add_argument("--host", default=None,
                    help="Network host/instance if different from --server")
    ap.add_argument("--driver", default="ODBC Driver 18 for SQL Server",
                    help="ODBC driver name (default: ODBC Driver 18 for SQL Server)")
    ap.add_argument("--sql-auth", action="store_true",
                    help="Use SQL login from CATALOG_DB_USER/CATALOG_DB_PASSWORD "
                         "instead of Windows auth")
    ap.add_argument("--include-views", action="store_true",
                    help="Also generate placeholders for views")
    ap.add_argument("--force", action="store_true",
                    help="Refresh the AUTO section of existing object files")
    ap.add_argument("--refresh", action="store_true",
                    help="Alias for --force (refresh AUTO sections, keep prose)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would change without writing files")
    args = ap.parse_args()

    host = args.host or args.server
    server_dir = SOURCES_DIR / args.server
    print(f"Server folder: sources/{args.server}/  (host: {host})")
    ensure_server_md(server_dir, args.server, args.dry_run)

    for database in args.databases:
        print(f"\nConnecting to [{database}] on {host}…")
        try:
            conn = connect(host, database, args.driver, args.sql_auth)
        except Exception as exc:  # pyodbc.Error et al.
            print(f"  [error] could not connect to {database}: {exc}")
            continue
        try:
            process_database(conn, server_dir, database, args.server, args)
        finally:
            conn.close()

    print("\nDone. Next: run `python bundle.py` to regenerate the catalog.")
    if args.dry_run:
        print("(dry-run — no files were written)")


if __name__ == "__main__":
    main()
