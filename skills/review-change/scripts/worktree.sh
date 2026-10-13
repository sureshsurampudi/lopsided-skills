#!/usr/bin/env bash
# Disposable, read-only review worktrees.
#
# These are a deliberate second class beside worktree-management's streams:
# they live in the system temp dir, are detached at the reviewed commit, never
# host a plan, and are always removed when the review ends.
#
#   worktree.sh create <repo> <label> <commit-ish>   # prints the worktree path
#   worktree.sh remove <repo> <path>                 # removes it and verifies
#   worktree.sh stale  <repo>                        # lists leftover review worktrees
#
# <label> is a short target name (e.g. pr144, bd-12); it only seeds the
# directory name.
set -euo pipefail

prefix() { (cd "${TMPDIR:-/tmp}" && pwd -P); }  # no trailing slash, symlinks resolved (macOS /var)

die() { echo "error: $*" >&2; exit 1; }

cmd=${1:-}; shift || true
case "$cmd" in
create)
	[ $# -eq 3 ] || die "usage: create <repo> <label> <commit-ish>"
	repo=$1 label=$2 rev=$3
	[[ "$label" =~ ^[A-Za-z0-9._-]+$ ]] || die "label must match [A-Za-z0-9._-]+"
	commit=$(git -C "$repo" rev-parse --verify --quiet "$rev^{commit}") || die "no such commit: $rev"
	dir=$(mktemp -d "$(prefix)/review-$label-XXXXXX")
	rmdir "$dir"  # git worktree add wants to create it
	git -C "$repo" worktree add --detach --quiet "$dir" "$commit" >&2
	echo "$dir"
	;;
remove)
	[ $# -eq 2 ] || die "usage: remove <repo> <path>"
	repo=$1 dir=$2
	case "$(basename "$dir")" in review-*) ;; *) die "refusing: $dir is not a review worktree" ;; esac
	if git -C "$repo" worktree list --porcelain | grep -qxF "worktree $dir"; then
		git -C "$repo" worktree remove --force "$dir"
	fi
	rm -rf -- "$dir"
	git -C "$repo" worktree prune
	if [ -e "$dir" ] || git -C "$repo" worktree list --porcelain | grep -qxF "worktree $dir"; then
		die "worktree still present: $dir"
	fi
	echo "removed $dir"
	;;
stale)
	[ $# -eq 1 ] || die "usage: stale <repo>"
	git -C "$1" worktree list --porcelain | sed -n 's/^worktree //p' |
		grep -E "^$(prefix)/review-[A-Za-z0-9._-]+-[A-Za-z0-9]{6}$" || true
	;;
*)
	sed -n '2,15p' "$0"
	exit 2
	;;
esac
