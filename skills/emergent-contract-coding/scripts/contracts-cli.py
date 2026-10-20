#!/usr/bin/env python3
"""Launcher for the contracts CLI so it can be invoked from anywhere:
`python3 <skill-directory>/scripts/contracts-cli.py <subcommand> ...`

Equivalent to `python3 -m contracts` with the scripts directory on sys.path.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from contracts import cli  # noqa: E402

sys.exit(cli.main(sys.argv[1:]))
