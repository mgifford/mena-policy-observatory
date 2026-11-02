#!/bin/sh
set -eu
if [ ! -d .git ]; then
  echo 'ERROR: Run this from the existing Git repository root (directory with .git).' >&2
  exit 2
fi
printf 'Repository: '; git remote get-url origin || true
printf 'Commit: '; git rev-parse --short HEAD
printf 'Branch: '; git branch --show-current
if [ -n "$(git status --porcelain)" ]; then
  echo 'ERROR: working tree is not clean. Commit or stash your changes first.' >&2
  git status --short
  exit 3
fi
for file in README.md framework/build.py framework/validate.py .github/workflows/pages.yml; do
  if [ ! -f "$file" ]; then echo "ERROR: missing $file" >&2; exit 4; fi
done
python3 framework/validate.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 framework/build.py --region mena
python3 framework/check_html.py
if [ -f framework/validate_provisions.py ]; then python3 framework/validate_provisions.py; else echo 'INFO: provision validator is not present yet.'; fi
printf '\nPreflight complete. Review any generated files before committing.\n'
