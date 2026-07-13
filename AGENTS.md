# THE ABOVE — Codex Implementation Guide

This file is the default instruction set for Codex-family coding agents. Read it before changing the
repository, together with [`ARCHITECTURE.md`](ARCHITECTURE.md), [`PLAN.md`](PLAN.md), and
[`PROGRESS.md`](PROGRESS.md).

## Role and ownership

Codex owns **implementation**: scoped GDScript/Python changes, tests, resource tooling, bug fixes,
integration of an approved design, and routine engineering documentation. Work from the current plan,
an approved Claude handoff, or a directly specified user request.

Codex must not take ownership of product/UI design or unresolved complex architecture. Those belong to
Claude and require a manual user handoff.

## Work Codex may perform

- Implement a clear, bounded feature or bug fix.
- Add or update automated tests and run the relevant Makefile checks.
- Wire an already-specified UI design into Godot scenes and scripts.
- Make mechanical localization, content-data, resource, build, or documentation changes whose rules
  are already explicit.
- Commit a completed, verified coding slice and push it to the configured GitHub `origin` at a
  Codex-to-Claude handoff.

Keep changes focused. Preserve unrelated working-tree changes. Do not edit `PLAN.md` or
`PROGRESS.md` unless the user expressly requests it or a completed milestone is being recorded as part
of the agreed workflow.

## Stop and hand off to Claude

Stop before implementation when any of the following is true:

- UI/UX needs to be invented, materially redesigned, or judged visually beyond an existing written
  specification.
- A feature changes architecture, public data contracts, autoload ownership/order, save/meta format,
  localization policy, rendering/export strategy, or spans multiple systems without an approved plan.
- Requirements, gameplay behaviour, failure behaviour, or acceptance criteria are ambiguous.
- A task needs a non-trivial trade-off between plausible approaches, broad investigation, or creative
  direction.

Do not guess, partially redesign the system, or leave speculative code behind. Instead:

1. Finish only the safe, already-specified work; otherwise make no code change.
2. Run the applicable checks for work already completed.
3. Inspect `git status` and preserve unrelated user changes.
4. Commit only the completed Codex-owned slice with a descriptive message.
5. Push the commit to `origin` for the user to continue manually in Claude. If pushing is unavailable,
   report the exact commit and failure without rewriting history.
6. Provide a concise handoff: what is complete, what decision Claude must make, affected files, and
   verification results.

The user will return to Codex after Claude has produced a stable implementation handoff. Resume only
the code and verification work described there.

## Completion rules

For a normal implementation task:

1. Respect all rules in [`ARCHITECTURE.md`](ARCHITECTURE.md).
2. Run the smallest relevant checks, then the milestone gate when the change warrants it:
   `make test`, `make pytest`, and/or `make tour`.
3. State exactly what was changed and what was verified.
4. Update [`PROGRESS.md`](PROGRESS.md) only when the user asks or when a milestone/checkbox has
   genuinely completed.

Never use destructive Git commands to clean a dirty worktree. Never push an unrelated user change.
