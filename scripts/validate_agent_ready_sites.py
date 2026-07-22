#!/usr/bin/env python3
"""Validate the two self-contained, agent-discoverable landing-site bundles."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SITES_ROOT = REPO_ROOT / "sites"
DISCOVERY_SCHEMA = "https://schemas.agentskills.io/discovery/0.2.0/schema.json"


@dataclass(frozen=True)
class Site:
    name: str
    host: str
    repository: str

    @property
    def root(self) -> Path:
        return SITES_ROOT / self.name


SITES = (
    Site("bookshelf", "https://bookshelf-8dz.pages.dev", "https://github.com/Amal-David/bookshelf"),
    Site("polyglot", "https://polyglot-5os.pages.dev", "https://github.com/Amal-David/polyglot"),
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_site(site: Site) -> None:
    required = (
        "index.html",
        "robots.txt",
        "sitemap.xml",
        "llms.txt",
        "_worker.js",
        "agent-skills/index.json",
        f"agent-skills/{site.name}/SKILL.md",
    )
    for relative in required:
        _require((site.root / relative).is_file(), f"{site.name}: missing {relative}")

    html = (site.root / "index.html").read_text(encoding="utf-8")
    _require(f'<link rel="canonical" href="{site.host}/">' in html, f"{site.name}: wrong canonical URL")
    _require(site.repository in html, f"{site.name}: public repository link is missing")
    _require("pagecast-6cv.pages.dev/p/" not in html, f"{site.name}: old shared publication URL remains")
    for relative_asset in set(re.findall(r'\./(assets/[^"\) ]+)', html)):
        _require((site.root / relative_asset).is_file(), f"{site.name}: missing {relative_asset}")

    if site.name == "bookshelf":
        demo_source = (REPO_ROOT / "videos/cli-recordings/bookshelf-claude-demo.sh").read_text(encoding="utf-8")
        _require("autoplay muted loop" in html, "bookshelf: terminal demo must autoplay as the primary experience")
        for implementation_detail in ("ambient.py", "systemMessage", "printf '{}'", 'print_line "{}"'):
            _require(implementation_detail not in demo_source, f"bookshelf: demo leaks hook plumbing: {implementation_detail}")
        for user_facing_moment in ("Claude Code", "bookshelf/skill/quote_picker.py", "Do nothing which is of no use."):
            _require(user_facing_moment in demo_source, f"bookshelf: demo is missing {user_facing_moment}")

    robots = (site.root / "robots.txt").read_text(encoding="utf-8")
    _require("User-agent: *" in robots and "Allow: /" in robots, f"{site.name}: invalid wildcard crawl rules")
    _require("Content-Signal: ai-train=no, search=yes, ai-input=yes" in robots, f"{site.name}: content signal missing")
    _require(f"Sitemap: {site.host}/sitemap.xml" in robots, f"{site.name}: sitemap directive is wrong")

    sitemap_root = ET.parse(site.root / "sitemap.xml").getroot()
    locations = [node.text for node in sitemap_root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    _require(locations == [f"{site.host}/"], f"{site.name}: sitemap canonical URL is wrong")

    index = json.loads((site.root / "agent-skills/index.json").read_text(encoding="utf-8"))
    _require(index.get("$schema") == DISCOVERY_SCHEMA, f"{site.name}: wrong discovery schema")
    skills = index.get("skills")
    _require(isinstance(skills, list) and len(skills) == 1, f"{site.name}: expected exactly one skill")
    skill = skills[0]
    _require(skill.get("name") == site.name, f"{site.name}: wrong skill name")
    _require(skill.get("type") == "skill-md", f"{site.name}: wrong skill type")
    _require(skill.get("url") == f"/.well-known/agent-skills/{site.name}/SKILL.md", f"{site.name}: wrong skill URL")

    llms = (site.root / "llms.txt").read_text(encoding="utf-8")
    for unsupported in ("does not expose a hosted API", "MCP server", "A2A agent", "commerce protocol"):
        _require(unsupported in llms, f"{site.name}: missing capability boundary: {unsupported}")

    worker = (site.root / "_worker.js").read_text(encoding="utf-8")
    _require('includes(MARKDOWN_ACCEPT)' in worker, f"{site.name}: markdown negotiation is missing")
    _require('new URL("/llms.txt", url)' in worker, f"{site.name}: markdown source is wrong")
    _require('rel="describedby"' in worker, f"{site.name}: skills Link relation is missing")
    _require("url.pathname.startsWith(SKILLS_PREFIX)" in worker, f"{site.name}: well-known skills routing is missing")
    _require('new Response("Not found", { status: 404 })' in worker, f"{site.name}: explicit soft-404 guard is missing")


def validate_all() -> None:
    for site in SITES:
        validate_site(site)


def main() -> int:
    try:
        validate_all()
    except (OSError, ValueError, ET.ParseError, json.JSONDecodeError) as error:
        print(f"agent-ready site validation failed: {error}", file=sys.stderr)
        return 1
    print("agent-ready site validation passed: bookshelf, polyglot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
