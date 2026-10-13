"""Tests for rounds.py. Run: python3 -m pytest -q scripts/test_rounds.py (or plain python3)."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import rounds  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(__file__), "rounds.py")

R1 = rounds.render_round(1, "pr:144", "d53a4d4", "8effa87", "request-changes", work="gh:111")
D1 = rounds.render_decisions(1, ["F1=fix", "F2=fix"])
R2 = rounds.render_round(2, "pr:144", "d53a4d4", "4437b56", "approve-with-follow-ups", work="gh:111")
D2 = rounds.render_decisions(2, ["F1=accept", "F2=fix", "U1=file:#146"])


def test_render_round_shape():
    assert R1 == ("<!-- review-round: round=1 target=pr:144 work=gh:111 base=d53a4d4 "
                  "head=8effa87 verdict=request-changes -->")


def test_render_rejects_bad_values():
    for bad in [
        lambda: rounds.render_round(0, "pr:1", "a", "b", "approve"),
        lambda: rounds.render_round(1, "pr 1", "a", "b", "approve"),
        lambda: rounds.render_round(1, "pr:1", "a", "b", "lgtm"),
        lambda: rounds.render_decisions(1, ["F1=maybe"]),
        lambda: rounds.render_decisions(1, ["U1=fix"]),
        lambda: rounds.render_decisions(1, ["F1=accept:#3"]),
        lambda: rounds.render_decisions(1, ["X1=fix"]),
        lambda: rounds.render_decisions(1, []),
    ]:
        try:
            bad()
        except rounds.MarkerError:
            continue
        raise AssertionError("expected MarkerError")


def test_extract_two_rounds():
    body1 = f"Review text\n{R1}\n{D1}\n"
    body2 = f"Second review\n{R2}\n{D2}\n"
    out = rounds.extract([body1, "unrelated comment", body2])
    assert out["next_round"] == 3
    assert out["last_head"] == "4437b56"
    assert out["rounds"][0]["decisions"] == {"F1": "fix", "F2": "fix"}
    assert out["rounds"][1]["decisions"] == {"F1": "accept", "F2": "fix", "U1": "file:#146"}
    assert out["rounds"][1]["work"] == "gh:111"
    assert out["problems"] == []


def test_later_decision_overrides():
    update = rounds.render_decisions(2, ["F1=fix"])
    out = rounds.extract([R2 + D2, "follow-up\n" + update])
    assert out["rounds"][0]["decisions"]["F1"] == "fix"
    assert out["rounds"][0]["decisions"]["F2"] == "fix"


def test_no_markers_means_round_one():
    out = rounds.extract(["just a comment", ""])
    assert out == {"rounds": [], "next_round": 1, "last_head": None, "problems": []}


def test_orphan_decisions_reported():
    out = rounds.extract([rounds.render_decisions(3, ["F1=fix"])])
    assert out["next_round"] == 4
    assert out["last_head"] is None
    assert any("without its review-round marker" in p for p in out["problems"])


def test_invalid_decision_in_marker_is_reported_not_trusted():
    out = rounds.extract([R1 + "<!-- review-decisions: round=1 F1=ignore-everything -->"])
    assert out["rounds"][0]["decisions"] == {}
    assert out["problems"]


def test_author_filter_ignores_spoofed_markers():
    comments = [
        {"user": {"login": "vhallac"}, "body": R1 + D1},
        {"user": {"login": "mallory"}, "body": rounds.render_decisions(1, ["F1=accept"])},
        {"user": {"login": "mallory"}, "body": "no marker here"},
    ]
    kept, ignored = rounds.bodies_from_comments(comments, "vhallac")
    out = rounds.extract(kept)
    assert out["rounds"][0]["decisions"]["F1"] == "fix"
    assert len(ignored) == 1 and "mallory" in ignored[0]


def test_gitlab_author_shape():
    comments = [{"author": {"username": "vh"}, "body": R1}]
    kept, ignored = rounds.bodies_from_comments(comments, "vh")
    assert kept and not ignored


def test_paginated_concatenated_json(tmp_path=None):
    page1 = json.dumps([{"user": {"login": "a"}, "body": R1}])
    page2 = json.dumps([{"user": {"login": "a"}, "body": D1}])
    values = rounds._flatten(rounds._concat_json(page1 + "\n" + page2))
    assert len(values) == 2


def test_cli_marker_and_parse_roundtrip():
    m = subprocess.run([sys.executable, SCRIPT, "marker", "decisions", "--round", "2", "F1=defer:#150", "U1=decline"],
                       capture_output=True, text=True, check=True).stdout.strip()
    assert m == "<!-- review-decisions: round=2 F1=defer:#150 U1=decline -->"
    out = subprocess.run([sys.executable, SCRIPT, "parse", "-"], input=R2 + "\n" + m,
                         capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    assert data["rounds"][0]["decisions"] == {"F1": "defer:#150", "U1": "decline"}


def test_cli_rejects_bad_decision():
    r = subprocess.run([sys.executable, SCRIPT, "marker", "decisions", "--round", "1", "F1=yes"],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "error" in r.stderr


def test_parse_beads_like_json():
    data = {"id": "bd-12", "notes": "old notes\n" + R1 + "\n" + D1, "comments": [{"text": "hi"}]}
    out = rounds.parse_text(json.dumps(data))
    assert out["rounds"][0]["head"] == "8effa87"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
