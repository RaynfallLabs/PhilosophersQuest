"""Prompt templates for LLM-driven validators and generators.

Each `.md` file in this directory is a self-contained prompt for a subagent
spawned from the Claude Code session. The Python pipeline writes batches of
questions needing LLM judgment to `tools/quizgen/state/queue/`, and the
session reads those + spawns subagents with the relevant template.

Templates are plain markdown so a human can read and edit them without
needing to understand Python.
"""
