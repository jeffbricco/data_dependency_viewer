"""catalog_lib.py — shared helpers for the catalog generator scripts.

Provides slug/ID helpers, an order-preserving frontmatter reader/writer, and
AUTO-section markers so tool-generated content can be refreshed in place without
destroying hand-written documentation or manual `depends_on` edits.
"""
import re
from collections import OrderedDict

# ─── IDs / slugs ──────────────────────────────────────────────────────────────


def slug(s):
    """Lowercase, replace non-alphanumerics with underscore, collapse repeats."""
    s = re.sub(r"[^a-z0-9]+", "_", str(s).lower())
    return s.strip("_")


def table_id(database, schema, table):
    return "tbl_" + slug(f"{database}_{schema}_{table}")


def view_id(database, schema, view):
    return "vw_" + slug(f"{database}_{schema}_{view}")


def report_id(name):
    return "rpt_" + slug(name)


# ─── Frontmatter (order-preserving, list-aware) ───────────────────────────────
#
# Values are either a str (scalar) or a list[str] (block/inline YAML list).
# This is intentionally a tiny subset of YAML — enough for our flat frontmatter,
# and it round-trips without needing PyYAML installed.


def parse_md(text):
    """Split a markdown file into (OrderedDict frontmatter, body string)."""
    fields = OrderedDict()
    if not text.startswith("---"):
        return fields, text
    end = text.find("\n---", 3)
    if end == -1:
        return fields, text
    fm = text[3:end].strip("\n")
    body = text[end + 4:]
    if body.startswith("\n"):
        body = body[1:]

    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("- "):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            items = [s.strip().strip("\"'") for s in val[1:-1].split(",")]
            fields[key] = [s for s in items if s]
        elif val == "":
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:].strip().strip("\"'"))
                i += 1
            fields[key] = items  # empty list if no items followed
        else:
            fields[key] = val.strip("\"'")
    return fields, body


def dump_md(fields, body):
    """Render (frontmatter, body) back into a markdown string."""
    out = ["---"]
    for key, val in fields.items():
        if isinstance(val, list):
            if val:
                out.append(f"{key}:")
                out.extend(f"  - {v}" for v in val)
            else:
                out.append(f"{key}: []")
        else:
            out.append(f"{key}: {val}")
    out.append("---")
    text = "\n".join(out) + "\n"
    if body:
        text += "\n" + body.lstrip("\n")
    if not text.endswith("\n"):
        text += "\n"
    return text


# ─── AUTO-generated body sections ─────────────────────────────────────────────


def _markers(name):
    return f"<!-- AUTO:{name}:start -->", f"<!-- AUTO:{name}:end -->"


def upsert_auto_section(body, name, content):
    """Insert or replace a delimited AUTO section in the body.

    Content between the markers is fully owned by the tool and overwritten on
    every refresh; everything outside the markers is hand-written and preserved.
    If the markers are absent, the section is appended.
    """
    start, end = _markers(name)
    block = f"{start}\n{content.rstrip()}\n{end}"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if pattern.search(body):
        return pattern.sub(lambda _: block, body)
    sep = "" if body.endswith("\n\n") or not body else "\n\n"
    return body.rstrip("\n") + ("\n\n" if body.strip() else "") + block + "\n"
