# Makefile for changelog drafting.
#
# The PUBLISHED changelog (docs/changes.md) is hand-curated BY THEME: it should
# let a reader quickly spot the important changes, linking milestone PRs (and the
# occasional notable commit) rather than logging every commit.
#
# This target does NOT touch docs/changes.md. It regenerates a raw, per-commit
# DRAFT (.maint/changelog-draft.md, gitignored) grouped by change type, which you
# then curate into docs/changes.md. It runs git-changelog through
# .maint/changelog.py, a thin wrapper that teaches the "angular" convention this
# repo's custom commit prefixes (enh:, doc:, sty:, maint:, ...); without it those
# commits would be dropped from the draft.

RELEASE = auto

# Regenerate the changelog draft. Override the version bump, e.g.:
#   make changelog_draft RELEASE=0.5.0
#   make changelog_draft RELEASE=minor
changelog_draft:
	python .maint/changelog.py --bump=$(RELEASE)
	@echo "Draft written to .maint/changelog-draft.md -- curate highlights into docs/changes.md by theme."
