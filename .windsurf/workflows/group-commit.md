---
description: Group related files and create meaningful commits, including partial file commits for multi-feature changes
---

# Commit Skill

This skill helps you create meaningful commits by grouping related files and changes, including partial file commits for multi-feature changes.

## Usage

Run this skill when you have made changes to multiple files and want to create a structured commit.

## Steps

1. **Analyze Changes**: The skill will first analyze all modified files to understand what has been changed
2. **Analyze Hunks**: For each file, changes are broken down into hunks (groups of consecutive lines) to identify distinct modifications
3. **Group Related Changes**: Changes (full files or partial hunks) are grouped based on their functionality and feature context
4. **Generate Commit Message**: A meaningful commit message will be generated based on the grouped changes
5. **Create Commits**: Multiple commits may be created, each containing the grouped files and partial changes for a single feature

## File Grouping Logic

Files are grouped based on:

- **Component changes**: React components, UI elements
- **Configuration changes**: package.json, webpack configs, build files
- **Documentation changes**: README, docs, comments
- **Style changes**: CSS, styled components, themes
- **Core functionality**: Main process, store, IPC handlers
- **Infrastructure**: Git ignore, build scripts, CI/CD

## Partial File Grouping Logic

When a file contains changes for multiple features, hunks are analyzed and grouped separately:

- **Feature-based hunk grouping**: Hunks are assigned to features based on code comments, function names, or logical groupings
- **Context-aware splitting**: The skill uses AI to understand the semantic meaning of changes and group related hunks
- **Sequential commits**: For files with multiple features, partial changes are committed sequentially to maintain feature isolation
- **Conflict prevention**: Ensures that staging partial hunks doesn't create merge conflicts or broken intermediate states

## Commit Message Format

Commits follow conventional commit format:

```bash
type(scope): description

[optional detailed body]
```

Types used:

- `feat`: New features
- `fix`: Bug fixes
- `refactor`: Code refactoring
- `style`: Styling changes
- `docs`: Documentation changes
- `build`: Build and dependency changes
- `chore`: Maintenance tasks

## Example Output

**Commit 1:**

```bash
feat(featureA): implement initial feature A functionality

- Add new feature logic to file1
- Update file2 with feature A changes (lines 10-20)

Files changed:
- src/file1.js
- src/file2.js (partial: lines 10-20)
```

**Commit 2:**

```bash
feat(featureB): implement feature B functionality

- Add feature B logic to file3
- Update file2 with feature B changes (remaining lines)

Files changed:
- src/file2.js (partial: remaining changes)
- src/file3.js
```

## Automation

This skill should not be run automatically.

### Explicit Rules

- **NEVER run commit automatically** - Only run when explicitly requested by the user
- **Wait for user confirmation** - Always ask before committing any changes
- **No auto-commit triggers** - Do not commit after code changes, refactoring, or fixes
- **Manual execution only** - This workflow requires explicit user command to execute

## Notes

- The skill will respect any existing .gitignore patterns
- Large changes may be split into multiple logical commits
- Conflicts will be highlighted for manual resolution
- The skill will not push commits automatically - you'll need to push manually
- Partial file commits use git's hunk staging to commit only specific changes from a file
- AI analysis helps determine which hunks belong to which features
- If hunk grouping is uncertain, the skill will prompt for manual confirmation
- Files with mixed features are staged partially to avoid committing unrelated changes together
