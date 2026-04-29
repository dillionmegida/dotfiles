---
description: Auto-generate commit message and commit staged or unstaged changes
---

A workflow that checks for staged changes (or all changes if staging area is empty), generates a meaningful commit message based on the diff, and creates the commit.

## Steps

1. Check if there are any staged changes in git

```bash
git diff --cached --name-only
```

2. If no staged changes, check if there are any unstaged changes

```bash
git status --short
```

3. If staging area is empty but there are unstaged changes, stage all changes

```bash
git add -A
```

4. Generate a commit message based on the diff. Analyze the changes to create a conventional commit style message (type: description). Consider:
   - File types changed (ts, tsx, css, etc.)
   - Scope of changes (which directories/modules)
   - Nature of changes (added, modified, deleted)
   - Common patterns (fix, feat, refactor, docs, test, chore)

Do not run the commit, just give me the commit message