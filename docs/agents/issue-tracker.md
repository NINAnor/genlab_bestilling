# Issue tracker: ClickUp

Issues and specs for this repo live as ClickUp tasks in the **IT Utvikling** space, list **2026**.

- **List ID**: `901520431481`
- **List URL**: https://app.clickup.com/9015709135/v/l/li/901520431481

Use the `clickup_*` MCP tools for all operations — there is no CLI equivalent to `gh`/`glab` here.

## Conventions

- **Create an issue**: `clickup_create_task` with `list_id` `901520431481`. New tasks start in status **`to do`** unless a skill has a reason to set another valid status.
- **Read an issue**: `clickup_get_task` (pass `include: ["description", "custom_fields"]` as needed) plus `clickup_get_task_comments` for discussion.
- **List issues**: `clickup_filter_tasks` scoped to `list_ids: ["901520431481"]`, filtered by `statuses` and/or `tags` as needed.
- **Comment on an issue**: `clickup_create_comment` with `entity_type: "task"`.
- **Apply / remove labels**: ClickUp has no native "labels" concept equivalent to GitHub — this repo uses **tags** for the triage vocabulary (see `docs/agents/triage-labels.md`). Use `clickup_add_tag_to_task` / `clickup_remove_tag_from_task`. Tags must already exist in the space before they can be applied.
- **Close / resolve**: update status via `clickup_update_task` (e.g. to `complete` or `aborted`), don't delete tasks.

## Statuses available on this list

| Status | Type | Rough meaning |
| --- | --- | --- |
| `to do` | open | Default status for new tasks |
| `to discuss` | unstarted | Needs discussion before work starts |
| `waiting` | unstarted | Blocked / waiting on something external |
| `in progress` | custom | Actively being worked |
| `testing` | custom | Implementation done, under test |
| `to deploy - test` | done | Ready to deploy to test environment |
| `feedback` | done | Deployed, awaiting feedback |
| `to deploy - prod` | done | Ready to deploy to production |
| `aborted` | done | Work stopped, not going to be finished (pairs with the `wontfix` tag) |
| `complete` | closed | Fully done |

## When a skill says "publish to the issue tracker"

Create a ClickUp task in list `901520431481` via `clickup_create_task`, status `to do`.

## When a skill says "fetch the relevant ticket"

Use `clickup_get_task` with the task ID, or `clickup_search` / `clickup_filter_tasks` (scoped to list `901520431481`) if only a name or partial description is known.

## Pull requests as a triage surface

Not applicable — ClickUp has no PR concept. Skills that branch on this flag should treat it as **no**.

## Wayfinding operations

Used by `/wayfinder`. Represent the wayfinder **map** and **children** as ClickUp tasks in list `901520431481`:

- **Map**: a task tagged `wayfinder-map`, holding the Notes / Decisions-so-far / Fog body in its description.
- **Child ticket**: a task linked to the map via `clickup_add_task_link` (or, if a strict parent/child hierarchy is wanted, created as a subtask of the map with `parent` set to the map's task ID). Tag children `wayfinder-research` / `wayfinder-prototype` / `wayfinder-grilling` / `wayfinder-task` as appropriate. Once claimed, assign the ticket to the driving dev via `clickup_update_task` (`assignees`).
- **Blocking**: use `clickup_add_task_dependency` with `type: "waiting_on"` on the blocked child, pointing at the blocker. A ticket is unblocked when every blocking dependency is resolved (blocker task status is a `done`/`closed`-type status).
- **Frontier query**: `clickup_filter_tasks` scoped to the map's children (via task links or subtasks), excluding tasks with an open blocking dependency or an existing assignee; first in map order wins.
- **Claim**: `clickup_update_task` to set `assignees: ["me"]`, the session's first write.
- **Resolve**: `clickup_create_comment` with the answer, then `clickup_update_task` to set status `complete` (or `aborted` if abandoned), then append a context pointer to the map's Decisions-so-far.
