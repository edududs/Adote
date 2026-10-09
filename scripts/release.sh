#!/usr/bin/env bash
# Cuts a release locally: next SemVer from the commits, CHANGELOG.md, release commit, annotated tag.
# It never pushes. See docs/runbooks/release.md.
#
#   scripts/release.sh --dry-run   show the next version and its notes, change nothing
#   scripts/release.sh             create the release commit and the tag
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

die() {
    echo "release: $*" >&2
    exit 1
}

dry_run=0
[[ "${1:-}" == "--dry-run" ]] && dry_run=1

cliff=(uv run --quiet git-cliff)
"${cliff[@]}" --version >/dev/null 2>&1 || die "git-cliff is missing: run uv sync"
[[ "$(git branch --show-current)" == "master" ]] || die "releases are cut from master"
[[ -z "$(git status --porcelain)" ]] || die "the working tree is not clean"

last="$(git describe --tags --abbrev=0 --match 'v[0-9]*' 2>/dev/null || true)"
next="$("${cliff[@]}" --bumped-version 2>/dev/null)"
[[ -n "$next" ]] || die "could not compute the next version"
[[ "$next" != "$last" ]] || die "nothing to release since $last"

notes="$("${cliff[@]}" --unreleased --tag "$next" --strip all 2>/dev/null)"

if ((dry_run)); then
    echo "last: ${last:-none}  next: $next"
    echo
    echo "$notes"
    exit 0
fi

# The version lives in the tag; the package metadata and the lock file follow it.
uv version "${next#v}" >/dev/null
"${cliff[@]}" --tag "$next" --output CHANGELOG.md 2>/dev/null

git add CHANGELOG.md pyproject.toml uv.lock
git commit --quiet -m "chore(release): $next"

# The tag message is the notes alone: the release workflow publishes it as the release body.
# --cleanup=verbatim keeps the markdown headings, which git would otherwise drop as comments.
printf '%s\n' "$notes" | sed '/./,$!d' | git tag --annotate "$next" --file - --cleanup=verbatim

echo "release: $next committed and tagged locally."
echo "release: to publish, the owner runs: git push --follow-tags"
