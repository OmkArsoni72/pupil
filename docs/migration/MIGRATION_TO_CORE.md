# Migration to core/ Consolidated Structure

This guide describes steps to consolidate code under core/ and update imports.

## Steps

1. Commit current work:
   git add -A && git commit -m "pre-core-migration"

2. Dry run:
   python scripts/refactor_to_core.py

3. Apply changes:
   APPLY=1 python scripts/refactor_to_core.py

4. Run tests:
   pytest -q

5. Smoke test app locally.

## Notes

- backup/ and \*.backup are untouched; move to archive/ manually if desired.
- Revert with: git reset --hard HEAD~1 (if last commit was migration).
