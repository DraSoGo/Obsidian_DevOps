"""Generate mkdocs pages from Obsidian notes.

- Copies every .md in the vault into docs/ (same folder layout)
- Rewrites Obsidian wiki-links [[a/b|name]] and image embeds ![[asset/...]]
- Converts Obsidian callouts (> [!summary] ...) to MkDocs admonitions
- Handles in-page heading links [[#Heading]] -> [#Heading](#heading)
"""
from pathlib import Path
import shutil
import re

VAULT = Path(__file__).resolve().parent.parent   # repo root
DOCS = VAULT / "docs"

WIKI_LINK = re.compile(r"(!?)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")

# Obsidian callout type -> MkDocs admonition type
CALLOUT_MAP = {
    "summary": "abstract",
    "tldr": "abstract",
    "info": "info",
    "todo": "info",
    "tip": "tip",
    "hint": "tip",
    "important": "tip",
    "success": "success",
    "check": "success",
    "done": "success",
    "question": "question",
    "help": "question",
    "faq": "question",
    "warning": "warning",
    "caution": "warning",
    "attention": "warning",
    "failure": "failure",
    "fail": "failure",
    "missing": "failure",
    "danger": "danger",
    "error": "danger",
    "bug": "bug",
    "example": "example",
    "quote": "quote",
    "cite": "quote",
    "note": "note",
}


def slugify_heading(heading: str) -> str:
    """MkDocs/Markdown anchor for a heading (lowercase, strip punct, spaces->-)."""
    s = heading.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    return re.sub(r"[\s]+", "-", s)


def rewrite_links(text: str) -> str:
    def repl(m):
        bang, target, label = m.group(1), m.group(2).strip(), m.group(3)
        if bang:  # image embed — copied verbatim under docs/asset/...
            return f"![](../{target.strip('/')})" if "/" in target else f"![]({target})"

        # in-page heading link [[#Some Heading]]
        if target.startswith("#"):
            heading = target[1:].strip()
            return f"[{label or heading}](#{slugify_heading(heading)})"

        page = target.split("#")[0]
        anchor = ""
        if "#" in target:
            anchor = "#" + slugify_heading(target.split("#", 1)[1])
        label = label or page
        if not page:
            return label
        for candidate in sorted({page, page.replace(" ", "_")}):
            hits = [p for p in DOCS.rglob(f"{candidate}.md") if p.stem == candidate] \
                or [p for p in DOCS.rglob(f"{candidate}/index.md") if p.parent.name == candidate]
            if hits:
                rel = hits[0].relative_to(DOCS).as_posix()
                return f"[{label}](../{rel}/{anchor})"
        return label  # coming-soon topic — plain text, no markup
    return WIKI_LINK.sub(repl, text)


def rewrite_callouts(text: str) -> str:
    """Convert Obsidian callout blocks to MkDocs admonitions.

    > [!info] Title
    > body line
    becomes
    !!! info "Title"
        body line
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^>\s*\[!(\w+)\]\s*(.*)$", lines[i])
        if m:
            ctype = CALLOUT_MAP.get(m.group(1).lower())
            title = m.group(2).strip()
            if ctype:
                out.append(f'!!! {ctype} "{title}"' if title else f"!!! {ctype}")
                i += 1
                # body: consecutive "> " lines, keep relative indent
                while i < len(lines) and lines[i].lstrip().startswith(">"):
                    body = re.sub(r"^\s*>\s?", "", lines[i])
                    out.append(f"    {body}" if body else "")
                    i += 1
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def rewrite(text: str) -> str:
    text = rewrite_links(text)
    text = rewrite_callouts(text)
    return text


def build():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)

    if (VAULT / "asset").exists():
        shutil.copytree(VAULT / "asset", DOCS / "asset")

    for md in VAULT.rglob("*.md"):
        rel = md.relative_to(VAULT)
        if rel.parts[0] in {".git", "docs", "scripts"}:
            continue
        if len(rel.parts) == 1 and rel.stem in {"Index", "README"}:
            continue  # handled separately below
        target = DOCS / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rewrite(md.read_text(encoding="utf-8")), encoding="utf-8")

    if (VAULT / "Index.md").exists():
        (DOCS / "index.md").write_text(
            rewrite((VAULT / "Index.md").read_text(encoding="utf-8")),
            encoding="utf-8",
        )

    print("docs generated:", len(list(DOCS.rglob("*.md"))), "pages")


if __name__ == "__main__":
    build()
