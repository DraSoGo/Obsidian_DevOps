"""Generate mkdocs pages from Obsidian notes.

- Copies every .md in the vault into docs/ (same folder layout)
- Rewrites Obsidian wiki-links [[a/b|name]] and image embeds ![[asset/...]]
- Adds a nav placeholder per planned topic folder (coming soon)
"""
from pathlib import Path
import shutil
import re

VAULT = Path(__file__).resolve().parent.parent   # repo root
DOCS = VAULT / "docs"

WIKI_LINK = re.compile(r"(!?)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def rewrite_links(text: str) -> str:
    def repl(m):
        bang, target, label = m.group(1), m.group(2).strip(), m.group(3)
        if bang:  # image embed — copied verbatim under docs/asset/...
            return f"![](../{target.strip('/')})" if "/" in target else f"![]({target})"
        page = target.split("#")[0]
        anchor = ""
        if "#" in target:
            anchor = "#" + target.split("#", 1)[1].strip().lower().replace(" ", "-")
        label = label or page
        if not page:
            return label
        for candidate in sorted({page, page.replace(" ", "_")}):
            hits = [p for p in DOCS.rglob(f"{candidate}.md") if p.stem == candidate] \
                or [p for p in DOCS.rglob(f"{candidate}/index.md") if p.parent.name == candidate]
            if hits:
                rel = hits[0].relative_to(DOCS).as_posix()
                return f"[{label}](../{rel}/{anchor})"
        return f"**{label}**"  # coming-soon topic — render bold
    return WIKI_LINK.sub(repl, text)


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
        target.write_text(rewrite_links(md.read_text(encoding="utf-8")), encoding="utf-8")

    if (VAULT / "Index.md").exists():
        (DOCS / "index.md").write_text(
            rewrite_links((VAULT / "Index.md").read_text(encoding="utf-8")),
            encoding="utf-8",
        )

    print("docs generated:", len(list(DOCS.rglob("*.md"))), "pages")


if __name__ == "__main__":
    build()
