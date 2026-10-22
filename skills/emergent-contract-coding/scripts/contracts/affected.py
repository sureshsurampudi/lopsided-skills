"""`contracts affected` — interfaces affected by a diff (S5).

Given a change set (a git ref diffed against the working tree, or a file
listing changed paths), reports the full blast radius: an interface is
affected when any of its registered call sites is in a changed file, or
when the changed set includes the file where the interface is defined.
For each affected interface, all its registered call sites are reported,
marked present/removed (a site removed from source vs the fresh
extraction); an interface whose registered call sites are all removed is
"possibly dead".
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from typing import TextIO
from pathlib import Path

from . import generate as generate_mod
from .cli import EXIT_FAIL, EXIT_OK, EXIT_USAGE, find_repo_root
from .generate import CallSite
from .registry import parse_registry


@dataclass
class AffectedInterface:
    call_sites: set[CallSite] = field(default_factory=set)
    removed_sites: set[CallSite] = field(default_factory=set)

    @property
    def possibly_dead(self) -> bool:
        return bool(self.call_sites) and self.call_sites == self.removed_sites


def _changed_from_ref(root: Path, ref: str) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-only", ref],
        capture_output=True, text=True, check=True,
    )
    return [l for l in out.stdout.splitlines() if l]


def _changed_from_file(path: Path | TextIO) -> list[str]:
    text = path.read_text(encoding="utf-8") if isinstance(path, Path) else path.read()
    return [l.strip() for l in text.splitlines() if l.strip()]


def changed_files(root: Path, diff: str) -> list[str]:
    """Resolve --diff value: '-', a git ref, or a path to a newline-separated list."""
    if diff == "-":
        return _changed_from_file(sys.stdin)  # type: ignore[arg-type]
    candidate = root / diff
    if candidate.is_file():
        return _changed_from_file(candidate)
    return _changed_from_ref(root, diff)


def affected_interfaces(root: Path, registry_text: str, cfg,
                        changed: list[str]) -> dict[str, AffectedInterface]:
    """All registered call sites of interfaces affected by the change set,
    marked present/removed (issue #28): a site removed from source vs the
    fresh extraction is `removed`; everything else is `present`. Sibling
    call sites in untouched files are never dropped. An interface whose
    registered call sites are all removed from source is possibly dead.
    """
    reg = parse_registry(registry_text)
    fresh_interfaces, fresh_unresolved = generate_mod._collect(root, cfg)
    fresh_reg = parse_registry(
        generate_mod.render_registry(fresh_interfaces, fresh_unresolved)
    )
    changed_set = set(changed)
    result: dict[str, AffectedInterface] = {}
    for ident, iface in reg.interfaces.items():
        def_hit = iface.definition is not None and iface.definition in changed_set
        site_hit = any(s.file in changed_set for s in iface.call_sites)
        if not (def_hit or site_hit):
            continue
        info = result.setdefault(ident, AffectedInterface())
        info.call_sites = set(iface.call_sites)
        fresh_sites = fresh_reg.interfaces.get(ident)
        fresh_set = fresh_sites.call_sites if fresh_sites else set()
        info.removed_sites = info.call_sites - fresh_set
    return result


def render_affected(affected: dict[str, AffectedInterface]) -> str:
    if not affected:
        return "no affected interfaces"
    lines = [f"{len(affected)} affected interface(s):"]
    for ident in sorted(affected):
        info = affected[ident]
        state = "POSSIBLY DEAD" if info.possibly_dead else "live"
        lines.append(f"  {ident} ({state})")
        for site in sorted(info.call_sites, key=lambda s: (s.file, s.symbol)):
            mark = "removed" if site in info.removed_sites else "present"
            lines.append(f"    - {site.file}:{site.symbol} [{mark}]")
    return "\n".join(lines)


def main_affected(args) -> int:
    root = find_repo_root()
    registry_path = root / generate_mod.REGISTRY_NAME
    if not registry_path.is_file():
        print(f"contracts: no {generate_mod.REGISTRY_NAME} — run `contracts generate` first")
        return EXIT_FAIL
    try:
        changed = changed_files(root, args.diff)
    except subprocess.CalledProcessError as exc:
        print(
            f"contracts affected: invalid --diff ref {args.diff!r}: "
            f"git diff failed ({exc.stderr.strip() or 'unknown git error'})",
            file=sys.stderr,
        )
        return EXIT_USAGE
    affected = affected_interfaces(
        root, registry_path.read_text(encoding="utf-8"), args.config, changed
    )
    print(render_affected(affected))
    return EXIT_OK
