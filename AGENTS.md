- ALWAYS use docker and docker compose to run any command
- ALWAYS source the `aliases.sh` script, check out the commands in there
- ALWAYS use the development profile
- ALWAYS use `pnmp` to install and handle javascript dependencies
- ALWAYS write python code compatible with the `ruff` configuration, execute it to make sure
- ALWAYS run `pre-commit` when you are done with changes
- ALWAYS make sure the javascript/react code follows eslint/prettier configuration
- PREFER backward compatible changes to APIs
- PREFER adding readonly fields for related fields in the REST API
- PREFER fat models over logic in the views
- AVOID using `select_related` with polymorphic models (e.g., `Plate` -> `ExtractionPlate`). It doesn't properly cache the subclass data and causes N+1 queries. Use `Subquery` with `OuterRef` to annotate the needed fields instead.

## Agent skills

### Issue tracker

Issues live in ClickUp, list "IT Utvikling / 2026". See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical triage roles map 1:1 to ClickUp tags. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` + `docs/adr/`. See `docs/agents/domain.md`.
