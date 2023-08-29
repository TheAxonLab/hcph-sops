# Makefile to update changelog using git-changelog

# Path to git-changelog executable
GIT_CHANGELOG = $(CONDA)/bin/git-changelog
RELEASE = auto

# Target: Update the changelog
update_changelog:
	$(GIT_CHANGELOG) --bump=$(RELEASE)
