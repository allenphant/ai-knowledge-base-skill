#!/bin/bash
# Sync ai-knowledge-base skill between Claude Code and Gemini CLI
# Run this after editing the skill in either location.
#
# Usage:
#   bash ~/.claude/skills/ai-knowledge-base/sync-skill.sh
#   bash ~/.claude/skills/ai-knowledge-base/sync-skill.sh --reverse  (Gemini → Claude)

CLAUDE_DIR="$HOME/.claude/skills/ai-knowledge-base"
GEMINI_DIR="$HOME/.gemini/skills/ai-knowledge-base"

if [ "$1" = "--reverse" ]; then
  SRC="$GEMINI_DIR"
  DST="$CLAUDE_DIR"
  echo "Syncing: Gemini → Claude"
else
  SRC="$CLAUDE_DIR"
  DST="$GEMINI_DIR"
  echo "Syncing: Claude → Gemini"
fi

mkdir -p "$DST/references"

# Sync shared instructions (the core content)
cp "$SRC/references/instructions.md" "$DST/references/instructions.md"

# SKILL.md is NOT synced — each CLI keeps its own frontmatter copy
# (they're identical now, but you might diverge them later)

echo "Done. Synced references/instructions.md"
echo "  Source: $SRC"
echo "  Target: $DST"
