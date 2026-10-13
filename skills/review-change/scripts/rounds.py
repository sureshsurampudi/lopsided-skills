#!/usr/bin/env python3
"""Review-round markers: render them, and recover earlier rounds from a channel.

A published review carries two hidden HTML-comment markers:

  <!-- review-round: round=2 target=pr:144 work=gh:111 base=d53a4d4 head=4437b56 verdict=approve-with-follow-ups -->
  <!-- review-decisions: round=2 F1=fix F2=accept U1=file:#146 -->

A later comment may carry another `review-decisions` marker for an earlier
round; later markers override earlier ones per finding ID.

Usage:
  rounds.py marker round --round N --target T [--work W] --base SHA --head SHA --verdict V
  rounds.py marker decisions --round N ID=DECISION [ID=DECISION ...]
  rounds.py fetch github --repo OWNER/REPO (--pr N | --issue N) [--author LOGIN | --any-author]
  rounds.py fetch gitlab --project ID-OR-PATH (--mr N | --issue N) [--author USER | --any-author]
  rounds.py fetch beads --id BD-ID
  rounds.py parse FILE            # a JSON dump of comments, or plain text
  rounds.py parse -               # same, from stdin

`fetch` and `parse` print JSON: {"rounds": [...], "next_round": N, "last_head": SHA|null}.

Only markers written by the operator count. For forges, `fetch` keeps markers
from comments by --author (default: the authenticated CLI user); anyone else's
comment containing a marker is reported under "ignored" and never trusted.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from typing import Any

MARKER_RE = re.compile(r"<!--\s*review-(round|decisions):\s*(.*?)\s*-->", re.S)
TOKEN_RE = re.compile(r"^[A-Za-z0-9_.:#/+-]+$")
ID_RE = re.compile(r"^[FU]\d+$")
VERDICTS = {
    "approve",
    "approve-with-follow-ups",
    "request-changes",
    "satisfied",
    "partially-satisfied",
    "not-satisfied",
    "aligned",
    "divergent",
}
FINDING_DECISIONS = {"fix", "accept", "defer"}
UNRELATED_DECISIONS = {"file", "decline"}


class MarkerError(ValueError):
    pass


# ---------------------------------------------------------------- rendering


def _check_token(name: str, value: str) -> str:
    if not value or not TOKEN_RE.match(value):
        raise MarkerError(f"{name}={value!r}: marker values must be non-empty and contain no spaces")
    return value


def validate_decision(fid: str, decision: str) -> None:
    if not ID_RE.match(fid):
        raise MarkerError(f"{fid!r}: IDs are F<n> (findings) or U<n> (unrelated problems)")
    kind, _, arg = decision.partition(":")
    allowed = FINDING_DECISIONS if fid.startswith("F") else UNRELATED_DECISIONS
    if kind not in allowed:
        raise MarkerError(f"{fid}={decision}: {fid[0]}-IDs take one of {sorted(allowed)}")
    if arg and kind not in {"defer", "file"}:
        raise MarkerError(f"{fid}={decision}: only defer/file take an argument (an issue reference)")
    if arg:
        _check_token(fid, arg)


def render_round(round_: int, target: str, base: str, head: str, verdict: str, work: str | None = None) -> str:
    if round_ < 1:
        raise MarkerError("round must be >= 1")
    if verdict not in VERDICTS:
        raise MarkerError(f"verdict {verdict!r} not in {sorted(VERDICTS)}")
    fields = [f"round={round_}", f"target={_check_token('target', target)}"]
    if work:
        fields.append(f"work={_check_token('work', work)}")
    fields += [f"base={_check_token('base', base)}", f"head={_check_token('head', head)}", f"verdict={verdict}"]
    return f"<!-- review-round: {' '.join(fields)} -->"


def render_decisions(round_: int, decisions: list[str]) -> str:
    if round_ < 1:
        raise MarkerError("round must be >= 1")
    if not decisions:
        raise MarkerError("at least one ID=DECISION is required")
    parts = [f"round={round_}"]
    for item in decisions:
        fid, sep, decision = item.partition("=")
        if not sep:
            raise MarkerError(f"{item!r}: expected ID=DECISION")
        validate_decision(fid, decision)
        parts.append(f"{fid}={decision}")
    return f"<!-- review-decisions: {' '.join(parts)} -->"


# ------------------------------------------------------------------ parsing


def _fields(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in raw.split():
        key, sep, value = part.partition("=")
        if sep:
            out[key] = value
    return out


def extract(bodies: list[str]) -> dict[str, Any]:
    """Fold markers from bodies (chronological order) into a round summary."""
    rounds: dict[int, dict[str, Any]] = {}
    problems: list[str] = []
    for body in bodies:
        for kind, raw in MARKER_RE.findall(body or ""):
            f = _fields(raw)
            try:
                n = int(f.get("round", ""))
            except ValueError:
                problems.append(f"marker without a valid round: {raw!r}")
                continue
            entry = rounds.setdefault(n, {"round": n, "decisions": {}})
            if kind == "round":
                for key in ("target", "work", "base", "head", "verdict"):
                    if key in f:
                        entry[key] = f[key]
            else:
                for key, value in f.items():
                    if key == "round":
                        continue
                    try:
                        validate_decision(key, value)
                    except MarkerError as err:
                        problems.append(str(err))
                        continue
                    entry["decisions"][key] = value  # later markers override
    ordered = [rounds[n] for n in sorted(rounds)]
    published = [r for r in ordered if "head" in r]
    for r in ordered:
        if "head" not in r:
            problems.append(f"decisions for round {r['round']} without its review-round marker")
    return {
        "rounds": ordered,
        "next_round": (max(rounds) + 1) if rounds else 1,
        "last_head": published[-1]["head"] if published else None,
        "problems": problems,
    }


def _concat_json(text: str) -> list[Any]:
    """Decode one JSON value, or several concatenated (paginated API output)."""
    dec = json.JSONDecoder()
    values, i = [], 0
    text = text.strip()
    while i < len(text):
        value, end = dec.raw_decode(text, i)
        values.append(value)
        i = end
        while i < len(text) and text[i].isspace():
            i += 1
    return values


def _flatten(values: list[Any]) -> list[Any]:
    out: list[Any] = []
    for v in values:
        out.extend(v if isinstance(v, list) else [v])
    return out


def _all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _all_strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _all_strings(v)]
    return []


def _author(comment: dict[str, Any]) -> str | None:
    user = comment.get("user") or comment.get("author") or {}
    if isinstance(user, dict):
        return user.get("login") or user.get("username")
    return None


def bodies_from_comments(comments: list[Any], author: str | None) -> tuple[list[str], list[str]]:
    kept, ignored = [], []
    for c in comments:
        if not isinstance(c, dict):
            continue
        body = c.get("body") or ""
        if not MARKER_RE.search(body):
            continue
        who = _author(c)
        if author is not None and who != author:
            ignored.append(f"marker in a comment by {who!r} (operator is {author!r}) — not trusted")
            continue
        kept.append(body)
    return kept, ignored


# ------------------------------------------------------------------ fetching


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    except FileNotFoundError:
        raise SystemExit(f"error: {cmd[0]} is not installed")
    except subprocess.CalledProcessError as err:
        raise SystemExit(f"error: {' '.join(cmd)} failed: {err.stderr.strip()}")


def fetch(args: list[str]) -> dict[str, Any]:
    if not args:
        raise SystemExit("fetch: expected github, gitlab, or beads")
    channel, opts = args[0], _opts(args[1:])
    if channel == "beads":
        data = _concat_json(_run(["bd", "show", opts["--id"], "--json"]))
        result = extract([s for s in _all_strings(data) if MARKER_RE.search(s)])
        result["ignored"] = []
        return result
    if channel == "github":
        n = opts.get("--pr") or opts.get("--issue")
        path = f"repos/{opts['--repo']}/issues/{n}/comments"  # PR comments are issue comments
        raw = _run(["gh", "api", "--paginate", path])
        author = None if "--any-author" in opts else opts.get("--author") or _run(
            ["gh", "api", "user", "--jq", ".login"]).strip()
    elif channel == "gitlab":
        proj = opts["--project"].replace("/", "%2F")
        kind, n = ("merge_requests", opts["--mr"]) if "--mr" in opts else ("issues", opts["--issue"])
        raw = _run(["glab", "api", "--paginate", f"projects/{proj}/{kind}/{n}/notes?sort=asc&order_by=created_at"])
        if "--any-author" in opts:
            author = None
        else:
            author = opts.get("--author") or json.loads(_run(["glab", "api", "user"]))["username"]
    else:
        raise SystemExit(f"fetch: unknown channel {channel!r}")
    kept, ignored = bodies_from_comments(_flatten(_concat_json(raw)), author)
    result = extract(kept)
    result["ignored"] = ignored
    return result


def _opts(args: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    i = 0
    while i < len(args):
        key = args[i]
        if key == "--any-author":
            out[key] = ""
            i += 1
            continue
        if i + 1 >= len(args):
            raise SystemExit(f"missing value for {key}")
        out[key] = args[i + 1]
        i += 2
    return out


def parse_text(text: str) -> dict[str, Any]:
    try:
        values = _flatten(_concat_json(text))
    except json.JSONDecodeError:
        return extract([text])
    if all(isinstance(v, dict) and "body" in v for v in values):
        return extract([v["body"] or "" for v in values])
    return extract([s for s in _all_strings(values) if MARKER_RE.search(s)])


# ---------------------------------------------------------------------- main


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print(__doc__)
        return 0 if len(argv) >= 2 else 2
    cmd = argv[1]
    try:
        if cmd == "marker" and len(argv) > 2 and argv[2] == "round":
            o = _opts(argv[3:])
            print(render_round(int(o["--round"]), o["--target"], o["--base"], o["--head"], o["--verdict"], o.get("--work")))
        elif cmd == "marker" and len(argv) > 2 and argv[2] == "decisions":
            if len(argv) < 5 or argv[3] != "--round":
                raise MarkerError("usage: marker decisions --round N ID=DECISION ...")
            print(render_decisions(int(argv[4]), argv[5:]))
        elif cmd == "fetch":
            print(json.dumps(fetch(argv[2:]), indent=2))
        elif cmd == "parse" and len(argv) == 3:
            text = sys.stdin.read() if argv[2] == "-" else open(argv[2], encoding="utf-8").read()
            print(json.dumps(parse_text(text), indent=2))
        else:
            print(__doc__, file=sys.stderr)
            return 2
    except (MarkerError, KeyError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
