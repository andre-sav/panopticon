# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds


---

## BMAD Method Integration

This project uses **BMAD Method** for structured AI-driven development.

### Getting Started
Run `*workflow-init` to analyze the project and select a development track.

### Phases
1. **Analysis** - Brainstorm, research (optional)
2. **Planning** - PRD, tech specs with PM agent
3. **Solutioning** - Architecture, UX design
4. **Implementation** - Story-driven development

### Key Commands
- `*workflow-init` - Start/resume workflow
- `*dev-checklist` - Implementation checklist
- Load agents from `.bmad/agents/` as needed

### Output Locations
- `_bmad-output/planning-artifacts/` - PRDs, architecture, UX specs
- `_bmad-output/implementation-artifacts/` - Sprint stories, tasks
- `docs/` - Long-term project documentation

### Workflow: BMAD Planning → Beads Tracking
1. Use BMAD PM agent to create PRD
2. Use BMAD Architect for technical design
3. Convert planned work into `bd` issues/epics
4. Track implementation progress with `bd ready`, `bd close`
