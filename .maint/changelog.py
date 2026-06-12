#!/usr/bin/env python
"""Generate a raw changelog DRAFT with *git-changelog*, taught this repo's prefixes.

The published changelog (``docs/changes.md``) is hand-curated by THEME -- it links
milestone PRs and notable commits rather than logging every commit. This wrapper
does NOT write it. Per ``.git-changelog.toml`` (``in-place = false``) it renders a
raw, per-commit draft to ``.maint/changelog-draft.md`` (gitignored), grouped by
change type, which a human then curates into ``docs/changes.md``.

This project's commit history uses a custom set of Conventional-Commit-style
prefixes (``enh:``, ``doc:``, ``sty:``, ``maint:``, ...) that the stock
*git-changelog* "angular" convention does not recognise -- it only knows
``feat/fix/docs/style/...``.  Unknown prefixes are parsed with an empty type and
silently dropped, and listing an unknown type in ``[git-changelog] sections``
even crashes the tool.  This wrapper extends the AngularConvention type table (and
its subject regex) with the prefixes actually used here, mapping aliases onto a
small set of readable section titles, then defers to the normal *git-changelog*
CLI.  Run it exactly like the CLI, e.g.::

    python .maint/changelog.py --bump 0.5.0      # write the draft

or via ``make changelog_draft``.
"""

from __future__ import annotations

import re
import sys

from git_changelog import AngularConvention, main

# Map every prefix used in this repo's history onto a readable section title.
# Aliases that share a title are merged into a single section; only one
# representative key per title needs to appear in ``sections`` (see
# ``.git-changelog.toml``).
TYPE_TITLES: dict[str, str] = {
    # New features & enhancements
    "feat": "New features & enhancements",
    "enh": "New features & enhancements",
    "en": "New features & enhancements",  # typo of ``enh`` seen once
    "add": "New features & enhancements",
    # Bug fixes
    "fix": "Bug fixes",
    "hotfix": "Bug fixes",
    "bugfix": "Bug fixes",
    # Documentation
    "doc": "Documentation",
    "docs": "Documentation",
    # Code style
    "sty": "Code style",
    "style": "Code style",
    # Refactoring / performance
    "refactor": "Code refactoring",
    "ref": "Code refactoring",
    "perf": "Performance",
    # Tooling
    "ci": "Continuous integration",
    "build": "Build & dependencies",
    "deps": "Build & dependencies",
    # Maintenance
    "maint": "Maintenance",
    "chore": "Maintenance",
    "update": "Maintenance",
    # Misc
    "wip": "Work in progress",
    "revert": "Reverts",
    "test": "Tests",
    "tests": "Tests",
}


def _teach_convention() -> None:
    """Extend AngularConvention so this repo's prefixes are recognised."""
    AngularConvention.TYPES = {**AngularConvention.TYPES, **TYPE_TITLES}
    # Rebuild the subject regex so the new prefixes match ``<type>[(scope)]: ...``.
    AngularConvention.SUBJECT_REGEX = re.compile(
        rf"^(?P<type>({'|'.join(AngularConvention.TYPES.keys())}))"
        r"(?:\((?P<scope>.+)\))?: (?P<subject>.+)$",
    )


if __name__ == "__main__":
    _teach_convention()
    sys.exit(main(sys.argv[1:]))
